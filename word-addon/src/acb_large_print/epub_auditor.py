"""Audit ePub files for ACB Large Print and WCAG accessibility compliance.

Uses Pandoc to extract HTML content for structural checks (headings, alt text,
tables, links) and parses the OPF metadata directly via XML for metadata checks
(title, language, navigation, accessibility metadata).

Falls back gracefully if Pandoc is not installed (metadata-only audit).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path

from . import constants as C
from .auditor import AuditResult, Finding


# Namespaces used in OPF files
_OPF_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "meta": "http://www.idpf.org/2007/opf",
}

# Ambiguous link text patterns (lowercase)
_AMBIGUOUS_LINK_RE = re.compile(
    r"^(click here|here|link|read more|learn more|more|more info|details|this|download)$",
    re.IGNORECASE,
)

# URL-like pattern
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


class _HTMLStructureParser(HTMLParser):
    """Lightweight HTML parser to extract headings, images, tables, and links."""

    def __init__(self):
        super().__init__()
        self.headings: list[int] = []  # heading levels in order
        self.images_without_alt: int = 0
        self.images_total: int = 0
        self.tables_without_headers: int = 0
        self.tables_total: int = 0
        self.ambiguous_links: list[str] = []
        self._in_table = False
        self._table_has_th = False
        self._in_link = False
        self._link_text = ""
        self._in_heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()

        # Headings
        if tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag_lower[1])
            self.headings.append(level)
            self._in_heading = True

        # Images
        elif tag_lower == "img":
            self.images_total += 1
            attr_dict = dict(attrs)
            alt = attr_dict.get("alt")
            if alt is None or alt.strip() == "":
                self.images_without_alt += 1

        # Tables
        elif tag_lower == "table":
            self._in_table = True
            self._table_has_th = False
            self.tables_total += 1
        elif tag_lower == "th" and self._in_table:
            self._table_has_th = True

        # Links
        elif tag_lower == "a":
            self._in_link = True
            self._link_text = ""

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower == "table" and self._in_table:
            if not self._table_has_th:
                self.tables_without_headers += 1
            self._in_table = False
        elif tag_lower == "a" and self._in_link:
            self._in_link = False
            text = self._link_text.strip()
            if text and (_AMBIGUOUS_LINK_RE.match(text) or _URL_RE.match(text)):
                self.ambiguous_links.append(text[:80])
        elif tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        if self._in_link:
            self._link_text += data


def audit_epub(file_path: str | Path) -> AuditResult:
    """Audit an ePub file for accessibility issues.

    Returns an AuditResult compatible with the existing audit pipeline.
    Checks OPF metadata directly (always available) and uses Pandoc for
    structural HTML analysis when installed.
    """
    file_path = Path(file_path)
    result = AuditResult(file_path=str(file_path))

    # Phase 1: OPF metadata checks (no external dependencies)
    _check_opf_metadata(file_path, result)

    # Phase 2: Structural checks via Pandoc HTML extraction
    _check_html_structure(file_path, result)

    return result


def _check_opf_metadata(file_path: Path, result: AuditResult) -> None:
    """Parse the ePub OPF file to check metadata."""
    try:
        with zipfile.ZipFile(str(file_path), "r") as zf:
            # Find the OPF file via the container.xml
            opf_path = _find_opf_path(zf)
            if not opf_path:
                return

            opf_xml = zf.read(opf_path).decode("utf-8", errors="replace")
            root = ET.fromstring(opf_xml)

            _check_title(root, result)
            _check_language(root, result)
            _check_nav_document(root, zf, opf_path, result)
            _check_accessibility_metadata(root, result)
    except (zipfile.BadZipFile, ET.ParseError, KeyError, OSError):
        # If we can't parse the ePub at all, still continue with Pandoc checks
        pass


def _find_opf_path(zf: zipfile.ZipFile) -> str | None:
    """Locate the OPF file inside the ePub ZIP."""
    try:
        container = zf.read("META-INF/container.xml").decode("utf-8", errors="replace")
        root = ET.fromstring(container)
        # container namespace
        ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
        rootfile = root.find(".//c:rootfile", ns)
        if rootfile is not None:
            return rootfile.get("full-path")
    except (KeyError, ET.ParseError):
        pass

    # Fallback: look for any .opf file
    for name in zf.namelist():
        if name.lower().endswith(".opf"):
            return name
    return None


def _check_title(root: ET.Element, result: AuditResult) -> None:
    """Check for dc:title in OPF metadata."""
    title_el = root.find(".//{http://purl.org/dc/elements/1.1/}title")
    if title_el is None or not (title_el.text or "").strip():
        result.add(
            "EPUB-TITLE",
            "ePub has no title set in OPF metadata",
        )


def _check_language(root: ET.Element, result: AuditResult) -> None:
    """Check for dc:language in OPF metadata."""
    lang_el = root.find(".//{http://purl.org/dc/elements/1.1/}language")
    if lang_el is None or not (lang_el.text or "").strip():
        result.add(
            "EPUB-LANGUAGE",
            "ePub has no language set in OPF metadata",
        )


def _check_nav_document(
    root: ET.Element,
    zf: zipfile.ZipFile,
    opf_path: str,
    result: AuditResult,
) -> None:
    """Check for a navigation document (EPUB 3 nav or EPUB 2 NCX)."""
    ns_opf = "http://www.idpf.org/2007/opf"

    # EPUB 3: look for item with properties="nav"
    manifest = root.find(f"{{{ns_opf}}}manifest")
    if manifest is not None:
        for item in manifest.findall(f"{{{ns_opf}}}item"):
            props = item.get("properties", "")
            if "nav" in props.split():
                return  # Has EPUB 3 nav document

    # EPUB 2: look for NCX in spine toc attribute or manifest
    spine = root.find(f"{{{ns_opf}}}spine")
    if spine is not None:
        toc_id = spine.get("toc")
        if toc_id and manifest is not None:
            ncx_item = manifest.find(f"{{{ns_opf}}}item[@id='{toc_id}']")
            if ncx_item is not None:
                return  # Has NCX

    # Check manifest for any NCX media type
    if manifest is not None:
        for item in manifest.findall(f"{{{ns_opf}}}item"):
            media_type = item.get("media-type", "")
            if media_type == "application/x-dtbncx+xml":
                return  # Has NCX

    result.add(
        "EPUB-NAV-DOCUMENT",
        "ePub has no navigation document (table of contents)",
    )


def _check_accessibility_metadata(root: ET.Element, result: AuditResult) -> None:
    """Check for schema.org accessibility metadata (EPUB Accessibility 1.1)."""
    ns_opf = "http://www.idpf.org/2007/opf"
    metadata = root.find(f"{{{ns_opf}}}metadata")
    if metadata is None:
        result.add(
            "EPUB-ACCESSIBILITY-METADATA",
            "ePub has no accessibility metadata (accessMode, accessibilityFeature)",
        )
        return

    # Look for meta elements with schema.org accessibility properties
    has_access_mode = False
    has_accessibility_feature = False

    for meta in metadata.findall(f"{{{ns_opf}}}meta"):
        prop = meta.get("property", "")
        if prop == "schema:accessMode":
            has_access_mode = True
        elif prop == "schema:accessibilityFeature":
            has_accessibility_feature = True

    if not has_access_mode and not has_accessibility_feature:
        result.add(
            "EPUB-ACCESSIBILITY-METADATA",
            "ePub has no schema.org accessibility metadata (accessMode, accessibilityFeature)",
        )


def _check_html_structure(file_path: Path, result: AuditResult) -> None:
    """Use Pandoc to convert ePub to HTML, then parse for structural issues."""
    exe = shutil.which("pandoc")
    if not exe:
        # Without Pandoc, we can only do metadata checks
        return

    try:
        proc = subprocess.run(
            [exe, "-f", "epub", "-t", "html", "--no-highlight", str(file_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return

        html = proc.stdout
    except (subprocess.SubprocessError, OSError):
        return

    parser = _HTMLStructureParser()
    parser.feed(html)

    # Heading hierarchy check
    _check_headings(parser.headings, result)

    # Alt text check
    if parser.images_without_alt > 0:
        result.add(
            "EPUB-MISSING-ALT-TEXT",
            f"{parser.images_without_alt} of {parser.images_total} images "
            f"missing alternative text",
        )

    # Table header check
    if parser.tables_without_headers > 0:
        result.add(
            "EPUB-TABLE-HEADERS",
            f"{parser.tables_without_headers} of {parser.tables_total} tables "
            f"missing <th> header cells",
        )

    # Ambiguous link text check
    if parser.ambiguous_links:
        examples = ", ".join(f"'{t}'" for t in parser.ambiguous_links[:5])
        if len(parser.ambiguous_links) > 5:
            examples += f" (and {len(parser.ambiguous_links) - 5} more)"
        result.add(
            "EPUB-LINK-TEXT",
            f"Non-descriptive link text found: {examples}",
        )


def _check_headings(headings: list[int], result: AuditResult) -> None:
    """Check heading hierarchy for skipped levels."""
    if len(headings) < 2:
        return

    for i in range(1, len(headings)):
        prev = headings[i - 1]
        curr = headings[i]
        # Skipped level: e.g., H1 -> H3
        if curr > prev + 1:
            result.add(
                "EPUB-HEADING-HIERARCHY",
                f"Heading level skipped: H{prev} followed by H{curr}",
            )
            return  # Report once
