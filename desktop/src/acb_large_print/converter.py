"""Convert documents to Markdown using MarkItDown.

Wraps Microsoft's MarkItDown library for document-to-markdown conversion.
Supports: .docx, .xlsx, .pptx, .pdf, .html, .csv, .json, .xml, .epub, .zip.

Audio transcription (.mp3, .wav, .m4a, .ogg, .flac, .aac, .opus) is handled
by whisper_convert() using faster-whisper (local CPU inference via CTranslate2).
Audio is never sent to any external service.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger("acb_large_print")

# Fraction of a text block's area that must overlap with a table's bounding box
# before the text block is considered part of the table (and excluded from the
# separate prose output to avoid duplication).
_TABLE_OVERLAP_THRESHOLD = 0.4


def _resolve_whisper_cache_dir() -> Path:
    """Return a writable cache directory for Whisper/Hugging Face assets."""
    cache_root = (
        os.environ.get("HUGGINGFACE_HUB_CACHE")
        or os.environ.get("HF_HOME")
        or os.environ.get("XDG_CACHE_HOME")
    )
    if cache_root:
        cache_dir = Path(cache_root)
    else:
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

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


def _bbox_overlaps_table(text_bbox: tuple, table_bbox: tuple) -> bool:
    """Return True if a text block's bounding box substantially overlaps a table's.

    Used to avoid double-emitting text that PyMuPDF also returns via
    find_tables().  A text block is considered "inside" the table when more
    than 40 % of its area intersects the table bounding box.
    """
    tx0, ty0, tx1, ty1 = text_bbox
    tbx0, tby0, tbx1, tby1 = table_bbox

    ix0 = max(tx0, tbx0)
    iy0 = max(ty0, tby0)
    ix1 = min(tx1, tbx1)
    iy1 = min(ty1, tby1)

    if ix1 <= ix0 or iy1 <= iy0:
        return False  # no intersection

    intersection_area = (ix1 - ix0) * (iy1 - iy0)
    text_area = (tx1 - tx0) * (ty1 - ty0)
    if text_area <= 0:
        return False

    return (intersection_area / text_area) > _TABLE_OVERLAP_THRESHOLD


def _format_table_as_markdown(table) -> str:
    """Format a PyMuPDF Table object as a Markdown pipe table.

    Returns an empty string when the table contains no usable content.
    Pipe characters inside cell content are escaped so they do not break
    the Markdown table syntax.
    """
    rows = table.extract()
    if not rows:
        return ""

    cleaned_rows: list[list[str]] = []
    for row in rows:
        cleaned_row = [
            (cell or "").strip().replace("\n", " ").replace("|", "\\|")
            for cell in row
        ]
        cleaned_rows.append(cleaned_row)

    if not cleaned_rows:
        return ""

    num_cols = max(len(row) for row in cleaned_rows)
    if num_cols == 0:
        return ""

    # Pad every row to the full column count
    padded = [row + [""] * (num_cols - len(row)) for row in cleaned_rows]

    lines: list[str] = []
    lines.append("| " + " | ".join(padded[0]) + " |")
    lines.append("| " + " | ".join(["---"] * num_cols) + " |")
    for row in padded[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def _pdf_to_markdown_with_tables(src_path: Path) -> str | None:
    """Extract a PDF to Markdown, preserving table structure via PyMuPDF.

    Uses PyMuPDF's ``Page.find_tables()`` to detect tables and render them as
    Markdown pipe tables.  Non-table text is extracted in reading order
    (top-to-bottom, left-to-right) and interleaved with the table Markdown.

    Returns ``None`` when PyMuPDF (``fitz``) is not importable, signalling the
    caller to fall back to MarkItDown's text-only extraction.

    Args:
        src_path: Path to the PDF file.

    Returns:
        Markdown string with table structure preserved, or ``None`` if PyMuPDF
        is unavailable or the document cannot be opened.
    """
    try:
        import fitz  # type: ignore[import-untyped]  # PyMuPDF
    except ImportError:
        log.info("PyMuPDF (fitz) not available; will use MarkItDown for PDF extraction")
        return None

    try:
        doc = fitz.open(str(src_path))
    except Exception as exc:
        log.warning(
            "PyMuPDF could not open %s (%s); falling back to MarkItDown",
            src_path.name,
            exc,
        )
        return None

    pages_md: list[str] = []

    try:
        for page in doc:
            try:
                tbl_finder = page.find_tables()
                tables = list(tbl_finder.tables) if tbl_finder else []
            except Exception:
                tables = []

            if not tables:
                text = page.get_text("text").strip()
                if text:
                    pages_md.append(text)
                continue

            # Collect text blocks (block_type 0 = text, 1 = image)
            raw_blocks = page.get_text("blocks")
            text_blocks = [b for b in raw_blocks if b[6] == 0]

            # Build a list of (top_y, kind, content) for sorting into reading order
            items: list[tuple[float, str, object]] = []

            for block in text_blocks:
                bx0, by0, bx1, by1, block_text, _, _ = block
                block_text = block_text.strip()
                if not block_text:
                    continue
                # Skip text that lives inside a table's bounding box to avoid
                # duplicate content – find_tables() already captures it.
                if any(
                    _bbox_overlaps_table((bx0, by0, bx1, by1), tbl.bbox)
                    for tbl in tables
                ):
                    continue
                items.append((by0, "text", block_text))

            for tbl in tables:
                items.append((tbl.bbox[1], "table", tbl))

            # Sort in reading order: top-to-bottom (primary), left-to-right (secondary)
            items.sort(key=lambda x: x[0])

            page_parts: list[str] = []
            for _, kind, content in items:
                if kind == "text":
                    page_parts.append(str(content))
                else:
                    md_table = _format_table_as_markdown(content)
                    if md_table:
                        page_parts.append(md_table)

            if page_parts:
                pages_md.append("\n\n".join(page_parts))
    finally:
        doc.close()

    return "\n\n".join(pages_md)


def convert_to_markdown(
    src_path: Path,
    output_path: Path | None = None,
) -> tuple[Path, str]:
    """Convert a document to Markdown.

    For PDF files, PyMuPDF's table-detection is attempted first so that tables
    embedded in the PDF are preserved as Markdown pipe tables.  This ensures
    that a subsequent PDF → Word (or PDF → HTML) conversion via Pandoc retains
    the table structure.  If PyMuPDF is not installed the conversion falls back
    to MarkItDown's text-only extraction.

    For all other supported formats MarkItDown is used directly.

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

    if output_path is None:
        output_path = src_path.with_suffix(".md")
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # For PDFs, attempt table-aware extraction via PyMuPDF first.
    # This preserves table structure as Markdown pipe tables so that downstream
    # conversions (e.g. to Word or HTML via Pandoc) include the tables.
    if ext == ".pdf":
        text = _pdf_to_markdown_with_tables(src_path)
        if text is not None:
            output_path.write_text(text, encoding="utf-8")
            log.info(
                "PDF table-aware extraction complete: %s -> %s (%d characters)",
                src_path.name,
                output_path.name,
                len(text),
            )
            return output_path, text
        log.info("PyMuPDF unavailable; using MarkItDown for PDF extraction")

    try:
        from markitdown import MarkItDown  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "MarkItDown is not installed. "
            "Install it with: pip install 'markitdown[pdf,docx,xlsx,pptx]'"
        ) from exc

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
    progress_callback: "Callable[[int, str], None] | None" = None,
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
    from typing import Callable

    callback: Callable[[int, str], None] | None = progress_callback

    def _emit_progress(percent: int, message: str) -> None:
        if callback is None:
            return
        try:
            callback(max(0, min(100, int(percent))), message)
        except Exception:
            # Progress reporting must never break transcription.
            pass

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
    _emit_progress(2, "Initializing Whisper model...")

    try:
        # Load model (int8 quantisation for CPU -- 4x faster than float32, same accuracy)
        whisper = WhisperModel(
            resolved_model,
            device="cpu",
            compute_type="int8",
            download_root=str(_resolve_whisper_cache_dir()),
        )
        _emit_progress(5, "Model ready. Beginning transcription...")
        segments, info = whisper.transcribe(
            str(src_path),
            language=language,
            beam_size=5,
            vad_filter=True,          # skip silent gaps automatically
            vad_parameters={"min_silence_duration_ms": 500},
        )
    except Exception as exc:
        log.exception("BITS Whisperer: transcription failed for %s", src_path.name)
        exc_text = str(exc).lower()
        if (
            "not enough space on the disk" in exc_text
            or "no space left on device" in exc_text
            or "os error 112" in exc_text
        ):
            raise RuntimeError(
                "The server does not have enough free disk space to load the Whisper model right now. "
                "Please try again later or contact the administrator."
            ) from exc
        if "snapshot_download" in exc_text or "huggingface" in exc_text or "cas service error" in exc_text:
            raise RuntimeError(
                "The server could not load the Whisper model required for transcription. "
                "Please try again later or contact the administrator."
            ) from exc
        # Pass through the actual exception message for any other transcription failure
        raise RuntimeError(str(exc)) from exc

    log.info(
        "Detected language: %s (probability %.2f)",
        info.language,
        info.language_probability,
    )

    # Collect segments into paragraphs
    segment_texts: list[str] = []
    last_progress = 5
    duration = float(getattr(info, "duration", 0.0) or 0.0)
    for seg in segments:
        text = seg.text.strip()
        if text:
            segment_texts.append(text)

        # Use Whisper's decoded segment end time against total duration for
        # real model progress. Falls back to incremental updates if duration is
        # unavailable.
        if duration > 0:
            seg_end = float(getattr(seg, "end", 0.0) or 0.0)
            progress = max(last_progress, min(95, int((seg_end / duration) * 95)))
        else:
            progress = min(95, last_progress + 1)

        if progress > last_progress:
            last_progress = progress
            _emit_progress(progress, f"Transcribing audio... {progress}%")

    title = src_path.stem.replace("-", " ").replace("_", " ").title()

    if output_format == "text":
        body = "\n\n".join(segment_texts)
        full_text = body
    else:
        # ACB-compliant Markdown: H1 title, one paragraph per segment
        paragraphs = "\n\n".join(segment_texts)
        full_text = f"# {title}\n\n{paragraphs}\n"

    try:
        output_path.write_text(full_text, encoding="utf-8")
    except OSError as exc:
        log.exception("BITS Whisperer: failed writing transcript for %s", src_path.name)
        raise RuntimeError(
            "The transcript could not be written to temporary storage. Please try again."
        ) from exc
    _emit_progress(100, "Transcription complete.")
    log.info(
        "BITS Whisperer: transcription complete -- %d segments, %d characters",
        len(segment_texts),
        len(full_text),
    )

    return output_path, full_text
