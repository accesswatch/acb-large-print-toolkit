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


@dataclass(frozen=True)
class RuleDef:
    """Audit rule metadata."""
    rule_id: str
    description: str
    severity: Severity
    acb_reference: str
    auto_fixable: bool = True


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
        auto_fixable=False,
    ),
    "ACB-DOC-LANGUAGE": RuleDef(
        rule_id="ACB-DOC-LANGUAGE",
        description="Document language must be set",
        severity=Severity.MEDIUM,
        acb_reference="WCAG 3.1.1 Language of Page",
        auto_fixable=True,
    ),
}
