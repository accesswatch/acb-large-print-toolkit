"""
Extended metadata for the Rules Reference page.

Each key is a rule_id from constants.AUDIT_RULES.
Each value is a dict with:
    full_description   -- 2-4 sentence explanation of WHY the rule matters
    suppress_guidance  -- when suppressing is legitimate

Rules without an explicit entry fall back to empty strings.
"""
from __future__ import annotations

RULE_EXTENDED_METADATA: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------------ ACB Word/print
    "ACB-FONT-FAMILY": {
        "full_description": (
            "Arial is a humanist sans-serif typeface specifically recommended by the ACB "
            "because its letterforms are highly legible at large sizes: open aperture, "
            "clear descenders, and consistent stroke width reduce letter-confusion for "
            "readers with low vision. Serif typefaces such as Times New Roman introduce "
            "sharp thin strokes that can blur for readers with contrast sensitivity loss, "
            "particularly at document edges. Using a single consistent typeface throughout "
            "also prevents cognitive fragmentation when readers constantly re-adjust to "
            "new letterforms."
        ),
        "suppress_guidance": (
            "Suppress only when an organisation policy mandates a specific sans-serif "
            "typeface (e.g. Helvetica, APHont) that has been confirmed accessible with "
            "end users. Do not suppress to permit serif body fonts."
        ),
    },
    "ACB-FONT-SIZE-BODY": {
        "full_description": (
            "18 point is the minimum body text size specified by the ACB for readers with "
            "low vision. Below 18 pt, most readers with moderate visual impairment must "
            "magnify the page, disrupting line tracking and increasing reading fatigue. "
            "18 pt is the crossover point at which normal reading distance (roughly 40 cm) "
            "becomes viable for people with visual acuity around 20/200. Documents below "
            "this threshold fail the basic purpose of a large-print format."
        ),
        "suppress_guidance": (
            "Suppress only if the document targets a different large-print size band "
            "(e.g. an APH submission where the contracted size differs) and that "
            "alternative has been explicitly agreed with the receiving organisation."
        ),
    },
    "ACB-FONT-SIZE-H1": {
        "full_description": (
            "Level-1 headings must be visually distinct from body text to allow readers "
            "to skim page structure without reading every word. At 22 pt they stand "
            "4 points above the 18 pt body minimum, sufficient for pre-attentive "
            "detection at normal large-print reading distance. Without a size hierarchy, "
            "a reader relying on visual scanning cannot locate section breaks."
        ),
        "suppress_guidance": (
            "Suppress only when the document deliberately contains no level-1 headings "
            "(e.g. a letter or short memo), or when a larger size hierarchy has been "
            "negotiated with the recipient."
        ),
    },
    "ACB-FONT-SIZE-H2": {
        "full_description": (
            "Level-2 headings must be 20 pt — 2 points above body text and 2 below H1 — "
            "to maintain a readable size hierarchy. A clear visual difference between "
            "heading levels lets readers build an accurate mental model of document "
            "structure without relying on position alone, which is especially important "
            "for readers using a magnifier that shows only a small viewport at a time."
        ),
        "suppress_guidance": (
            "Suppress only when the document contains no sub-section headings, or when "
            "the heading hierarchy has been redesigned in full consultation with end users."
        ),
    },
    "ACB-NO-ITALIC": {
        "full_description": (
            "Italic type is prohibited in ACB large-print documents because the slant and "
            "reduced vertical stroke width of italic letterforms significantly reduce "
            "legibility for readers with low vision. Research shows letter spacing and "
            "upright stroke angles are critical for character identification; italic "
            "degrades both. Screen magnification also introduces anti-aliasing artefacts "
            "on slanted strokes, making italic text appear blurry at high zoom."
        ),
        "suppress_guidance": (
            "Do not suppress. There is no accessibility-approved substitute; use "
            "underline for inline emphasis instead. The only exception is scientific or "
            "legal notation where italic is mandated by convention (e.g. species names), "
            "and even then the text should be prefaced with a descriptive label."
        ),
    },
    "ACB-BOLD-HEADINGS-ONLY": {
        "full_description": (
            "Bold creates a strong visual contrast that can be confused with a heading "
            "when applied to body text. Readers using structural skimming rely on bold "
            "text as a heading cue; unexpected bold in body copy breaks that heuristic "
            "and increases cognitive load. ACB guidelines restrict bold to headings and "
            "require underline for all inline body emphasis."
        ),
        "suppress_guidance": (
            "Suppress only when the document is a legal or regulatory form where bold "
            "is structurally required by the issuing body. Always pair suppression with "
            "a note explaining the bold usage to the reader."
        ),
    },
    "ACB-ALIGNMENT": {
        "full_description": (
            "Justified text creates uneven inter-word spaces ('rivers') that fragment "
            "visual flow across the line, especially disruptive for readers using a "
            "tracking finger or ruler guide. Centered and right-aligned text eliminates "
            "the consistent left edge that low-vision readers use as a return anchor. "
            "Flush-left (ragged-right) alignment preserves clean left margin and natural "
            "word spacing, both proven to improve reading speed for people with low vision."
        ),
        "suppress_guidance": (
            "Suppress only for elements that are conventionally center-aligned by design "
            "convention (e.g. title pages, cover sheets, poems) when the audience has "
            "acknowledged the deviation from large-print standards."
        ),
    },
    "ACB-LIST-INDENT": {
        "full_description": (
            "ACB guidelines specify flush-left list indentation so the ragged-right "
            "column extends to the full page width, maximising words per line at large "
            "print sizes. Indented lists reduce effective line length, forcing more line "
            "breaks and increasing eye movements per list item. The fixer applies the "
            "configured indent setting — check Audit/Fix form options if your organisation "
            "uses a non-default indent."
        ),
        "suppress_guidance": (
            "Suppress when your organisation style requires a standard indented list "
            "layout and that preference has been set in the audit/fix options. This rule "
            "checks against the configured setting, not a hard-coded value."
        ),
    },
    "ACB-PARA-INDENT": {
        "full_description": (
            "Left indent on non-list body paragraphs narrows the text column, reducing "
            "words per line and forcing additional line breaks. For large-print readers "
            "each break requires a return sweep of 3–5 cm rather than 1–2 cm of normal "
            "print. ACB guidelines mandate flush-left paragraphs (zero indent) so readers "
            "can use the page margin as a reliable visual anchor."
        ),
        "suppress_guidance": (
            "Suppress only for blockquote or pull-quote elements intentionally set off "
            "from body text by indentation, and only when those elements are clearly "
            "labelled in context."
        ),
    },
    "ACB-FIRST-LINE-INDENT": {
        "full_description": (
            "First-line indentation is a typographic convention from proportional-width "
            "print that serves no functional purpose in large-print documents and reduces "
            "effective line length of the opening sentence of every paragraph. ACB "
            "guidelines prohibit first-line indents to maximise text area and maintain "
            "the consistent left edge used for line-return tracking."
        ),
        "suppress_guidance": (
            "Suppress only for deliberate stylistic reasons confirmed by the recipient "
            "organisation. Do not suppress as a general style preference."
        ),
    },
    "ACB-LINE-SPACING": {
        "full_description": (
            "The ACB specifies 1.15 line spacing for print output to provide sufficient "
            "interline clearance without increasing page count excessively. Single-spaced "
            "text (1.0) is the most common cause of line-tracking errors for low-vision "
            "readers: adjacent lines are so close that a reader can inadvertently re-read "
            "the same line or skip to the wrong line. WCAG 2.2 AA digital supplement "
            "requires 1.5 for digital/HTML rendering; the auditor applies 1.15 to "
            "Word/print output only."
        ),
        "suppress_guidance": (
            "Suppress only for tables, headers, or footers where tighter spacing is "
            "necessary to fit content, and only after confirming line-tracking is not "
            "impaired at the reduced spacing."
        ),
    },
    "ACB-MARGINS": {
        "full_description": (
            "One-inch margins on all sides serve two purposes: they provide a physical "
            "holding zone for readers who grip the page, and they ensure clearance from "
            "the binding edge so text is not obscured when the document is bound. Narrower "
            "margins shift text toward the binding edge where page curvature can make "
            "characters difficult to resolve for readers with limited contrast sensitivity."
        ),
        "suppress_guidance": (
            "Suppress only for documents that will be delivered digitally only (no print) "
            "or where a binding allowance larger than 0.5 inch has been added manually."
        ),
    },
    "ACB-WIDOW-ORPHAN": {
        "full_description": (
            "A widow is a single line of a paragraph left at the top of a page; an orphan "
            "is a single line left at the bottom. Both disrupt visual continuity and make "
            "it harder to determine where a paragraph begins and ends. At large print "
            "sizes an orphaned line can occupy up to 10% of a page. Enabling widow/orphan "
            "control in Word ensures paragraphs are kept together."
        ),
        "suppress_guidance": (
            "Suppress only when document layout is tightly controlled for print "
            "production and widow/orphan control is handled manually by a typesetter."
        ),
    },
    "ACB-NO-HYPHENATION": {
        "full_description": (
            "Automatic hyphenation splits words across lines at unexpected points, causing "
            "misreading when readers with low vision see only a fragment of the word "
            "before the line break. Readers using screen magnification may not see the "
            "line break at all, reading the first syllable as a different word. ACB "
            "guidelines require hyphenation to be disabled so every word is presented "
            "whole on a single line."
        ),
        "suppress_guidance": (
            "Do not suppress for body text. Hyphenation in large-print documents has "
            "no readability benefit and introduces reading errors."
        ),
    },
    "ACB-PAGE-NUMBERS": {
        "full_description": (
            "Page numbers in the footer allow readers to orient themselves when returning "
            "to a document after a pause, or when navigating a physical large-print book "
            "alongside an audio description or sighted-reader transcript. Without page "
            "numbers a reader who loses their place must scan the entire document visually "
            "to relocate it."
        ),
        "suppress_guidance": (
            "Suppress only for one-page documents where page numbering is meaningless, "
            "or for documents delivered in a bound series with pre-printed sequential "
            "numbers."
        ),
    },
    "ACB-HEADING-HIERARCHY": {
        "full_description": (
            "Skipping heading levels (e.g. H1 to H3 without H2) breaks the structural "
            "tree that assistive technologies use to build a navigation outline. Screen "
            "reader users press H to jump between headings; a missing level creates a "
            "structural gap making the outline misleading. For low-vision readers who "
            "skim headings visually, the gap creates a false impression of flat structure."
        ),
        "suppress_guidance": (
            "Do not suppress. Heading hierarchy is a hard structural requirement. If "
            "the original document skips levels, use the fixer's heading detection to "
            "remap headings before suppressing this rule."
        ),
    },
    "ACB-NO-ALLCAPS": {
        "full_description": (
            "ALL CAPS text dramatically reduces word-shape differentiation: every word "
            "becomes a uniform rectangle, removing the ascenders and descenders used "
            "for fast word recognition. For low-vision readers this increases word-by-word "
            "serial decoding. Some screen readers also spell out each letter of ALL CAPS "
            "text individually, which is disruptive in audio playback."
        ),
        "suppress_guidance": (
            "Suppress only for short fixed-format elements such as acronyms, callsigns, "
            "or standard form field labels where ALL CAPS is required by convention."
        ),
    },
    "ACB-DOC-TITLE": {
        "full_description": (
            "The document title in Word properties is exposed to assistive technologies "
            "as the programmatic page title, satisfying WCAG 2.4.2. Screen readers "
            "announce the document title when the file opens, giving users immediate "
            "context. Without a title, the OS falls back to the filename (often a cryptic "
            "auto-generated string). Document title also populates the title field when "
            "documents are converted to EPUB, PDF, or HTML."
        ),
        "suppress_guidance": (
            "Suppress only for template files or working drafts that will have a title "
            "added before distribution."
        ),
    },
    "ACB-DOC-LANGUAGE": {
        "full_description": (
            "Setting the document language (e.g. 'en-US') enables screen readers to "
            "select the correct pronunciation model and spell-checker. Without a declared "
            "language, a screen reader may read English text with an incorrect "
            "text-to-speech voice, degrading comprehension for non-visual users. "
            "WCAG 3.1.1 Level A requires language declaration."
        ),
        "suppress_guidance": (
            "Suppress only for documents with mixed language content where language is "
            "marked at the paragraph level."
        ),
    },
    "ACB-MISSING-ALT-TEXT": {
        "full_description": (
            "Images and non-decorative shapes without alternative text are completely "
            "invisible to screen readers and braille displays. WCAG 1.1.1 (Level A) "
            "mandates a text alternative for all non-text content. For large-print readers "
            "this is also relevant: readers using screen magnification may be unable to "
            "perceive image content that is not described textually, particularly if the "
            "image contains fine detail or color-dependent meaning."
        ),
        "suppress_guidance": (
            "Suppress only for purely decorative images that carry no informational "
            "content (e.g. a page-border ornament) explicitly marked as decorative in "
            "document properties."
        ),
    },
    "ACB-TABLE-HEADER-ROW": {
        "full_description": (
            "Designating a header row in a Word table exposes it as column headers to "
            "assistive technologies, allowing screen readers to announce the column name "
            "as a user navigates through data cells. Without a header row the reader "
            "hears only cell co-ordinates (A1, B1). Header rows also instruct Word to "
            "repeat the row on subsequent pages — directly useful for large-print "
            "documents where a 25-row table may span 3 or more pages."
        ),
        "suppress_guidance": (
            "Suppress only for purely layout tables (no data), or for single-row tables "
            "containing a title rather than column headings."
        ),
    },
    "ACB-LINK-TEXT": {
        "full_description": (
            "Link text such as 'click here' or a raw URL provides no context when read "
            "in isolation, which is exactly how screen readers present links in a links "
            "list view. WCAG 2.4.4 requires that every link's purpose is clear from link "
            "text or its immediate context. For large-print print readers, a raw URL is "
            "also inaccessible because the reader must type a long string manually."
        ),
        "suppress_guidance": (
            "Suppress only for internal documents where all hyperlinks are followed by "
            "the full URL in parentheses explicitly for print accessibility, and link "
            "text itself is descriptive."
        ),
    },
    "ACB-FORM-FIELD-LABEL": {
        "full_description": (
            "Word form fields (content controls and legacy form fields) must have "
            "descriptive help text so screen readers can announce the field's purpose "
            "when it receives focus. Without help text a screen reader user hears only "
            "the field type ('text box') with no indication of what to enter. "
            "WCAG 1.3.1 requires that form relationships are programmatically determinable."
        ),
        "suppress_guidance": (
            "Suppress only for forms where labels are provided visually in the document "
            "body immediately before each field and that proximity relationship has been "
            "confirmed to be correctly interpreted by the target screen reader."
        ),
    },
    "ACB-COMPLEX-TABLE": {
        "full_description": (
            "Tables with both row headers and column headers (multi-level header tables) "
            "require additional structural markup to be correctly interpreted by screen "
            "readers. Without proper header association a reader navigating to a data cell "
            "cannot determine which row and column it belongs to. Word's built-in table "
            "accessibility does not fully support complex header tables; the recommended "
            "remediation is to simplify the table or split it into multiple simpler tables."
        ),
        "suppress_guidance": (
            "Suppress only after the table has been manually verified with a screen "
            "reader and confirmed to be navigable with correct header announcement."
        ),
    },
    "ACB-EMPTY-TABLE-CELL": {
        "full_description": (
            "Completely empty table cells create ambiguity: a screen reader user cannot "
            "tell whether the cell is blank intentionally or whether content was "
            "accidentally omitted. Inserting a placeholder such as a dash or 'N/A' makes "
            "the intentional absence explicit and prevents screen readers from reading "
            "empty cells as silence, which can be confused with the end of the row."
        ),
        "suppress_guidance": (
            "Suppress only for tables where empty cells represent structural spanning "
            "or are genuinely decorative layout cells."
        ),
    },
    "ACB-FLOATING-CONTENT": {
        "full_description": (
            "Text boxes, SmartArt, and other floating objects in Word are positioned in "
            "a separate drawing layer that most screen readers process after the main text "
            "layer, regardless of visual position. A floating caption that appears above "
            "a figure is read after the entire document body. For readers who rely on "
            "reading order, this can make content incomprehensible. All content should "
            "be inline with text flow."
        ),
        "suppress_guidance": (
            "Suppress only if the floating content is purely decorative (no informational "
            "content) or if the content has been duplicated in the main text body."
        ),
    },
    "ACB-FAKE-LIST": {
        "full_description": (
            "Lists created by typing bullet characters or sequential numbers as plain "
            "text are not identified as lists by assistive technologies. Screen readers "
            "that announce 'list, 5 items' for a proper list will simply read the "
            "characters as body text, removing navigation shortcuts and count "
            "announcements that users rely on."
        ),
        "suppress_guidance": (
            "Suppress only for documents where the target output format does not support "
            "semantic list structures (e.g. a plain-text form field)."
        ),
    },
    "ACB-REPEATED-SPACES": {
        "full_description": (
            "Multiple consecutive spaces used for visual alignment disrupt screen reader "
            "output (each space is announced as a pause or spoken character) and are "
            "brittle for large-print reformatting because changing font size collapses "
            "the alignment. Use tabs, indent settings, or table cells for alignment."
        ),
        "suppress_guidance": (
            "Suppress only for pre-formatted code or data fields where the space "
            "characters are part of the content structure."
        ),
    },
    "ACB-LONG-SECTION": {
        "full_description": (
            "More than 20 paragraphs without a heading creates an undifferentiated block "
            "of text with no navigational waypoints. Screen reader users cannot jump to "
            "a section of interest and must listen to the entire block sequentially. For "
            "low-vision readers using magnification, the absence of visual landmarks means "
            "they must scroll large distances to find their previous reading position."
        ),
        "suppress_guidance": (
            "Suppress for documents intentionally structured as continuous narrative "
            "(fiction, personal letters) where headings would be inappropriate."
        ),
    },
    "ACB-DUPLICATE-HEADING": {
        "full_description": (
            "Screen readers build a navigation outline from heading text. If two headings "
            "at the same level have identical text (e.g. two H2s labelled 'Overview') the "
            "user cannot distinguish between them in the headings list and cannot predict "
            "which section they are navigating to. Each heading should uniquely describe "
            "its section content."
        ),
        "suppress_guidance": (
            "Suppress only for documents with a deliberate repeating-section structure "
            "(e.g. meeting minutes) where an alternative navigation method (date, page "
            "number) provides disambiguation."
        ),
    },
    "ACB-LINK-UNDERLINE": {
        "full_description": (
            "Hyperlinks distinguished only by color (typically blue) are inaccessible "
            "to readers with color vision deficiency and difficult to detect for readers "
            "with contrast sensitivity loss. WCAG 1.4.1 requires that color is not the "
            "sole visual means of conveying information. Underlining provides a non-color "
            "visual cue that links are present and clickable."
        ),
        "suppress_guidance": (
            "Suppress only for read-only print documents where hyperlinks serve as "
            "citations and will not be clicked (e.g. a printed reference list). Never "
            "suppress for interactive digital documents."
        ),
    },
    "ACB-DOC-AUTHOR": {
        "full_description": (
            "Document author is required by several accessibility metadata standards and "
            "enables readers to identify who produced the document and contact them with "
            "accessibility questions. It also populates the author field when documents "
            "are converted to EPUB, PDF, or HTML."
        ),
        "suppress_guidance": (
            "Suppress for template files, anonymous publications, or documents where "
            "authorship is deliberately withheld for privacy or review-process reasons."
        ),
    },
    "ACB-FAUX-HEADING": {
        "full_description": (
            "Paragraphs visually formatted to look like headings (large, bold, centered) "
            "but using the Normal style are invisible to screen reader heading navigation. "
            "WCAG 1.3.1 requires that information conveyed through presentation also be "
            "available programmatically. The fixer can automatically apply the appropriate "
            "Heading style to detected faux headings."
        ),
        "suppress_guidance": (
            "Suppress or adjust the confidence threshold if the detector flags intentional "
            "design elements (pull quotes, call-outs, captions) as headings. Review the "
            "detected headings list in the audit report before suppressing."
        ),
    },
    # ------------------------------------------------------------------ XLSX
    "XLSX-TITLE": {
        "full_description": (
            "A workbook title in document properties is announced by screen readers when "
            "the file opens, giving users immediate context about the workbook's purpose. "
            "Without a title, screen readers fall back to the filename. For large-print "
            "Excel users, the title also appears in the taskbar and window header where "
            "it is visible during screen magnification."
        ),
        "suppress_guidance": (
            "Suppress for template files or internal working spreadsheets that will have "
            "a title added before distribution."
        ),
    },
    "XLSX-SHEET-NAME": {
        "full_description": (
            "Generic sheet names (Sheet1, Sheet2) provide no information about sheet "
            "content. Screen readers announce the sheet name when a user switches tabs; "
            "'Sheet3' gives no indication of what data awaits. Descriptive sheet names "
            "also appear in formula references, making the workbook self-documenting "
            "and easier to navigate without sight."
        ),
        "suppress_guidance": (
            "Suppress only for single-sheet workbooks where navigation is not required."
        ),
    },
    "XLSX-TABLE-HEADERS": {
        "full_description": (
            "Excel Tables with the header row enabled expose column headers to assistive "
            "technologies via the accessibility tree. Screen readers can announce the "
            "column name as a user navigates through cells. Without a header row the "
            "reader hears only cell co-ordinates (A1, B1) with no column context, making "
            "data interpretation extremely difficult."
        ),
        "suppress_guidance": (
            "Suppress only for single-row lookup tables where no column grouping "
            "semantics are present."
        ),
    },
    "XLSX-MERGED-CELLS": {
        "full_description": (
            "Merged cells disrupt the regular cell grid that screen readers use to "
            "navigate tables. When a cell spans multiple columns or rows, the assistive "
            "technology's column-count calculation breaks down and navigation becomes "
            "unpredictable. Merged cells also break Excel Table functionality and "
            "sort/filter operations, making data less usable for everyone."
        ),
        "suppress_guidance": (
            "Suppress only for purely decorative merged title rows that contain no data "
            "and are not part of a data table."
        ),
    },
    "XLSX-BLANK-COLUMN-HEADER": {
        "full_description": (
            "A blank column header in an Excel Table leaves screen reader users without "
            "any label for an entire column of data. When navigating cells, the reader "
            "hears the data value but has no column name to contextualise it. Every data "
            "column must have a descriptive, non-blank header."
        ),
        "suppress_guidance": (
            "Do not suppress. A blank column header is always an accessibility defect."
        ),
    },
    "XLSX-COLOR-ONLY": {
        "full_description": (
            "Cells that use only background color to convey meaning (green = pass, "
            "red = fail) are inaccessible to readers with color blindness and provide no "
            "information to screen readers. WCAG 1.4.1 prohibits color as the sole visual "
            "means of conveying information. Always pair color with a text label, icon, "
            "or symbol in the cell."
        ),
        "suppress_guidance": (
            "Suppress only for cells used purely for aesthetic banding (alternating row "
            "colors) that carry no semantic meaning."
        ),
    },
    "XLSX-HIDDEN-CONTENT": {
        "full_description": (
            "Hidden rows or columns may be skipped or silently omitted by some screen "
            "readers, making audible data inconsistent with the visual presentation. If "
            "hidden content is genuinely informational it must be made visible or removed "
            "entirely; if it is only for printing it should be documented."
        ),
        "suppress_guidance": (
            "Suppress only when hidden rows/columns are confirmed as structural scaffolding "
            "(calculation helpers with no display purpose) and verified as correctly "
            "skipped by the target screen reader."
        ),
    },
    "XLSX-HEADER-FROZEN": {
        "full_description": (
            "Freezing the header row keeps column labels visible as a user scrolls down "
            "through a long dataset. For large-print Excel users who see fewer rows at a "
            "time due to magnification, losing the column header after scrolling 3-4 rows "
            "forces constant scroll-back. Frozen headers significantly reduce navigation "
            "effort in data-heavy workbooks."
        ),
        "suppress_guidance": (
            "Suppress for workbooks with no scrollable data, or for tables with fewer "
            "than 15 rows where scrolling is not required."
        ),
    },
    "XLSX-SHEET-NAME-LENGTH": {
        "full_description": (
            "Excel truncates sheet names at 31 characters. Names at or near this limit "
            "may be truncated in tab display, making them unreadable when combined with "
            "the ellipsis. Shorter names within 20-25 characters are more legible in "
            "the sheet tab strip, particularly for users with screen magnification who "
            "may see only one or two tabs at a time."
        ),
        "suppress_guidance": (
            "Suppress when the full 31-character name is genuinely necessary and "
            "truncation does not create ambiguity between tab names."
        ),
    },
    "XLSX-BLANK-ROWS-LAYOUT": {
        "full_description": (
            "Using multiple consecutive blank rows for visual spacing creates false "
            "structural gaps in the data model. Screen readers may interpret repeated "
            "blank rows as the end of a table, stopping navigation prematurely. "
            "Excel's row-height settings or Table styles should be used for spacing."
        ),
        "suppress_guidance": (
            "Suppress only for data separated into distinct logical sections by blank "
            "rows where each section is individually labelled."
        ),
    },
    "XLSX-DEFAULT-TABLE-NAME": {
        "full_description": (
            "Excel auto-generates table names like Table1 and Table2. When a workbook "
            "has multiple tables, these names appear in formula references and the Name "
            "Box but provide no indication of the table's content. Descriptive names "
            "(e.g. SalesData2024, StaffRoster) make formulas self-documenting and help "
            "screen reader users orient themselves when switching between named ranges."
        ),
        "suppress_guidance": (
            "Suppress for workbooks with a single table or for tables whose content is "
            "fully described by the sheet name."
        ),
    },
    # ------------------------------------------------------------------ PPTX
    "PPTX-TITLE": {
        "full_description": (
            "The presentation title in document properties is announced by screen readers "
            "when the file opens and is used as the document name in OS accessibility "
            "APIs. Without a title, screen readers announce the filename which is often "
            "a dated file-name string that provides no meaningful context."
        ),
        "suppress_guidance": (
            "Suppress for template files that will have a title added before distribution."
        ),
    },
    "PPTX-SLIDE-TITLE": {
        "full_description": (
            "Every slide must have a unique, non-empty title so screen reader users can "
            "navigate the slide deck using the slide outline and thumbnail panel. Without "
            "a slide title the slide is announced as 'Untitled slide N', forcing the user "
            "to read all slide content to find the slide they need. PowerPoint's "
            "Accessibility Checker flags missing slide titles as a Critical error."
        ),
        "suppress_guidance": (
            "Do not suppress. Missing slide titles are a Critical accessibility error. "
            "If a slide intentionally has no visible title, use a hidden title placeholder."
        ),
    },
    "PPTX-READING-ORDER": {
        "full_description": (
            "Screen readers process slide objects in the order defined by the selection "
            "pane reading order, which may differ from visual layout. A chart appearing "
            "above its caption visually may be read after it if the caption's z-order is "
            "lower, producing confusing audio: the reader hears a description before the "
            "thing being described. Reading order should match top-to-bottom, "
            "left-to-right visual layout."
        ),
        "suppress_guidance": (
            "Suppress after verifying the slide with a screen reader and confirming "
            "that audio reading order matches the intended content sequence."
        ),
    },
    "PPTX-TITLE-READING-ORDER": {
        "full_description": (
            "The Title placeholder should be the first object in reading order so screen "
            "readers announce the slide title before any content. If the title is "
            "processed after body content, the user must listen to the entire slide "
            "before learning what it is about. This is equivalent to a web page that "
            "places the H1 after the main body text."
        ),
        "suppress_guidance": (
            "Suppress only after verifying that the screen reader announces the title "
            "correctly as the first item on the slide."
        ),
    },
    "PPTX-SMALL-FONT": {
        "full_description": (
            "Text below 18 pt on a projected slide is commonly too small for attendees "
            "with moderate visual impairment to read from typical presentation distances. "
            "While less critical for presentations converted to large-print handouts, it "
            "is relevant for presentations distributed as digital files where the viewer "
            "controls zoom. The ACB minimum of 18 pt applies."
        ),
        "suppress_guidance": (
            "Suppress for slide elements where small text is necessary (e.g. footnotes, "
            "source citations in charts) and the content is also provided in speaker "
            "notes or a handout."
        ),
    },
    "PPTX-SPEAKER-NOTES": {
        "full_description": (
            "Speaker notes provide an accessible text channel for content conveyed "
            "visually on the slide (complex charts, infographics, diagrams). Screen "
            "readers can access speaker notes; attendees who receive a PDF or DOCX export "
            "can read the notes as extended alt text. For large-print users who receive "
            "a printed handout, speaker notes provide detail that the compact slide "
            "layout cannot contain."
        ),
        "suppress_guidance": (
            "Suppress for slides that are entirely text-based with no visual content "
            "requiring additional description."
        ),
    },
    "PPTX-CHART-ALT-TEXT": {
        "full_description": (
            "Charts in PowerPoint or Excel slides must have alternative text describing "
            "the key finding or trend, not just the chart type. A screen reader user who "
            "cannot see the chart should receive the same informational takeaway as a "
            "sighted viewer. Good alt text for a bar chart says 'Sales increased 32% "
            "from Q1 to Q4' -- not 'Bar chart'."
        ),
        "suppress_guidance": (
            "Do not suppress. Charts without alt text are completely invisible to "
            "non-visual users."
        ),
    },
    "PPTX-DUPLICATE-SLIDE-TITLE": {
        "full_description": (
            "Slides with identical titles create ambiguous navigation. In the slide "
            "thumbnail panel and slide outline view, a screen reader user sees a list of "
            "slide titles; if two slides are both titled 'Summary' the user cannot tell "
            "them apart without visiting each. Unique titles ensure navigation targets "
            "are unambiguous."
        ),
        "suppress_guidance": (
            "Suppress for presentations with a deliberate repeating-section structure "
            "(e.g. monthly report template) where another differentiator (date, section) "
            "is included in each slide."
        ),
    },
    "PPTX-HEADING-SKIP": {
        "full_description": (
            "When slide text uses heading styles they must not skip levels. A jump from "
            "a slide title (treated as H1) directly to H3 creates an invisible structural "
            "gap in the accessibility tree. The same heading hierarchy rules that apply "
            "to Word documents apply to styled text on PowerPoint slides."
        ),
        "suppress_guidance": (
            "Suppress only when heading level labels on the slide are confirmed as "
            "decorative and the actual structural hierarchy is provided through another "
            "mechanism."
        ),
    },
    "PPTX-FAST-AUTO-ADVANCE": {
        "full_description": (
            "Slides set to auto-advance in under 3 seconds deny users sufficient time "
            "to read the content, especially readers requiring magnification or additional "
            "processing time. WCAG 2.2.1 requires that automatically advancing content "
            "can be paused or timing can be extended. Auto-advance shorter than 3 seconds "
            "is also a failure for cognitive accessibility."
        ),
        "suppress_guidance": (
            "Suppress only for animated splash screens or countdown timers where the "
            "transition is intentional and clearly signalled. All informational slides "
            "must allow sufficient reading time."
        ),
    },
    "PPTX-REPEATING-ANIMATION": {
        "full_description": (
            "Animations set to repeat indefinitely cannot be paused by the user, "
            "violating WCAG 2.2.2 which requires that moving content lasting more than "
            "5 seconds can be paused, stopped, or hidden. Indefinitely looping animations "
            "also create distraction for readers with attention disabilities and can "
            "trigger symptoms in users with vestibular disorders."
        ),
        "suppress_guidance": (
            "Do not suppress. Remove the repeat setting from the animation, or add a "
            "pause control accessible by keyboard."
        ),
    },
    "PPTX-RAPID-AUTO-ANIMATION": {
        "full_description": (
            "Multiple auto-start animations with delays under 1 second create a rapid "
            "sequence of visual changes that can be disorienting for readers with low "
            "vision, cognitive disabilities, or vestibular disorders. Even if individual "
            "animations do not loop, a rapid sequence can trigger motion sensitivity. "
            "Animations should start on click or have delays of at least 1 second."
        ),
        "suppress_guidance": (
            "Suppress only after verifying that the rapid animation sequence does not "
            "convey essential information that cannot be provided through static content."
        ),
    },
    "PPTX-FAST-TRANSITION": {
        "full_description": (
            "Slide transitions set to 'Fast' move quickly enough to be disorienting for "
            "users with vestibular sensitivity. WCAG 2.3.3 (Level AAA) recommends "
            "avoiding animation from interactions, and fast transitions are a known pain "
            "point for readers with motion sensitivity. Switching to 'Medium' or 'Slow' "
            "transitions, or disabling transitions entirely, eliminates this risk."
        ),
        "suppress_guidance": (
            "Suppress for presentations where fast transitions are an intentional design "
            "choice confirmed by the audience. This is a Low-severity advisory rule."
        ),
    },
    # ------------------------------------------------------------------ Markdown
    "MD-HEADING-HIERARCHY": {
        "full_description": (
            "Markdown heading levels map directly to HTML H1-H6 elements when rendered. "
            "Skipping heading levels (e.g. # followed by ###) creates the same structural "
            "gap in the HTML accessibility tree as skipping heading styles in Word. "
            "Screen reader users who navigate via headings will encounter a confusing "
            "jump in hierarchy. Markdownlint rule MD001 checks for this same condition."
        ),
        "suppress_guidance": (
            "Suppress only after confirming the heading level gap is intentional and the "
            "document has been tested with a screen reader to confirm correct navigation."
        ),
    },
    "MD-MULTIPLE-H1": {
        "full_description": (
            "HTML documents should have exactly one H1 element representing the page "
            "title. Multiple H1 headings create ambiguity about the primary topic of the "
            "document. Most markdown processors map '# heading' to H1; having several H1s "
            "produces a flat top-level structure in the heading outline with no clear "
            "document title."
        ),
        "suppress_guidance": (
            "Suppress for documentation systems (e.g. Docusaurus, mkdocs) that inject "
            "the site/page title as H1 and treat the markdown H1 as the section heading, "
            "if this pattern is consistent and tested."
        ),
    },
    "MD-NO-ITALIC": {
        "full_description": (
            "Italic emphasis in Markdown (*text* or _text_) renders as emphasis in HTML. "
            "However ACB guidelines prohibit italic for the same legibility reasons as "
            "Word: slanted strokes are harder to resolve at large sizes and under "
            "magnification. Use underline HTML (<u>text</u>) for inline emphasis in "
            "ACB-compliant Markdown documents."
        ),
        "suppress_guidance": (
            "Suppress only for Markdown documents that will not be converted to "
            "large-print print output, such as software README files or API documentation."
        ),
    },
    "MD-BOLD-EMPHASIS": {
        "full_description": (
            "Bold in Markdown (**text**) renders as strong emphasis in HTML. ACB "
            "guidelines require that body emphasis uses underline so bold is reserved "
            "for structural elements (headings, table headers). Using bold for body "
            "emphasis blurs the visual distinction between structural and inline emphasis."
        ),
        "suppress_guidance": (
            "Suppress for technical documentation where bold is a conventional emphasis "
            "standard (e.g. UI control names, command names) and the document is not "
            "being produced for large-print distribution."
        ),
    },
    "MD-BARE-URL": {
        "full_description": (
            "A bare URL in Markdown is often auto-linked by renderers but provides no "
            "description of the destination. Screen readers announce the full URL "
            "character by character, which is extremely verbose for long URLs. For print "
            "output a bare URL is also inaccessible because there is nothing meaningful "
            "to read. All URLs should be wrapped in descriptive link text."
        ),
        "suppress_guidance": (
            "Suppress only for reference lists where the URL itself is the reference "
            "and a verbal description would not add clarity."
        ),
    },
    "MD-AMBIGUOUS-LINK": {
        "full_description": (
            "Link text such as 'click here', 'here', 'read more', or 'link' provides no "
            "context when read in isolation. Screen readers offer a 'links list' navigation "
            "mode where only link text is announced; a list of 'here, here, here' links "
            "is completely unusable. Every link should describe its destination or action."
        ),
        "suppress_guidance": (
            "Do not suppress. Ambiguous link text is a WCAG 2.4.4 failure. Replace with "
            "descriptive text."
        ),
    },
    "MD-EMPTY-LINK-TEXT": {
        "full_description": (
            "A Markdown link with empty text renders as a link with no visible label. "
            "Screen readers announce it as an unlabelled link. WCAG 4.1.2 requires that "
            "all interactive elements have an accessible name."
        ),
        "suppress_guidance": "Do not suppress. Empty link text is always an accessibility error.",
    },
    "MD-URL-AS-LINK-TEXT": {
        "full_description": (
            "Using a URL as the visible link text provides the same experience as a bare "
            "URL: verbose and unhelpful when read by a screen reader. The link text "
            "should describe the destination, not repeat the URL."
        ),
        "suppress_guidance": (
            "Suppress only in reference sections where the URL is the citation and a "
            "separate description is provided in the surrounding text."
        ),
    },
    "MD-MISSING-ALT-TEXT": {
        "full_description": (
            "Images in Markdown without alt text render as images with no accessible "
            "name. Screen readers announce these as 'image' or read the filename aloud. "
            "Alt text must describe the informational content. Decorative images should "
            "use empty alt text, which is detected as intentionally decorative."
        ),
        "suppress_guidance": (
            "Do not suppress. Missing alt text on informational images is a "
            "WCAG 1.1.1 Level A failure."
        ),
    },
    "MD-NO-EMOJI": {
        "full_description": (
            "Emoji characters are announced by screen readers using their Unicode name "
            "(e.g. 'Thumbs Up Sign'), which can be verbose, unexpected, or culturally "
            "ambiguous. In large-print print output emoji render as small Unicode symbols "
            "that may be illegible or print as question marks on some printers. ACB "
            "guidelines require emoji to be removed or replaced with plain-text equivalents."
        ),
        "suppress_guidance": (
            "Suppress only for digital-only documents (not for print) where emoji are "
            "part of the brand voice and the audience is confirmed to be comfortable "
            "with screen reader emoji announcements."
        ),
    },
    "MD-TABLE-NO-DESCRIPTION": {
        "full_description": (
            "Markdown pipe tables do not support native captions. A table without a "
            "preceding text description forces the reader to infer its purpose from the "
            "data. For screen reader users the table is announced immediately without "
            "context. WCAG best practice requires all complex data tables to have a "
            "description or caption identifying the data set."
        ),
        "suppress_guidance": (
            "Suppress only for tables where the heading immediately above provides a "
            "clear and unambiguous description of the table content."
        ),
    },
    "MD-EM-DASH": {
        "full_description": (
            "Em-dashes and en-dashes are announced inconsistently by screen readers: "
            "some say 'em dash', some pause silently, and some skip them entirely. This "
            "creates ambiguous sentence flow in audio rendering. For print output the "
            "em-dash character may print as a question mark on systems without full "
            "Unicode font support. Plain hyphens or double hyphens are more portable."
        ),
        "suppress_guidance": (
            "Suppress for academic or literary documents where em-dashes are a required "
            "stylistic element and the output is digital-only with a confirmed modern "
            "screen reader."
        ),
    },
    "MD-ALT-TEXT-FILENAME": {
        "full_description": (
            "Alt text that is a filename (e.g. 'photo.jpg', 'IMG_2034.png') provides no "
            "useful description of image content. It is a common auto-populated default "
            "from some Markdown editors. Screen readers announce the filename literally, "
            "which is unhelpful. Alt text should describe what the image shows."
        ),
        "suppress_guidance": "Do not suppress. A filename as alt text is always an error; write a real description.",
    },
    "MD-ALT-TEXT-REDUNDANT-PREFIX": {
        "full_description": (
            "Alt text beginning with 'image of', 'picture of', or 'photo of' is redundant "
            "because screen readers already announce the element as an image before reading "
            "the alt text. The prefix wastes listener attention and delays the actual "
            "description. Start alt text directly with the description."
        ),
        "suppress_guidance": (
            "Suppress only if the document is print-only output where the prefix provides "
            "clarity to print readers who cannot rely on screen reader role announcement."
        ),
    },
    "MD-ALT-TEXT-TOO-SHORT": {
        "full_description": (
            "Alt text shorter than 3 characters is almost certainly not a meaningful "
            "description of any image. Extremely short alt text may be a cut-and-paste "
            "error or a placeholder never completed. WCAG 1.1.1 requires a genuine text "
            "equivalent."
        ),
        "suppress_guidance": (
            "Suppress only for images confirmed as decorative where the 1- or 2-character "
            "alt text is an intentional empty-equivalent marker."
        ),
    },
    "MD-NO-YAML-FRONT-MATTER": {
        "full_description": (
            "YAML front matter is the conventional location for document metadata in "
            "Markdown: title, language, author, and description. Without a front matter "
            "block the document title cannot be automatically derived, and Pandoc/Hugo/"
            "Docusaurus renderers cannot set the HTML title element. WCAG 2.4.2 requires "
            "every page to have a descriptive title."
        ),
        "suppress_guidance": (
            "Suppress for Markdown fragments (included into a larger document) rather "
            "than standalone pages, where the parent document provides the title."
        ),
    },
    "MD-YAML-UNCLOSED-FENCE": {
        "full_description": (
            "A YAML front matter block that opens with '---' but has no closing '---' "
            "fence is treated as a thematic break or fenced block by most Markdown "
            "parsers, so metadata is not parsed and the rest of the document may be "
            "misformatted. This is almost always a structural error."
        ),
        "suppress_guidance": "Do not suppress. Close the YAML fence with '---' on its own line.",
    },
    "MD-YAML-MISSING-TITLE": {
        "full_description": (
            "The 'title:' field in YAML front matter is used by Pandoc, Jekyll, Hugo, "
            "and most static site generators to set the title element of the rendered "
            "HTML page. Without it, WCAG 2.4.2 cannot be satisfied automatically during "
            "conversion. The title should be a concise description of the document, "
            "not the filename."
        ),
        "suppress_guidance": (
            "Suppress for Markdown fragments included into a parent document that "
            "provides the title."
        ),
    },
    "MD-YAML-MISSING-LANG": {
        "full_description": (
            "The 'lang:' or 'language:' field sets the HTML lang attribute during "
            "conversion, enabling screen readers to select the correct pronunciation "
            "model. WCAG 3.1.1 (Level A) requires language declaration. The value must "
            "be a valid BCP 47 language tag (e.g. 'en', 'en-US', 'fr-CA')."
        ),
        "suppress_guidance": (
            "Suppress only for document fragments. For standalone documents, always "
            "include a lang: field."
        ),
    },
    "MD-YAML-MISSING-AUTHOR": {
        "full_description": (
            "An author field in YAML front matter enables downstream processors to "
            "include author attribution in the rendered output and in document properties. "
            "While not a WCAG requirement, it is a best practice for accessible publishing "
            "that allows readers to identify who produced the document."
        ),
        "suppress_guidance": (
            "Suppress for anonymous publications, template files, or documents where "
            "authorship is withheld for privacy or review reasons."
        ),
    },
    "MD-YAML-MISSING-DESCRIPTION": {
        "full_description": (
            "A description field provides a short summary used in social previews, search "
            "engine snippets, and document metadata. While not a WCAG requirement, it "
            "improves findability and previewing for users who rely on document summaries "
            "to decide whether to read a file."
        ),
        "suppress_guidance": (
            "Suppress for internal documents, template files, or documents where a "
            "separate abstract is provided in the document body."
        ),
    },
    "MD-NO-HEADINGS": {
        "full_description": (
            "A Markdown document with no headings produces an HTML page with no "
            "structural navigation landmarks. Screen reader users who navigate via "
            "headings will hear 'no headings found'. Long documents without headings "
            "also deny low-vision readers the visual landmarks used for scanning and "
            "re-orientation."
        ),
        "suppress_guidance": (
            "Suppress for intentionally flat documents (very short FAQs, single-topic "
            "reference cards, cover letters) where headings would be artificial."
        ),
    },
    "MD-DUPLICATE-HEADING-TEXT": {
        "full_description": (
            "Duplicate heading text at the same level creates ambiguity in the document "
            "outline. Screen readers list headings by text; two identical entries make "
            "navigation confusing. Each heading should uniquely describe its section."
        ),
        "suppress_guidance": (
            "Suppress for documents with deliberate repeating-section structures "
            "(e.g. per-chapter notes) where an additional differentiator is clear from "
            "context."
        ),
    },
    "MD-LONG-SECTION-WITHOUT-HEADING": {
        "full_description": (
            "Sections with 20 or more paragraphs between headings create long undivided "
            "blocks of text with no navigational waypoints. Screen reader users must "
            "listen through the entire section; low-vision readers scrolling with "
            "magnification lose their place easily. Breaking long sections with "
            "sub-headings dramatically improves navigation."
        ),
        "suppress_guidance": (
            "Suppress for narrative content (fiction, poetry, personal essays) where "
            "section headings would be stylistically inappropriate."
        ),
    },
    "MD-EMPTY-HEADING": {
        "full_description": (
            "A heading marker with no text creates an invisible heading in document "
            "structure. Screen readers announce it as a heading with no text, which is "
            "confusing. The heading appears in navigation outlines as a blank entry. "
            "This is almost always an authoring error."
        ),
        "suppress_guidance": "Do not suppress. Remove or complete the empty heading.",
    },
    "MD-HEADING-TOO-LONG": {
        "full_description": (
            "Headings exceeding 120 characters become unwieldy navigation targets. In "
            "the screen reader headings list, table of contents, and sidebar navigation, "
            "long headings overflow or are truncated. They are also harder to scan "
            "visually at large text sizes. Good headings are concise labels, not full "
            "sentences."
        ),
        "suppress_guidance": (
            "Suppress for technical documentation where heading text must include a "
            "full function signature or code path for search indexing purposes."
        ),
    },
    "MD-HEADING-ENDS-PUNCTUATION": {
        "full_description": (
            "Headings ending with a period, semicolon, or colon cause some screen readers "
            "to insert an audible pause mid-navigation (as if the heading were a sentence). "
            "Headings are labels, not sentences, and should not end with sentence-final "
            "punctuation."
        ),
        "suppress_guidance": (
            "Suppress for headings structured as questions (ending with '?') or "
            "exclamations ('!'), which are stylistically appropriate and do not cause "
            "screen reader announce issues."
        ),
    },
    "MD-CODE-BLOCK-NO-LANGUAGE": {
        "full_description": (
            "Fenced code blocks without a language identifier cannot be syntax-highlighted "
            "by renderers and cannot be programmatically identified as a specific content "
            "type. This prevents screen readers from activating specialized reading modes "
            "for code and prevents conversion tools from applying appropriate styling."
        ),
        "suppress_guidance": (
            "Suppress for code blocks where the language is genuinely unknown or the "
            "block contains pseudo-code with no specific language mapping."
        ),
    },
    "MD-INDENTED-CODE-BLOCK": {
        "full_description": (
            "4-space indented code blocks are a legacy Markdown feature that cannot "
            "carry a language identifier. They are also harder to distinguish visually "
            "from deeply nested blockquotes. Using fenced code blocks with an explicit "
            "language tag is the modern best practice and enables syntax highlighting "
            "and accessibility metadata."
        ),
        "suppress_guidance": (
            "Suppress for documents generated by tools that output indented code blocks "
            "and cannot be easily reconfigured to produce fenced blocks."
        ),
    },
    "MD-RAW-HTML-TABLE": {
        "full_description": (
            "Raw HTML table elements in Markdown must include th header cells with "
            "appropriate scope attributes and a caption element to satisfy WCAG 1.3.1. "
            "A plain HTML table with only td cells provides no column or row header "
            "context to screen readers navigating cell by cell."
        ),
        "suppress_guidance": (
            "Suppress after verifying that the HTML table includes all required "
            "accessibility attributes and has been tested with a screen reader."
        ),
    },
    "MD-MOVING-CONTENT": {
        "full_description": (
            "The marquee and blink HTML elements create moving or flashing content that "
            "cannot be paused or stopped by users, violating WCAG 2.2.2. Both elements "
            "are also deprecated in HTML5. They should be removed or replaced with "
            "static content."
        ),
        "suppress_guidance": "Do not suppress. Remove the element entirely.",
    },
    "MD-RAW-BR-TAG": {
        "full_description": (
            "Using raw br tags in Markdown for line breaks reduces portability and "
            "prevents some Markdown processors from handling line breaks correctly. "
            "CommonMark specifies that two trailing spaces create a hard line break; "
            "using br mixes HTML and Markdown syntax in a way that may not render "
            "correctly in all processors."
        ),
        "suppress_guidance": (
            "Suppress for Markdown that targets HTML output only and where the author "
            "has confirmed br renders correctly in the deployment environment."
        ),
    },
    "MD-RAW-HTML-GENERIC-CONTAINER": {
        "full_description": (
            "Raw div and span elements in Markdown are invisible to renderers that "
            "strip HTML, and add no semantic value. For accessible large-print content, "
            "all structure should be expressed in Markdown syntax so it can be converted "
            "cleanly to Word, PDF, or EPUB without HTML post-processing."
        ),
        "suppress_guidance": (
            "Suppress for Markdown targeting a specific HTML-aware renderer where div "
            "classes provide necessary layout or accessibility roles."
        ),
    },
    "MD-RAW-HTML-PRESENTATIONAL": {
        "full_description": (
            "The font and center elements are deprecated HTML4 presentational tags that "
            "carry no semantic value and are not supported in HTML5. They override the "
            "intended ACB styling when the document is rendered and may produce unexpected "
            "output when converted to Word, PDF, or EPUB."
        ),
        "suppress_guidance": "Do not suppress. Replace with Markdown syntax or CSS.",
    },
    "MD-BLANK-TABLE-HEADER": {
        "full_description": (
            "Pipe tables with blank column headers leave those columns without a label "
            "for screen reader navigation. When a user navigates to a cell in a headerless "
            "column, the screen reader cannot announce which column the cell belongs to. "
            "Every data column must have a descriptive, non-blank header."
        ),
        "suppress_guidance": "Do not suppress. Provide a header for every column, even if brief.",
    },
    "MD-TABLE-COLUMN-MISMATCH": {
        "full_description": (
            "A data row with a different column count than the header row produces "
            "misaligned or orphaned cells when rendered. Screen readers may announce "
            "extra cells as belonging to incorrect columns, or skip them. This is "
            "almost always an authoring error (a missing or extra pipe character)."
        ),
        "suppress_guidance": "Do not suppress. Fix the column count mismatch.",
    },
    "MD-FAKE-LIST-BULLET": {
        "full_description": (
            "Unicode bullet characters typed inline instead of using Markdown list syntax "
            "produce unstructured text that screen readers cannot identify as a list. "
            "The list count and navigation shortcuts are lost. Use proper Markdown list "
            "syntax (- item or * item)."
        ),
        "suppress_guidance": (
            "Suppress only for content where the bullet character is used in a non-list "
            "context (e.g. a bullet as a design separator or brand element)."
        ),
    },
    "MD-FAKE-NUMBERED-LIST": {
        "full_description": (
            "Lines that manually simulate an ordered list outside of Markdown ordered "
            "list syntax are treated as body text. Screen readers cannot identify the "
            "list count or provide list navigation. Use proper ordered list syntax."
        ),
        "suppress_guidance": (
            "Suppress for content where numbers are part of the text rather than list "
            "markers (e.g. procedural steps in a table cell, numbered citations)."
        ),
    },
    "MD-FAKE-INLINE-BULLET": {
        "full_description": (
            "Inline bullet characters within a paragraph create visual pseudo-lists that "
            "have no semantic structure. This pattern is common in legacy documents "
            "converted from Word where list formatting was lost. The inline bullets "
            "should be converted to a proper Markdown list."
        ),
        "suppress_guidance": (
            "Suppress for content where the bullet character is an intentional inline "
            "separator or brand symbol."
        ),
    },
    "MD-EXCESSIVE-BLANK-LINES": {
        "full_description": (
            "Three or more consecutive blank lines are usually accidental whitespace from "
            "copy-paste operations. In rendered output they produce large visual gaps "
            "that can be mistaken for section or page breaks. For large-print print output "
            "excessive blank lines waste page space."
        ),
        "suppress_guidance": (
            "Suppress for Markdown files used as plain-text source where whitespace is "
            "used for visual readability in the editor but is stripped before rendering."
        ),
    },
    "MD-EXCESSIVE-TRAILING-SPACES": {
        "full_description": (
            "More than two trailing spaces at end of a line create a CommonMark hard "
            "line break in most renderers. Three or more trailing spaces are usually "
            "accidental whitespace from editor autocomplete or copy-paste and create "
            "unexpected line breaks in the rendered output."
        ),
        "suppress_guidance": (
            "Suppress for auto-generated Markdown where trailing spaces are part of "
            "the generation format."
        ),
    },
    "MD-ENTIRE-LINE-BOLDED": {
        "full_description": (
            "An entire body line bolded is visually similar to a heading but carries no "
            "heading semantics. Screen readers do not identify bold lines as headings and "
            "cannot include them in heading navigation. If the intention is to mark a "
            "section boundary or key point, use a Markdown heading instead."
        ),
        "suppress_guidance": (
            "Suppress for lines where bold is used for emphasis of a complete statement "
            "rather than as a structural heading substitute."
        ),
    },
    "MD-ALLCAPS": {
        "full_description": (
            "ALL CAPS body text suffers from the same legibility problems in Markdown "
            "as in Word: reduced word shape differentiation, potential screen reader "
            "letter-by-letter announcement, and visual fatigue. ACB guidelines prohibit "
            "ALL CAPS. Short acronyms (3 letters or fewer) and standard initialisms are "
            "excluded from this rule."
        ),
        "suppress_guidance": (
            "Suppress only for documents where ALL CAPS is mandated by the publishing "
            "context (e.g. legal headings, official notices) and cannot be changed."
        ),
    },
    # ------------------------------------------------------------------ PDF
    "PDF-TITLE": {
        "full_description": (
            "The PDF document title metadata is announced by PDF readers and screen "
            "readers when the file opens. Without a title, readers hear the filename "
            "(often a generated string like '20240408_final_v3.pdf'). "
            "WCAG 2.4.2 requires a descriptive page title."
        ),
        "suppress_guidance": (
            "Suppress only for template PDFs or internal working files that will have "
            "a title added before distribution."
        ),
    },
    "PDF-LANGUAGE": {
        "full_description": (
            "Setting the document language in PDF metadata activates the correct "
            "text-to-speech model in PDF screen readers such as Adobe Acrobat's built-in "
            "reader. Without it, text-to-speech may use the wrong accent or skip "
            "pronunciation rules. WCAG 3.1.1 Level A requires language declaration."
        ),
        "suppress_guidance": (
            "Suppress only for language-mixed PDFs where language is marked at the "
            "paragraph or span level, not document level."
        ),
    },
    "PDF-TAGGED": {
        "full_description": (
            "PDF tagging (structural markup) is the foundation of PDF accessibility. "
            "An untagged PDF is effectively an image to a screen reader: reading order, "
            "heading structure, table semantics, and alt text are all invisible. "
            "WCAG 1.3.1 requires all information conveyed visually is also available "
            "programmatically. Tagging should be applied when the PDF is originally "
            "generated rather than as a post-processing step."
        ),
        "suppress_guidance": (
            "Do not suppress. An untagged PDF cannot be made accessible without full "
            "retagging."
        ),
    },
    "PDF-FONT-SIZE": {
        "full_description": (
            "Text below 18 pt in a PDF is too small for readers with low vision at "
            "normal document viewing distance. PDF fonts are embedded at a specific size; "
            "unlike Word documents, PDFs are not reflowable by default, so the viewer "
            "cannot easily increase font size without scrolling and zooming. ACB "
            "guidelines require 18 pt minimum for all body text."
        ),
        "suppress_guidance": (
            "Suppress only for PDFs created from sources that pre-date the ACB guidelines "
            "and cannot be regenerated at this time."
        ),
    },
    "PDF-FONT-FAMILY": {
        "full_description": (
            "PDF documents should use Arial or a comparable humanist sans-serif font "
            "for body text per ACB guidelines. Serif fonts in PDFs can appear blurry "
            "on screen at certain resolutions due to hinting and anti-aliasing. Arial "
            "is the canonical ACB recommendation."
        ),
        "suppress_guidance": (
            "Suppress when the PDF was created from a source using an approved accessible "
            "sans-serif font (Helvetica, APHont, Verdana) and visual quality has been "
            "confirmed by low-vision users."
        ),
    },
    "PDF-NO-IMAGES-OF-TEXT": {
        "full_description": (
            "PDFs consisting entirely of scanned page images have no underlying text "
            "layer. Screen readers cannot read the content at all; text-to-speech produces "
            "silence. WCAG 1.4.5 prohibits images of text except where the particular "
            "presentation of text is essential. Scanned PDFs must be OCR'd and then "
            "manually reviewed for reading order and tagging."
        ),
        "suppress_guidance": (
            "Suppress only for archival scans of historical documents where OCR is not "
            "feasible and the document is clearly labelled as a visual scan with an "
            "alternative accessible version provided."
        ),
    },
    "PDF-IMAGE-RESOLUTION": {
        "full_description": (
            "Images in scanned PDFs below 150 DPI cannot be reliably OCR'd because "
            "character outlines are too degraded for automatic text recognition. "
            "Low-resolution scans also appear blurry when zoomed, especially harmful "
            "for low-vision readers who use magnification. 300 DPI is the recommended "
            "minimum for accessible scanned documents."
        ),
        "suppress_guidance": (
            "Suppress only for historical archives where higher-resolution source "
            "material is unavailable."
        ),
    },
    "PDF-BOOKMARKS": {
        "full_description": (
            "PDF bookmarks (outlines) provide a navigable document outline equivalent "
            "to heading navigation in HTML. Screen reader users in Adobe Acrobat can "
            "open the Bookmarks panel and jump to any section directly. For large-print "
            "PDFs with many pages, bookmarks are essential for efficient navigation."
        ),
        "suppress_guidance": (
            "Suppress only for single-page PDFs or very short documents (fewer than "
            "5 pages) where bookmarks would be redundant."
        ),
    },
    # ------------------------------------------------------------------ EPUB
    "EPUB-TITLE": {
        "full_description": (
            "The ePub OPF title metadata is the accessible name of the publication. "
            "Reading systems announce it when the ePub is opened and display it in "
            "library lists. Without a title, the ePub appears as an unnamed file in "
            "the user's library."
        ),
        "suppress_guidance": (
            "Suppress for ePub template files that will have a title added before "
            "distribution."
        ),
    },
    "EPUB-LANGUAGE": {
        "full_description": (
            "The ePub OPF language metadata is used by reading systems to select the "
            "appropriate text-to-speech voice. Without it, the reading system may use a "
            "default locale that does not match the publication language, degrading "
            "comprehension for non-visual readers."
        ),
        "suppress_guidance": (
            "Suppress only for multilingual ePubs where language is declared at the "
            "content document level."
        ),
    },
    "EPUB-NAV-DOCUMENT": {
        "full_description": (
            "The ePub navigation document provides the table of contents that reading "
            "systems display in their navigation panel. Without it, users cannot jump "
            "directly to chapters or sections. EPUB Accessibility 1.1 requires a "
            "navigation document for conformance."
        ),
        "suppress_guidance": "Do not suppress. The nav document is required by the EPUB 3 specification.",
    },
    "EPUB-HEADING-HIERARCHY": {
        "full_description": (
            "ePub content documents use the same HTML heading elements as web pages. "
            "Skipped heading levels create the same structural gap in the accessibility "
            "tree as in Word or Markdown. Reading system users who navigate by headings "
            "will encounter a confusing jump in structure."
        ),
        "suppress_guidance": (
            "Suppress only after verifying with a screen reader that navigation is "
            "unambiguous despite the heading level gap."
        ),
    },
    "EPUB-MISSING-ALT-TEXT": {
        "full_description": (
            "Images in ePub content documents without alt text are invisible to "
            "non-visual users, violating WCAG 1.1.1. ePub reading systems announce "
            "images without alt text as 'image' or read the filename. Every informational "
            "image must have a meaningful text alternative."
        ),
        "suppress_guidance": (
            "Suppress only for images confirmed as decorative and marked with empty "
            "alt text."
        ),
    },
    "EPUB-TABLE-HEADERS": {
        "full_description": (
            "Tables in ePub content documents that use only td cells without th header "
            "cells provide no column or row context to screen readers. The first row or "
            "column should use th elements with appropriate scope attributes to identify "
            "headers."
        ),
        "suppress_guidance": (
            "Suppress only for layout tables that carry no data semantics and have been "
            "confirmed as read correctly by the target reading system."
        ),
    },
    "EPUB-ACCESSIBILITY-METADATA": {
        "full_description": (
            "Schema.org accessibility metadata in the OPF package document describes "
            "the access modes, features, and hazards of the publication. This metadata "
            "enables library catalogues, reading systems, and distribution platforms to "
            "filter ePubs by accessibility properties, helping readers find books that "
            "meet their needs."
        ),
        "suppress_guidance": (
            "Suppress only for internal ePubs that will not be distributed through "
            "platforms that use accessibility metadata for filtering."
        ),
    },
    "EPUB-LINK-TEXT": {
        "full_description": (
            "Hyperlinks in ePub content documents must have descriptive link text for "
            "the same reasons as in HTML: screen readers build a links list from link "
            "text, and non-descriptive links such as 'click here' or raw URLs are not "
            "useful in isolation."
        ),
        "suppress_guidance": (
            "Suppress only for reference lists where the URL itself is the citation "
            "and a verbal description is provided in the surrounding text."
        ),
    },
    "EPUB-ACCESSIBILITY-HAZARD": {
        "full_description": (
            "EPUB Accessibility 1.1 requires publishers to declare known hazards in "
            "OPF metadata: flashing content (epilepsy risk), motion simulation "
            "(vestibular disorder risk), or sound (for deaf/hard-of-hearing). If no "
            "hazards are present, the value 'none' must be declared explicitly."
        ),
        "suppress_guidance": "Do not suppress. Declare either the specific hazards or 'none' explicitly.",
    },
    "EPUB-ACCESS-MODE-SUFFICIENT": {
        "full_description": (
            "The accessModeSufficient metadata declares which combination of access "
            "modes (textual, visual, auditory, tactile) is sufficient to access the full "
            "informational content of the publication. This metadata helps users with "
            "specific modality needs select publications that are fully accessible to "
            "them."
        ),
        "suppress_guidance": (
            "Suppress only for internal ePubs that will not be catalogued or distributed "
            "through accessibility-aware platforms."
        ),
    },
    "EPUB-PAGE-LIST": {
        "full_description": (
            "A page list in the ePub nav document maps ePub reading positions to printed "
            "page numbers, enabling co-reading between a physical print edition and the "
            "ePub. This is essential for classroom use where the instructor cites page "
            "numbers and students need to find the same location in their accessible "
            "digital edition."
        ),
        "suppress_guidance": (
            "Suppress for ePubs with no corresponding print edition or where page "
            "navigation is not required by the audience."
        ),
    },
    "EPUB-PAGE-SOURCE": {
        "full_description": (
            "When an ePub includes a page list, it should also declare the source of "
            "the page numbers in OPF metadata. This enables reading systems and "
            "catalogues to identify which print edition the page numbers correspond to, "
            "preventing ambiguity when multiple print editions exist."
        ),
        "suppress_guidance": (
            "Suppress if there is no corresponding print edition or if the page list "
            "was added for structural purposes rather than print co-reading."
        ),
    },
    "EPUB-MATHML-ALT": {
        "full_description": (
            "MathML elements in ePub content must carry an alttext attribute so reading "
            "systems that do not support MathML rendering can present a text equivalent. "
            "Without alttext, non-visual readers who use a reading system without MathML "
            "support hear silence when the math expression is encountered."
        ),
        "suppress_guidance": (
            "Suppress only if the ePub targets reading systems confirmed to render "
            "MathML visually and provide built-in speech output."
        ),
    },
    "EPUB-TEXT-INDENT": {
        "full_description": (
            "CSS text-indent or large margin-left values on body text in ePub content "
            "narrow the reading column. For ePub reflowable content often read at large "
            "text sizes or on small screens, indented paragraphs significantly reduce "
            "words per line and increase reading effort. ACB guidelines require flush-left "
            "alignment."
        ),
        "suppress_guidance": (
            "Suppress when the indentation is a deliberate ACB-deviation agreed with "
            "the receiving organisation."
        ),
    },
    "EPUBCHECK-ERROR": {
        "full_description": (
            "EPUBCheck validation errors indicate that the ePub package does not conform "
            "to the EPUB specification. These errors can prevent the ePub from opening in "
            "some reading systems, or can cause incorrect rendering that undermines the "
            "accessibility of the content."
        ),
        "suppress_guidance": "Do not suppress. Fix the underlying structural error identified by EPUBCheck.",
    },
    "EPUBCHECK-WARNING": {
        "full_description": (
            "EPUBCheck warnings indicate non-conformant but not necessarily catastrophic "
            "issues in the ePub package. Some warnings indicate deprecated features that "
            "may not be supported in future reading systems; others indicate best-practice "
            "deviations."
        ),
        "suppress_guidance": (
            "Suppress only after reviewing the specific warning and confirming it does "
            "not affect accessibility or reading system compatibility."
        ),
    },
    "ACE-EPUB-CHECK": {
        "full_description": (
            "The DAISY Ace accessibility checker runs a suite of EPUB-specific rules "
            "against the content documents and package structure. This catch-all rule "
            "captures any Ace finding not mapped to a more specific rule. Review the "
            "Ace report for the specific rule ID and description."
        ),
        "suppress_guidance": (
            "Suppress only after reviewing the Ace report and confirming the finding is "
            "a false positive or is not applicable to this ePub."
        ),
    },
    "ACE-AXE-CHECK": {
        "full_description": (
            "DAISY Ace runs axe-core HTML accessibility checks against the content "
            "documents inside the ePub. This catch-all rule captures axe-core findings "
            "not mapped to a more specific EPUB rule. Review the Ace report for the "
            "specific axe rule ID, its impact level, and the HTML element affected."
        ),
        "suppress_guidance": (
            "Suppress only after reviewing the Ace/axe report and confirming the finding "
            "is a false positive or does not apply to this content type."
        ),
    },
}
