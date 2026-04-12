"""ACB Large Print Guidelines -- canonical style specifications.

Every constant here is derived from the ACB Large Print Guidelines
(revised and approved May 6, 2025, ACB Board of Publications).

These values are the single source of truth consumed by the template
builder, auditor, and fixer modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ---------------------------------------------------------------------------
# Font specifications
# ---------------------------------------------------------------------------

FONT_FAMILY = "Arial"

# Point sizes
BODY_SIZE_PT = 18.0
HEADING1_SIZE_PT = 22.0
HEADING2_SIZE_PT = 20.0
HEADING3_SIZE_PT = 20.0
LIST_SIZE_PT = 18.0
FOOTER_SIZE_PT = 18.0
MIN_SIZE_PT = 18.0

# Line spacing
LINE_SPACING_MULTIPLE = 1.15  # ACB print spec

# Paragraph spacing (points)
SPACE_AFTER_BODY_PT = 12.0
SPACE_BEFORE_H1_PT = 18.0
SPACE_AFTER_H1_PT = 12.0
SPACE_BEFORE_H2_PT = 16.0
SPACE_AFTER_H2_PT = 10.0
SPACE_BEFORE_H3_PT = 14.0
SPACE_AFTER_H3_PT = 8.0

# Page layout (inches)
MARGIN_TOP_IN = 1.0
MARGIN_BOTTOM_IN = 1.0
MARGIN_LEFT_IN = 1.0
MARGIN_RIGHT_IN = 1.0
BINDING_EXTRA_IN = 0.5
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0

# List formatting (inches)
LIST_INDENT_IN = 0.5
LIST_HANGING_IN = 0.25


# ---------------------------------------------------------------------------
# Style definitions (consumed by template builder and fixer)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FontDef:
    """Immutable font definition."""
    name: str = FONT_FAMILY
    size_pt: float = BODY_SIZE_PT
    bold: bool = False
    italic: bool = False
    all_caps: bool = False


@dataclass(frozen=True)
class ParaDef:
    """Immutable paragraph format definition."""
    alignment: str = "LEFT"       # LEFT | CENTER | RIGHT | JUSTIFY
    line_spacing: float = LINE_SPACING_MULTIPLE
    space_before_pt: float = 0.0
    space_after_pt: float = SPACE_AFTER_BODY_PT
    widow_control: bool = True
    keep_with_next: bool = False
    first_line_indent_in: float = 0.0
    left_indent_in: float = 0.0
    hanging_indent_in: float = 0.0


@dataclass(frozen=True)
class StyleDef:
    """Complete style definition pairing font and paragraph rules."""
    font: FontDef
    para: ParaDef


# Master style table -- every Word style we configure
ACB_STYLES: dict[str, StyleDef] = {
    "Normal": StyleDef(
        font=FontDef(size_pt=BODY_SIZE_PT),
        para=ParaDef(space_after_pt=SPACE_AFTER_BODY_PT),
    ),
    "Heading 1": StyleDef(
        font=FontDef(size_pt=HEADING1_SIZE_PT, bold=True),
        para=ParaDef(
            space_before_pt=SPACE_BEFORE_H1_PT,
            space_after_pt=SPACE_AFTER_H1_PT,
            keep_with_next=True,
        ),
    ),
    "Heading 2": StyleDef(
        font=FontDef(size_pt=HEADING2_SIZE_PT, bold=True),
        para=ParaDef(
            space_before_pt=SPACE_BEFORE_H2_PT,
            space_after_pt=SPACE_AFTER_H2_PT,
            keep_with_next=True,
        ),
    ),
    "Heading 3": StyleDef(
        font=FontDef(size_pt=HEADING3_SIZE_PT, bold=True),
        para=ParaDef(
            space_before_pt=SPACE_BEFORE_H3_PT,
            space_after_pt=SPACE_AFTER_H3_PT,
            keep_with_next=True,
        ),
    ),
    "List Bullet": StyleDef(
        font=FontDef(size_pt=LIST_SIZE_PT),
        para=ParaDef(
            space_after_pt=0.0,
            left_indent_in=LIST_INDENT_IN,
            hanging_indent_in=LIST_HANGING_IN,
        ),
    ),
    "List Number": StyleDef(
        font=FontDef(size_pt=LIST_SIZE_PT),
        para=ParaDef(
            space_after_pt=0.0,
            left_indent_in=LIST_INDENT_IN,
            hanging_indent_in=LIST_HANGING_IN,
        ),
    ),
}


# ---------------------------------------------------------------------------
# Audit rule definitions
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    """Finding severity levels."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RuleCategory(str, Enum):
    """Rule source category -- allows toggling rule sets on/off."""
    ACB = "acb"    # ACB Large Print Guidelines
    MSAC = "msac"  # Microsoft Accessibility Checker / WCAG baseline


class DocFormat(str, Enum):
    """Document formats a rule can apply to."""
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"


# Shorthand sets for tagging rules
_ALL_FORMATS = frozenset({DocFormat.DOCX, DocFormat.XLSX, DocFormat.PPTX})
_DOCX_ONLY = frozenset({DocFormat.DOCX})
_XLSX_ONLY = frozenset({DocFormat.XLSX})
_PPTX_ONLY = frozenset({DocFormat.PPTX})
_DOCX_PPTX = frozenset({DocFormat.DOCX, DocFormat.PPTX})
_XLSX_PPTX = frozenset({DocFormat.XLSX, DocFormat.PPTX})


@dataclass(frozen=True)
class RuleDef:
    """Audit rule metadata."""
    rule_id: str
    description: str
    severity: Severity
    acb_reference: str
    category: RuleCategory = RuleCategory.ACB
    auto_fixable: bool = True
    formats: frozenset[DocFormat] = _DOCX_ONLY


# Audit rules keyed by rule_id
AUDIT_RULES: dict[str, RuleDef] = {
    "ACB-FONT-FAMILY": RuleDef(
        rule_id="ACB-FONT-FAMILY",
        description="All text must use Arial font",
        severity=Severity.CRITICAL,
        acb_reference="ACB Guidelines Section 1: Font",
        auto_fixable=True,
    ),
    "ACB-FONT-SIZE-BODY": RuleDef(
        rule_id="ACB-FONT-SIZE-BODY",
        description=f"Body text must be {BODY_SIZE_PT}pt minimum",
        severity=Severity.CRITICAL,
        acb_reference="ACB Guidelines Section 1: Font Size",
        auto_fixable=True,
    ),
    "ACB-FONT-SIZE-H1": RuleDef(
        rule_id="ACB-FONT-SIZE-H1",
        description=f"Heading 1 must be {HEADING1_SIZE_PT}pt",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 2: Headings",
        auto_fixable=True,
    ),
    "ACB-FONT-SIZE-H2": RuleDef(
        rule_id="ACB-FONT-SIZE-H2",
        description=f"Heading 2 must be {HEADING2_SIZE_PT}pt",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 2: Headings",
        auto_fixable=True,
    ),
    "ACB-NO-ITALIC": RuleDef(
        rule_id="ACB-NO-ITALIC",
        description="Italic formatting is prohibited",
        severity=Severity.CRITICAL,
        acb_reference="ACB Guidelines Section 3: Emphasis",
        auto_fixable=True,
    ),
    "ACB-BOLD-HEADINGS-ONLY": RuleDef(
        rule_id="ACB-BOLD-HEADINGS-ONLY",
        description="Bold in body text should be underline emphasis instead",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 3: Emphasis",
        auto_fixable=True,
    ),
    "ACB-ALIGNMENT": RuleDef(
        rule_id="ACB-ALIGNMENT",
        description="Text must be flush left (not justified, centered, or right-aligned)",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 4: Alignment",
        auto_fixable=True,
    ),
    "ACB-LINE-SPACING": RuleDef(
        rule_id="ACB-LINE-SPACING",
        description=f"Line spacing must be {LINE_SPACING_MULTIPLE}",
        severity=Severity.MEDIUM,
        acb_reference="ACB Guidelines Section 5: Spacing",
        auto_fixable=True,
    ),
    "ACB-MARGINS": RuleDef(
        rule_id="ACB-MARGINS",
        description="Page margins must be 1 inch on all sides",
        severity=Severity.MEDIUM,
        acb_reference="ACB Guidelines Section 6: Margins",
        auto_fixable=True,
    ),
    "ACB-WIDOW-ORPHAN": RuleDef(
        rule_id="ACB-WIDOW-ORPHAN",
        description="Widow and orphan control must be enabled",
        severity=Severity.LOW,
        acb_reference="ACB Guidelines Section 7: Pagination",
        auto_fixable=True,
    ),
    "ACB-NO-HYPHENATION": RuleDef(
        rule_id="ACB-NO-HYPHENATION",
        description="Automatic hyphenation must be disabled",
        severity=Severity.MEDIUM,
        acb_reference="ACB Guidelines Section 8: Hyphenation",
        auto_fixable=True,
    ),
    "ACB-PAGE-NUMBERS": RuleDef(
        rule_id="ACB-PAGE-NUMBERS",
        description="Page numbers must be present in the footer",
        severity=Severity.MEDIUM,
        acb_reference="ACB Guidelines Section 9: Page Numbers",
        auto_fixable=True,
    ),
    "ACB-HEADING-HIERARCHY": RuleDef(
        rule_id="ACB-HEADING-HIERARCHY",
        description="Heading levels must not skip (e.g., H1 to H3)",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 2: Headings",
        auto_fixable=False,
    ),
    "ACB-NO-ALLCAPS": RuleDef(
        rule_id="ACB-NO-ALLCAPS",
        description="Text must not use ALL CAPS formatting",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 1: Font",
        auto_fixable=True,
    ),
    "ACB-DOC-TITLE": RuleDef(
        rule_id="ACB-DOC-TITLE",
        description="Document must have a title in properties",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 2.4.2 Page Titled",
        auto_fixable=True,
    ),
    "ACB-DOC-LANGUAGE": RuleDef(
        rule_id="ACB-DOC-LANGUAGE",
        description="Document language must be set",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 3.1.1 Language of Page",
        auto_fixable=True,
    ),
    # -----------------------------------------------------------------
    # Microsoft Accessibility Checker (MSAC) rules
    # These mirror checks from the built-in MS Office Accessibility
    # Checker and axe-core WCAG 2.1 rules (cf. extCheck by Jamal Mazrui).
    # Users can toggle this category on/off independently of ACB rules.
    # -----------------------------------------------------------------
    "ACB-MISSING-ALT-TEXT": RuleDef(
        rule_id="ACB-MISSING-ALT-TEXT",
        description="Images and shapes must have alternative text",
        severity=Severity.CRITICAL,
        acb_reference="WCAG 1.1.1 Non-text Content",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_ALL_FORMATS,
    ),
    "ACB-TABLE-HEADER-ROW": RuleDef(
        rule_id="ACB-TABLE-HEADER-ROW",
        description="Tables must have a designated header row",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_DOCX_ONLY,
    ),
    "ACB-LINK-TEXT": RuleDef(
        rule_id="ACB-LINK-TEXT",
        description="Hyperlink text must be descriptive (not 'click here' or a raw URL)",
        severity=Severity.HIGH,
        acb_reference="WCAG 2.4.4 Link Purpose (In Context)",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_ALL_FORMATS,
    ),
    "ACB-FORM-FIELD-LABEL": RuleDef(
        rule_id="ACB-FORM-FIELD-LABEL",
        description="Form fields must have descriptive help text",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
    ),
    "ACB-COMPLEX-TABLE": RuleDef(
        rule_id="ACB-COMPLEX-TABLE",
        description="Tables with both row and column headers may confuse screen readers",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
    ),
    "ACB-EMPTY-TABLE-CELL": RuleDef(
        rule_id="ACB-EMPTY-TABLE-CELL",
        description="Empty table cells should contain a placeholder (dash or N/A)",
        severity=Severity.LOW,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=frozenset({DocFormat.DOCX, DocFormat.XLSX}),
    ),
    "ACB-FLOATING-CONTENT": RuleDef(
        rule_id="ACB-FLOATING-CONTENT",
        description="Floating text boxes may be read out of order by screen readers",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.3.2 Meaningful Sequence",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_DOCX_ONLY,
    ),
    "ACB-FAKE-LIST": RuleDef(
        rule_id="ACB-FAKE-LIST",
        description="Manually typed bullet or number characters should use built-in list styles",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_DOCX_PPTX,
    ),
    "ACB-REPEATED-SPACES": RuleDef(
        rule_id="ACB-REPEATED-SPACES",
        description="Consecutive spaces used for visual layout should be replaced with proper formatting",
        severity=Severity.LOW,
        acb_reference="WCAG 1.3.2 Meaningful Sequence",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_DOCX_ONLY,
    ),
    "ACB-LONG-SECTION": RuleDef(
        rule_id="ACB-LONG-SECTION",
        description="More than 20 paragraphs without a heading impairs screen reader navigation",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 2.4.6 Headings and Labels",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_DOCX_ONLY,
    ),
    "ACB-DUPLICATE-HEADING": RuleDef(
        rule_id="ACB-DUPLICATE-HEADING",
        description="Headings at the same level with identical text create ambiguous navigation",
        severity=Severity.LOW,
        acb_reference="WCAG 2.4.6 Headings and Labels",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_DOCX_PPTX,
    ),
    "ACB-LINK-UNDERLINE": RuleDef(
        rule_id="ACB-LINK-UNDERLINE",
        description="Hyperlinks must be underlined to be distinguishable from body text",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.4.1 Use of Color",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_DOCX_ONLY,
    ),
    "ACB-DOC-AUTHOR": RuleDef(
        rule_id="ACB-DOC-AUTHOR",
        description="Document author should be set in properties",
        severity=Severity.LOW,
        acb_reference="WCAG 2.4.2 Page Titled",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_ALL_FORMATS,
    ),
    # -----------------------------------------------------------------
    # Excel-specific rules  (cf. extCheck by Jamal Mazrui)
    # -----------------------------------------------------------------
    "XLSX-TITLE": RuleDef(
        rule_id="XLSX-TITLE",
        description="Workbook title must be set in document properties",
        severity=Severity.HIGH,
        acb_reference="WCAG 2.4.2 Page Titled",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_XLSX_ONLY,
    ),
    "XLSX-SHEET-NAME": RuleDef(
        rule_id="XLSX-SHEET-NAME",
        description="Worksheet tabs must have descriptive names (not Sheet1, Sheet2)",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 2.4.6 Headings and Labels",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_XLSX_ONLY,
    ),
    "XLSX-TABLE-HEADERS": RuleDef(
        rule_id="XLSX-TABLE-HEADERS",
        description="Excel Tables must have the header row enabled",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_XLSX_ONLY,
    ),
    "XLSX-MERGED-CELLS": RuleDef(
        rule_id="XLSX-MERGED-CELLS",
        description="Merged cells disrupt screen reader table navigation",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_XLSX_ONLY,
    ),
    "XLSX-BLANK-COLUMN-HEADER": RuleDef(
        rule_id="XLSX-BLANK-COLUMN-HEADER",
        description="Table column headers must not be blank or generic",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_XLSX_ONLY,
    ),
    "XLSX-COLOR-ONLY": RuleDef(
        rule_id="XLSX-COLOR-ONLY",
        description="Cells with background color but no text may convey meaning through color alone",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.4.1 Use of Color",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_XLSX_ONLY,
    ),
    "XLSX-HIDDEN-CONTENT": RuleDef(
        rule_id="XLSX-HIDDEN-CONTENT",
        description="Hidden rows or columns may be skipped by screen readers",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.3.2 Meaningful Sequence",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_XLSX_ONLY,
    ),
    "XLSX-HEADER-FROZEN": RuleDef(
        rule_id="XLSX-HEADER-FROZEN",
        description="Header row should be frozen so it stays visible when scrolling",
        severity=Severity.LOW,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_XLSX_ONLY,
    ),
    "XLSX-SHEET-NAME-LENGTH": RuleDef(
        rule_id="XLSX-SHEET-NAME-LENGTH",
        description="Worksheet tab name exceeds 31 characters (Excel maximum)",
        severity=Severity.LOW,
        acb_reference="WCAG 2.4.6 Headings and Labels",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_XLSX_ONLY,
    ),
    # -----------------------------------------------------------------
    # PowerPoint-specific rules  (cf. extCheck by Jamal Mazrui)
    # -----------------------------------------------------------------
    "PPTX-TITLE": RuleDef(
        rule_id="PPTX-TITLE",
        description="Presentation title must be set in document properties",
        severity=Severity.HIGH,
        acb_reference="WCAG 2.4.2 Page Titled",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PPTX_ONLY,
    ),
    "PPTX-SLIDE-TITLE": RuleDef(
        rule_id="PPTX-SLIDE-TITLE",
        description="Every slide must have a unique, non-empty title",
        severity=Severity.CRITICAL,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PPTX_ONLY,
    ),
    "PPTX-READING-ORDER": RuleDef(
        rule_id="PPTX-READING-ORDER",
        description="Slide reading order should match visual layout (top-to-bottom, left-to-right)",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.3.2 Meaningful Sequence",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PPTX_ONLY,
    ),
    "PPTX-TITLE-READING-ORDER": RuleDef(
        rule_id="PPTX-TITLE-READING-ORDER",
        description="Title placeholder should be first in reading order",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.3.2 Meaningful Sequence",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PPTX_ONLY,
    ),
    "PPTX-SMALL-FONT": RuleDef(
        rule_id="PPTX-SMALL-FONT",
        description="Text on slides should be at least 18pt for readability",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.4.3 Contrast (Minimum)",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PPTX_ONLY,
    ),
    "PPTX-SPEAKER-NOTES": RuleDef(
        rule_id="PPTX-SPEAKER-NOTES",
        description="Slides with visual content should have speaker notes for context",
        severity=Severity.LOW,
        acb_reference="WCAG 1.1.1 Non-text Content",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PPTX_ONLY,
    ),
    "PPTX-CHART-ALT-TEXT": RuleDef(
        rule_id="PPTX-CHART-ALT-TEXT",
        description="Charts must have alternative text describing the key finding",
        severity=Severity.CRITICAL,
        acb_reference="WCAG 1.1.1 Non-text Content",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_XLSX_PPTX,
    ),
    "PPTX-DUPLICATE-SLIDE-TITLE": RuleDef(
        rule_id="PPTX-DUPLICATE-SLIDE-TITLE",
        description="Multiple slides share identical titles, creating ambiguous navigation",
        severity=Severity.LOW,
        acb_reference="WCAG 2.4.6 Headings and Labels",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PPTX_ONLY,
    ),
    "PPTX-HEADING-SKIP": RuleDef(
        rule_id="PPTX-HEADING-SKIP",
        description="Heading levels are skipped on a slide (e.g., Title followed by H3)",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PPTX_ONLY,
    ),
}


# Convenience sets for category-based filtering
ACB_RULE_IDS: frozenset[str] = frozenset(
    rid for rid, r in AUDIT_RULES.items() if r.category == RuleCategory.ACB
)
MSAC_RULE_IDS: frozenset[str] = frozenset(
    rid for rid, r in AUDIT_RULES.items() if r.category == RuleCategory.MSAC
)


def rules_for_format(fmt: DocFormat) -> dict[str, RuleDef]:
    """Return only the rules applicable to a given document format."""
    return {rid: r for rid, r in AUDIT_RULES.items() if fmt in r.formats}


DOCX_RULE_IDS: frozenset[str] = frozenset(
    rid for rid, r in AUDIT_RULES.items() if DocFormat.DOCX in r.formats
)
XLSX_RULE_IDS: frozenset[str] = frozenset(
    rid for rid, r in AUDIT_RULES.items() if DocFormat.XLSX in r.formats
)
PPTX_RULE_IDS: frozenset[str] = frozenset(
    rid for rid, r in AUDIT_RULES.items() if DocFormat.PPTX in r.formats
)
