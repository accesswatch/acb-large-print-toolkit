"""Audit PDF files for ACB Large Print and WCAG accessibility compliance.

Uses PyMuPDF (fitz) to extract metadata, structure, and font information.
Falls back gracefully if PyMuPDF is not installed.
"""

from __future__ import annotations

from pathlib import Path

from . import constants as C
from .auditor import AuditResult, Finding

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


# Known sans-serif font families (lowercase, prefix match)
_SANS_SERIF_PREFIXES = (
    "arial", "helvetica", "verdana", "tahoma", "trebuchet",
    "calibri", "segoe", "roboto", "open sans", "noto sans",
    "liberation sans", "dejavu sans", "freesans",
)


def audit_pdf(file_path: str | Path) -> AuditResult:
    """Audit a PDF file for accessibility issues.

    Returns an AuditResult compatible with the existing audit pipeline.
    Requires PyMuPDF (fitz) for full analysis; returns a single finding
    if the library is not available.
    """
    file_path = Path(file_path)
    result = AuditResult(file_path=str(file_path))

    if not HAS_PYMUPDF:
        result.findings.append(Finding(
            rule_id="PDF-TAGGED",
            severity=C.Severity.CRITICAL,
            message="PyMuPDF is not installed; PDF audit requires it (pip install pymupdf)",
            auto_fixable=False,
        ))
        return result

    doc = fitz.open(str(file_path))
    try:
        _check_metadata(doc, result)
        _check_tagged(doc, result)
        _check_fonts(doc, result)
        _check_images_of_text(doc, result)
        _check_bookmarks(doc, result)
    finally:
        doc.close()

    return result


def _check_metadata(doc, result: AuditResult) -> None:
    """Check document title and language metadata."""
    metadata = doc.metadata or {}

    title = (metadata.get("title") or "").strip()
    if not title:
        result.add(
            "PDF-TITLE",
            "PDF has no title set in document metadata",
        )

    # PDF language is stored in the catalog, not standard metadata
    # Try to get it from the catalog /Lang entry
    lang = ""
    try:
        catalog = doc.pdf_catalog()
        if catalog:
            # fitz returns catalog as xref; read the /Lang value
            lang_val = doc.xref_get_key(catalog, "Lang")
            if lang_val and lang_val[0] != "null":
                lang = lang_val[1].strip("()")
    except Exception:
        pass

    if not lang:
        result.add(
            "PDF-LANGUAGE",
            "PDF has no language set in document metadata",
        )


def _check_tagged(doc, result: AuditResult) -> None:
    """Check if the PDF is tagged (has a structure tree)."""
    is_tagged = False
    try:
        catalog = doc.pdf_catalog()
        if catalog:
            mark_info = doc.xref_get_key(catalog, "MarkInfo")
            if mark_info and mark_info[0] != "null":
                is_tagged = "true" in mark_info[1].lower()
    except Exception:
        pass

    if not is_tagged:
        result.add(
            "PDF-TAGGED",
            "PDF is not tagged; screen readers cannot determine document structure",
        )


def _check_fonts(doc, result: AuditResult) -> None:
    """Check font sizes and families across all pages."""
    small_font_pages: set[int] = set()
    non_arial_fonts: set[str] = set()
    pages_checked = 0

    for page_num in range(min(doc.page_count, 50)):  # Cap at 50 pages
        page = doc[page_num]
        pages_checked += 1
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE).get("blocks", [])

        for block in blocks:
            if block.get("type") != 0:  # text blocks only
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = span.get("size", 0)
                    font = span.get("font", "")
                    text = span.get("text", "").strip()

                    if not text:
                        continue

                    # Font size check (allow small tolerance for PDF rounding)
                    if size < C.MIN_SIZE_PT - 0.5 and size > 4:
                        small_font_pages.add(page_num + 1)

                    # Font family check
                    font_lower = font.lower()
                    if not any(font_lower.startswith(p) for p in _SANS_SERIF_PREFIXES):
                        if font_lower and len(text) > 2:  # Skip tiny fragments
                            non_arial_fonts.add(font)

    if small_font_pages:
        pages_str = ", ".join(str(p) for p in sorted(small_font_pages)[:10])
        if len(small_font_pages) > 10:
            pages_str += f" (and {len(small_font_pages) - 10} more)"
        result.add(
            "PDF-FONT-SIZE",
            f"Text smaller than 18pt found on pages: {pages_str}",
        )

    if non_arial_fonts:
        fonts_str = ", ".join(sorted(non_arial_fonts)[:5])
        if len(non_arial_fonts) > 5:
            fonts_str += f" (and {len(non_arial_fonts) - 5} more)"
        result.add(
            "PDF-FONT-FAMILY",
            f"Non-sans-serif fonts found: {fonts_str}",
        )


def _check_images_of_text(doc, result: AuditResult) -> None:
    """Detect pages that appear to be scanned images (no extractable text)."""
    image_only_pages: list[int] = []

    for page_num in range(min(doc.page_count, 50)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        images = page.get_images()

        # Page has images but no extractable text -> likely scanned
        if images and not text:
            image_only_pages.append(page_num + 1)

    if image_only_pages:
        pages_str = ", ".join(str(p) for p in image_only_pages[:10])
        if len(image_only_pages) > 10:
            pages_str += f" (and {len(image_only_pages) - 10} more)"
        result.add(
            "PDF-NO-IMAGES-OF-TEXT",
            f"Scanned or image-only pages with no extractable text: {pages_str}",
        )


def _check_bookmarks(doc, result: AuditResult) -> None:
    """Check for bookmarks in multi-page PDFs."""
    if doc.page_count <= 2:
        return  # Short docs don't need bookmarks

    toc = doc.get_toc()
    if not toc:
        result.add(
            "PDF-BOOKMARKS",
            f"PDF has {doc.page_count} pages but no bookmarks for navigation",
        )
