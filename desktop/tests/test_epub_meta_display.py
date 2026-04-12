"""Tests for epub_meta_display -- W3C Accessibility Metadata Display Guide 2.0."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from acb_large_print.epub_meta_display import (
    EpubAccessibilityDisplay,
    MetadataSection,
    extract_metadata_display,
)


# ---------------------------------------------------------------------------
# Helpers -- build minimal EPUBs in memory
# ---------------------------------------------------------------------------

_CONTAINER_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">'
    '<rootfiles><rootfile full-path="OEBPS/content.opf" '
    'media-type="application/oebps-package+xml"/></rootfiles></container>'
)

_NAV_XHTML = "<html><body>Nav</body></html>"


def _build_epub(meta_elements: str, *, version: str = "3.0") -> Path:
    """Create a minimal EPUB with the given OPF metadata elements."""
    opf = (
        f'<?xml version="1.0" encoding="utf-8"?>'
        f'<package xmlns="http://www.idpf.org/2007/opf" version="{version}" xml:lang="en">'
        f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f'{meta_elements}'
        f'</metadata>'
        f'<manifest><item id="nav" href="nav.xhtml" '
        f'media-type="application/xhtml+xml" properties="nav"/></manifest>'
        f'<spine/>'
        f'</package>'
    )

    tmp = Path(tempfile.mktemp(suffix=".epub"))
    with zipfile.ZipFile(str(tmp), "w") as zf:
        zf.writestr("META-INF/container.xml", _CONTAINER_XML)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/nav.xhtml", _NAV_XHTML)
    return tmp


def _cleanup(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Section count and structure tests
# ---------------------------------------------------------------------------

class TestStructure:
    def test_always_returns_eight_sections(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            assert display is not None
            assert len(display.sections()) == 8
        finally:
            _cleanup(path)

    def test_section_order(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            titles = [s.title for s in display.sections()]
            assert titles == [
                "Ways of Reading",
                "Conformance",
                "Navigation",
                "Rich Content",
                "Hazards",
                "Accessibility Summary",
                "Legal Considerations",
                "Additional Accessibility Information",
            ]
        finally:
            _cleanup(path)

    def test_empty_metadata_has_no_real_metadata(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            assert display.has_any_metadata is False
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Ways of Reading (Section 3.1)
# ---------------------------------------------------------------------------

class TestWaysOfReading:
    def test_display_transformability(self):
        meta = '<meta property="schema:accessibilityFeature">displayTransformability</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.ways_of_reading.statements
            assert any("Appearance can be modified" in s for s in stmts)
            assert display.ways_of_reading.has_metadata is True
        finally:
            _cleanup(path)

    def test_pre_paginated_not_modifiable(self):
        meta = '<meta property="rendition:layout">pre-paginated</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.ways_of_reading.statements
            assert any("cannot be modified" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_no_info_fallback(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            stmts = display.ways_of_reading.statements
            assert any("No information" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_textual_sufficient_means_readable(self):
        meta = (
            '<meta property="schema:accessModeSufficient">textual</meta>'
            '<meta property="schema:accessMode">textual</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.ways_of_reading.statements
            assert any("Readable in read aloud or dynamic braille" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_alt_text_features_noted(self):
        meta = '<meta property="schema:accessibilityFeature">alternativeText</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.ways_of_reading.statements
            assert any("alternative text" in s.lower() for s in stmts)
        finally:
            _cleanup(path)

    def test_synchronized_audio(self):
        meta = '<meta property="schema:accessibilityFeature">synchronizedAudioText</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.ways_of_reading.statements
            assert any("synchronized" in s.lower() for s in stmts)
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Conformance (Section 3.2)
# ---------------------------------------------------------------------------

class TestConformance:
    def test_wcag_aa_conformance(self):
        meta = (
            '<meta property="dcterms:conformsTo">'
            'EPUB Accessibility 1.1 - WCAG 2.2 Level AA'
            '</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.conformance.statements
            assert any("meets accepted accessibility standards" in s for s in stmts)
            assert display.conformance.has_metadata is True
        finally:
            _cleanup(path)

    def test_wcag_aaa_exceeds(self):
        meta = (
            '<meta property="dcterms:conformsTo">'
            'EPUB Accessibility 1.1 - WCAG 2.1 Level AAA'
            '</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.conformance.statements
            assert any("exceeds" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_wcag_a_minimum(self):
        meta = (
            '<meta property="dcterms:conformsTo">'
            'EPUB Accessibility 1.0 - WCAG 2.0 Level A'
            '</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.conformance.statements
            assert any("minimum" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_certifier_shown(self):
        meta = (
            '<meta property="dcterms:conformsTo">'
            'EPUB Accessibility 1.1 - WCAG 2.2 Level AA'
            '</meta>'
            '<meta property="a11y:certifiedBy">ACB Team</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.conformance.statements
            assert any("ACB Team" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_no_conformance_info(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            stmts = display.conformance.statements
            assert any("No conformance" in s for s in stmts)
            assert display.conformance.has_metadata is False
        finally:
            _cleanup(path)

    def test_epub10_uri_conformance(self):
        meta = (
            '<meta property="dcterms:conformsTo">'
            'http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-aa'
            '</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.conformance.statements
            assert any("meets accepted accessibility standards" in s for s in stmts)
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Navigation (Section 3.3)
# ---------------------------------------------------------------------------

class TestNavigation:
    def test_toc_detected(self):
        meta = '<meta property="schema:accessibilityFeature">tableOfContents</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.navigation.statements
            assert any("Table of contents" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_structural_navigation(self):
        meta = '<meta property="schema:accessibilityFeature">structuralNavigation</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.navigation.statements
            assert any("Headings" in s for s in stmts)
            assert display.navigation.has_metadata is True
        finally:
            _cleanup(path)

    def test_page_navigation(self):
        meta = '<meta property="schema:accessibilityFeature">pageNavigation</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.navigation.statements
            assert any("page" in s.lower() for s in stmts)
        finally:
            _cleanup(path)

    def test_index_feature(self):
        meta = '<meta property="schema:accessibilityFeature">index</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.navigation.statements
            assert any("Index" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_no_navigation_info(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            stmts = display.navigation.statements
            assert any("No navigation" in s for s in stmts)
            assert display.navigation.has_metadata is False
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Rich Content (Section 3.4)
# ---------------------------------------------------------------------------

class TestRichContent:
    def test_mathml(self):
        meta = '<meta property="schema:accessibilityFeature">MathML</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.rich_content.statements
            assert any("MathML" in s for s in stmts)
            assert display.rich_content.has_metadata is True
        finally:
            _cleanup(path)

    def test_closed_captions(self):
        meta = '<meta property="schema:accessibilityFeature">closedCaptions</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.rich_content.statements
            assert any("closed captions" in s.lower() for s in stmts)
        finally:
            _cleanup(path)

    def test_long_descriptions(self):
        meta = '<meta property="schema:accessibilityFeature">longDescriptions</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.rich_content.statements
            assert any("extended descriptions" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_transcript(self):
        meta = '<meta property="schema:accessibilityFeature">transcript</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.rich_content.statements
            assert any("Transcript" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_no_rich_content_info(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            stmts = display.rich_content.statements
            assert any("No rich content" in s for s in stmts)
            assert display.rich_content.has_metadata is False
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Hazards (Section 3.5)
# ---------------------------------------------------------------------------

class TestHazards:
    def test_no_hazards(self):
        meta = '<meta property="schema:accessibilityHazard">none</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.hazards.statements
            assert any("No hazards" in s for s in stmts)
            assert display.hazards.has_metadata is True
        finally:
            _cleanup(path)

    def test_individual_no_hazards(self):
        meta = (
            '<meta property="schema:accessibilityHazard">noFlashingHazard</meta>'
            '<meta property="schema:accessibilityHazard">noMotionSimulationHazard</meta>'
            '<meta property="schema:accessibilityHazard">noSoundHazard</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.hazards.statements
            assert any("No flashing" in s for s in stmts)
            assert any("No motion" in s for s in stmts)
            assert any("No sound" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_flashing_hazard(self):
        meta = '<meta property="schema:accessibilityHazard">flashing</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.hazards.statements
            assert any("Flashing" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_unknown_hazards(self):
        meta = '<meta property="schema:accessibilityHazard">unknown</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.hazards.statements
            assert any("unknown" in s.lower() for s in stmts)
        finally:
            _cleanup(path)

    def test_no_hazard_info(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            stmts = display.hazards.statements
            assert any("No hazard information" in s for s in stmts)
            assert display.hazards.has_metadata is False
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Accessibility Summary (Section 3.6)
# ---------------------------------------------------------------------------

class TestAccessibilitySummary:
    def test_summary_present(self):
        meta = (
            '<meta property="schema:accessibilitySummary">'
            'This publication is fully accessible.'
            '</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.accessibility_summary.statements
            assert "This publication is fully accessible." in stmts
            assert display.accessibility_summary.has_metadata is True
        finally:
            _cleanup(path)

    def test_no_summary(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            stmts = display.accessibility_summary.statements
            assert any("No accessibility summary" in s for s in stmts)
            assert display.accessibility_summary.has_metadata is False
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Legal Considerations (Section 3.7)
# ---------------------------------------------------------------------------

class TestLegal:
    def test_exemption_declared(self):
        meta = '<meta property="a11y:exemption">true</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.legal.statements
            assert any("exemption" in s.lower() for s in stmts)
            assert display.legal.has_metadata is True
        finally:
            _cleanup(path)

    def test_no_legal_info(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            stmts = display.legal.statements
            assert any("No legal" in s for s in stmts)
            assert display.legal.has_metadata is False
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Additional Accessibility Information (Section 3.8)
# ---------------------------------------------------------------------------

class TestAdditionalInfo:
    def test_aria_and_large_print(self):
        meta = (
            '<meta property="schema:accessibilityFeature">aria</meta>'
            '<meta property="schema:accessibilityFeature">largePrint</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.additional_info.statements
            assert any("ARIA" in s for s in stmts)
            assert any("Large print" in s for s in stmts)
            assert display.additional_info.has_metadata is True
        finally:
            _cleanup(path)

    def test_tts_markup(self):
        meta = '<meta property="schema:accessibilityFeature">ttsMarkup</meta>'
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.additional_info.statements
            assert any("Text-to-speech" in s for s in stmts)
        finally:
            _cleanup(path)

    def test_no_additional_info(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            stmts = display.additional_info.statements
            assert any("No additional" in s for s in stmts)
            assert display.additional_info.has_metadata is False
        finally:
            _cleanup(path)

    def test_duplicate_page_breaks_deduped(self):
        """pageBreakMarkers and printPageNumbers should produce one statement."""
        meta = (
            '<meta property="schema:accessibilityFeature">pageBreakMarkers</meta>'
            '<meta property="schema:accessibilityFeature">printPageNumbers</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            stmts = display.additional_info.statements
            page_stmts = [s for s in stmts if "Page breaks" in s]
            assert len(page_stmts) == 1
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Serialisation tests
# ---------------------------------------------------------------------------

class TestSerialisation:
    def test_to_text_includes_section_titles(self):
        meta = (
            '<meta property="schema:accessibilityFeature">tableOfContents</meta>'
            '<meta property="schema:accessibilityHazard">none</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            text = display.to_text()
            assert "Navigation" in text
            assert "Hazards" in text
            assert "Table of contents" in text
        finally:
            _cleanup(path)

    def test_to_text_skips_empty_by_default(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            text = display.to_text(include_empty=False)
            # No sections with real metadata, so text should be minimal
            assert "No conformance" not in text
        finally:
            _cleanup(path)

    def test_to_text_include_empty(self):
        path = _build_epub("")
        try:
            display = extract_metadata_display(path)
            text = display.to_text(include_empty=True)
            assert "Conformance" in text
            assert "No conformance" in text
        finally:
            _cleanup(path)

    def test_to_dict_has_all_sections(self):
        meta = (
            '<meta property="schema:accessibilityFeature">tableOfContents</meta>'
            '<meta property="dcterms:conformsTo">'
            'EPUB Accessibility 1.1 - WCAG 2.2 Level AA</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            d = display.to_dict()
            assert "navigation" in d
            assert "conformance" in d
            assert "raw_metadata" in d
            assert d["conformance"]["has_metadata"] is True
            assert isinstance(d["navigation"]["statements"], list)
        finally:
            _cleanup(path)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_corrupt_file_returns_none(self):
        tmp = Path(tempfile.mktemp(suffix=".epub"))
        tmp.write_bytes(b"not a zip file")
        try:
            result = extract_metadata_display(tmp)
            assert result is None
        finally:
            _cleanup(tmp)

    def test_missing_opf_returns_none(self):
        tmp = Path(tempfile.mktemp(suffix=".epub"))
        with zipfile.ZipFile(str(tmp), "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
        try:
            result = extract_metadata_display(tmp)
            assert result is None
        finally:
            _cleanup(tmp)

    def test_nonexistent_file_returns_none(self):
        result = extract_metadata_display(Path("/nonexistent/file.epub"))
        assert result is None

    def test_rich_metadata_epub(self):
        """Full metadata EPUB should have has_any_metadata True."""
        meta = (
            '<dc:title>Test Book</dc:title>'
            '<dc:language>en</dc:language>'
            '<meta property="schema:accessMode">textual</meta>'
            '<meta property="schema:accessMode">visual</meta>'
            '<meta property="schema:accessModeSufficient">textual</meta>'
            '<meta property="schema:accessibilityFeature">tableOfContents</meta>'
            '<meta property="schema:accessibilityFeature">structuralNavigation</meta>'
            '<meta property="schema:accessibilityFeature">alternativeText</meta>'
            '<meta property="schema:accessibilityFeature">displayTransformability</meta>'
            '<meta property="schema:accessibilityFeature">longDescriptions</meta>'
            '<meta property="schema:accessibilityFeature">MathML</meta>'
            '<meta property="schema:accessibilityFeature">closedCaptions</meta>'
            '<meta property="schema:accessibilityFeature">aria</meta>'
            '<meta property="schema:accessibilityFeature">largePrint</meta>'
            '<meta property="schema:accessibilityHazard">noFlashingHazard</meta>'
            '<meta property="schema:accessibilityHazard">noMotionSimulationHazard</meta>'
            '<meta property="schema:accessibilityHazard">noSoundHazard</meta>'
            '<meta property="schema:accessibilitySummary">Fully accessible.</meta>'
            '<meta property="dcterms:conformsTo">'
            'EPUB Accessibility 1.1 - WCAG 2.2 Level AA</meta>'
            '<meta property="a11y:certifiedBy">ACB Team</meta>'
        )
        path = _build_epub(meta)
        try:
            display = extract_metadata_display(path)
            assert display.has_any_metadata is True
            # All sections should have metadata except Legal
            for section in display.sections():
                if section.title != "Legal Considerations":
                    assert section.has_metadata is True, f"{section.title} should have metadata"
        finally:
            _cleanup(path)
