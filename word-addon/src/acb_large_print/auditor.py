"""Audit Word documents for ACB Large Print Guidelines compliance."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from . import constants as C


@dataclass
class Finding:
    """A single audit finding."""
    rule_id: str
    severity: C.Severity
    message: str
    location: str = ""
    auto_fixable: bool = True

    @property
    def rule(self) -> C.RuleDef:
        return C.AUDIT_RULES[self.rule_id]


@dataclass
class AuditResult:
    """Complete audit results for a document."""
    file_path: str
    findings: list[Finding] = field(default_factory=list)
    total_paragraphs: int = 0
    total_runs: int = 0

    @property
    def passed(self) -> bool:
        return len(self.findings) == 0

    @property
    def score(self) -> int:
        """Compliance score 0-100. Deduct points per severity."""
        if not self.findings:
            return 100
        deductions = {
            C.Severity.CRITICAL: 15,
            C.Severity.HIGH: 10,
            C.Severity.MEDIUM: 5,
            C.Severity.LOW: 2,
        }
        total = sum(deductions.get(f.severity, 5) for f in self.findings)
        return max(0, 100 - total)

    @property
    def grade(self) -> str:
        """Letter grade from score."""
        s = self.score
        if s >= 90:
            return "A"
        if s >= 80:
            return "B"
        if s >= 70:
            return "C"
        if s >= 60:
            return "D"
        return "F"

    def add(self, rule_id: str, message: str, location: str = "") -> None:
        rule = C.AUDIT_RULES[rule_id]
        self.findings.append(Finding(
            rule_id=rule_id,
            severity=rule.severity,
            message=message,
            location=location,
            auto_fixable=rule.auto_fixable,
        ))

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == C.Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == C.Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == C.Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == C.Severity.LOW)


def _effective_font_name(run) -> str | None:
    """Get the effective font name for a run (checks direct + style)."""
    if run.font.name:
        return run.font.name
    if run.style and run.style.font.name:
        return run.style.font.name
    para_style = run._element.getparent()
    if para_style is not None:
        # Walk up to paragraph, then check its style
        pass
    return None


def _effective_font_size(run) -> float | None:
    """Get effective font size in points for a run."""
    if run.font.size is not None:
        return run.font.size.pt
    if run.style and run.style.font.size:
        return run.style.font.size.pt
    return None


def _is_heading_style(style_name: str) -> bool:
    """Check if a style name is a heading style."""
    return bool(re.match(r"^Heading \d+$", style_name))


def _heading_level(style_name: str) -> int:
    """Extract heading level number from style name."""
    match = re.match(r"^Heading (\d+)$", style_name)
    return int(match.group(1)) if match else 0


def _check_document_properties(doc: Document, result: AuditResult) -> None:
    """Check document-level properties."""
    # Title
    title = doc.core_properties.title
    if not title or not title.strip():
        result.add(
            "ACB-DOC-TITLE",
            "Document has no title set in properties",
            "Document Properties",
        )

    # Language
    styles_elem = doc.styles.element
    doc_defaults = styles_elem.find(qn("w:docDefaults"))
    rpr = None
    if doc_defaults is not None:
        rpr_default = doc_defaults.find(qn("w:rPrDefault"))
        if rpr_default is not None:
            rpr = rpr_default.find(qn("w:rPr"))
    if rpr is not None:
        lang = rpr.find(qn("w:lang"))
        if lang is None or not lang.get(qn("w:val")):
            result.add(
                "ACB-DOC-LANGUAGE",
                "Document language is not set",
                "Document Properties",
            )
    else:
        result.add(
            "ACB-DOC-LANGUAGE",
            "Document language is not set",
            "Document Properties",
        )


def _check_page_setup(doc: Document, result: AuditResult) -> None:
    """Check page margins and orientation."""
    for i, section in enumerate(doc.sections):
        loc = f"Section {i + 1}"
        margin_tolerance = Inches(0.05)

        if section.top_margin is not None:
            if abs(section.top_margin - Inches(C.MARGIN_TOP_IN)) > margin_tolerance:
                result.add(
                    "ACB-MARGINS",
                    f"Top margin is {section.top_margin.inches:.2f} inches (expected {C.MARGIN_TOP_IN})",
                    loc,
                )

        if section.bottom_margin is not None:
            if abs(section.bottom_margin - Inches(C.MARGIN_BOTTOM_IN)) > margin_tolerance:
                result.add(
                    "ACB-MARGINS",
                    f"Bottom margin is {section.bottom_margin.inches:.2f} inches (expected {C.MARGIN_BOTTOM_IN})",
                    loc,
                )

        if section.left_margin is not None:
            if abs(section.left_margin - Inches(C.MARGIN_LEFT_IN)) > margin_tolerance:
                result.add(
                    "ACB-MARGINS",
                    f"Left margin is {section.left_margin.inches:.2f} inches (expected {C.MARGIN_LEFT_IN})",
                    loc,
                )

        if section.right_margin is not None:
            if abs(section.right_margin - Inches(C.MARGIN_RIGHT_IN)) > margin_tolerance:
                result.add(
                    "ACB-MARGINS",
                    f"Right margin is {section.right_margin.inches:.2f} inches (expected {C.MARGIN_RIGHT_IN})",
                    loc,
                )


def _check_styles(doc: Document, result: AuditResult) -> None:
    """Check that named styles match ACB specifications."""
    for style_name, style_def in C.ACB_STYLES.items():
        try:
            style = doc.styles[style_name]
        except KeyError:
            continue

        loc = f"Style: {style_name}"
        font = style.font
        pf = style.paragraph_format

        # Font family
        if font.name and font.name != C.FONT_FAMILY:
            result.add(
                "ACB-FONT-FAMILY",
                f"{style_name} uses '{font.name}' instead of '{C.FONT_FAMILY}'",
                loc,
            )

        # Font size
        expected_size = style_def.font.size_pt
        if font.size and abs(font.size.pt - expected_size) > 0.5:
            size_rule = "ACB-FONT-SIZE-BODY"
            if style_name == "Heading 1":
                size_rule = "ACB-FONT-SIZE-H1"
            elif style_name == "Heading 2":
                size_rule = "ACB-FONT-SIZE-H2"
            result.add(
                size_rule,
                f"{style_name} is {font.size.pt}pt (expected {expected_size}pt)",
                loc,
            )

        # Italic check
        if font.italic:
            result.add(
                "ACB-NO-ITALIC",
                f"{style_name} style has italic enabled",
                loc,
            )

        # Alignment
        if pf.alignment is not None and pf.alignment != WD_ALIGN_PARAGRAPH.LEFT:
            result.add(
                "ACB-ALIGNMENT",
                f"{style_name} is not flush left",
                loc,
            )


def _check_paragraph_content(doc: Document, result: AuditResult) -> None:
    """Check each paragraph and run for direct formatting violations."""
    prev_heading_level = 0

    for i, para in enumerate(doc.paragraphs):
        result.total_paragraphs += 1
        loc = f"Paragraph {i + 1}"
        style_name = para.style.name if para.style else "Normal"
        text_preview = para.text[:60].strip()
        if text_preview:
            loc = f"Paragraph {i + 1}: '{text_preview}...'" if len(para.text) > 60 else f"Paragraph {i + 1}: '{text_preview}'"

        is_heading = _is_heading_style(style_name)

        # Heading hierarchy check
        if is_heading:
            level = _heading_level(style_name)
            if prev_heading_level > 0 and level > prev_heading_level + 1:
                result.add(
                    "ACB-HEADING-HIERARCHY",
                    f"Heading level skipped: H{prev_heading_level} to H{level}",
                    loc,
                )
            prev_heading_level = level

        # Direct alignment override
        if para.paragraph_format.alignment is not None:
            if para.paragraph_format.alignment != WD_ALIGN_PARAGRAPH.LEFT:
                result.add(
                    "ACB-ALIGNMENT",
                    f"Direct alignment override (not flush left)",
                    loc,
                )

        # Check each run
        for run in para.runs:
            result.total_runs += 1

            # Italic at run level
            if run.font.italic:
                result.add(
                    "ACB-NO-ITALIC",
                    f"Italic text found: '{run.text[:40]}'",
                    loc,
                )

            # Bold in body text (not headings)
            if run.font.bold and not is_heading and run.text.strip():
                # Only flag if the bold run is a substantial portion of the paragraph
                if len(run.text.strip()) > 5:
                    result.add(
                        "ACB-BOLD-HEADINGS-ONLY",
                        f"Bold used in body text: '{run.text[:40]}'",
                        loc,
                    )

            # Font family override at run level
            if run.font.name and run.font.name != C.FONT_FAMILY:
                result.add(
                    "ACB-FONT-FAMILY",
                    f"Non-Arial font '{run.font.name}' in: '{run.text[:40]}'",
                    loc,
                )

            # Font size below minimum at run level
            if run.font.size and run.font.size.pt < C.MIN_SIZE_PT - 0.5:
                result.add(
                    "ACB-FONT-SIZE-BODY",
                    f"Font size {run.font.size.pt}pt below {C.MIN_SIZE_PT}pt minimum",
                    loc,
                )

            # All caps at run level
            if run.font.all_caps:
                result.add(
                    "ACB-NO-ALLCAPS",
                    f"ALL CAPS formatting on: '{run.text[:40]}'",
                    loc,
                )

        # Check for all-caps text content (not formatting, but typed in caps)
        if para.text.strip() and para.text.strip().isupper() and len(para.text.strip()) > 3:
            if is_heading:
                result.add(
                    "ACB-NO-ALLCAPS",
                    f"Heading text is ALL CAPS",
                    loc,
                )


def _check_hyphenation(doc: Document, result: AuditResult) -> None:
    """Check whether auto-hyphenation is enabled."""
    settings = doc.settings.element
    auto_hyph = settings.find(qn("w:autoHyphenation"))
    if auto_hyph is not None:
        val = auto_hyph.get(qn("w:val"), "true")
        if val.lower() not in ("false", "0", "off"):
            result.add(
                "ACB-NO-HYPHENATION",
                "Automatic hyphenation is enabled",
                "Document Settings",
            )


def _check_page_numbers(doc: Document, result: AuditResult) -> None:
    """Check for page number fields in footer."""
    has_page_numbers = False
    for section in doc.sections:
        footer = section.footer
        if footer is None:
            continue
        footer_xml = footer._element.xml
        if "PAGE" in footer_xml or "w:fldChar" in footer_xml:
            has_page_numbers = True
            break

    if not has_page_numbers:
        result.add(
            "ACB-PAGE-NUMBERS",
            "No page numbers found in document footer",
            "Footer",
        )


def audit_document(file_path: str | Path) -> AuditResult:
    """Run a full ACB Large Print compliance audit on a Word document.

    Args:
        file_path: Path to the .docx file to audit.

    Returns:
        AuditResult with all findings.
    """
    file_path = Path(file_path)
    result = AuditResult(file_path=str(file_path))

    doc = Document(str(file_path))

    _check_document_properties(doc, result)
    _check_page_setup(doc, result)
    _check_styles(doc, result)
    _check_paragraph_content(doc, result)
    _check_hyphenation(doc, result)
    _check_page_numbers(doc, result)

    # Sort findings by severity
    severity_order = {
        C.Severity.CRITICAL: 0,
        C.Severity.HIGH: 1,
        C.Severity.MEDIUM: 2,
        C.Severity.LOW: 3,
    }
    result.findings.sort(key=lambda f: severity_order.get(f.severity, 99))

    return result
