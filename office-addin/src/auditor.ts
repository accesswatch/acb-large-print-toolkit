/**
 * Audit Word documents for ACB Large Print Guidelines compliance.
 *
 * Uses the Office.js Word API to inspect the active document.
 * Mirrors desktop/src/acb_large_print/auditor.py.
 */

import {
    AUDIT_RULES,
    ACB_STYLES,
    FONT_FAMILY,
    MIN_SIZE_PT,
    MARGIN_TOP_IN,
    MARGIN_BOTTOM_IN,
    MARGIN_LEFT_IN,
    MARGIN_RIGHT_IN,
    MARGIN_TOLERANCE_IN,
    Severity,
    SEVERITY_DEDUCTIONS,
} from "./constants";

export interface Finding {
    ruleId: string;
    severity: Severity;
    message: string;
    location: string;
    autoFixable: boolean;
}

export interface AuditResult {
    findings: Finding[];
    totalParagraphs: number;
    score: number;
    grade: string;
}

function addFinding(
    findings: Finding[],
    ruleId: string,
    message: string,
    location: string,
): void {
    const rule = AUDIT_RULES[ruleId];
    if (!rule) return;
    findings.push({
        ruleId,
        severity: rule.severity,
        message,
        location,
        autoFixable: rule.autoFixable,
    });
}

function computeScore(findings: Finding[]): number {
    const total = findings.reduce(
        (sum, f) => sum + (SEVERITY_DEDUCTIONS[f.severity] ?? 5),
        0,
    );
    return Math.max(0, 100 - total);
}

function gradeFromScore(score: number): string {
    if (score >= 90) return "A";
    if (score >= 80) return "B";
    if (score >= 70) return "C";
    if (score >= 60) return "D";
    return "F";
}

/**
 * Run a full ACB Large Print compliance audit on the active Word document.
 */
export async function auditDocument(): Promise<AuditResult> {
    const findings: Finding[] = [];
    let totalParagraphs = 0;
    const nonArialFontLocations = new Map<string, string[]>();

    await Word.run(async (context) => {
        // ----- Document properties -----
        const docProps = context.document.properties;
        docProps.load("title");
        await context.sync();

        if (!docProps.title || !docProps.title.trim()) {
            addFinding(findings, "ACB-DOC-TITLE", "Document has no title set in properties", "Document Properties");
        }

        // ----- Page margins -----
        const sections = context.document.sections;
        sections.load("items");
        await context.sync();

        for (let i = 0; i < sections.items.length; i++) {
            const section = sections.items[i];
            const body = section.body;
            body.load("font");
            // Section-level properties for margins
            section.load("headerFooterDistance");
            await context.sync();

            // Use OOXML to check margins (Office.js sections don't expose margins directly)
            const sectionOoxml = section.body.getOoxml();
            await context.sync();

            const marginChecks = parseMargins(sectionOoxml.value);
            const loc = `Section ${i + 1}`;

            if (marginChecks.top !== null && Math.abs(marginChecks.top - MARGIN_TOP_IN) > MARGIN_TOLERANCE_IN) {
                addFinding(findings, "ACB-MARGINS", `Top margin is ${marginChecks.top.toFixed(2)} inches (expected ${MARGIN_TOP_IN})`, loc);
            }
            if (marginChecks.bottom !== null && Math.abs(marginChecks.bottom - MARGIN_BOTTOM_IN) > MARGIN_TOLERANCE_IN) {
                addFinding(findings, "ACB-MARGINS", `Bottom margin is ${marginChecks.bottom.toFixed(2)} inches (expected ${MARGIN_BOTTOM_IN})`, loc);
            }
            if (marginChecks.left !== null && Math.abs(marginChecks.left - MARGIN_LEFT_IN) > MARGIN_TOLERANCE_IN) {
                addFinding(findings, "ACB-MARGINS", `Left margin is ${marginChecks.left.toFixed(2)} inches (expected ${MARGIN_LEFT_IN})`, loc);
            }
            if (marginChecks.right !== null && Math.abs(marginChecks.right - MARGIN_RIGHT_IN) > MARGIN_TOLERANCE_IN) {
                addFinding(findings, "ACB-MARGINS", `Right margin is ${marginChecks.right.toFixed(2)} inches (expected ${MARGIN_RIGHT_IN})`, loc);
            }
        }

        // ----- Paragraph + run checks -----
        const paragraphs = context.document.body.paragraphs;
        paragraphs.load("items");
        await context.sync();

        // Load all paragraph properties
        for (const para of paragraphs.items) {
            para.load("text,style,alignment");
        }
        await context.sync();

        let prevHeadingLevel = 0;
        totalParagraphs = paragraphs.items.length;

        for (let i = 0; i < paragraphs.items.length; i++) {
            const para = paragraphs.items[i];
            const styleName = para.style || "Normal";
            const textPreview = para.text.length > 60
                ? `${para.text.substring(0, 60)}...`
                : para.text;
            const loc = textPreview
                ? `Paragraph ${i + 1}: '${textPreview}'`
                : `Paragraph ${i + 1}`;

            const isHeading = /^Heading \d+$/.test(styleName);
            const headingLevel = isHeading
                ? parseInt(styleName.replace("Heading ", ""), 10)
                : 0;

            // Heading hierarchy
            if (isHeading && headingLevel > 0) {
                if (prevHeadingLevel > 0 && headingLevel > prevHeadingLevel + 1) {
                    addFinding(
                        findings,
                        "ACB-HEADING-HIERARCHY",
                        `Heading level skipped: H${prevHeadingLevel} to H${headingLevel}`,
                        loc,
                    );
                }
                prevHeadingLevel = headingLevel;
            }

            // Alignment (not flush left)
            if (para.alignment && para.alignment !== Word.Alignment.left) {
                addFinding(findings, "ACB-ALIGNMENT", "Direct alignment override (not flush left)", loc);
            }

            // ALL CAPS in heading text
            if (isHeading && para.text.trim() && para.text.trim() === para.text.trim().toUpperCase() && para.text.trim().length > 3) {
                addFinding(findings, "ACB-NO-ALLCAPS", "Heading text is ALL CAPS", loc);
            }

            // Check runs for font issues
            const inlineResults = para.getRange().getTextRanges([" "], false);
            // Simpler approach: load font from the paragraph itself
            const paraFont = para.font;
            paraFont.load("name,size,italic,bold,allCaps");
            await context.sync();

            // Paragraph-level font checks
            if (paraFont.name && paraFont.name !== FONT_FAMILY && paraFont.name !== "mixed") {
                const existing = nonArialFontLocations.get(paraFont.name) ?? [];
                existing.push(loc);
                nonArialFontLocations.set(paraFont.name, existing);
            }

            if (paraFont.size && paraFont.size < MIN_SIZE_PT - 0.5) {
                addFinding(findings, "ACB-FONT-SIZE-BODY", `Font size ${paraFont.size}pt below ${MIN_SIZE_PT}pt minimum`, loc);
            }

            if (paraFont.italic === true) {
                addFinding(findings, "ACB-NO-ITALIC", `Italic text found`, loc);
            }

            if (paraFont.bold === true && !isHeading && para.text.trim().length > 5) {
                addFinding(findings, "ACB-BOLD-HEADINGS-ONLY", `Bold used in body text`, loc);
            }

            if (paraFont.allCaps === true) {
                addFinding(findings, "ACB-NO-ALLCAPS", "ALL CAPS formatting applied", loc);
            }

            // Check heading font sizes against ACB specs
            if (isHeading && paraFont.size) {
                const expectedStyle = ACB_STYLES[styleName];
                if (expectedStyle && Math.abs(paraFont.size - expectedStyle.font.sizePt) > 0.5) {
                    const sizeRule = styleName === "Heading 1" ? "ACB-FONT-SIZE-H1" : "ACB-FONT-SIZE-H2";
                    addFinding(findings, sizeRule, `${styleName} is ${paraFont.size}pt (expected ${expectedStyle.font.sizePt}pt)`, loc);
                }
            }
        }
    });

    for (const [fontName, locations] of Array.from(nonArialFontLocations.entries()).sort()) {
        for (const location of locations.slice(0, 3)) {
            addFinding(findings, "ACB-FONT-FAMILY", `Non-Arial font '${fontName}'`, location);
        }
        if (locations.length > 3) {
            addFinding(
                findings,
                "ACB-FONT-FAMILY",
                `Non-Arial font '${fontName}' also appears in ${locations.length - 3} additional paragraph(s); showing the first 3 locations only`,
                "Document-wide",
            );
        }
    }

    // Sort findings by severity
    const severityOrder = { [Severity.CRITICAL]: 0, [Severity.HIGH]: 1, [Severity.MEDIUM]: 2, [Severity.LOW]: 3 };
    findings.sort((a, b) => (severityOrder[a.severity] ?? 9) - (severityOrder[b.severity] ?? 9));

    const score = computeScore(findings);
    return {
        findings,
        totalParagraphs,
        score,
        grade: gradeFromScore(score),
    };
}

/** Parse OOXML for section margin values (twips -> inches). */
function parseMargins(ooxml: string): { top: number | null; bottom: number | null; left: number | null; right: number | null } {
    const result = { top: null as number | null, bottom: null as number | null, left: null as number | null, right: null as number | null };
    const twipsToInches = (twips: number) => twips / 1440;

    const topMatch = ooxml.match(/w:top="(\d+)"/);
    if (topMatch) result.top = twipsToInches(parseInt(topMatch[1], 10));

    const bottomMatch = ooxml.match(/w:bottom="(\d+)"/);
    if (bottomMatch) result.bottom = twipsToInches(parseInt(bottomMatch[1], 10));

    const leftMatch = ooxml.match(/w:left="(\d+)"/);
    if (leftMatch) result.left = twipsToInches(parseInt(leftMatch[1], 10));

    const rightMatch = ooxml.match(/w:right="(\d+)"/);
    if (rightMatch) result.right = twipsToInches(parseInt(rightMatch[1], 10));

    return result;
}
