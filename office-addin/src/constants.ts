/**
 * ACB Large Print Guidelines -- canonical style specifications.
 *
 * Every constant here is derived from the ACB Large Print Guidelines
 * (revised and approved May 6, 2025, ACB Board of Publications).
 *
 * These values are the single source of truth for the Word add-in,
 * mirroring desktop/src/acb_large_print/constants.py exactly.
 */

// ---------------------------------------------------------------------------
// Font specifications
// ---------------------------------------------------------------------------

export const FONT_FAMILY = "Arial";

// APH references (Research-Based Large Print Guidelines).
// Arial remains the enforced ACB default in current rule logic.
export const APH_ACCEPTED_FONT_FAMILIES = [
    "APHont",
    "Verdana",
    "Tahoma",
    "Helvetica",
    "Antique Olive",
    "Comic Sans",
] as const;
export const APH_LINE_SPACING_RECOMMENDED = 1.25;

export enum StandardsProfile {
    ACB_2025 = "acb_2025",
    APH_SUBMISSION = "aph_submission",
    COMBINED_STRICT = "combined_strict",
}

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

// List formatting (inches) -- default flush left per ACB alignment rules
export const LIST_INDENT_IN = 0.0;
export const LIST_HANGING_IN = 0.0;

// Presets: [leftIndent, hangingIndent] in inches
export const LIST_INDENT_FLUSH: [number, number] = [0.0, 0.0];
export const LIST_INDENT_STANDARD: [number, number] = [0.5, 0.25];

// Paragraph indentation (inches) -- default flush left per ACB alignment rules
export const PARA_INDENT_IN = 0.0;
export const FIRST_LINE_INDENT_IN = 0.0;
export const PARA_INDENT_FLUSH = 0.0;
export const PARA_INDENT_BLOCKQUOTE = 0.5;

// Margin tolerance (inches)
export const MARGIN_TOLERANCE_IN = 0.05;

// ---------------------------------------------------------------------------
// Heading detection thresholds
// ---------------------------------------------------------------------------

export const HEADING_CONFIDENCE_THRESHOLD = 50;
export const HEADING_HIGH_CONFIDENCE = 75;

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
    "Heading 4": {
        font: fontDef({ sizePt: HEADING3_SIZE_PT, bold: true }),
        para: paraDef({
            spaceBeforePt: SPACE_BEFORE_H3_PT,
            spaceAfterPt: SPACE_AFTER_H3_PT,
            keepWithNext: true,
        }),
    },
    "Heading 5": {
        font: fontDef({ sizePt: HEADING3_SIZE_PT, bold: true }),
        para: paraDef({
            spaceBeforePt: SPACE_BEFORE_H3_PT,
            spaceAfterPt: SPACE_AFTER_H3_PT,
            keepWithNext: true,
        }),
    },
    "Heading 6": {
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

/**
 * Style names that accept user-supplied font-size overrides.
 *
 * Matches Python `OVERRIDABLE_STYLE_NAMES` in `desktop/src/acb_large_print/constants.py`.
 */
export const OVERRIDABLE_STYLE_NAMES = [
    "Normal",
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Heading 4",
    "Heading 5",
    "Heading 6",
] as const;

/** Lower bound for user-supplied font sizes (matches Python `MIN_USER_FONT_PT`). */
export const MIN_USER_FONT_PT = 8.0;
/** Upper bound for user-supplied font sizes (matches Python `MAX_USER_FONT_PT`). */
export const MAX_USER_FONT_PT = 96.0;

/** User-supplied per-style size overrides: { "Normal": 20, "Heading 1": 26, ... } */
export type StyleSizeOverrides = Partial<Record<string, number>>;

function clampSize(pt: number): number {
    return Math.max(MIN_USER_FONT_PT, Math.min(MAX_USER_FONT_PT, pt));
}

/**
 * Apply user size overrides on top of `ACB_STYLES`. Mirrors Python
 * `effective_styles()` -- body overrides also propagate to List Bullet/Number.
 */
export function effectiveStyles(
    overrides?: StyleSizeOverrides,
): Record<string, StyleDef> {
    if (!overrides) {
        return { ...ACB_STYLES };
    }
    const cleaned: Record<string, number> = {};
    for (const [name, value] of Object.entries(overrides)) {
        if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
            continue;
        }
        cleaned[name] = clampSize(value);
    }
    if (Object.keys(cleaned).length === 0) {
        return { ...ACB_STYLES };
    }

    const out: Record<string, StyleDef> = {};
    const bodyPt = cleaned["Normal"];
    for (const [name, def] of Object.entries(ACB_STYLES)) {
        let target = cleaned[name];
        if (target === undefined && bodyPt !== undefined &&
            (name === "List Bullet" || name === "List Number")) {
            target = bodyPt;
        }
        if (target === undefined) {
            out[name] = def;
            continue;
        }
        out[name] = {
            font: { ...def.font, sizePt: target },
            para: def.para,
        };
    }
    return out;
}

/**
 * Effective body-size floor used for run-level minimum-size checks.
 * Mirrors Python `effective_min_body_pt()`.
 */
export function effectiveMinBodyPt(overrides?: StyleSizeOverrides): number {
    if (overrides && typeof overrides["Normal"] === "number" && overrides["Normal"]! > 0) {
        return clampSize(overrides["Normal"]!);
    }
    return MIN_SIZE_PT;
}

// ---------------------------------------------------------------------------
// Audit rule definitions
// ---------------------------------------------------------------------------

export enum Severity {
    CRITICAL = "Critical",
    HIGH = "High",
    MEDIUM = "Medium",
    LOW = "Low",
}

export enum RuleCategory {
    ACB = "acb",    // ACB Large Print Guidelines
    MSAC = "msac",  // Microsoft Accessibility Checker / WCAG baseline
}

export enum DocFormat {
    DOCX = "docx",
    XLSX = "xlsx",
    PPTX = "pptx",
    MD = "md",
    EPUB = "epub",
}

const ALL_FORMATS: ReadonlySet<DocFormat> = new Set([DocFormat.DOCX, DocFormat.XLSX, DocFormat.PPTX]);
const DOCX_ONLY: ReadonlySet<DocFormat> = new Set([DocFormat.DOCX]);
const XLSX_ONLY: ReadonlySet<DocFormat> = new Set([DocFormat.XLSX]);
const PPTX_ONLY: ReadonlySet<DocFormat> = new Set([DocFormat.PPTX]);
const MD_ONLY: ReadonlySet<DocFormat> = new Set([DocFormat.MD]);
const EPUB_ONLY: ReadonlySet<DocFormat> = new Set([DocFormat.EPUB]);
const DOCX_PPTX: ReadonlySet<DocFormat> = new Set([DocFormat.DOCX, DocFormat.PPTX]);

export interface RuleDef {
    ruleId: string;
    description: string;
    severity: Severity;
    acbReference: string;
    category: RuleCategory;
    autoFixable: boolean;
    formats: ReadonlySet<DocFormat>;
}

export const AUDIT_RULES: Record<string, RuleDef> = {
    "ACB-FONT-FAMILY": {
        ruleId: "ACB-FONT-FAMILY",
        description: "All text must use Arial font",
        severity: Severity.CRITICAL,
        acbReference: "ACB Guidelines Section 1: Font",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-FONT-SIZE-BODY": {
        ruleId: "ACB-FONT-SIZE-BODY",
        description: `Body text must be ${BODY_SIZE_PT}pt minimum`,
        severity: Severity.CRITICAL,
        acbReference: "ACB Guidelines Section 1: Font Size",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-FONT-SIZE-H1": {
        ruleId: "ACB-FONT-SIZE-H1",
        description: `Heading 1 must be ${HEADING1_SIZE_PT}pt`,
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 2: Headings",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-FONT-SIZE-H2": {
        ruleId: "ACB-FONT-SIZE-H2",
        description: `Heading 2 must be ${HEADING2_SIZE_PT}pt`,
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 2: Headings",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-NO-ITALIC": {
        ruleId: "ACB-NO-ITALIC",
        description: "Italic formatting is prohibited",
        severity: Severity.CRITICAL,
        acbReference: "ACB Guidelines Section 3: Emphasis",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-BOLD-HEADINGS-ONLY": {
        ruleId: "ACB-BOLD-HEADINGS-ONLY",
        description: "Bold in body text should be underline emphasis instead",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 3: Emphasis",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-ALIGNMENT": {
        ruleId: "ACB-ALIGNMENT",
        description: "Text must be flush left (not justified, centered, or right-aligned)",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 4: Alignment",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-LINE-SPACING": {
        ruleId: "ACB-LINE-SPACING",
        description: `Line spacing must be ${LINE_SPACING_MULTIPLE}`,
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 5: Spacing",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-MARGINS": {
        ruleId: "ACB-MARGINS",
        description: "Page margins must be 1 inch on all sides",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 6: Margins",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-WIDOW-ORPHAN": {
        ruleId: "ACB-WIDOW-ORPHAN",
        description: "Widow and orphan control must be enabled",
        severity: Severity.LOW,
        acbReference: "ACB Guidelines Section 7: Pagination",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-NO-HYPHENATION": {
        ruleId: "ACB-NO-HYPHENATION",
        description: "Automatic hyphenation must be disabled",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 8: Hyphenation",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-PAGE-NUMBERS": {
        ruleId: "ACB-PAGE-NUMBERS",
        description: "Page numbers must be present in the footer",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 9: Page Numbers",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-HEADING-HIERARCHY": {
        ruleId: "ACB-HEADING-HIERARCHY",
        description: "Heading levels must not skip (e.g., H1 to H3)",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 2: Headings",
        category: RuleCategory.ACB,
        autoFixable: false,
        formats: DOCX_ONLY,
    },
    "ACB-NO-ALLCAPS": {
        ruleId: "ACB-NO-ALLCAPS",
        description: "Text must not use ALL CAPS formatting",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 1: Font",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-DOC-TITLE": {
        ruleId: "ACB-DOC-TITLE",
        description: "Document must have a title in properties",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-DOC-LANGUAGE": {
        ruleId: "ACB-DOC-LANGUAGE",
        description: "Document language must be set",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 3.1.1 Language of Page",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-LIST-INDENT": {
        ruleId: "ACB-LIST-INDENT",
        description: "List item indentation does not match the configured list indent value",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 4: Alignment",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-PARA-INDENT": {
        ruleId: "ACB-PARA-INDENT",
        description: "Paragraph left indent does not match the configured setting; ACB defaults to flush-left alignment",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 4: Alignment",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-FIRST-LINE-INDENT": {
        ruleId: "ACB-FIRST-LINE-INDENT",
        description: "Paragraph first-line indent does not match the configured setting; ACB defaults to no indentation",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 4: Alignment",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-BLOCKQUOTE-INDENT": {
        ruleId: "ACB-BLOCKQUOTE-INDENT",
        description: "Paragraph appears to be an indented block quote; consider using a proper style instead of manual indentation",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 4: Alignment",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    // -----------------------------------------------------------------
    // Microsoft Accessibility Checker (MSAC) rules
    // -----------------------------------------------------------------
    "ACB-MISSING-ALT-TEXT": {
        ruleId: "ACB-MISSING-ALT-TEXT",
        description: "Images and shapes must have alternative text",
        severity: Severity.CRITICAL,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: ALL_FORMATS,
    },
    "ACB-TABLE-HEADER-ROW": {
        ruleId: "ACB-TABLE-HEADER-ROW",
        description: "Tables must have a designated header row",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-LINK-TEXT": {
        ruleId: "ACB-LINK-TEXT",
        description: "Hyperlink text must be descriptive (not 'click here' or a raw URL)",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.4 Link Purpose (In Context)",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: ALL_FORMATS,
    },
    "ACB-FORM-FIELD-LABEL": {
        ruleId: "ACB-FORM-FIELD-LABEL",
        description: "Form fields must have descriptive help text",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: DOCX_ONLY,
    },
    "ACB-COMPLEX-TABLE": {
        ruleId: "ACB-COMPLEX-TABLE",
        description: "Tables with both row and column headers may confuse screen readers",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: DOCX_ONLY,
    },
    "ACB-EMPTY-TABLE-CELL": {
        ruleId: "ACB-EMPTY-TABLE-CELL",
        description: "Empty table cells should contain a placeholder (dash or N/A)",
        severity: Severity.LOW,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: true,
        formats: new Set([DocFormat.DOCX, DocFormat.XLSX]),
    },
    "ACB-FLOATING-CONTENT": {
        ruleId: "ACB-FLOATING-CONTENT",
        description: "Floating text boxes may be read out of order by screen readers",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.2 Meaningful Sequence",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: DOCX_ONLY,
    },
    "ACB-FAKE-LIST": {
        ruleId: "ACB-FAKE-LIST",
        description: "Manually typed bullet or number characters should use built-in list styles",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: DOCX_PPTX,
    },
    "ACB-REPEATED-SPACES": {
        ruleId: "ACB-REPEATED-SPACES",
        description: "Consecutive spaces used for visual layout should be replaced with proper formatting",
        severity: Severity.LOW,
        acbReference: "WCAG 1.3.2 Meaningful Sequence",
        category: RuleCategory.MSAC,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-LONG-SECTION": {
        ruleId: "ACB-LONG-SECTION",
        description: "More than 20 paragraphs without a heading impairs screen reader navigation",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: DOCX_ONLY,
    },
    "ACB-DUPLICATE-HEADING": {
        ruleId: "ACB-DUPLICATE-HEADING",
        description: "Headings at the same level with identical text create ambiguous navigation",
        severity: Severity.LOW,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: DOCX_PPTX,
    },
    "ACB-LINK-UNDERLINE": {
        ruleId: "ACB-LINK-UNDERLINE",
        description: "Hyperlinks must be underlined to be distinguishable from body text",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.4.1 Use of Color",
        category: RuleCategory.MSAC,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-DOC-AUTHOR": {
        ruleId: "ACB-DOC-AUTHOR",
        description: "Document author should be set in properties",
        severity: Severity.LOW,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: ALL_FORMATS,
    },
    // -----------------------------------------------------------------
    // Excel-specific MSAC rules
    // -----------------------------------------------------------------
    "XLSX-TITLE": {
        ruleId: "XLSX-TITLE",
        description: "Workbook title must be set in document properties",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    "XLSX-SHEET-NAME": {
        ruleId: "XLSX-SHEET-NAME",
        description: "Worksheet tabs must have descriptive names (not Sheet1, Sheet2)",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    "XLSX-TABLE-HEADERS": {
        ruleId: "XLSX-TABLE-HEADERS",
        description: "Excel Tables must have the header row enabled",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: true,
        formats: XLSX_ONLY,
    },
    "XLSX-MERGED-CELLS": {
        ruleId: "XLSX-MERGED-CELLS",
        description: "Merged cells disrupt screen reader table navigation",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    "XLSX-ALT-TEXT": {
        ruleId: "XLSX-ALT-TEXT",
        description: "Charts, images, and shapes must have alternative text",
        severity: Severity.CRITICAL,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    "XLSX-BLANK-COLUMN-HEADER": {
        ruleId: "XLSX-BLANK-COLUMN-HEADER",
        description: "Table column headers must not be blank or generic",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    "XLSX-COLOR-ONLY": {
        ruleId: "XLSX-COLOR-ONLY",
        description: "Cells with background color but no text may convey meaning through color alone",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.4.1 Use of Color",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    "XLSX-HIDDEN-CONTENT": {
        ruleId: "XLSX-HIDDEN-CONTENT",
        description: "Hidden rows or columns may be skipped by screen readers",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.2 Meaningful Sequence",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    "XLSX-HEADER-FROZEN": {
        ruleId: "XLSX-HEADER-FROZEN",
        description: "Header row should be frozen so it stays visible when scrolling",
        severity: Severity.LOW,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: true,
        formats: XLSX_ONLY,
    },
    "XLSX-SHEET-NAME-LENGTH": {
        ruleId: "XLSX-SHEET-NAME-LENGTH",
        description: "Worksheet tab name exceeds 31 characters (Excel maximum)",
        severity: Severity.LOW,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    "XLSX-DOC-TITLE": {
        ruleId: "XLSX-DOC-TITLE",
        description: "Workbook must have a title in properties",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    // -----------------------------------------------------------------
    // PowerPoint-specific MSAC rules
    // -----------------------------------------------------------------
    "PPTX-TITLE": {
        ruleId: "PPTX-TITLE",
        description: "Presentation title must be set in document properties",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-SLIDE-TITLE": {
        ruleId: "PPTX-SLIDE-TITLE",
        description: "Every slide must have a unique, non-empty title",
        severity: Severity.CRITICAL,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-READING-ORDER": {
        ruleId: "PPTX-READING-ORDER",
        description: "Slide reading order should match visual layout (top-to-bottom, left-to-right)",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.2 Meaningful Sequence",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-TITLE-READING-ORDER": {
        ruleId: "PPTX-TITLE-READING-ORDER",
        description: "Title placeholder should be first in reading order",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.2 Meaningful Sequence",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-ALT-TEXT": {
        ruleId: "PPTX-ALT-TEXT",
        description: "Images and shapes must have alternative text",
        severity: Severity.CRITICAL,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-SMALL-FONT": {
        ruleId: "PPTX-SMALL-FONT",
        description: "Text on slides should be at least 18pt for readability",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.4.3 Contrast (Minimum)",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-SPEAKER-NOTES": {
        ruleId: "PPTX-SPEAKER-NOTES",
        description: "Slides with visual content should have speaker notes for context",
        severity: Severity.LOW,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-DUPLICATE-TITLE": {
        ruleId: "PPTX-DUPLICATE-TITLE",
        description: "Multiple slides share the same title, creating ambiguous navigation",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-TABLE-HEADER": {
        ruleId: "PPTX-TABLE-HEADER",
        description: "Tables on slides must have a designated header row",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-CHART-ALT-TEXT": {
        ruleId: "PPTX-CHART-ALT-TEXT",
        description: "Charts must have alternative text or data table fallback",
        severity: Severity.CRITICAL,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: new Set([DocFormat.XLSX, DocFormat.PPTX]),
    },
    "PPTX-LINK-TEXT": {
        ruleId: "PPTX-LINK-TEXT",
        description: "Hyperlink text must be descriptive (not 'click here' or raw URL)",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.4 Link Purpose (In Context)",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-DUPLICATE-SLIDE-TITLE": {
        ruleId: "PPTX-DUPLICATE-SLIDE-TITLE",
        description: "Multiple slides share identical titles, creating ambiguous navigation",
        severity: Severity.LOW,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-HEADING-SKIP": {
        ruleId: "PPTX-HEADING-SKIP",
        description: "Heading levels are skipped on a slide (e.g., Title followed by H3)",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    // -----------------------------------------------------------------
    // PPTX timing and animation rules (WCAG 2.2 / 2.3)
    // -----------------------------------------------------------------
    "PPTX-FAST-AUTO-ADVANCE": {
        ruleId: "PPTX-FAST-AUTO-ADVANCE",
        description: "Slide auto-advances in less than 3 seconds, giving users insufficient reading time (WCAG 2.2.1)",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.2.1 Timing Adjustable",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-REPEATING-ANIMATION": {
        ruleId: "PPTX-REPEATING-ANIMATION",
        description: "Slide contains an animation that loops indefinitely; users cannot pause or stop it (WCAG 2.2.2)",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.2.2 Pause, Stop, Hide",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-RAPID-AUTO-ANIMATION": {
        ruleId: "PPTX-RAPID-AUTO-ANIMATION",
        description: "Multiple animation effects fire in rapid succession (under 1 second apart), creating a distracting or seizure-risk experience",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.2.2 Pause, Stop, Hide",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    "PPTX-FAST-TRANSITION": {
        ruleId: "PPTX-FAST-TRANSITION",
        description: "Slide transition speed is set to 'fast', which may trigger discomfort for vestibular-sensitive users (WCAG 2.3.3)",
        severity: Severity.LOW,
        acbReference: "WCAG 2.3.3 Animation from Interactions",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: PPTX_ONLY,
    },
    // -----------------------------------------------------------------
    // XLSX layout and naming rules
    // -----------------------------------------------------------------
    "XLSX-BLANK-ROWS-LAYOUT": {
        ruleId: "XLSX-BLANK-ROWS-LAYOUT",
        description: "Three or more consecutive blank rows used for visual spacing confuse screen reader navigation (WCAG 1.3.2)",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.2 Meaningful Sequence",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    "XLSX-DEFAULT-TABLE-NAME": {
        ruleId: "XLSX-DEFAULT-TABLE-NAME",
        description: "Excel Table has a default auto-generated name (e.g. Table1); rename it to describe the data it contains (WCAG 2.4.6)",
        severity: Severity.LOW,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: XLSX_ONLY,
    },
    // -----------------------------------------------------------------
    // Markdown-specific rules
    // -----------------------------------------------------------------
    "MD-ALT-TEXT-FILENAME": {
        ruleId: "MD-ALT-TEXT-FILENAME",
        description: "Image alt text appears to be a filename (e.g. photo.jpg) rather than a meaningful description",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-ALT-TEXT-REDUNDANT-PREFIX": {
        ruleId: "MD-ALT-TEXT-REDUNDANT-PREFIX",
        description: "Alt text begins with a redundant prefix such as 'image of' or 'picture of'; screen readers already announce the image role",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-ALT-TEXT-TOO-SHORT": {
        ruleId: "MD-ALT-TEXT-TOO-SHORT",
        description: "Image alt text is fewer than 3 characters and is unlikely to convey meaningful information",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-EMPTY-LINK-TEXT": {
        ruleId: "MD-EMPTY-LINK-TEXT",
        description: "Markdown link has empty visible text ([](...)); links must have descriptive text",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.4 Link Purpose (In Context)",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-URL-AS-LINK-TEXT": {
        ruleId: "MD-URL-AS-LINK-TEXT",
        description: "Markdown link text is a raw URL; replace with descriptive link text",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.4 Link Purpose (In Context)",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-NO-YAML-FRONT-MATTER": {
        ruleId: "MD-NO-YAML-FRONT-MATTER",
        description: "Document has no YAML front matter block; title and language metadata cannot be verified",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-YAML-UNCLOSED-FENCE": {
        ruleId: "MD-YAML-UNCLOSED-FENCE",
        description: "YAML front matter block is opened with --- but has no closing --- fence; metadata cannot be parsed",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-YAML-MISSING-TITLE": {
        ruleId: "MD-YAML-MISSING-TITLE",
        description: "YAML front matter is present but has no 'title:' field; document title cannot be verified (WCAG 2.4.2)",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-YAML-MISSING-LANG": {
        ruleId: "MD-YAML-MISSING-LANG",
        description: "YAML front matter is present but has no 'lang:' or 'language:' field; document language cannot be verified (WCAG 3.1.1)",
        severity: Severity.HIGH,
        acbReference: "WCAG 3.1.1 Language of Page",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-YAML-MISSING-AUTHOR": {
        ruleId: "MD-YAML-MISSING-AUTHOR",
        description: "YAML front matter is present but has no 'author:' field",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-YAML-MISSING-DESCRIPTION": {
        ruleId: "MD-YAML-MISSING-DESCRIPTION",
        description: "YAML front matter is present but has no 'description:' field",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-NO-HEADINGS": {
        ruleId: "MD-NO-HEADINGS",
        description: "Document contains no headings, reducing structural navigation",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-DUPLICATE-HEADING-TEXT": {
        ruleId: "MD-DUPLICATE-HEADING-TEXT",
        description: "Same-level headings repeat identical text, creating ambiguous navigation landmarks",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-LONG-SECTION-WITHOUT-HEADING": {
        ruleId: "MD-LONG-SECTION-WITHOUT-HEADING",
        description: "Long section has 20 or more paragraphs without a heading break",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-EMPTY-HEADING": {
        ruleId: "MD-EMPTY-HEADING",
        description: "Heading marker (#) has no text, creating an invisible empty heading in document structure",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-HEADING-TOO-LONG": {
        ruleId: "MD-HEADING-TOO-LONG",
        description: "Heading text exceeds 120 characters, making navigation landmarks and table-of-contents entries unwieldy",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.4.6 Headings and Labels",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-HEADING-ENDS-PUNCTUATION": {
        ruleId: "MD-HEADING-ENDS-PUNCTUATION",
        description: "Heading ends with a period, semicolon, or colon, which causes some screen readers to insert an audible pause mid-navigation",
        severity: Severity.LOW,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-CODE-BLOCK-NO-LANGUAGE": {
        ruleId: "MD-CODE-BLOCK-NO-LANGUAGE",
        description: "Fenced code block has no language identifier, preventing programmatic identification of content type",
        severity: Severity.LOW,
        acbReference: "WCAG 1.3.3 Sensory Characteristics",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-INDENTED-CODE-BLOCK": {
        ruleId: "MD-INDENTED-CODE-BLOCK",
        description: "4-space indented code block cannot carry a language identifier; use fenced code blocks (```) instead",
        severity: Severity.LOW,
        acbReference: "WCAG 1.3.3 Sensory Characteristics",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-RAW-HTML-TABLE": {
        ruleId: "MD-RAW-HTML-TABLE",
        description: "Raw HTML <table> in Markdown must include <th scope> header cells and a <caption> element",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-MOVING-CONTENT": {
        ruleId: "MD-MOVING-CONTENT",
        description: "Raw <marquee> or <blink> HTML creates moving content that cannot be paused or stopped",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.2.2 Pause, Stop, Hide",
        category: RuleCategory.MSAC,
        autoFixable: true,
        formats: MD_ONLY,
    },
    "MD-RAW-BR-TAG": {
        ruleId: "MD-RAW-BR-TAG",
        description: "Raw HTML <br> tag used in Markdown",
        severity: Severity.LOW,
        acbReference: "CommonMark portability and structure",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-RAW-HTML-GENERIC-CONTAINER": {
        ruleId: "MD-RAW-HTML-GENERIC-CONTAINER",
        description: "Raw HTML <div> or <span> used in Markdown",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-RAW-HTML-PRESENTATIONAL": {
        ruleId: "MD-RAW-HTML-PRESENTATIONAL",
        description: "Presentational HTML tag (<font> or <center>) used in Markdown",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-BLANK-TABLE-HEADER": {
        ruleId: "MD-BLANK-TABLE-HEADER",
        description: "Pipe table has one or more blank column header cells, preventing screen readers from identifying columns",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-TABLE-COLUMN-MISMATCH": {
        ruleId: "MD-TABLE-COLUMN-MISMATCH",
        description: "Pipe table data row has a different column count than the header row, producing misaligned or orphaned data cells",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-FAKE-LIST-BULLET": {
        ruleId: "MD-FAKE-LIST-BULLET",
        description: "Unicode bullet character (•, ◦, ▪, ‣) used inline instead of a proper Markdown list item",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-FAKE-NUMBERED-LIST": {
        ruleId: "MD-FAKE-NUMBERED-LIST",
        description: "Lines appear to be manually numbered (1. item, 2. item) outside of Markdown ordered list syntax",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-FAKE-INLINE-BULLET": {
        ruleId: "MD-FAKE-INLINE-BULLET",
        description: "Inline Unicode bullet character appears mid-sentence instead of a proper list structure",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-EXCESSIVE-BLANK-LINES": {
        ruleId: "MD-EXCESSIVE-BLANK-LINES",
        description: "Three or more consecutive blank lines reduce readability and structural consistency",
        severity: Severity.LOW,
        acbReference: "ACB readability quality",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-EXCESSIVE-TRAILING-SPACES": {
        ruleId: "MD-EXCESSIVE-TRAILING-SPACES",
        description: "Line ends with more than two trailing spaces",
        severity: Severity.LOW,
        acbReference: "CommonMark line break behavior",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-ENTIRE-LINE-BOLDED": {
        ruleId: "MD-ENTIRE-LINE-BOLDED",
        description: "Entire body line is bolded; use headings or plain body text",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: MD_ONLY,
    },
    "MD-ALLCAPS": {
        ruleId: "MD-ALLCAPS",
        description: "Body text contains ALL CAPS words, which some screen readers may spell out letter by letter instead of reading naturally",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 2: Capitalization; WCAG 1.4.8",
        category: RuleCategory.ACB,
        autoFixable: false,
        formats: MD_ONLY,
    },
    // -----------------------------------------------------------------
    // ePub-specific rules
    // -----------------------------------------------------------------
    "EPUB-TITLE": {
        ruleId: "EPUB-TITLE",
        description: "ePub must have a title set in OPF metadata",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.2 Page Titled",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-LANGUAGE": {
        ruleId: "EPUB-LANGUAGE",
        description: "ePub must have a language set in OPF metadata",
        severity: Severity.HIGH,
        acbReference: "WCAG 3.1.1 Language of Page",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-NAV-DOCUMENT": {
        ruleId: "EPUB-NAV-DOCUMENT",
        description: "ePub must include a navigation document (table of contents)",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.5 Multiple Ways",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-HEADING-HIERARCHY": {
        ruleId: "EPUB-HEADING-HIERARCHY",
        description: "Heading levels must not skip (e.g., H1 to H3 without H2)",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-MISSING-ALT-TEXT": {
        ruleId: "EPUB-MISSING-ALT-TEXT",
        description: "Images in ePub content must have alternative text",
        severity: Severity.CRITICAL,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-TABLE-HEADERS": {
        ruleId: "EPUB-TABLE-HEADERS",
        description: "Tables in ePub content must use <th> header cells",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.3.1 Info and Relationships",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-ACCESSIBILITY-METADATA": {
        ruleId: "EPUB-ACCESSIBILITY-METADATA",
        description: "ePub should include schema.org accessibility metadata (accessMode, accessibilityFeature)",
        severity: Severity.MEDIUM,
        acbReference: "EPUB Accessibility 1.1",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-LINK-TEXT": {
        ruleId: "EPUB-LINK-TEXT",
        description: "Hyperlink text must be descriptive (not 'click here' or a raw URL)",
        severity: Severity.HIGH,
        acbReference: "WCAG 2.4.4 Link Purpose (In Context)",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-ACCESSIBILITY-HAZARD": {
        ruleId: "EPUB-ACCESSIBILITY-HAZARD",
        description: "ePub should declare accessibility hazards (flashing, motion, sound) in metadata",
        severity: Severity.MEDIUM,
        acbReference: "EPUB Accessibility 1.1",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-ACCESS-MODE-SUFFICIENT": {
        ruleId: "EPUB-ACCESS-MODE-SUFFICIENT",
        description: "ePub should declare sufficient access modes (textual, visual, auditory)",
        severity: Severity.MEDIUM,
        acbReference: "EPUB Accessibility 1.1",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-PAGE-LIST": {
        ruleId: "EPUB-PAGE-LIST",
        description: "ePub with page navigation metadata should include a page list",
        severity: Severity.MEDIUM,
        acbReference: "EPUB Accessibility 1.1",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-PAGE-SOURCE": {
        ruleId: "EPUB-PAGE-SOURCE",
        description: "Reflowable ePub with a page list should declare dc:source or pageBreakSource",
        severity: Severity.MEDIUM,
        acbReference: "EPUB Accessibility 1.1",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-MATHML-ALT": {
        ruleId: "EPUB-MATHML-ALT",
        description: "MathML elements must have an alttext attribute or annotation for screen readers",
        severity: Severity.HIGH,
        acbReference: "WCAG 1.1.1 Non-text Content",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUB-TEXT-INDENT": {
        ruleId: "EPUB-TEXT-INDENT",
        description: "Body text elements use CSS text-indent or margin-left for indentation",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 4: Alignment",
        category: RuleCategory.ACB,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUBCHECK-ERROR": {
        ruleId: "EPUBCHECK-ERROR",
        description: "EPUBCheck reported a package/content validation error",
        severity: Severity.HIGH,
        acbReference: "EPUB Accessibility 1.1",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "EPUBCHECK-WARNING": {
        ruleId: "EPUBCHECK-WARNING",
        description: "EPUBCheck reported a package/content validation warning",
        severity: Severity.MEDIUM,
        acbReference: "EPUB Accessibility 1.1",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "ACE-EPUB-CHECK": {
        ruleId: "ACE-EPUB-CHECK",
        description: "EPUB accessibility issue detected by DAISY Ace checker",
        severity: Severity.MEDIUM,
        acbReference: "EPUB Accessibility 1.1",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "ACE-AXE-CHECK": {
        ruleId: "ACE-AXE-CHECK",
        description: "HTML accessibility issue detected by axe-core via DAISY Ace",
        severity: Severity.MEDIUM,
        acbReference: "WCAG 2.2 Level AA",
        category: RuleCategory.MSAC,
        autoFixable: false,
        formats: EPUB_ONLY,
    },
    "ACB-FAUX-HEADING": {
        ruleId: "ACB-FAUX-HEADING",
        description: "Paragraph looks like a heading (bold/large/short) but uses Normal or another non-heading style",
        severity: Severity.HIGH,
        acbReference: "ACB LPG Heading Hierarchy",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-PAGE-SIZE": {
        ruleId: "ACB-PAGE-SIZE",
        description: "Page size must be US Letter (8.5 × 11 in) for ACB large print",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 2: Page Setup",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-MULTIPLE-COLUMNS": {
        ruleId: "ACB-MULTIPLE-COLUMNS",
        description: "Multi-column layout is not permitted in ACB large print documents",
        severity: Severity.HIGH,
        acbReference: "ACB Guidelines Section 3: Layout",
        category: RuleCategory.ACB,
        autoFixable: false,
        formats: DOCX_ONLY,
    },
    "ACB-FONT-COLOR": {
        ruleId: "ACB-FONT-COLOR",
        description: "Text must use black (automatic) font color — colored text reduces contrast",
        severity: Severity.MEDIUM,
        acbReference: "ACB Guidelines Section 4: Typography; WCAG 1.4.3 Contrast",
        category: RuleCategory.ACB,
        autoFixable: true,
        formats: DOCX_ONLY,
    },
    "ACB-STRIKETHROUGH": {
        ruleId: "ACB-STRIKETHROUGH",
        description: "Strikethrough text should be removed — it is confusing for low-vision readers",
        severity: Severity.LOW,
        acbReference: "ACB Guidelines Section 4: Typography",
        category: RuleCategory.ACB,
        autoFixable: false,
        formats: DOCX_ONLY,
    },
};

/** Convenience sets for category-based filtering. */
export const ACB_RULE_IDS: ReadonlySet<string> = new Set(
    Object.entries(AUDIT_RULES)
        .filter(([, r]) => r.category === RuleCategory.ACB)
        .map(([id]) => id),
);
export const MSAC_RULE_IDS: ReadonlySet<string> = new Set(
    Object.entries(AUDIT_RULES)
        .filter(([, r]) => r.category === RuleCategory.MSAC)
        .map(([id]) => id),
);

/** Format-based rule filtering. */
export function rulesForFormat(fmt: DocFormat): Record<string, RuleDef> {
    const result: Record<string, RuleDef> = {};
    for (const [id, rule] of Object.entries(AUDIT_RULES)) {
        if (rule.formats.has(fmt)) {
            result[id] = rule;
        }
    }
    return result;
}

export const DOCX_RULE_IDS: ReadonlySet<string> = new Set(
    Object.entries(AUDIT_RULES)
        .filter(([, r]) => r.formats.has(DocFormat.DOCX))
        .map(([id]) => id),
);
export const XLSX_RULE_IDS: ReadonlySet<string> = new Set(
    Object.entries(AUDIT_RULES)
        .filter(([, r]) => r.formats.has(DocFormat.XLSX))
        .map(([id]) => id),
);
export const PPTX_RULE_IDS: ReadonlySet<string> = new Set(
    Object.entries(AUDIT_RULES)
        .filter(([, r]) => r.formats.has(DocFormat.PPTX))
        .map(([id]) => id),
);
export const EPUB_RULE_IDS: ReadonlySet<string> = new Set(
    Object.entries(AUDIT_RULES)
        .filter(([, r]) => r.formats.has(DocFormat.EPUB))
        .map(([id]) => id),
);

/** Severity deduction map for scoring. */
export const SEVERITY_DEDUCTIONS: Record<Severity, number> = {
    [Severity.CRITICAL]: 15,
    [Severity.HIGH]: 10,
    [Severity.MEDIUM]: 5,
    [Severity.LOW]: 2,
};
