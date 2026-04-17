"""Convert documents to Markdown using MarkItDown.

Wraps Microsoft's MarkItDown library for document-to-markdown conversion.
Supports: .docx, .xlsx, .pptx, .pdf, .html, .csv, .json, .xml, .epub, .zip.

Audio transcription (.mp3, .wav, .m4a, .ogg, .flac, .aac, .opus) is handled
by whisper_convert() using faster-whisper (local CPU inference via CTranslate2).
Audio is never sent to any external service.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("acb_large_print")

# File extensions MarkItDown can convert (no audio -- handled by whisper_convert)
CONVERTIBLE_EXTENSIONS = {
    ".docx",
    ".xlsx",
    ".xls",
    ".pptx",
    ".pdf",
    ".html",
    ".htm",
    ".csv",
    ".json",
    ".xml",
    ".epub",
    ".zip",
    # Image files (new in MarkItDown 0.2+, with optional LLM for descriptions)
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".tiff",
}

# Audio file extensions handled by faster-whisper
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".opus"}

# YouTube URL patterns (regex strings for detection)
_YOUTUBE_URL_PATTERNS = (
    r"https?://(?:www\.)?youtube\.com/watch\?v=",
    r"https?://youtu\.be/",
    r"https?://(?:www\.)?youtube\.com/playlist\?list=",
)


def convert_with_llm_descriptions(
    src_path: Path,
    output_path: Path | None = None,
    *,
    llm_client=None,
    llm_model: str | None = None,
    llm_prompt: str | None = None,
) -> tuple[Path, str]:
    """Convert a document (esp. PPTX/images) to Markdown with LLM image descriptions.

    Uses MarkItDown with a language model to generate alt text for images in
    PowerPoints and image files. The LLM runs entirely on this server (typically
    Ollama/Llama3 via acb_large_print.ai_provider).

    Args:
        src_path: Path to input file (PPTX or image).
        output_path: Optional output path. Defaults to same stem + .md.
        llm_client: Initialized LLM client (e.g., OpenAI-compatible, or custom).
        llm_model: Model name (e.g. "gpt-4o" or from Ollama).
        llm_prompt: Optional custom system prompt for image descriptions.
            Defaults to a WCAG/accessibility-focused prompt.

    Returns:
        (output_path, markdown_text)

    Raises:
        FileNotFoundError: If src_path does not exist.
        ValueError: If the extension is not supported.
        RuntimeError: If MarkItDown is not installed.
    """
    src_path = Path(src_path)
    if not src_path.exists():
        raise FileNotFoundError(f"File not found: {src_path}")

    ext = src_path.suffix.lower()
    if ext not in CONVERTIBLE_EXTENSIONS:
        raise ValueError(
            f"Cannot convert '{ext}' files. "
            f"Supported: {', '.join(sorted(CONVERTIBLE_EXTENSIONS))}"
        )

    try:
        from markitdown import MarkItDown  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "MarkItDown is not installed. "
            "Install it with: pip install 'markitdown[all]'"
        ) from exc

    if output_path is None:
        output_path = src_path.with_suffix(".md")
    else:
        output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use LLM for image descriptions if provided
    default_prompt = (
        "You are an accessibility specialist. Generate a concise, descriptive alt text "
        "for this image that conveys its purpose and content to a visually impaired user. "
        "Keep it under 125 words. Be specific. Do not say 'This is a screenshot' or 'This "
        "is an image' -- describe what the image shows."
    )
    prompt = llm_prompt or default_prompt

    md = MarkItDown(
        enable_plugins=False,
        llm_client=llm_client,
        llm_model=llm_model,
        llm_prompt=prompt,
    )

    log.info(
        "Converting %s -> %s (with LLM image descriptions: %s)",
        src_path.name,
        output_path.name,
        "yes" if llm_client else "no",
    )

    result = md.convert(str(src_path))
    text = result.text_content or ""

    output_path.write_text(text, encoding="utf-8")
    log.info("Conversion complete: %d characters written", len(text))

    return output_path, text


def youtube_to_markdown(
    url: str,
    output_path: Path | None = None,
) -> tuple[Path | None, str]:
    """Fetch YouTube transcript and convert to Markdown.

    Uses MarkItDown to fetch and convert YouTube transcripts. The transcript is
    YouTube's own caption data, not generated locally.

    Args:
        url: YouTube URL (watch, youtu.be, or playlist link).
        output_path: Optional output path. Defaults to a temp .md file.

    Returns:
        (output_path, markdown_text) or (None, text) if output_path not specified.

    Raises:
        ValueError: If the URL is not a valid YouTube link.
        RuntimeError: If MarkItDown is not installed or transcript fetch fails.
    """
    import re

    url = url.strip()
    if not any(re.match(pattern, url) for pattern in _YOUTUBE_URL_PATTERNS):
        raise ValueError(
            f"'{url}' is not a valid YouTube URL. "
            "Supported: youtube.com/watch?v=..., youtu.be/..., youtube.com/playlist?list=..."
        )

    try:
        from markitdown import MarkItDown  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "MarkItDown is not installed. "
            "Install it with: pip install 'markitdown[all]'"
        ) from exc

    if output_path is None:
        from tempfile import NamedTemporaryFile
        # Create a temp file without closing it (will be written to)
        temp = NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        temp.close()
        output_path = Path(temp.name)
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Fetching YouTube transcript: %s", url)

    md = MarkItDown(enable_plugins=False)
    result = md.convert(url)
    text = result.text_content or ""

    if output_path:
        output_path.write_text(text, encoding="utf-8")
        log.info("YouTube transcript saved: %d characters", len(text))
        return output_path, text
    else:
        return None, text


def convert_to_markdown(
    src_path: Path,
    output_path: Path | None = None,
) -> tuple[Path, str]:
    """Convert a document to Markdown.

    Args:
        src_path: Path to input file.
        output_path: Optional path for the .md file.  Defaults to same
            directory / stem as *src_path* with ``.md`` extension.

    Returns:
        (output_path, markdown_text)

    Raises:
        FileNotFoundError: If *src_path* does not exist.
        ValueError: If the extension is not in CONVERTIBLE_EXTENSIONS.
        RuntimeError: If MarkItDown is not installed or conversion fails.
    """
    src_path = Path(src_path)
    if not src_path.exists():
        raise FileNotFoundError(f"File not found: {src_path}")

    ext = src_path.suffix.lower()
    if ext not in CONVERTIBLE_EXTENSIONS:
        raise ValueError(
            f"Cannot convert '{ext}' files. "
            f"Supported: {', '.join(sorted(CONVERTIBLE_EXTENSIONS))}"
        )

    try:
        from markitdown import MarkItDown  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "MarkItDown is not installed. "
            "Install it with: pip install 'markitdown[pdf,docx,xlsx,pptx]'"
        ) from exc

    if output_path is None:
        output_path = src_path.with_suffix(".md")
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Converting %s -> %s", src_path.name, output_path.name)

    md = MarkItDown(enable_plugins=False)
    result = md.convert(str(src_path))
    text = result.text_content or ""

    output_path.write_text(text, encoding="utf-8")
    log.info("Conversion complete: %d characters written", len(text))

    return output_path, text


# ---------------------------------------------------------------------------
# BITS Whisperer -- on-server audio transcription via faster-whisper
# ---------------------------------------------------------------------------

#: Default Whisper model used by BITS Whisperer.  "medium" gives the best
#: accuracy-to-speed trade-off on a 10-core / 12 GB CPU server.  Override
#: via the ``WHISPER_MODEL`` environment variable (e.g. "small", "large-v3").
WHISPER_DEFAULT_MODEL = "medium"


def whisper_available() -> bool:
    """Return True if faster-whisper is installed."""
    try:
        import faster_whisper  # noqa: F401  # type: ignore[import-untyped]
        return True
    except ImportError:
        return False


def whisper_convert(
    src_path: Path,
    output_path: Path | None = None,
    *,
    model: str | None = None,
    language: str | None = None,
    output_format: str = "markdown",
) -> tuple[Path, str]:
    """Transcribe an audio file to Markdown (or plain text) using BITS Whisperer.

    BITS Whisperer runs entirely on the GLOW server using the faster-whisper
    library (CTranslate2 backend).  Audio is **never** sent to any external
    service.

    Supported inputs: .mp3, .wav, .m4a, .ogg, .flac, .aac, .opus
    Supported output formats: "markdown" (default, .md) or "text" (.txt)

    The transcription is structured as ACB-compliant Markdown:
      - An H1 heading derived from the filename
      - One paragraph per segment (natural speech pauses)
      - No italic, no bold emphasis -- plain prose

    Args:
        src_path: Path to the audio file.
        output_path: Optional output path.  Defaults to same directory / stem
            with ``.md`` (or ``.txt``) extension.
        model: Whisper model name.  Defaults to ``WHISPER_DEFAULT_MODEL``
            ("medium") or the ``WHISPER_MODEL`` environment variable.
        language: BCP-47 language code (e.g. "en", "es").  If None,
            faster-whisper auto-detects from the first 30 seconds.
        output_format: "markdown" (default) or "text".

    Returns:
        (output_path, transcription_text)

    Raises:
        FileNotFoundError: If src_path does not exist.
        ValueError: If the extension is not an audio format.
        RuntimeError: If faster-whisper is not installed or transcription fails.
    """
    import os

    src_path = Path(src_path)
    if not src_path.exists():
        raise FileNotFoundError(f"Audio file not found: {src_path}")

    ext = src_path.suffix.lower()
    if ext not in AUDIO_EXTENSIONS:
        raise ValueError(
            f"'{ext}' is not a supported audio format. "
            f"Supported: {', '.join(sorted(AUDIO_EXTENSIONS))}"
        )

    try:
        from faster_whisper import WhisperModel  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. "
            "Install it with: pip install faster-whisper"
        ) from exc

    # Resolve model: argument > env var > default
    resolved_model = model or os.environ.get("WHISPER_MODEL", WHISPER_DEFAULT_MODEL)

    suffix = ".txt" if output_format == "text" else ".md"
    if output_path is None:
        output_path = src_path.with_suffix(suffix)
    else:
        output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(
        "BITS Whisperer: transcribing %s with model=%s language=%s",
        src_path.name,
        resolved_model,
        language or "auto-detect",
    )

    # Load model (int8 quantisation for CPU -- 4x faster than float32, same accuracy)
    whisper = WhisperModel(resolved_model, device="cpu", compute_type="int8")
    segments, info = whisper.transcribe(
        str(src_path),
        language=language,
        beam_size=5,
        vad_filter=True,          # skip silent gaps automatically
        vad_parameters={"min_silence_duration_ms": 500},
    )

    log.info(
        "Detected language: %s (probability %.2f)",
        info.language,
        info.language_probability,
    )

    # Collect segments into paragraphs
    segment_texts: list[str] = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            segment_texts.append(text)

    title = src_path.stem.replace("-", " ").replace("_", " ").title()

    if output_format == "text":
        body = "\n\n".join(segment_texts)
        full_text = body
    else:
        # ACB-compliant Markdown: H1 title, one paragraph per segment
        paragraphs = "\n\n".join(segment_texts)
        full_text = f"# {title}\n\n{paragraphs}\n"

    output_path.write_text(full_text, encoding="utf-8")
    log.info(
        "BITS Whisperer: transcription complete -- %d segments, %d characters",
        len(segment_texts),
        len(full_text),
    )

    return output_path, full_text
