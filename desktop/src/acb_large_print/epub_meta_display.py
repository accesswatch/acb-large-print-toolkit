"""Extract and display EPUB accessibility metadata per W3C Display Guide 2.0.

Implements the `Accessibility Metadata Display Guide 2.0`_ algorithm for
EPUB publications, producing human-readable statements organised into
eight display sections (Ways of Reading, Conformance, Navigation, Rich
Content, Hazards, Accessibility Summary, Legal Considerations, and
Additional Accessibility Information).

This is an independent Python implementation of the same W3C specification
that the DAISY Consortium's `a11y-meta-viewer`_ implements in JavaScript.
The vendored JS source is in ``vendor/daisy-a11y-meta-viewer/`` for
reference and attribution.

.. _Accessibility Metadata Display Guide 2.0:
   https://w3c.github.io/publ-a11y/a11y-meta-display-guide/2.0/draft/techniques/epub-metadata/
.. _a11y-meta-viewer:
   https://github.com/daisy/a11y-meta-viewer
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# OPF namespaces
_NS_OPF = "http://www.idpf.org/2007/opf"
_NS_DC = "http://purl.org/dc/elements/1.1/"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class MetadataSection:
    """A single display section of accessibility metadata."""
    title: str
    statements: list[str] = field(default_factory=list)
    has_metadata: bool = True


@dataclass
class EpubAccessibilityDisplay:
    """Complete accessibility metadata display for an EPUB file.

    Sections follow the W3C Display Guide 2.0 order.
    """
    ways_of_reading: MetadataSection | None = None
    conformance: MetadataSection | None = None
    navigation: MetadataSection | None = None
    rich_content: MetadataSection | None = None
    hazards: MetadataSection | None = None
    accessibility_summary: MetadataSection | None = None
    legal: MetadataSection | None = None
    additional_info: MetadataSection | None = None
    raw_metadata: dict[str, list[str]] = field(default_factory=dict)

    def sections(self) -> list[MetadataSection]:
        """Return all non-None sections in display order."""
        return [s for s in (
            self.ways_of_reading,
            self.conformance,
            self.navigation,
            self.rich_content,
            self.hazards,
            self.accessibility_summary,
            self.legal,
            self.additional_info,
        ) if s is not None]

    @property
    def has_any_metadata(self) -> bool:
        return any(s.has_metadata for s in self.sections())

    def to_text(self, *, include_empty: bool = False) -> str:
        """Render all sections as plain text for report inclusion."""
        lines: list[str] = []
        for section in self.sections():
            if not section.has_metadata and not include_empty:
                continue
            lines.append(f"  {section.title}")
            for stmt in section.statements:
                lines.append(f"    - {stmt}")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialise for JSON reports."""
        result: dict = {}
        for section in self.sections():
            key = section.title.lower().replace(" ", "_")
            result[key] = {
                "title": section.title,
                "statements": section.statements,
                "has_metadata": section.has_metadata,
            }
        result["raw_metadata"] = {k: v for k, v in self.raw_metadata.items()}
        return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_metadata_display(epub_path: str | Path) -> EpubAccessibilityDisplay | None:
    """Extract and format accessibility metadata from an EPUB file.

    Returns an :class:`EpubAccessibilityDisplay` with human-readable
    statements organised by section, or ``None`` if the EPUB is
    unparseable.
    """
    epub_path = Path(epub_path)
    try:
        with zipfile.ZipFile(str(epub_path), "r") as zf:
            opf_path = _find_opf(zf)
            if not opf_path:
                return None
            opf_xml = zf.read(opf_path).decode("utf-8", errors="replace")
            root = ET.fromstring(opf_xml)
    except (zipfile.BadZipFile, ET.ParseError, KeyError, OSError):
        return None

    version = root.get("version", "3.0")
    is_epub2 = version.startswith("2")

    raw = _extract_raw_metadata(root, is_epub2)

    display = EpubAccessibilityDisplay(raw_metadata=raw)
    display.ways_of_reading = _build_ways_of_reading(raw)
    display.conformance = _build_conformance(raw)
    display.navigation = _build_navigation(raw)
    display.rich_content = _build_rich_content(raw)
    display.hazards = _build_hazards(raw)
    display.accessibility_summary = _build_summary(raw)
    display.legal = _build_legal(raw)
    display.additional_info = _build_additional_info(raw)

    return display


# ---------------------------------------------------------------------------
# OPF parsing helpers
# ---------------------------------------------------------------------------

def _find_opf(zf: zipfile.ZipFile) -> str | None:
    """Locate the OPF file inside the EPUB ZIP."""
    try:
        container = zf.read("META-INF/container.xml").decode("utf-8", errors="replace")
        croot = ET.fromstring(container)
        ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
        rootfile = croot.find(".//c:rootfile", ns)
        if rootfile is not None:
            return rootfile.get("full-path")
    except (KeyError, ET.ParseError):
        pass
    for name in zf.namelist():
        if name.lower().endswith(".opf"):
            return name
    return None


def _extract_raw_metadata(root: ET.Element, is_epub2: bool) -> dict[str, list[str]]:
    """Extract all accessibility-relevant metadata from the OPF."""
    metadata = root.find(f"{{{_NS_OPF}}}metadata")
    if metadata is None:
        return {}

    raw: dict[str, list[str]] = {}

    for meta in metadata.findall(f"{{{_NS_OPF}}}meta"):
        if is_epub2:
            prop = meta.get("name", "")
            value = meta.get("content", "").strip()
        else:
            prop = meta.get("property", "")
            value = (meta.text or "").strip()
        if prop and value:
            raw.setdefault(prop, []).append(value)

    # EPUB 3 link elements (certifier reports, conformsTo)
    for link in metadata.findall(f"{{{_NS_OPF}}}link"):
        rel = link.get("rel", "")
        href = link.get("href", "")
        if rel and href:
            raw.setdefault(f"link:{rel}", []).append(href)

    # Dublin Core elements
    for el_name in ("language", "title", "source"):
        for el in metadata.findall(f"{{{_NS_DC}}}{el_name}"):
            text = (el.text or "").strip()
            if text:
                raw.setdefault(f"dc:{el_name}", []).append(text)

    return raw


def _has(raw: dict[str, list[str]], prop: str, value: str = "") -> bool:
    values = raw.get(prop, [])
    if not value:
        return len(values) > 0
    return value in values


def _get(raw: dict[str, list[str]], prop: str) -> str:
    values = raw.get(prop, [])
    return values[0] if values else ""


def _get_all(raw: dict[str, list[str]], prop: str) -> list[str]:
    return raw.get(prop, [])


# ---------------------------------------------------------------------------
# Section 3.1: Ways of Reading
# ---------------------------------------------------------------------------

def _build_ways_of_reading(raw: dict[str, list[str]]) -> MetadataSection:
    section = MetadataSection(title="Ways of Reading")
    features = _get_all(raw, "schema:accessibilityFeature")
    modes = _get_all(raw, "schema:accessMode")
    sufficient = _get_all(raw, "schema:accessModeSufficient")
    has_real_metadata = False

    # 3.1.1 Visual adjustments
    if "displayTransformability" in features:
        section.statements.append("Appearance can be modified.")
        has_real_metadata = True
    elif _has(raw, "rendition:layout", "pre-paginated"):
        section.statements.append("Appearance cannot be modified.")
        has_real_metadata = True
    else:
        section.statements.append(
            "No information about appearance modifiability is available."
        )

    # 3.1.2 Nonvisual reading
    text_features = {"longDescription", "alternativeText", "describedMath", "transcript"}
    has_textual_alts = bool(text_features & set(features))
    textual_only_mode = (modes == ["textual"])
    textual_sufficient = "textual" in sufficient
    has_some_textual = "textual" in modes or any("textual" in s for s in sufficient)
    audio_only = (modes == ["auditory"])
    visual_only = (modes == ["visual"]) and not has_some_textual

    if textual_sufficient or textual_only_mode:
        section.statements.append(
            "Readable in read aloud or dynamic braille."
        )
        has_real_metadata = True
    elif has_some_textual or has_textual_alts:
        section.statements.append(
            "Not fully readable in read aloud or dynamic braille."
        )
        has_real_metadata = True
    elif audio_only or visual_only:
        section.statements.append(
            "Not readable in read aloud or dynamic braille."
        )
        has_real_metadata = True
    else:
        section.statements.append(
            "No information about nonvisual reading is available."
        )

    if has_textual_alts:
        section.statements.append("Has alternative text descriptions for images.")

    # 3.1.3 Prerecorded audio
    if "synchronizedAudioText" in features:
        section.statements.append("Prerecorded audio synchronized with text.")
        has_real_metadata = True
    elif textual_sufficient and audio_only:
        section.statements.append("Prerecorded audio only.")
        has_real_metadata = True
    elif "auditory" in modes:
        section.statements.append("Prerecorded audio clips.")
        has_real_metadata = True
    else:
        section.statements.append(
            "No information about prerecorded audio is available."
        )

    section.has_metadata = has_real_metadata
    return section


# ---------------------------------------------------------------------------
# Section 3.2: Conformance
# ---------------------------------------------------------------------------

_CONFORMANCE_RE = re.compile(
    r"EPUB Accessibility\s+1\.(\d)\s*-\s*WCAG\s+(2\.[0-2])\s+Level\s+([A]{1,3})",
    re.IGNORECASE,
)


def _build_conformance(raw: dict[str, list[str]]) -> MetadataSection:
    section = MetadataSection(title="Conformance")

    conformance_values = _get_all(raw, "dcterms:conformsTo")

    epub_version: str = ""
    wcag_version: str = ""
    wcag_level: str = ""

    for val in conformance_values:
        m = _CONFORMANCE_RE.search(val)
        if m:
            epub_version = f"1.{m.group(1)}"
            wcag_version = m.group(2)
            wcag_level = m.group(3)
            break

    # EPUB 1.0 URIs
    if not epub_version:
        ea10 = "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-"
        for val in conformance_values:
            if ea10 in val:
                epub_version = "1.0"
                wcag_version = "2.0"
                if val.endswith("aaa"):
                    wcag_level = "AAA"
                elif val.endswith("aa"):
                    wcag_level = "AA"
                elif val.endswith("a"):
                    wcag_level = "A"
                break

    if not wcag_level:
        section.statements.append("No conformance information is available.")
        section.has_metadata = False
        return section

    # Main conformance statement
    level_label = {
        "AAA": "exceeds accepted accessibility standards",
        "AA": "meets accepted accessibility standards",
        "A": "meets minimum accessibility standards",
    }.get(wcag_level, "meets accessibility standards")
    section.statements.append(f"This publication {level_label}.")

    # Certifier
    certifier = _get(raw, "a11y:certifiedBy")
    if certifier:
        section.statements.append(
            f"The publication was certified by {certifier}."
        )

    certifier_cred = _get(raw, "a11y:certifierCredential")
    if certifier_cred:
        section.statements.append(
            f"The certifier's credential is {certifier_cred}."
        )

    # Detailed conformance claim
    epub_label = f"EPUB Accessibility {epub_version}" if epub_version else ""
    wcag_label = {
        "2.0": "WCAG 2.0",
        "2.1": "WCAG 2.1",
        "2.2": "WCAG 2.2",
    }.get(wcag_version, f"WCAG {wcag_version}" if wcag_version else "")
    level_detail = f"Level {wcag_level}" if wcag_level else ""

    claim_parts = [p for p in (epub_label, wcag_label, level_detail) if p]
    if claim_parts:
        section.statements.append(
            f"Claims to meet {' '.join(claim_parts)}."
        )

    # Certification date
    cert_date = _get(raw, "dcterms:date")
    if cert_date:
        section.statements.append(
            f"The publication was certified on {cert_date}."
        )

    # Certifier report
    cert_report = _get(raw, "link:a11y:certifierReport") or _get(raw, "a11y:certifierReport")
    if cert_report:
        section.statements.append(
            f"For more information refer to the certifier's report: {cert_report}"
        )

    return section


# ---------------------------------------------------------------------------
# Section 3.3: Navigation
# ---------------------------------------------------------------------------

def _build_navigation(raw: dict[str, list[str]]) -> MetadataSection:
    section = MetadataSection(title="Navigation")
    features = _get_all(raw, "schema:accessibilityFeature")

    nav_items: list[str] = []
    if "tableOfContents" in features:
        nav_items.append("Table of contents.")
    if "index" in features:
        nav_items.append("Index with links to referenced entries.")
    if "pageNavigation" in features or "printPageNumbers" in features or "pageBreakMarkers" in features:
        nav_items.append("Go to page (page list from print source).")
    if "structuralNavigation" in features:
        nav_items.append("Headings and structural navigation.")

    if nav_items:
        section.statements = nav_items
    else:
        section.statements.append("No navigation information is available.")
        section.has_metadata = False

    return section


# ---------------------------------------------------------------------------
# Section 3.4: Rich Content
# ---------------------------------------------------------------------------

def _build_rich_content(raw: dict[str, list[str]]) -> MetadataSection:
    section = MetadataSection(title="Rich Content")
    features = _get_all(raw, "schema:accessibilityFeature")
    modes = _get_all(raw, "schema:accessMode")

    items: list[str] = []

    if "MathML" in features:
        items.append("Math formulas in accessible format (MathML).")
    if "latex" in features:
        items.append("Math formulas in accessible format (LaTeX).")
    if "describedMath" in features and "MathML" not in features and "latex" not in features:
        items.append("Text descriptions of math are provided.")

    if "MathML-chemistry" in features:
        items.append("Chemical formulas in accessible format (MathML).")
    if "latex-chemistry" in features:
        items.append("Chemical formulas in accessible format (LaTeX).")

    if "longDescriptions" in features:
        items.append(
            "Information-rich images are described by extended descriptions."
        )

    if "closedCaptions" in features:
        items.append("Videos have closed captions.")
    if "openCaptions" in features:
        items.append("Videos have open captions.")
    if "transcript" in features:
        items.append("Transcript(s) provided.")

    if items:
        section.statements = items
    else:
        section.statements.append("No rich content information is available.")
        section.has_metadata = False

    return section


# ---------------------------------------------------------------------------
# Section 3.5: Hazards
# ---------------------------------------------------------------------------

def _build_hazards(raw: dict[str, list[str]]) -> MetadataSection:
    section = MetadataSection(title="Hazards")
    hazard_values = _get_all(raw, "schema:accessibilityHazard")

    if not hazard_values:
        section.statements.append("No hazard information is available.")
        section.has_metadata = False
        return section

    if "none" in hazard_values:
        section.statements.append("No hazards.")
        return section

    if "unknown" in hazard_values:
        section.statements.append("The presence of hazards is unknown.")
        return section

    items: list[str] = []

    # Flashing
    if "flashing" in hazard_values:
        items.append("Flashing content.")
    elif "noFlashingHazard" in hazard_values:
        items.append("No flashing hazards.")
    elif "unknownFlashingHazard" in hazard_values:
        items.append("Flashing hazards not known.")

    # Motion
    if "motionSimulation" in hazard_values:
        items.append("Motion simulation.")
    elif "noMotionSimulationHazard" in hazard_values:
        items.append("No motion simulation hazards.")
    elif "unknownMotionSimulationHazard" in hazard_values:
        items.append("Motion simulation hazards not known.")

    # Sound
    if "sound" in hazard_values:
        items.append("Sounds.")
    elif "noSoundHazard" in hazard_values:
        items.append("No sound hazards.")
    elif "unknownSoundHazard" in hazard_values:
        items.append("Sound hazards not known.")

    section.statements = items if items else ["The presence of hazards is unknown."]
    return section


# ---------------------------------------------------------------------------
# Section 3.6: Accessibility Summary
# ---------------------------------------------------------------------------

def _build_summary(raw: dict[str, list[str]]) -> MetadataSection:
    section = MetadataSection(title="Accessibility Summary")

    summary = _get(raw, "schema:accessibilitySummary")
    if summary:
        section.statements.append(summary)
    else:
        section.statements.append("No accessibility summary is available.")
        section.has_metadata = False

    return section


# ---------------------------------------------------------------------------
# Section 3.7: Legal Considerations
# ---------------------------------------------------------------------------

def _build_legal(raw: dict[str, list[str]]) -> MetadataSection:
    section = MetadataSection(title="Legal Considerations")

    if _has(raw, "a11y:exemption"):
        section.statements.append(
            "Claims an accessibility exemption in some jurisdictions."
        )
    else:
        section.statements.append("No legal information is available.")
        section.has_metadata = False

    return section


# ---------------------------------------------------------------------------
# Section 3.8: Additional Accessibility Information
# ---------------------------------------------------------------------------

_ADDITIONAL_INFO_MAP: list[tuple[str, str]] = [
    ("aria", "ARIA roles included."),
    ("audioDescription", "Audio descriptions."),
    ("braille", "Braille."),
    ("fullRubyAnnotations", "Full ruby annotations."),
    ("highContrastAudio", "High contrast between foreground and background audio."),
    ("highContrastDisplay", "High contrast between foreground text and background."),
    ("largePrint", "Large print."),
    ("pageBreakMarkers", "Page breaks included from the original print source."),
    ("printPageNumbers", "Page breaks included from the original print source."),
    ("rubyAnnotations", "Some ruby annotations."),
    ("signLanguage", "Sign language."),
    ("tactileGraphic", "Tactile graphics included."),
    ("tactileObject", "Tactile 3D objects."),
    ("ttsMarkup", "Text-to-speech hinting provided."),
]


def _build_additional_info(raw: dict[str, list[str]]) -> MetadataSection:
    section = MetadataSection(title="Additional Accessibility Information")
    features = set(_get_all(raw, "schema:accessibilityFeature"))

    items: list[str] = []
    seen_statements: set[str] = set()
    for feature_val, statement in _ADDITIONAL_INFO_MAP:
        if feature_val in features and statement not in seen_statements:
            items.append(statement)
            seen_statements.add(statement)

    if items:
        items.sort()
        section.statements = items
    else:
        section.statements.append(
            "No additional accessibility information is available."
        )
        section.has_metadata = False

    return section
