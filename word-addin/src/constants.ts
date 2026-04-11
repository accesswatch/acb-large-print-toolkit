/**
 * ACB Large Print Guidelines -- canonical style specifications.
 *
 * Every constant here is derived from the ACB Large Print Guidelines
 * (revised and approved May 6, 2025, ACB Board of Publications).
 *
 * These values are the single source of truth for the Word add-in,
 * mirroring word-addon/src/acb_large_print/constants.py exactly.
 */

// ---------------------------------------------------------------------------
// Font specifications
// ---------------------------------------------------------------------------

export const FONT_FAMILY = "Arial";

// Point sizes
export const BODY_SIZE_PT = 18.0;
export const HEADING1_SIZE_PT = 22.0;
export const HEADING2_SIZE_PT = 20.0;
export const HEADING3_SIZE_PT = 20.0;
export const LIST_SIZE_PT = 18.0;
export const FOOTER_SIZE_PT = 18.0;
export const MIN_SIZE_PT = 18.0;

// Line spacing
export const LINE_SPACING_MULTIPLE = 1.15; // ACB print spec

// Paragraph spacing (points)
export const SPACE_AFTER_BODY_PT = 12.0;
export const SPACE_BEFORE_H1_PT = 18.0;
export const SPACE_AFTER_H1_PT = 12.0;
export const SPACE_BEFORE_H2_PT = 16.0;
export const SPACE_AFTER_H2_PT = 10.0;
export const SPACE_BEFORE_H3_PT = 14.0;
export const SPACE_AFTER_H3_PT = 8.0;

// Page layout (inches -- converted to points for Office.js: 1 inch = 72 pt)
export const MARGIN_TOP_IN = 1.0;
export const MARGIN_BOTTOM_IN = 1.0;
export const MARGIN_LEFT_IN = 1.0;
export const MARGIN_RIGHT_IN = 1.0;
export const BINDING_EXTRA_IN = 0.5;
export const PAGE_WIDTH_IN = 8.5;
export const PAGE_HEIGHT_IN = 11.0;

// List formatting (inches)
export const LIST_INDENT_IN = 0.5;
export const LIST_HANGING_IN = 0.25;

// Margin tolerance (inches)
export const MARGIN_TOLERANCE_IN = 0.05;

// ---------------------------------------------------------------------------
// Style definitions
// ---------------------------------------------------------------------------

export interface FontDef {
    name: string;
    sizePt: number;
    bold: boolean;
    italic: boolean;
    allCaps: boolean;
}

export interface ParaDef {
    alignment: "Left" | "Centered" | "Right" | "Justified";
    lineSpacing: number;
    spaceBeforePt: number;
    spaceAfterPt: number;
    keepWithNext: boolean;
    leftIndentIn: number;
    hangingIndentIn: number;
}

export interface StyleDef {
    font: FontDef;
    para: ParaDef;
}

function fontDef(overrides: Partial<FontDef> = {}): FontDef {
    return {
        name: FONT_FAMILY,
        sizePt: BODY_SIZE_PT,
        bold: false,
        italic: false,
        allCaps: false,
        ...overrides,
    };
}

function paraDef(overrides: Partial<ParaDef> = {}): ParaDef {
    return {
        alignment: "Left",
        lineSpacing: LINE_SPACING_MULTIPLE,
        spaceBeforePt: 0,
        spaceAfterPt: SPACE_AFTER_BODY_PT,
        keepWithNext: false,
        leftIndentIn: 0,
        hangingIndentIn: 0,
        ...overrides,
    };
}

/** Master style table -- matches Python ACB_STYLES exactly. */
export const ACB_STYLES: Record<string, StyleDef> = {
    Normal: {
        font: fontDef(),
        para: paraDef(),
    },
    "Heading 1": {
        font: fontDef({ sizePt: HEADING1_SIZE_PT, bold: true }),
        para: paraDef({
            spaceBeforePt: SPACE_BEFORE_H1_PT,
            spaceAfterPt: SPACE_AFTER_H1_PT,
            keepWithNext: true,
        }),
    },
    "Heading 2": {
        font: fontDef({ sizePt: HEADING2_SIZE_PT, bold: true }),
        para: paraDef({
            spaceBeforePt: SPACE_BEFORE_H2_PT,
            spaceAfterPt: SPACE_AFTER_H2_PT,
            keepWithNext: true,
        }),
    },
    "Heading 3": {
        font: fontDef({ sizePt: HEADING3_SIZE_PT, bold: true }),
        para: paraDef({
            spaceBeforePt: SPACE_BEFORE_H3_PT,
            spaceAfterPt: SPACE_AFTER_H3_PT,
            keepWithNext: true,
        }),
    },
    "List Bullet": {
        font: fontDef({ sizePt: LIST_SIZE_PT }),
        para: paraDef({
            spaceAfterPt: 0,
            leftIndentIn: LIST_INDENT_IN,
            hangingIndentIn: LIST_HANGING_IN,
        }),
    },
    "List Number": {
        font: fontDef({ sizePt: LIST_SIZE_PT }),
        para: paraDef({
            spaceAfterPt: 0,
            leftIndentIn: LIST_INDENT_IN,
            hangingIndentIn: LIST_HANGING_IN,
        }),
    },
};

// ---------------------------------------------------------------------------
// Audit rule definitions
// ---------------------------------------------------------------------------

export enum Severity {
    CRITICAL = "Critical",
    HIGH = "High",
    MEDIUM = "Medium",
    LOW = "Low",
}

export interface RuleDef {
    ruleId: string;
    description: string;
    severity: Severity;
    acbReference: string;
    autoFixable: boolean;
}

export const AUDIT_RULES: Record<string, RuleDef> = {
    "ACB-FONT-FAMILY": {
        ruleId: "ACB-FONT-FAMILY",
        description: "All text must use Arial font",
        severity: Severity.CRITICAL,
        acbReference: "ACB Guidelines Section 1: Font",
        autoFixable: true,
    },
    "ACB-FONT-SIZE-BODY": {
        ruleId: "ACB-FONT-SIZE-BODY",
        description: `Body text must be ${BODY_SIZE_PT}pt minimum`,
        severity: Severity.CRITICAL,
        acbReference: "ACB Guidelines Section 1: Font Size",
        autoFixable: true,
    },
    "ACB-FONT-SIZE-H1": {
        ruleId: "ACB-FONT-SIZE-H1",
        description: `Heading 1 must be ${HEADING1_SIZE_PT}pt`,
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 2: Headings",
        autoFixable: true,
    },
    "ACB-FONT-SIZE-H2": {
        ruleId: "ACB-FONT-SIZE-H2",
        description: `Heading 2 must be ${HEADING2_SIZE_PT}pt`,
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 2: Headings",
        autoFixable: true,
    },
    "ACB-NO-ITALIC": {
        ruleId: "ACB-NO-ITALIC",
        description: "Italic formatting is prohibited",
        severity: Severity.CRITICAL,
        acbReference: "ACB Guidelines Section 3: Emphasis",
        autoFixable: true,
    },
    "ACB-BOLD-HEADINGS-ONLY": {
        ruleId: "ACB-BOLD-HEADINGS-ONLY",
        description: "Bold in body text should be underline emphasis instead",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 3: Emphasis",
        autoFixable: true,
    },
    "ACB-ALIGNMENT": {
        ruleId: "ACB-ALIGNMENT",
        description: "Text must be flush left (not justified, centered, or right-aligned)",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 4: Alignment",
        autoFixable: true,
    },
    "ACB-LINE-SPACING": {
        ruleId: "ACB-LINE-SPACING",
        description: `Line spacing must be ${LINE_SPACING_MULTIPLE}`,
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 5: Spacing",
        autoFixable: true,
    },
    "ACB-MARGINS": {
        ruleId: "ACB-MARGINS",
        description: "Page margins must be 1 inch on all sides",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 6: Margins",
        autoFixable: true,
    },
    "ACB-WIDOW-ORPHAN": {
        ruleId: "ACB-WIDOW-ORPHAN",
        description: "Widow and orphan control must be enabled",
        severity: Severity.LOW,
        acbReference: "ACB Guidelines Section 7: Pagination",
        autoFixable: true,
    },
    "ACB-NO-HYPHENATION": {
        ruleId: "ACB-NO-HYPHENATION",
        description: "Automatic hyphenation must be disabled",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 8: Hyphenation",
        autoFixable: true,
    },
    "ACB-PAGE-NUMBERS": {
        ruleId: "ACB-PAGE-NUMBERS",
        description: "Page numbers must be present in the footer",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 9: Page Numbers",
        autoFixable: true,
    },
    "ACB-HEADING-HIERARCHY": {
        ruleId: "ACB-HEADING-HIERARCHY",
        description: "Heading levels must not skip (e.g., H1 to H3)",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 2: Headings",
        autoFixable: false,
    },
    "ACB-NO-ALLCAPS": {
        ruleId: "ACB-NO-ALLCAPS",
        description: "Text must not use ALL CAPS formatting",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 1: Font",
        autoFixable: true,
    },
    "ACB-DOC-TITLE": {
        ruleId: "ACB-DOC-TITLE",
        description: "Document must have a title in properties",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.2 Page Titled",
        autoFixable: true,
    },
    "ACB-DOC-LANGUAGE": {
        ruleId: "ACB-DOC-LANGUAGE",
        description: "Document language must be set",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 3.1.1 Language of Page",
        autoFixable: true,
    },
};

/** Severity deduction map for scoring. */
export const SEVERITY_DEDUCTIONS: Record<Severity, number> = {
    [Severity.CRITICAL]: 15,
    [Severity.HIGH]: 10,
    [Severity.MEDIUM]: 5,
    [Severity.LOW]: 2,
};
