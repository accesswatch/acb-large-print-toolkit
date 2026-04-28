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
    "arial",
    "helvetica",
    "verdana",
    "tahoma",
    "trebuchet",
    "calibri",
    "segoe",
    "roboto",
    "open sans",
    "noto sans",
    "liberation sans",
    "dejavu sans",
    "freesans",
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
        result.findings.append(
            Finding(
                rule_id="PDF-TAGGED",
                severity=C.Severity.CRITICAL,
                message=(
                    "PyMuPDF is not installed; PDF audit requires it "
                    "(pip install pymupdf)"
                ),
                auto_fixable=False,
            )
        )
        return result

    doc = fitz.open(str(file_path))
    try:
        _check_metadata(doc, result)
        _check_tagged(doc, result)
        _check_fonts(doc, result)
        image_only_pages = _check_images_of_text(doc, result)
        _check_image_resolution(doc, image_only_pages, result)
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
            "PDF is not tagged; screen readers cannot determine "
            "document structure",
        )


def _check_fonts(doc, result: AuditResult) -> None:
    """Check font sizes and families across all pages."""
    small_font_pages: set[int] = set()
    non_arial_fonts: set[str] = set()
    pages_checked = 0

    for page_num in range(min(doc.page_count, 50)):  # Cap at 50 pages
        page = doc[page_num]
        pages_checked += 1
        blocks = page.get_text(
            "dict", flags=fitz.TEXT_PRESERVE_WHITESPACE
        ).get("blocks", [])

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
                    if not any(
                        font_lower.startswith(p)
                        for p in _SANS_SERIF_PREFIXES
                    ):
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


def _check_images_of_text(doc, result: AuditResult) -> list[int]:
    """Detect pages that appear to be scanned images (no extractable text).

    A page is classified as image-only when it contains at least one image that
    covers 40 % or more of the page area and has no extractable text.  Pages
    with small decorative images (logos, watermarks) alongside real text are
    not flagged.

    Returns the list of 1-based page numbers that were classified as image-only
    so the caller can pass them to the DPI check.
    """
    checked = min(doc.page_count, 50)
    image_only_pages: list[int] = []

    for page_num in range(checked):
        page = doc[page_num]
        text = page.get_text("text").strip()
        if text:
            # Real text present — not an image-only page
            continue

        images = page.get_images()
        if not images:
            continue

        # Require images to cover at least 40 % of the page before flagging.
        # This avoids false positives from pages that contain only a tiny
        # watermark or a blank page with a single pixel image.
        page_area = page.rect.width * page.rect.height
        image_area = 0.0
        try:
            for info in page.get_image_info():
                r = fitz.Rect(info["bbox"])
                image_area += r.width * r.height
        except Exception:
            # Fallback: treat any image presence as sufficient when bbox info
            # is unavailable (older PyMuPDF builds).
            image_area = page_area  # assume full coverage

        if page_area > 0 and (image_area / page_area) >= 0.40:
            image_only_pages.append(page_num + 1)

    if not image_only_pages:
        return image_only_pages

    total = doc.page_count
    pct = int(round(100 * len(image_only_pages) / total))
    pages_str = ", ".join(str(p) for p in image_only_pages[:10])
    if len(image_only_pages) > 10:
        pages_str += f" (and {len(image_only_pages) - 10} more)"

    if len(image_only_pages) >= total * 0.9:
        # Entire document is scanned images
        msg = (
            f"This PDF appears to be entirely scanned (all {total} pages"
            f" are image-only with no extractable text).  Run OCR"
            f" (e.g. Adobe Acrobat 'Recognize Text', Tesseract, or ABBYY"
            f" FineReader) before attempting accessibility remediation."
        )
    elif pct >= 50:
        msg = (
            f"{len(image_only_pages)} of {total} pages ({pct}%) are"
            f" image-only with no extractable text (pages: {pages_str})."
            f"  OCR is required on these pages before screen readers can"
            f" access the content."
        )
    else:
        msg = (
            f"{len(image_only_pages)} page(s) appear to be scanned images"
            f" with no extractable text (pages: {pages_str}).  These pages"
            f" require OCR to become screen-reader accessible."
        )

    result.add("PDF-NO-IMAGES-OF-TEXT", msg)
    return image_only_pages


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


def _check_image_resolution(
    doc, image_only_pages: list[int], result: AuditResult
) -> None:
    """Check DPI of images on image-only pages.

    Images below 150 DPI will produce poor OCR results and cannot be reliably
    remediated.  300 DPI is the recommended minimum for archival-quality OCR.
    Only pages that were already identified as image-only are inspected so that
    small decorative images on text pages are not evaluated.
    """
    if not image_only_pages:
        return

    low_res_pages: list[tuple[int, int]] = []  # (page_num_1based, min_dpi)

    for page_num_1 in image_only_pages:
        page = doc[page_num_1 - 1]
        try:
            infos = page.get_image_info()
        except Exception:
            continue

        for info in infos:
            bbox = fitz.Rect(info["bbox"])
            w_pts = bbox.width
            h_pts = bbox.height
            w_px = info.get("width", 0)
            h_px = info.get("height", 0)
            if w_pts <= 0 or h_pts <= 0 or w_px <= 0 or h_px <= 0:
                continue
            dpi_x = (w_px / w_pts) * 72
            dpi_y = (h_px / h_pts) * 72
            min_dpi = int(min(dpi_x, dpi_y))
            if min_dpi < 150:
                low_res_pages.append((page_num_1, min_dpi))
                break  # one low-res image is enough to flag the page

    if low_res_pages:
        detail = ", ".join(
            f"p.{p} ({d} DPI)" for p, d in low_res_pages[:8]
        )
        if len(low_res_pages) > 8:
            detail += f" (and {len(low_res_pages) - 8} more)"
        result.add(
            "PDF-IMAGE-RESOLUTION",
            f"Scanned pages have low image resolution (below 150 DPI);"
            f" OCR quality will be poor: {detail}."
            f"  Re-scan at 300 DPI or higher.",
        )
