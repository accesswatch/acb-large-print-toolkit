"""Convert documents to Markdown using MarkItDown.

Wraps Microsoft's MarkItDown library for document-to-markdown conversion.
Supports: .docx, .xlsx, .pptx, .pdf, .html, .csv, .json, .xml, .epub, .zip.
Audio files (.mp3, .wav) are NOT supported in server mode (privacy: requires
sending audio to external transcription APIs).
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("acb_large_print")

# File extensions MarkItDown can convert (no audio -- see module docstring)
CONVERTIBLE_EXTENSIONS = {
    ".docx", ".xlsx", ".xls", ".pptx", ".pdf",
    ".html", ".htm",
    ".csv", ".json", ".xml",
    ".epub", ".zip",
}


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
