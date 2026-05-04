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

# Bullet characters commonly used as list markers in PDF text
_PDF_BULLET_CHARS = frozenset(
    "\u2022\u2023\u25cf\u25cb\u25e6\u2043\u2219\u00b7\u25aa\u25a0\u25ba"
)


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
    ".ipynb",  # Jupyter notebooks (MarkItDown 0.2+)
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


def _yaml_safe(text: str) -> str:
    """Wrap a string in YAML double-quotes, escaping backslashes and quotes."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _pdf_block_to_markdown(block: dict, body_size: float) -> str:
    """Convert a PyMuPDF text-block dict to a Markdown paragraph or heading.

    Heading level is inferred from the block's maximum font size relative to
    *body_size* (the document's modal body font size).  Bold spans produce
    ``**text**``; italic spans use ``<u>text</u>`` (ACB underline convention).
    Leading bullet-character lines become ``- item`` list entries.

    Args:
        block: PyMuPDF block dict with ``"lines"`` containing ``"spans"``.
        body_size: Modal body font size used to compute the heading-level ratio.

    Returns:
        Markdown string, or empty string when the block has no visible text.
    """
    import re as _re

    lines = block.get("lines", [])
    if not lines:
        return ""

    all_spans = [
        span
        for line in lines
        for span in line.get("spans", [])
        if span.get("text", "").strip()
    ]
    if not all_spans:
        return ""

    max_size = max((s.get("size", 0.0) for s in all_spans), default=0.0)
    ratio = max_size / body_size if body_size > 0 else 1.0

    # Map size ratio to heading level
    if ratio >= 1.4:
        heading_level = 1
    elif ratio >= 1.2:
        heading_level = 2
    elif ratio >= 1.05:
        heading_level = 3
    else:
        heading_level = 0

    if heading_level > 0:
        # Headings: plain text only (no inline markup)
        words = " ".join(
            " ".join(span.get("text", "") for span in line.get("spans", []))
            for line in lines
        ).split()
        return "#" * heading_level + " " + " ".join(words)

    # Body text: preserve bold / italic inline formatting
    result_lines: list[str] = []
    for line in lines:
        parts: list[str] = []
        for span in line.get("spans", []):
            text = span.get("text", "")
            if not text:
                continue
            flags = span.get("flags", 0)
            is_bold = bool(flags & 16)   # PyMuPDF bit 4 = bold
            is_italic = bool(flags & 2)  # PyMuPDF bit 1 = italic
            stripped = text.strip()
            if not stripped:
                parts.append(text)
                continue
            leading = text[: len(text) - len(text.lstrip())]
            trailing = text[len(text.rstrip()):]
            if is_bold:
                parts.append(f"{leading}**{stripped}**{trailing}")
            elif is_italic:
                # ACB toolkit convention: italic → underline
                parts.append(f"{leading}<u>{stripped}</u>{trailing}")
            else:
                parts.append(text)
        result_lines.append("".join(parts))

    full_text = " ".join(result_lines).strip()
    if not full_text:
        return ""

    # Bullet list detection (common PDF bullet characters)
    if full_text[0] in _PDF_BULLET_CHARS:
        return "- " + full_text[1:].lstrip()

    # Numbered list detection (e.g. "1. " or "2) ")
    if _re.match(r"^\d{1,3}[.)]\s", full_text):
        return full_text  # GFM/Pandoc will render this as an ordered list

    return full_text


def _pdf_to_markdown_structured(src_path: Path) -> str | None:
    """Extract a PDF to structured Markdown using PyMuPDF.

    Two-pass extraction:

    **Pass 1 – statistics**: all text spans are scanned to determine the modal
    (most common by character count) body font size.

    **Pass 2 – content**: text blocks are classified as headings (font-size
    ratio ≥ 1.05×), bold/italic inline spans, bullet/numbered list items, or
    plain body paragraphs.  Tables are detected using the ``"lines"`` strategy
    first; if a page has no line-bordered tables the ``"text"`` strategy is
    retried so borderless and lightly-bordered tables are also captured.

    PDF metadata (title, author, subject) is emitted as a YAML front-matter
    block so that downstream Pandoc conversions can set the document title.

    Returns ``None`` when PyMuPDF (``fitz``) is not importable, signalling the
    caller to fall back to MarkItDown's text-only extraction.

    Args:
        src_path: Path to the PDF file.

    Returns:
        Structured Markdown string, or ``None`` if PyMuPDF is unavailable or
        the document cannot be opened.
    """
    from collections import Counter

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

    try:
        # ------------------------------------------------------------
        # YAML front matter from PDF metadata
        # ------------------------------------------------------------
        meta = doc.metadata or {}
        yaml_fields: list[str] = []
        raw_title = (meta.get("title") or "").strip()
        raw_author = (meta.get("author") or "").strip()
        raw_subject = (meta.get("subject") or "").strip()
        if raw_title:
            yaml_fields.append(f"title: {_yaml_safe(raw_title)}")
        if raw_author:
            yaml_fields.append(f"author: {_yaml_safe(raw_author)}")
        if raw_subject:
            yaml_fields.append(f"description: {_yaml_safe(raw_subject)}")
        yaml_fields.append('lang: "en"')
        front_matter = "---\n" + "\n".join(yaml_fields) + "\n---\n\n"

        # ------------------------------------------------------------
        # Pass 1: determine modal body font size
        # ------------------------------------------------------------
        size_counter: Counter = Counter()
        for page in doc:
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        size = span.get("size", 0.0)
                        text = span.get("text", "")
                        if size > 4 and text.strip():
                            size_counter[round(size, 1)] += len(text.strip())

        body_size: float = size_counter.most_common(1)[0][0] if size_counter else 10.0
        log.debug("PDF body font size detected: %.1f pt", body_size)

        # ------------------------------------------------------------
        # Pass 2: extract content with structure
        # ------------------------------------------------------------
        pages_md: list[str] = []

        for page in doc:
            # Table detection: try "lines" (border-based) first; fall back
            # to "text" (position-based) for borderless / lightly bordered tables.
            tables: list = []
            try:
                tf = page.find_tables()
                tables = list(tf.tables) if tf else []
            except Exception:
                tables = []

            if not tables:
                try:
                    tf2 = page.find_tables(strategy="text")
                    tables = list(tf2.tables) if tf2 else []
                    if tables:
                        log.debug(
                            "Page %d: no line-bordered tables; found %d via text strategy",
                            page.number + 1,
                            len(tables),
                        )
                except Exception:
                    tables = []

            # Structured text extraction
            page_dict = page.get_text("dict")
            raw_text_blocks = [
                b for b in page_dict.get("blocks", []) if b.get("type") == 0
            ]

            items: list[tuple[float, str, object]] = []
            for block in raw_text_blocks:
                bbox = block.get("bbox", (0.0, 0.0, 0.0, 0.0))
                bx0, by0, bx1, by1 = bbox
                # Skip text inside table bounding boxes to avoid duplicate content
                if any(
                    _bbox_overlaps_table((bx0, by0, bx1, by1), tbl.bbox)
                    for tbl in tables
                ):
                    continue
                items.append((by0, "block", block))

            for tbl in tables:
                items.append((tbl.bbox[1], "table", tbl))

            # Sort in reading order (top-to-bottom)
            items.sort(key=lambda x: x[0])

            page_parts: list[str] = []
            for _, kind, content in items:
                if kind == "table":
                    md_table = _format_table_as_markdown(content)  # type: ignore[arg-type]
                    if md_table:
                        page_parts.append(md_table)
                else:
                    md_block = _pdf_block_to_markdown(content, body_size)  # type: ignore[arg-type]
                    if md_block:
                        page_parts.append(md_block)

            if page_parts:
                pages_md.append("\n\n".join(page_parts))

        return front_matter + "\n\n".join(pages_md)

    finally:
        doc.close()


def _docx_mammoth_fallback(src_path: Path) -> str:
    """Extract Markdown from a DOCX via mammoth when MarkItDown returns empty text.

    Handles non-standard OOXML structures produced by some third-party tools
    (e.g. Google Workspace add-ins, Strict Open XML schema) that python-docx /
    MarkItDown may not traverse correctly.

    Args:
        src_path: Path to the .docx file.

    Returns:
        Markdown string (may be empty if mammoth also finds no content).
    """
    try:
        import mammoth  # type: ignore[import-untyped]
    except ImportError:
        log.debug("mammoth not available; skipping DOCX fallback extraction")
        return ""

    try:
        with open(src_path, "rb") as fh:
            result = mammoth.convert_to_markdown(fh)
        text = result.value or ""
        if text.strip():
            log.info(
                "mammoth fallback succeeded for %s (%d chars)", src_path.name, len(text)
            )
        else:
            log.warning(
                "mammoth fallback also returned empty text for %s", src_path.name
            )
        return text
    except Exception as exc:
        log.warning("mammoth fallback failed for %s: %s", src_path.name, exc)
        return ""


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

    # For PDFs, attempt structured extraction via PyMuPDF first.
    # This preserves table structure, headings, bold text, and metadata so
    # downstream conversions (e.g. to Word or HTML via Pandoc) retain structure.
    if ext == ".pdf":
        text = _pdf_to_markdown_structured(src_path)
        if text is not None:
            output_path.write_text(text, encoding="utf-8")
            log.info(
                "PDF structured extraction complete: %s -> %s (%d characters)",
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

    # For DOCX files: when MarkItDown returns empty text, fall back to mammoth.
    # Mammoth handles non-standard OOXML structures (Strict Open XML schema,
    # SDT-heavy documents, Google Workspace add-in output) that python-docx /
    # MarkItDown may not traverse correctly.
    if ext == ".docx" and not text.strip():
        log.info(
            "MarkItDown returned empty for %s; trying mammoth fallback", src_path.name
        )
        fallback = _docx_mammoth_fallback(src_path)
        if fallback.strip():
            text = fallback

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
