"""Tests for epub_auditor -- EPUB accessibility audit pipeline."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from acb_large_print.epub_auditor import audit_epub
from acb_large_print.reporter import generate_text_report, generate_json_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONTAINER_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">'
    '<rootfiles><rootfile full-path="OEBPS/content.opf" '
    'media-type="application/oebps-package+xml"/></rootfiles></container>'
)


def _build_epub(
    meta: str,
    *,
    nav: bool = True,
    content_html: str = "",
    version: str = "3.0",
) -> Path:
    """Create a minimal EPUB for testing."""
    nav_item = (
        '<item id="nav" href="nav.xhtml" '
        'media-type="application/xhtml+xml" properties="nav"/>'
        if nav else ""
    )
    opf = (
        f'<?xml version="1.0" encoding="utf-8"?>'
        f'<package xmlns="http://www.idpf.org/2007/opf" version="{version}" xml:lang="en">'
        f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f'{meta}'
        f'</metadata>'
        f'<manifest>{nav_item}'
        f'<item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>'
        f'</manifest>'
        f'<spine><itemref idref="ch1"/></spine>'
        f'</package>'
    )

    tmp = Path(tempfile.mktemp(suffix=".epub"))
    with zipfile.ZipFile(str(tmp), "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", _CONTAINER_XML)
        zf.writestr("OEBPS/content.opf", opf)
        if nav:
            zf.writestr("OEBPS/nav.xhtml", "<html><body>Nav</body></html>")
        html = content_html or "<html><body><h1>Chapter 1</h1><p>Content</p></body></html>"
        zf.writestr("OEBPS/ch1.xhtml", html)
    return tmp


def _cleanup(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Basic audit tests
# ---------------------------------------------------------------------------

class TestBasicAudit:
    def test_audit_returns_result(self):
        path = _build_epub(
            '<dc:title>Test</dc:title><dc:language>en</dc:language>'
        )
        try:
            result = audit_epub(path)
            assert result is not None
            assert result.file_path == str(path)
        finally:
            _cleanup(path)

    def test_missing_title_flagged(self):
        path = _build_epub('<dc:language>en</dc:language>')
        try:
            result = audit_epub(path)
            rule_ids = [f.rule_id for f in result.findings]
            assert "EPUB-TITLE" in rule_ids
        finally:
            _cleanup(path)

    def test_missing_language_flagged(self):
        path = _build_epub('<dc:title>Test</dc:title>')
        try:
            result = audit_epub(path)
            rule_ids = [f.rule_id for f in result.findings]
            assert "EPUB-LANGUAGE" in rule_ids
        finally:
            _cleanup(path)

    def test_missing_nav_flagged(self):
        path = _build_epub(
            '<dc:title>Test</dc:title><dc:language>en</dc:language>',
            nav=False,
        )
        try:
            result = audit_epub(path)
            rule_ids = [f.rule_id for f in result.findings]
            assert "EPUB-NAV-DOCUMENT" in rule_ids
        finally:
            _cleanup(path)

    def test_missing_accessibility_metadata_flagged(self):
        path = _build_epub(
            '<dc:title>Test</dc:title><dc:language>en</dc:language>'
        )
        try:
            result = audit_epub(path)
            rule_ids = [f.rule_id for f in result.findings]
            assert "EPUB-ACCESSIBILITY-METADATA" in rule_ids
        finally:
            _cleanup(path)

    def test_missing_hazard_declaration_flagged(self):
        path = _build_epub(
            '<dc:title>Test</dc:title><dc:language>en</dc:language>'
        )
        try:
            result = audit_epub(path)
            rule_ids = [f.rule_id for f in result.findings]
            assert "EPUB-ACCESSIBILITY-HAZARD" in rule_ids
        finally:
            _cleanup(path)

    def test_missing_access_mode_sufficient_flagged(self):
        path = _build_epub(
            '<dc:title>Test</dc:title><dc:language>en</dc:language>'
        )
        try:
            result = audit_epub(path)
            rule_ids = [f.rule_id for f in result.findings]
            assert "EPUB-ACCESS-MODE-SUFFICIENT" in rule_ids
        finally:
            _cleanup(path)

    def test_compliant_epub_has_fewer_findings(self):
        meta = (
            '<dc:title>Test Book</dc:title>'
            '<dc:language>en</dc:language>'
            '<meta property="schema:accessMode">textual</meta>'
            '<meta property="schema:accessModeSufficient">textual</meta>'
            '<meta property="schema:accessibilityFeature">structuralNavigation</meta>'
            '<meta property="schema:accessibilityHazard">noFlashingHazard</meta>'
        )
        path = _build_epub(meta)
        try:
            result = audit_epub(path)
            # Should not have title, language, metadata, hazard, or access mode findings
            rule_ids = [f.rule_id for f in result.findings]
            assert "EPUB-TITLE" not in rule_ids
            assert "EPUB-LANGUAGE" not in rule_ids
            assert "EPUB-ACCESSIBILITY-METADATA" not in rule_ids
            assert "EPUB-ACCESSIBILITY-HAZARD" not in rule_ids
            assert "EPUB-ACCESS-MODE-SUFFICIENT" not in rule_ids
        finally:
            _cleanup(path)

    def test_corrupt_epub_does_not_crash(self):
        tmp = Path(tempfile.mktemp(suffix=".epub"))
        tmp.write_bytes(b"not a zip file")
        try:
            result = audit_epub(tmp)
            assert result is not None
        finally:
            _cleanup(tmp)


# ---------------------------------------------------------------------------
# Metadata display integration
# ---------------------------------------------------------------------------

class TestMetadataDisplayIntegration:
    def test_metadata_display_attached(self):
        meta = (
            '<dc:title>Test</dc:title><dc:language>en</dc:language>'
            '<meta property="schema:accessMode">textual</meta>'
            '<meta property="schema:accessModeSufficient">textual</meta>'
            '<meta property="schema:accessibilityFeature">tableOfContents</meta>'
            '<meta property="schema:accessibilityHazard">noFlashingHazard</meta>'
        )
        path = _build_epub(meta)
        try:
            result = audit_epub(path)
            assert result.metadata_display is not None
            assert result.metadata_display.has_any_metadata is True
        finally:
            _cleanup(path)

    def test_empty_epub_has_metadata_display(self):
        path = _build_epub("")
        try:
            result = audit_epub(path)
            # metadata_display should still be attached (just with no real metadata)
            assert result.metadata_display is not None
            assert result.metadata_display.has_any_metadata is False
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Reporter integration
# ---------------------------------------------------------------------------

class TestReporterIntegration:
    def test_text_report_includes_metadata_section(self):
        meta = (
            '<dc:title>Test Book</dc:title><dc:language>en</dc:language>'
            '<meta property="schema:accessMode">textual</meta>'
            '<meta property="schema:accessModeSufficient">textual</meta>'
            '<meta property="schema:accessibilityFeature">tableOfContents</meta>'
            '<meta property="schema:accessibilityFeature">structuralNavigation</meta>'
            '<meta property="schema:accessibilityHazard">noFlashingHazard</meta>'
            '<meta property="schema:accessibilityHazard">noMotionSimulationHazard</meta>'
            '<meta property="schema:accessibilityHazard">noSoundHazard</meta>'
            '<meta property="schema:accessibilitySummary">Accessible.</meta>'
            '<meta property="dcterms:conformsTo">'
            'EPUB Accessibility 1.1 - WCAG 2.2 Level AA</meta>'
        )
        path = _build_epub(meta)
        try:
            result = audit_epub(path)
            report = generate_text_report(result)
            assert "Accessibility Metadata" in report
            assert "Ways of Reading" in report
            assert "Navigation" in report
            assert "Hazards" in report
        finally:
            _cleanup(path)

    def test_json_report_includes_metadata(self):
        import json

        meta = (
            '<dc:title>Test Book</dc:title><dc:language>en</dc:language>'
            '<meta property="schema:accessibilityFeature">tableOfContents</meta>'
            '<meta property="schema:accessibilityHazard">noFlashingHazard</meta>'
            '<meta property="dcterms:conformsTo">'
            'EPUB Accessibility 1.1 - WCAG 2.2 Level AA</meta>'
        )
        path = _build_epub(meta)
        try:
            result = audit_epub(path)
            report_json = generate_json_report(result)
            data = json.loads(report_json)
            assert "accessibility_metadata" in data
            assert "navigation" in data["accessibility_metadata"]
            assert "conformance" in data["accessibility_metadata"]
        finally:
            _cleanup(path)

    def test_text_report_no_metadata_for_bare_epub(self):
        path = _build_epub("")
        try:
            result = audit_epub(path)
            report = generate_text_report(result)
            # Metadata section header should still appear, with empty info
            assert "Accessibility Metadata" in report
        finally:
            _cleanup(path)
