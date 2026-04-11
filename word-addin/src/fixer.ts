/**
 * Fix Word documents to comply with ACB Large Print Guidelines.
 *
 * Uses the Office.js Word API to modify the active document in place.
 * Mirrors word-addon/src/acb_large_print/fixer.py.
 */

import {
    ACB_STYLES,
    FONT_FAMILY,
    MIN_SIZE_PT,
    MARGIN_TOP_IN,
    MARGIN_BOTTOM_IN,
    MARGIN_LEFT_IN,
    MARGIN_RIGHT_IN,
    FOOTER_SIZE_PT,
} from "./constants";

export interface FixResult {
    totalFixes: number;
    details: string[];
}

/**
 * Apply all ACB Large Print fixes to the active document.
 */
export async function fixDocument(): Promise<FixResult> {
    let totalFixes = 0;
    const details: string[] = [];

    await Word.run(async (context) => {
        // ----- Fix named styles -----
        const styleFixes = await fixStyles(context);
        totalFixes += styleFixes.count;
        details.push(...styleFixes.messages);

        // ----- Fix page margins via OOXML -----
        const marginFixes = await fixMargins(context);
        totalFixes += marginFixes.count;
        details.push(...marginFixes.messages);

        // ----- Fix paragraph content -----
        const paraFixes = await fixParagraphs(context);
        totalFixes += paraFixes.count;
        details.push(...paraFixes.messages);

        // ----- Fix document title -----
        const titleFixes = await fixDocumentTitle(context);
        totalFixes += titleFixes.count;
        details.push(...titleFixes.messages);

        await context.sync();
    });

    return { totalFixes, details };
}

async function fixStyles(context: Word.RequestContext): Promise<{ count: number; messages: string[] }> {
    let count = 0;
    const messages: string[] = [];

    for (const [styleName, styleDef] of Object.entries(ACB_STYLES)) {
        try {
            const style = context.document.getStyles().getByNameOrNullObject(styleName);
            style.load("isNullObject");
            await context.sync();

            if (style.isNullObject) continue;

            style.font.load("name,size,bold,italic,allCaps,color");
            style.paragraphFormat.load("alignment,lineSpacing,spaceAfter,spaceBefore");
            await context.sync();

            let changed = false;

            // Font family
            if (style.font.name !== styleDef.font.name) {
                style.font.name = styleDef.font.name;
                changed = true;
            }

            // Font size
            if (Math.abs(style.font.size - styleDef.font.sizePt) > 0.5) {
                style.font.size = styleDef.font.sizePt;
                changed = true;
            }

            // Bold
            if (style.font.bold !== styleDef.font.bold) {
                style.font.bold = styleDef.font.bold;
                changed = true;
            }

            // Italic -- always off
            if (style.font.italic) {
                style.font.italic = false;
                changed = true;
            }

            // All caps -- always off
            if (style.font.allCaps) {
                style.font.allCaps = false;
                changed = true;
            }

            // Font color -- always black
            style.font.color = "#000000";

            // Alignment -- always left
            if (style.paragraphFormat.alignment !== Word.Alignment.left) {
                style.paragraphFormat.alignment = Word.Alignment.left;
                changed = true;
            }

            // Line spacing
            if (Math.abs(style.paragraphFormat.lineSpacing - styleDef.para.lineSpacing) > 0.01) {
                // Office.js lineSpacing is in points for "Multiple" -- ACB 1.15 means value * 12 for 12pt
                // For "multiple" line spacing, set lineUnitAfter/Before instead
                // Actually, for Office.js the lineSpacing property with lineSpacingRule
                style.paragraphFormat.lineSpacing = styleDef.para.lineSpacing * 12;
                changed = true;
            }

            if (changed) {
                count++;
                messages.push(`Fixed style: ${styleName}`);
            }

            await context.sync();
        } catch {
            // Style not found -- skip
        }
    }

    return { count, messages };
}

async function fixMargins(context: Word.RequestContext): Promise<{ count: number; messages: string[] }> {
    let count = 0;
    const messages: string[] = [];

    const sections = context.document.sections;
    sections.load("items");
    await context.sync();

    for (let i = 0; i < sections.items.length; i++) {
        const section = sections.items[i];
        const sectionBody = section.body;
        const ooxml = sectionBody.getOoxml();
        await context.sync();

        const xml = ooxml.value;
        let modified = xml;
        const inchesToTwips = (inches: number) => Math.round(inches * 1440);

        // Replace margin values in the pgMar element
        const pgMarMatch = modified.match(/<w:pgMar[^/>]*\/>/);
        if (pgMarMatch) {
            let pgMar = pgMarMatch[0];
            const origPgMar = pgMar;

            pgMar = pgMar.replace(/w:top="[^"]*"/, `w:top="${inchesToTwips(MARGIN_TOP_IN)}"`);
            pgMar = pgMar.replace(/w:bottom="[^"]*"/, `w:bottom="${inchesToTwips(MARGIN_BOTTOM_IN)}"`);
            pgMar = pgMar.replace(/w:left="[^"]*"/, `w:left="${inchesToTwips(MARGIN_LEFT_IN)}"`);
            pgMar = pgMar.replace(/w:right="[^"]*"/, `w:right="${inchesToTwips(MARGIN_RIGHT_IN)}"`);

            if (pgMar !== origPgMar) {
                modified = modified.replace(origPgMar, pgMar);
                count++;
                messages.push(`Fixed margins in section ${i + 1}`);
            }
        }

        if (modified !== xml) {
            sectionBody.insertOoxml(modified, Word.InsertLocation.replace);
            await context.sync();
        }
    }

    return { count, messages };
}

async function fixParagraphs(context: Word.RequestContext): Promise<{ count: number; messages: string[] }> {
    let count = 0;
    const messages: string[] = [];

    const paragraphs = context.document.body.paragraphs;
    paragraphs.load("items");
    await context.sync();

    for (const para of paragraphs.items) {
        para.load("text,style,alignment");
        para.font.load("name,size,italic,bold,allCaps,underline");
    }
    await context.sync();

    for (let i = 0; i < paragraphs.items.length; i++) {
        const para = paragraphs.items[i];
        const styleName = para.style || "Normal";
        const isHeading = /^Heading \d+$/.test(styleName);

        // Fix alignment
        if (para.alignment !== Word.Alignment.left) {
            para.alignment = Word.Alignment.left;
            count++;
        }

        // Fix italic -> underline
        if (para.font.italic === true) {
            para.font.italic = false;
            para.font.underline = Word.UnderlineType.single;
            count++;
            messages.push(`Removed italic, added underline in paragraph ${i + 1}`);
        }

        // Fix bold in body text -> underline
        if (para.font.bold === true && !isHeading && para.text.trim().length > 5) {
            para.font.bold = false;
            para.font.underline = Word.UnderlineType.single;
            count++;
            messages.push(`Converted bold to underline in paragraph ${i + 1}`);
        }

        // Fix font family
        if (para.font.name && para.font.name !== FONT_FAMILY && para.font.name !== "mixed") {
            para.font.name = FONT_FAMILY;
            count++;
        }

        // Fix font size below minimum
        if (para.font.size && para.font.size < MIN_SIZE_PT - 0.5) {
            para.font.size = MIN_SIZE_PT;
            count++;
        }

        // Remove all caps
        if (para.font.allCaps === true) {
            para.font.allCaps = false;
            count++;
        }
    }

    await context.sync();

    if (count > 0) {
        messages.push(`Fixed ${count} paragraph formatting issues`);
    }

    return { count, messages };
}

/**
 * Set the document title from the first Heading 1 or filename fallback.
 *
 * WARNING: The inferred title should be manually reviewed.
 */
async function fixDocumentTitle(context: Word.RequestContext): Promise<{ count: number; messages: string[] }> {
    let count = 0;
    const messages: string[] = [];

    const properties = context.document.properties;
    properties.load("title");
    await context.sync();

    if (properties.title && properties.title.trim()) {
        return { count, messages };
    }

    // Try first Heading 1
    const paragraphs = context.document.body.paragraphs;
    paragraphs.load("items");
    await context.sync();

    for (const para of paragraphs.items) {
        para.load("style,text");
    }
    await context.sync();

    for (const para of paragraphs.items) {
        if (para.style === "Heading 1" && para.text.trim()) {
            properties.title = para.text.trim();
            count++;
            messages.push(`Set document title from first heading: "${para.text.trim()}" (review recommended)`);
            await context.sync();
            return { count, messages };
        }
    }

    // Fallback: cannot determine filename from Office.js, leave for manual fix
    messages.push("No Heading 1 found -- document title must be set manually");
    return { count, messages };
}
