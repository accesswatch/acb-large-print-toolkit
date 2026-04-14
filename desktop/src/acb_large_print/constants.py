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
# Default: flush left (0.0) per ACB guidelines.
# When the user unchecks flush-left, values revert to 0.5 / 0.25.
LIST_INDENT_IN = 0.0
LIST_HANGING_IN = 0.0

# Named presets for UI controls (left_indent, hanging_indent)
LIST_INDENT_FLUSH = (0.0, 0.0)  # Flush left -- ACB default
LIST_INDENT_STANDARD = (0.5, 0.25)  # Standard Word indent (user override)

# Paragraph indentation (inches)
# Default: flush left (0.0) per ACB guidelines Section 4: Alignment.
# Non-list paragraphs should have no left indent or first-line indent.
PARA_INDENT_IN = 0.0  # Default: flush left (ACB compliant)
FIRST_LINE_INDENT_IN = 0.0  # Default: no first-line indent
PARA_INDENT_FLUSH = 0.0  # Named preset
PARA_INDENT_BLOCKQUOTE = 0.5  # Common blockquote indent if user opts in

# AI heading detection
HEADING_CONFIDENCE_THRESHOLD = 50  # Minimum heuristic score (0-100)
HEADING_HIGH_CONFIDENCE = 75  # Score at which heuristic alone is trusted


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

    alignment: str = "LEFT"  # LEFT | CENTER | RIGHT | JUSTIFY
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

    ACB = "acb"  # ACB Large Print Guidelines
    MSAC = "msac"  # Microsoft Accessibility Checker / WCAG baseline


class DocFormat(str, Enum):
    """Document formats a rule can apply to."""

    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    MD = "md"
    PDF = "pdf"
    EPUB = "epub"


# Shorthand sets for tagging rules
_ALL_FORMATS = frozenset({DocFormat.DOCX, DocFormat.XLSX, DocFormat.PPTX})
_ALL_WITH_MD_PDF = frozenset(DocFormat)
_DOCX_ONLY = frozenset({DocFormat.DOCX})
_XLSX_ONLY = frozenset({DocFormat.XLSX})
_PPTX_ONLY = frozenset({DocFormat.PPTX})
_MD_ONLY = frozenset({DocFormat.MD})
_PDF_ONLY = frozenset({DocFormat.PDF})
_EPUB_ONLY = frozenset({DocFormat.EPUB})
_DOCX_PPTX = frozenset({DocFormat.DOCX, DocFormat.PPTX})
_XLSX_PPTX = frozenset({DocFormat.XLSX, DocFormat.PPTX})
_MD_PDF = frozenset({DocFormat.MD, DocFormat.PDF})


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


# Fix-record categories (used by FixRecord and reporter grouping)
FIX_CATEGORY_HEADINGS = "Headings"
FIX_CATEGORY_FONT = "Font Family & Size"
FIX_CATEGORY_ALIGNMENT = "Alignment & Indentation"
FIX_CATEGORY_EMPHASIS = "Emphasis"
FIX_CATEGORY_SPACING = "Spacing"
FIX_CATEGORY_PAGE = "Page Setup"
FIX_CATEGORY_PROPS = "Document Properties"


@dataclass
class FixRecord:
    """A single fix applied by the fixer."""

    rule_id: str
    category: str  # One of FIX_CATEGORY_* constants
    description: str  # Human-readable description of what was fixed
    location: str = ""  # e.g. "Paragraph 5", "Style: Heading 1"


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
    "ACB-LIST-INDENT": RuleDef(
        rule_id="ACB-LIST-INDENT",
        description="List indentation must match the configured indent setting",
        severity=Severity.MEDIUM,
        acb_reference="ACB Guidelines Section 4: Alignment",
        auto_fixable=True,
    ),
    "ACB-PARA-INDENT": RuleDef(
        rule_id="ACB-PARA-INDENT",
        description="Non-list paragraph left indent must match the configured setting (flush left by default)",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 4: Alignment",
        auto_fixable=True,
    ),
    "ACB-FIRST-LINE-INDENT": RuleDef(
        rule_id="ACB-FIRST-LINE-INDENT",
        description="First-line paragraph indent must match the configured setting (zero by default)",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 4: Alignment",
        auto_fixable=True,
    ),
    "ACB-BLOCKQUOTE-INDENT": RuleDef(
        rule_id="ACB-BLOCKQUOTE-INDENT",
        description="Blockquote-style indentation detected; should be flush left or use a named style",
        severity=Severity.MEDIUM,
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
    "ACB-FAUX-HEADING": RuleDef(
        rule_id="ACB-FAUX-HEADING",
        description="Paragraph formatted like a heading but without a heading style",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_DOCX_ONLY,
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
    # -----------------------------------------------------------------
    # Markdown-specific rules
    # -----------------------------------------------------------------
    "MD-HEADING-HIERARCHY": RuleDef(
        rule_id="MD-HEADING-HIERARCHY",
        description="Heading levels must not skip (e.g., # to ### without ##)",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_MD_ONLY,
    ),
    "MD-MULTIPLE-H1": RuleDef(
        rule_id="MD-MULTIPLE-H1",
        description="Document should have only one top-level heading (H1)",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_MD_ONLY,
    ),
    "MD-NO-ITALIC": RuleDef(
        rule_id="MD-NO-ITALIC",
        description="Italic emphasis (*text* or _text_) is prohibited by ACB guidelines",
        severity=Severity.CRITICAL,
        acb_reference="ACB Guidelines Section 3: Emphasis",
        category=RuleCategory.ACB,
        auto_fixable=True,
        formats=_MD_ONLY,
    ),
    "MD-BOLD-EMPHASIS": RuleDef(
        rule_id="MD-BOLD-EMPHASIS",
        description="Bold (**text**) should not be used for body emphasis; use <u>text</u> instead",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 3: Emphasis",
        category=RuleCategory.ACB,
        auto_fixable=False,
        formats=_MD_ONLY,
    ),
    "MD-BARE-URL": RuleDef(
        rule_id="MD-BARE-URL",
        description="URLs should be wrapped in descriptive link text, not shown raw",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 2.4.4 Link Purpose (In Context)",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_MD_ONLY,
    ),
    "MD-AMBIGUOUS-LINK": RuleDef(
        rule_id="MD-AMBIGUOUS-LINK",
        description="Link text must be descriptive (not 'click here', 'here', 'link', 'read more')",
        severity=Severity.HIGH,
        acb_reference="WCAG 2.4.4 Link Purpose (In Context)",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_MD_ONLY,
    ),
    "MD-MISSING-ALT-TEXT": RuleDef(
        rule_id="MD-MISSING-ALT-TEXT",
        description="Images must have alternative text: ![description](url)",
        severity=Severity.CRITICAL,
        acb_reference="WCAG 1.1.1 Non-text Content",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_MD_ONLY,
    ),
    "MD-NO-EMOJI": RuleDef(
        rule_id="MD-NO-EMOJI",
        description="Emoji characters must be removed or replaced with plain text equivalents",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.3.3 Sensory Characteristics",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_MD_ONLY,
    ),
    "MD-TABLE-NO-DESCRIPTION": RuleDef(
        rule_id="MD-TABLE-NO-DESCRIPTION",
        description="Tables should be preceded by a text description or caption",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_MD_ONLY,
    ),
    "MD-EM-DASH": RuleDef(
        rule_id="MD-EM-DASH",
        description="Em-dashes and en-dashes should be replaced with plain dashes",
        severity=Severity.MEDIUM,
        acb_reference="Cognitive Accessibility",
        category=RuleCategory.MSAC,
        auto_fixable=True,
        formats=_MD_ONLY,
    ),
    # -----------------------------------------------------------------
    # PDF-specific rules
    # -----------------------------------------------------------------
    "PDF-TITLE": RuleDef(
        rule_id="PDF-TITLE",
        description="PDF must have a title set in document metadata",
        severity=Severity.HIGH,
        acb_reference="WCAG 2.4.2 Page Titled",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PDF_ONLY,
    ),
    "PDF-LANGUAGE": RuleDef(
        rule_id="PDF-LANGUAGE",
        description="PDF must have a language set in document metadata",
        severity=Severity.HIGH,
        acb_reference="WCAG 3.1.1 Language of Page",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PDF_ONLY,
    ),
    "PDF-TAGGED": RuleDef(
        rule_id="PDF-TAGGED",
        description="PDF must be tagged (structured) for screen reader access",
        severity=Severity.CRITICAL,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PDF_ONLY,
    ),
    "PDF-FONT-SIZE": RuleDef(
        rule_id="PDF-FONT-SIZE",
        description="Text must be at least 18pt per ACB guidelines",
        severity=Severity.CRITICAL,
        acb_reference="ACB Guidelines Section 1: Font",
        category=RuleCategory.ACB,
        auto_fixable=False,
        formats=_PDF_ONLY,
    ),
    "PDF-FONT-FAMILY": RuleDef(
        rule_id="PDF-FONT-FAMILY",
        description="Text should use Arial or a comparable sans-serif font",
        severity=Severity.HIGH,
        acb_reference="ACB Guidelines Section 1: Font",
        category=RuleCategory.ACB,
        auto_fixable=False,
        formats=_PDF_ONLY,
    ),
    "PDF-NO-IMAGES-OF-TEXT": RuleDef(
        rule_id="PDF-NO-IMAGES-OF-TEXT",
        description="Scanned or image-only pages cannot be read by screen readers",
        severity=Severity.CRITICAL,
        acb_reference="WCAG 1.4.5 Images of Text",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PDF_ONLY,
    ),
    "PDF-BOOKMARKS": RuleDef(
        rule_id="PDF-BOOKMARKS",
        description="Multi-page PDFs should have bookmarks for navigation",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 2.4.5 Multiple Ways",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_PDF_ONLY,
    ),
    # -----------------------------------------------------------------
    # ePub-specific rules
    # -----------------------------------------------------------------
    "EPUB-TITLE": RuleDef(
        rule_id="EPUB-TITLE",
        description="ePub must have a title set in OPF metadata",
        severity=Severity.HIGH,
        acb_reference="WCAG 2.4.2 Page Titled",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-LANGUAGE": RuleDef(
        rule_id="EPUB-LANGUAGE",
        description="ePub must have a language set in OPF metadata",
        severity=Severity.HIGH,
        acb_reference="WCAG 3.1.1 Language of Page",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-NAV-DOCUMENT": RuleDef(
        rule_id="EPUB-NAV-DOCUMENT",
        description="ePub must include a navigation document (table of contents)",
        severity=Severity.HIGH,
        acb_reference="WCAG 2.4.5 Multiple Ways",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-HEADING-HIERARCHY": RuleDef(
        rule_id="EPUB-HEADING-HIERARCHY",
        description="Heading levels must not skip (e.g., H1 to H3 without H2)",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-MISSING-ALT-TEXT": RuleDef(
        rule_id="EPUB-MISSING-ALT-TEXT",
        description="Images in ePub content must have alternative text",
        severity=Severity.CRITICAL,
        acb_reference="WCAG 1.1.1 Non-text Content",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-TABLE-HEADERS": RuleDef(
        rule_id="EPUB-TABLE-HEADERS",
        description="Tables in ePub content must use <th> header cells",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.3.1 Info and Relationships",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-ACCESSIBILITY-METADATA": RuleDef(
        rule_id="EPUB-ACCESSIBILITY-METADATA",
        description="ePub should include schema.org accessibility metadata (accessMode, accessibilityFeature)",
        severity=Severity.MEDIUM,
        acb_reference="EPUB Accessibility 1.1",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-LINK-TEXT": RuleDef(
        rule_id="EPUB-LINK-TEXT",
        description="Hyperlink text must be descriptive (not 'click here' or a raw URL)",
        severity=Severity.HIGH,
        acb_reference="WCAG 2.4.4 Link Purpose (In Context)",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-ACCESSIBILITY-HAZARD": RuleDef(
        rule_id="EPUB-ACCESSIBILITY-HAZARD",
        description="ePub should declare accessibility hazards (flashing, motion, sound) in metadata",
        severity=Severity.MEDIUM,
        acb_reference="EPUB Accessibility 1.1",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-ACCESS-MODE-SUFFICIENT": RuleDef(
        rule_id="EPUB-ACCESS-MODE-SUFFICIENT",
        description="ePub should declare sufficient access modes (textual, visual, auditory)",
        severity=Severity.MEDIUM,
        acb_reference="EPUB Accessibility 1.1",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-PAGE-LIST": RuleDef(
        rule_id="EPUB-PAGE-LIST",
        description="ePub with page navigation metadata should include a page list",
        severity=Severity.MEDIUM,
        acb_reference="EPUB Accessibility 1.1",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-PAGE-SOURCE": RuleDef(
        rule_id="EPUB-PAGE-SOURCE",
        description="Reflowable ePub with a page list should declare dc:source or pageBreakSource",
        severity=Severity.MEDIUM,
        acb_reference="EPUB Accessibility 1.1",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-MATHML-ALT": RuleDef(
        rule_id="EPUB-MATHML-ALT",
        description="MathML elements must have an alttext attribute or annotation for screen readers",
        severity=Severity.HIGH,
        acb_reference="WCAG 1.1.1 Non-text Content",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "EPUB-TEXT-INDENT": RuleDef(
        rule_id="EPUB-TEXT-INDENT",
        description="Body text in ePub content has CSS text-indent or margin-left indentation",
        severity=Severity.MEDIUM,
        acb_reference="ACB Guidelines Section 4: Alignment",
        category=RuleCategory.ACB,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    # Catch-all for Ace findings that don't map to other EPUB rules
    "ACE-EPUB-CHECK": RuleDef(
        rule_id="ACE-EPUB-CHECK",
        description="EPUB accessibility issue detected by DAISY Ace checker",
        severity=Severity.MEDIUM,
        acb_reference="EPUB Accessibility 1.1",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
    ),
    "ACE-AXE-CHECK": RuleDef(
        rule_id="ACE-AXE-CHECK",
        description="HTML accessibility issue detected by axe-core via DAISY Ace",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 2.2 Level AA",
        category=RuleCategory.MSAC,
        auto_fixable=False,
        formats=_EPUB_ONLY,
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
MD_RULE_IDS: frozenset[str] = frozenset(
    rid for rid, r in AUDIT_RULES.items() if DocFormat.MD in r.formats
)
PDF_RULE_IDS: frozenset[str] = frozenset(
    rid for rid, r in AUDIT_RULES.items() if DocFormat.PDF in r.formats
)
EPUB_RULE_IDS: frozenset[str] = frozenset(
    rid for rid, r in AUDIT_RULES.items() if DocFormat.EPUB in r.formats
)
