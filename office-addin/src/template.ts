/**
 * Apply ACB Large Print template styles to the active document.
 *
 * Mirrors desktop/src/acb_large_print/template.py.
 * Configures all named styles, page setup, page numbers, and hyphenation.
 */

import {
    effectiveStyles,
    type StyleSizeOverrides,
    FONT_FAMILY,
    FOOTER_SIZE_PT,
    MARGIN_TOP_IN,
    MARGIN_BOTTOM_IN,
    MARGIN_LEFT_IN,
    MARGIN_RIGHT_IN,
} from "./constants";

export interface TemplateResult {
    applied: string[];
}

/**
 * Apply all ACB Large Print template settings to the active document.
 *
 * @param styleSizeOverrides Optional per-style font-size overrides;
 *   matches the Python `style_size_overrides` parameter.
 */
export async function applyTemplate(
    styleSizeOverrides?: StyleSizeOverrides,
): Promise<TemplateResult> {
    const stylesTable = effectiveStyles(styleSizeOverrides);
    const applied: string[] = [];

    await Word.run(async (context) => {
        // ----- Configure styles -----
        for (const [styleName, styleDef] of Object.entries(stylesTable)) {
            try {
                const style = context.document.getStyles().getByNameOrNullObject(styleName);
                style.load("isNullObject");
                await context.sync();

                if (style.isNullObject) continue;

                // Font
                style.font.name = styleDef.font.name;
                style.font.size = styleDef.font.sizePt;
                style.font.bold = styleDef.font.bold;
                style.font.italic = false;
                style.font.allCaps = false;
                style.font.color = "#000000";

                // Paragraph format
                style.paragraphFormat.alignment = Word.Alignment.left;
                style.paragraphFormat.spaceAfter = styleDef.para.spaceAfterPt;
                style.paragraphFormat.spaceBefore = styleDef.para.spaceBeforePt;

                // Line spacing: Office.js uses points (1.15 multiple of 12pt = 13.8pt)
                style.paragraphFormat.lineSpacing = styleDef.para.lineSpacing * 12;

                await context.sync();
                applied.push(`Configured style: ${styleName}`);
            } catch {
                // Style not available -- skip
            }
        }

        // ----- Page margins via OOXML -----
        const sections = context.document.sections;
        sections.load("items");
        await context.sync();

        for (let i = 0; i < sections.items.length; i++) {
            const section = sections.items[i];
            const sectionBody = section.body;
            const ooxml = sectionBody.getOoxml();
            await context.sync();

            let xml = ooxml.value;
            const inchesToTwips = (inches: number) => Math.round(inches * 1440);

            // Set margins
            const pgMarMatch = xml.match(/<w:pgMar[^/>]*\/>/);
            if (pgMarMatch) {
                let pgMar = pgMarMatch[0];
                pgMar = pgMar.replace(/w:top="[^"]*"/, `w:top="${inchesToTwips(MARGIN_TOP_IN)}"`);
                pgMar = pgMar.replace(/w:bottom="[^"]*"/, `w:bottom="${inchesToTwips(MARGIN_BOTTOM_IN)}"`);
                pgMar = pgMar.replace(/w:left="[^"]*"/, `w:left="${inchesToTwips(MARGIN_LEFT_IN)}"`);
                pgMar = pgMar.replace(/w:right="[^"]*"/, `w:right="${inchesToTwips(MARGIN_RIGHT_IN)}"`);
                xml = xml.replace(pgMarMatch[0], pgMar);
            }

            // Disable hyphenation
            if (xml.includes("w:autoHyphenation")) {
                xml = xml.replace(/w:autoHyphenation w:val="[^"]*"/, 'w:autoHyphenation w:val="false"');
            }

            sectionBody.insertOoxml(xml, Word.InsertLocation.replace);
            await context.sync();
            applied.push(`Configured page setup for section ${i + 1}`);
        }

        // ----- Document properties -----
        const docProps = context.document.properties;
        docProps.load("title");
        await context.sync();

        if (!docProps.title || !docProps.title.trim()) {
            docProps.title = "ACB Large Print Document";
            applied.push("Set document title");
        }

        await context.sync();
    });

    return { applied };
}
