# ACB Document Accessibility Toolkit -- User Guide

Everything you need to know to audit, fix, convert, and template your documents for ACB Large Print compliance. New to accessibility? Start with the quick-start walkthrough below.

## In This Guide

1. [Quick-Start Walkthrough](#1-quick-start-walkthrough)
2. [How to Audit a Document](#2-how-to-audit-a-document)
3. [How to Fix a Document](#3-how-to-fix-a-document)
4. [How to Create a Template](#4-how-to-create-a-template)
5. [How to Export to HTML](#5-how-to-export-to-html)
6. [How to Convert Between Formats](#6-how-to-convert-between-formats)
7. [Understanding Your Results](#7-understanding-your-results)
8. [Common Issues and How to Fix Them](#8-common-issues-and-how-to-fix-them)
9. [Tips by Document Format](#9-tips-by-document-format)
10. [Recommended Workflows](#10-recommended-workflows)
11. [DAISY Accessibility Tools](#11-daisy-accessibility-tools)
12. [Keyboard and Screen Reader Tips](#12-keyboard-and-screen-reader-tips)
13. [Frequently Asked Questions](#13-frequently-asked-questions)
14. [Getting Help](#14-getting-help)

---

## 1. Quick-Start Walkthrough

If this is your first time, follow these three steps to check and fix a document in under two minutes:

### Step 1: Audit your document

Go to Audit, upload your file, and click Run Audit. You will get a compliance report showing every issue found, organized by severity.

Tip: First-time users should use Full Audit mode to see everything. You can switch to Quick Audit later once you know what to look for.

### Step 2: Fix what you can automatically

Go to Fix and upload the same file. For Word documents, the tool automatically corrects fonts, sizes, spacing, alignment, and emphasis. You download a fixed copy -- your original stays untouched.

Tip: Not all issues can be auto-fixed. The fix report tells you exactly which issues need your manual attention and how to fix them step by step.

### Step 3: Re-audit to confirm

Upload the fixed document back to Audit to confirm all auto-fixable issues are resolved. Address any remaining manual items from the report.

Tip: A perfect score means zero Critical and High findings. Medium and Low findings are best practices -- good to fix but not blocking.

### Starting from scratch?

If you have not written your document yet, start with Create a Template. This gives you a Word document with all ACB styles pre-configured. Write your content in the template and it will be compliant from the start -- no fixing needed.

---

## 2. How to Audit a Document

### Supported formats

- **Word (.docx)** -- full ACB + WCAG rule set (fonts, sizes, spacing, emphasis, headings, margins, document properties)
- **Excel (.xlsx)** -- sheet names, table headers, merged cells, alt text, color-only data, hyperlink text
- **PowerPoint (.pptx)** -- slide titles, reading order, alt text, font sizes, speaker notes, chart descriptions
- **Markdown (.md)** -- heading hierarchy, emphasis violations, link text, alt text, emoji, em-dashes, tables
- **PDF (.pdf)** -- title, language, tagging, font sizes, font families, scanned pages, bookmarks
- **ePub (.epub)** -- title, language, navigation, heading hierarchy, alt text, table headers, accessibility metadata, link text, MathML detection. Includes comprehensive DAISY Ace checks (100+ axe-core rules).

### Choosing an audit mode

- **Full Audit** (recommended for first use) -- Checks every rule applicable to your file type. Gives you the complete picture. Use this until you know your document's common issues.
- **Quick Audit** -- Checks only Critical and High severity rules. Use this for a fast pass when you are already familiar with your document's formatting.
- **Custom Audit** -- Pick individual rules to check. Useful when you are working on specific issues (e.g., only font rules) or running a targeted re-check.

### Step-by-step

1. Go to Audit.
2. Choose your rule categories (ACB Large Print, MS Accessibility Checker, or both).
3. Select an audit mode.
4. Upload your file (500 MB maximum).
5. Click Run Audit.
6. Review the report. Each finding shows the rule ID, severity, location in the document, and a description of what is wrong.

Tip: The audit report groups findings by severity. Tackle Critical issues first -- these make the document unreadable for low-vision users. Then work down through High, Medium, and Low.

---

## 3. How to Fix a Document

### What gets auto-fixed

| Format | Auto-Fix Level | What Is Corrected |
|--------|---------------|-------------------|
| Word (.docx) | Full auto-fix | Fonts to Arial, sizes to 18pt/22pt/20pt, italic removed, bold emphasis to underline, flush-left alignment, line spacing, margins, widow/orphan control, hyphenation off, language set |
| Markdown (.md) | Partial auto-fix | Heading hierarchy correction, italic removal, em-dash replacement |
| Excel, PowerPoint, PDF, ePub | Audit only | You receive a detailed report with manual fix guidance for each finding |

### Step-by-step

1. Go to Fix.
2. Upload your document.
3. Choose a fix mode (Full, Essentials, or Custom).
4. Click Fix Document.
5. For Word and Markdown: download the corrected file. Your original is untouched.
6. For other formats: review the audit report with step-by-step manual fix instructions.

Tip: The fix mode controls what appears in the report, not what gets corrected. Your Word document always receives all available auto-fixes regardless of mode.

---

## 4. How to Create a Template

A template (.dotx) is the easiest way to start compliant. Every new document you create from this template inherits all ACB formatting automatically.

### Step-by-step

1. Go to Template.
2. Enter a document title (or leave blank for the default).
3. Optionally check "Include sample content" if you want to see examples of correct formatting.
4. Check "Add binding margin" if the document will be printed and bound.
5. Click Create Template and save the downloaded .dotx file.
6. In Word, double-click the .dotx file to create a new document based on it.

### How to install the template in Word

1. Save the downloaded .dotx file to your Templates folder:
   - **Windows:** `%APPDATA%\Microsoft\Templates`
   - **macOS:** `~/Library/Group Containers/UBF8T346G9.Office/User Content/Templates`
2. In Word, go to File, New, Personal (or Custom on Mac).
3. Select the ACB Large Print template.
4. Start writing. All styles are already configured.

---

## 5. How to Export to HTML

Export converts a Word document to a web page with ACB-compliant CSS already applied. Choose between two output modes:

- **Standalone HTML** -- A complete web page with its own CSS file. Upload both files to your web server. Good for dedicated pages, intranet publishing, or email attachments.
- **CMS Fragment** -- An HTML snippet with embedded CSS scoped to a wrapper class. Paste it into WordPress, Drupal, or any CMS editor block. The scoped CSS will not conflict with your site theme.

### Step-by-step

1. Go to Export.
2. Upload a Word (.docx) file.
3. Optionally set a page title.
4. Choose Standalone or CMS Fragment.
5. Click Export and download your result.

Tip: If your source is Markdown instead of Word, use Convert with the "Accessible web page" option instead.

---

## 6. How to Convert Between Formats

The Convert page offers six conversion directions, each powered by a different engine. Choose the one that matches what you need to produce.

### To Markdown (plain text extraction)

**Powered by:** [Microsoft MarkItDown](https://github.com/microsoft/markitdown)

Extracts readable text from any supported file. Good for feeding documents into AI tools, creating starting points for documentation, or getting a simple version you can search and copy-paste. MarkItDown handles the widest range of input formats but produces plain text, not a finished web page.

**Accepts:** Word (.docx), Excel (.xlsx, .xls), PowerPoint (.pptx), PDF (.pdf), HTML, CSV, JSON, XML, ePub (.epub), and ZIP files.

**You get back:** a `.md` (Markdown) file -- plain text with formatting marks for headings, lists, and links. Opens in any text editor.

**Best when:** you need the raw content out of a document, regardless of its original format. Also the right first step if you plan to convert to HTML, Word, EPUB, or PDF later -- extract to Markdown, clean up the result, then convert from there.

### To accessible web page (HTML)

**Powered by:** [Pandoc](https://pandoc.org/) (John MacFarlane, UC Berkeley)

Turns a document into a complete, accessible HTML page with ACB Large Print CSS built in. Pandoc is the gold standard for document-to-HTML conversion -- it understands heading hierarchy, semantic lists, tables, footnotes, and cross-references, and produces clean, well-structured HTML. We embed our ACB Large Print CSS so the output meets accessibility standards out of the box.

**Accepts:** Markdown (.md), Word (.docx), reStructuredText (.rst), OpenDocument (.odt), Rich Text (.rtf), and ePub (.epub).

**You get back:** a standalone `.html` web page with all accessibility formatting included -- Arial font, large text, proper spacing, high contrast, and all other ACB requirements.

**Options:**

- **ACB formatting** (on by default) -- applies the full ACB Large Print stylesheet
- **Binding margin** -- shifts content right by 0.5 inches for printed/bound documents
- **Print stylesheet** -- adds `@media print` rules for ACB's tighter print line-height (1.15 instead of 1.5)

**Best when:** you need a web page that people will read in a browser, print on paper, email as an attachment, or upload to a website. Markdown (.md) files produce the cleanest output because Pandoc was specifically designed for Markdown-to-HTML conversion.

### To Word document (.docx)

**Powered by:** [Pandoc](https://pandoc.org/) (John MacFarlane, UC Berkeley)

Converts a document into a Word file. Pandoc maps headings, lists, tables, and emphasis into Word's native styles, so the output is immediately editable in Microsoft Word.

**Accepts:** Markdown (.md), reStructuredText (.rst), OpenDocument (.odt), Rich Text (.rtf), HTML (.html), and ePub (.epub).

**You get back:** a `.docx` file that opens directly in Microsoft Word or LibreOffice Writer.

**Best when:** you have a Markdown or HTML document and need a Word version for colleagues who work in Word, or when you want to run the toolkit's audit and auto-fix on content that started in another format. A common workflow: extract to Markdown, clean up, convert to Word, then run Fix for full ACB compliance.

### To EPUB 3 e-book (via Pandoc)

**Powered by:** [Pandoc](https://pandoc.org/) (John MacFarlane, UC Berkeley)

Creates a lightweight EPUB 3 e-book with ACB Large Print CSS embedded in the stylesheet. Pandoc generates proper EPUB structure including a navigation document, content documents with semantic markup, and EPUB metadata from the document title.

**Accepts:** Markdown (.md), Word (.docx), reStructuredText (.rst), OpenDocument (.odt), Rich Text (.rtf), and HTML (.html).

**You get back:** an `.epub` file that opens in any e-reader application (Apple Books, Calibre, Thorium, etc.).

**Options:**

- **ACB formatting** (on by default) -- embeds the ACB Large Print stylesheet in the EPUB
- **Binding margin** -- not applicable to EPUB (ignored)
- **Print stylesheet** -- not applicable to EPUB (ignored)

**Best when:** you need a simple, portable e-book and do not require DAISY Pipeline's advanced metadata and accessibility features. For a quick Markdown-to-EPUB conversion, this is the fastest path. For production-quality accessible EPUB with full schema.org metadata, use the DAISY Pipeline option instead.

### To accessible PDF

**Powered by:** [Pandoc](https://pandoc.org/) + [WeasyPrint](https://weasyprint.org/) (CourtBouillon)

Creates an accessible PDF formatted with ACB BOP print-optimized rules. Pandoc converts the source document to HTML, then WeasyPrint renders that HTML to PDF using a dedicated print stylesheet with @page rules. The PDF uses Liberation Sans (metrically identical to Arial) for consistent typography, 18pt body text, 22pt headings, 1.15 line spacing (the ACB print specification), and 1-inch margins.

**Accepts:** Markdown (.md), Word (.docx), reStructuredText (.rst), OpenDocument (.odt), Rich Text (.rtf), ePub (.epub), and HTML (.html).

**You get back:** a `.pdf` file ready for printing or distribution.

**Options:**

- **Binding margin** -- adds 0.5 inches of extra left margin for printed/bound documents

**Best when:** you need a print-ready document with ACB-compliant formatting. Good for meeting agendas, newsletters, and reports that will be printed and distributed in large print. Note: WeasyPrint produces CSS-rendered PDFs that are visually formatted but may not be fully PDF/UA tagged. For maximum PDF accessibility, fix the source document first and use your word processor's PDF export.

### To EPUB or DAISY (via DAISY Pipeline)

**Powered by:** [DAISY Pipeline 2](https://daisy.github.io/pipeline/) (DAISY Consortium)

Creates accessible publications in structured formats designed for reading systems used by people with print disabilities. Unlike the other tools, Pipeline produces packaged publications -- EPUB e-books and DAISY talking books -- with proper accessibility metadata, navigation documents, and reading order.

Available conversions:

- **Word to EPUB 3** -- converts a Word document (.docx) to an accessible EPUB 3 e-book through a DTBook intermediate format that preserves document structure
- **HTML to EPUB 3** -- packages an HTML page (.html) into a portable, accessible e-book
- **EPUB to DAISY 2.02** -- converts an ePub (.epub) to DAISY 2.02 talking book format for playback on dedicated DAISY hardware
- **EPUB to DAISY 3** -- converts an ePub (.epub) to DAISY 3 / DTBook structured text format

**You get back:** an `.epub` file (for EPUB conversions) or a `.zip` file containing the DAISY output folder.

Note: Pipeline conversions appear automatically when the DAISY Pipeline is installed on the server. If you do not see these options, Pipeline is not available on this server instance.

### How do I decide between them?

Think about **who will read the result** and **how they will read it:**

- **Reading on screen or printing from a browser?** Use "Accessible web page" -- an HTML file with ACB formatting that works in any browser and prints cleanly.
- **Need a print-ready PDF?** Use "Accessible PDF" -- formatted with ACB print rules (1.15 line spacing, 1-inch margins, Arial 18pt).
- **Need a Word file to edit or run through Fix?** Use "Word document" -- gives you a .docx to open in Microsoft Word.
- **Need a simple e-book?** Use "EPUB 3 e-book (via Pandoc)" -- a quick path to a portable .epub file.
- **Reading on a DAISY player or need full EPUB accessibility metadata?** Use "EPUB or DAISY" via Pipeline -- these are the formats those devices expect.
- **Editing, searching, or feeding to an AI tool?** Use "Plain text" -- raw content in a simple format that works everywhere.
- **Pasting into WordPress or Drupal?** Use the Export page instead -- it has CMS Fragment mode.

### Chaining conversions for better results

You can get the best output by using two conversions in sequence:

1. **Extract to Markdown** to pull text from a PDF, PowerPoint, or other complex format.
2. **Edit the Markdown** in any text editor to clean up headings, fix links, and improve structure.
3. **Convert the Markdown** to an accessible web page, Word document, EPUB, or PDF.

This two-step approach almost always produces better results than a one-step direct conversion, because you can review and improve the content between steps.

---

## 7. Understanding Your Results

### Severity levels

| Level | What It Means | Action |
|-------|--------------|--------|
| Critical | Makes the document unreadable for low-vision users or completely blocks assistive technology | Must fix. These are deal-breakers. |
| High | Significant readability or structure problems | Should fix. Major quality issues. |
| Medium | Compliance gaps that affect quality but may not block reading | Fix when possible. Good for polishing. |
| Low | Minor issues or best-practice recommendations | Nice to fix. Not blocking compliance. |

### Reading the report

Each finding in the audit report includes:

- **Rule ID** -- a short code like `ACB-FONT-FAMILY` or `EPUB-MISSING-ALT-TEXT`. Click the help links (in the web app) to learn more about each rule.
- **Severity** -- Critical, High, Medium, or Low.
- **Location** -- where in the document the issue was found (paragraph number, slide number, sheet name, heading text, etc.).
- **Description** -- what is wrong and why it matters.
- **Help links** -- links to the DAISY Knowledge Base, Microsoft support, or WCAG documentation for detailed remediation guidance.

---

## 8. Common Issues and How to Fix Them

### "All text must use Arial font" (ACB-FONT-FAMILY)

**Why:** Arial is required because it is a clean sans-serif font with excellent legibility at large sizes.

**Auto-fix:** Yes -- the fixer changes all fonts to Arial automatically.

**Manual fix:** In Word, select all text (Ctrl+A), then change the font to Arial.

### "Body text must be 18pt minimum" (ACB-FONT-SIZE-BODY)

**Why:** 18pt is the absolute floor for any text, including footnotes and captions.

**Auto-fix:** Yes -- the fixer increases all body text to 18pt.

**Manual fix:** Select text smaller than 18pt and increase the font size.

### "Italic formatting is prohibited" (ACB-NO-ITALIC)

**Why:** Italic text is harder to read for people with low vision because slanted shapes reduce letter distinction.

**Auto-fix:** Yes -- the fixer removes all italic formatting.

**Manual fix:** Select italic text, press Ctrl+I to remove italic. If emphasis is needed, use underline (Ctrl+U) instead.

### "Images must have alt text" (Various rules)

**Why:** Screen readers cannot describe images without alternative text. Users who cannot see the image rely entirely on the alt text.

**Auto-fix:** No -- alt text requires human judgment about the image content.

**Manual fix in Word:** Right-click the image, Edit Alt Text. Describe what the image shows in 1-2 sentences. If the image is purely decorative, check "Mark as decorative."

**Manual fix in ePub:** Add an `alt` attribute to the `<img>` tag in the content document.

### "Heading levels must not skip" (ACB-HEADING-HIERARCHY / EPUB-HEADING-HIERARCHY)

**Why:** Screen reader users navigate by heading levels. Jumping from H1 to H3 breaks their mental model of the document structure.

**Auto-fix:** Not automatically -- heading intent requires human judgment.

**Manual fix:** Review your heading hierarchy. Each H3 must have an H2 parent, each H2 must have an H1 parent. Restructure or re-level headings as needed.

### "Links must have descriptive text" (Various rules)

**Why:** Vague links like "click here" or "read more" do not tell screen reader users where the link goes. Links should make sense read out of context.

**Auto-fix:** No -- link text requires human judgment.

**Manual fix:** Replace vague text with descriptive text. For example, change "click here to download the report" to "download the annual report (PDF)".

### "ePub should include accessibility metadata" (EPUB-ACCESSIBILITY-METADATA)

**Why:** Accessibility metadata tells reading systems and library catalogs what accessibility features the publication offers.

**Manual fix:** Add schema.org metadata to the OPF package document: accessMode, accessibilityFeature, accessibilitySummary, and accessibilityHazard. See the [DAISY Knowledge Base on schema.org metadata](https://kb.daisy.org/publishing/docs/metadata/schema.org/index.html).

---

## 9. Tips by Document Format

### Word (.docx)

- Use Word's built-in heading styles (Heading 1, Heading 2, etc.) instead of manually formatting text to look like a heading.
- Use real bulleted and numbered lists (Home, Bullets/Numbering), not manually typed dashes or numbers.
- Set the document title in File, Properties, Title.
- Set the document language in Review, Language.
- For emphasis, use underline -- never italic, and avoid bold in body text.
- After using the fix tool, always re-audit to catch any remaining manual-fix items.

### Excel (.xlsx)

- Give every sheet a meaningful name -- "Sheet1" is not helpful to screen reader users.
- Use Format as Table so each column has a proper header row.
- Avoid merged cells -- they confuse screen readers navigating the grid.
- Add alt text to any embedded images or charts.
- Do not rely on color alone to convey information (e.g., red cells for errors).

### PowerPoint (.pptx)

- Every slide must have a unique title.
- Check the reading order in the Selection Pane (View, Selection Pane). Objects are read bottom-to-top, so the title should be at the bottom of the list.
- Add alt text to every image, chart, and SmartArt graphic.
- Use slide layouts with built-in placeholders instead of manually placed text boxes.
- Add speaker notes for slide content that is primarily visual.

### Markdown (.md)

- Use ATX-style headings (`# Heading 1`) not Setext-style (underlines).
- Never use italic (`*text*`) -- use `<u>text</u>` for emphasis instead.
- Write descriptive link text: `[download the annual report](url)` not `[click here](url)`.
- Add alt text to all images: `![Description of the image](image.png)`.
- Do not leave blank lines between list items.
- Avoid bare URLs -- wrap them in link syntax.

### PDF (.pdf)

- PDFs should be tagged (structured) for accessibility. Scanned documents without OCR will fail many checks.
- Set the document title and language in the PDF properties.
- Use bookmarks for navigation in long documents.
- The best approach for PDFs is to fix the source (usually Word) and re-export.

### ePub (.epub)

- Include a navigation document (table of contents) -- this is required by EPUB Accessibility 1.1.
- Add schema.org accessibility metadata to the OPF file.
- Ensure all images have alt text in the content documents.
- Use proper heading levels (h1-h6) without skipping.
- ePub audits include DAISY Ace, which runs 100+ axe-core accessibility checks beyond the basic structural rules.
- When your ePub includes schema.org accessibility metadata, the audit report shows a human-readable "Accessibility Metadata" section describing how the publication can be read (visual adjustments, read aloud, braille), conformance claims, navigation features, hazards, and more. This follows the W3C Accessibility Metadata Display Guide 2.0.
- If your ePub contains MathML, the audit will detect it and provide specific accessibility guidance for mathematical content.

---

## 10. Recommended Workflows

### Workflow A: Fix an existing document

1. **Audit first** -- upload to Audit to understand the scope of issues.
2. **Auto-fix** -- upload to Fix to correct everything the tool can handle.
3. **Manual fixes** -- open the fixed document and address remaining items from the fix report.
4. **Re-audit** -- upload the manually-fixed document to Audit to confirm.
5. **Publish** -- optionally Export to accessible HTML for web publishing.

### Workflow B: Start a new document from scratch

1. **Create a template** -- use Template to generate a pre-configured .dotx file.
2. **Write in the template** -- use the built-in styles for all formatting.
3. **Quick audit** -- when done, upload to Audit with Quick Audit mode to verify compliance.

### Workflow C: Publish meeting minutes or agendas online

1. Write your content in Markdown or Word.
2. **Audit** to check compliance.
3. **Fix** if needed.
4. **Convert** to accessible HTML using the Convert page with "Accessible web page" selected.
5. Upload the HTML file to your website.

### Workflow D: Create accessible EPUB publications

1. Start with a properly formatted Word document or Markdown file.
2. **Audit** the source document for ACB compliance.
3. **Convert to EPUB** using the Convert page -- choose "EPUB 3 e-book (via Pandoc)" for a quick e-book, or a DAISY Pipeline conversion for production-quality EPUB with full accessibility metadata.
4. **Audit the EPUB** -- upload the .epub to Audit for EPUB-specific accessibility checks (DAISY Ace runs automatically).
5. Fix any EPUB-specific issues (metadata, alt text, navigation) and re-audit.

### Workflow E: Produce large print PDF for distribution

1. Write your content in Markdown or Word.
2. **Audit** to check compliance.
3. **Fix** if needed (for Word documents).
4. **Convert to PDF** using the Convert page with "Accessible PDF" selected. Enable "Binding margin" if the document will be printed and bound.
5. Distribute the PDF for printing. The output uses ACB BOP print formatting -- Arial 18pt, 1.15 line spacing, 1-inch margins.

---

## 11. DAISY Accessibility Tools

This toolkit integrates with open source tools from the [DAISY Consortium](https://daisy.org/), an international association serving people with print disabilities. Here is how each integration works:

### DAISY Ace -- EPUB Accessibility Checker

[Ace by DAISY](https://daisy.github.io/ace/) is bundled with the web application and runs 100+ automated accessibility checks on EPUB publications using the axe-core engine. Every ePub audit automatically includes:

- All axe-core HTML accessibility rules (contrast, ARIA, landmarks, tables, forms)
- EPUB-specific metadata validation (accessibility metadata, package structure)
- Content document structure checks (headings, images, links)
- Findings linked to the [DAISY Knowledge Base](https://kb.daisy.org/publishing/) for remediation guidance

### DAISY Pipeline -- Document Conversion

[DAISY Pipeline](https://daisy.github.io/pipeline/) performs format conversions optimized for accessible publishing. When installed, the Convert page gains additional options:

- Word (.docx) to EPUB 3
- HTML to EPUB 3
- HTML to DAISY 2.02 (digital talking book format)
- EPUB 2 to EPUB 3 upgrade

### DAISY Knowledge Base

The [Accessible Publishing Knowledge Base](https://kb.daisy.org/publishing/) provides the help links you see throughout audit reports. Every ePub-related finding links to a specific Knowledge Base article with detailed remediation guidance.

### MathML and Mathematical Content

When ePub files contain MathML (mathematical markup), the audit detects it and provides guidance on making mathematical content accessible. The [MathCAT project](https://github.com/daisy/MathCAT) (Math Capable Assistive Technology) by DAISY generates speech, braille, and navigation from MathML for screen readers. If your ePub uses MathML, ensure it is properly structured so tools like MathCAT and MathJax can process it.

---

## 12. Keyboard and Screen Reader Tips

This tool is designed to work fully without a mouse. Here are tips for keyboard and screen reader users:

- **Skip link:** Press Tab on any page to reveal a "Skip to main content" link that jumps past the navigation.
- **Navigation:** The main navigation is a list of links. Use Tab and Enter to navigate between pages.
- **Forms:** All form fields have visible labels and description text. Errors are announced with the alert role.
- **Accordions:** Help sections use details/summary elements. Press Enter or Space on a summary to expand or collapse. Screen readers announce the expanded/collapsed state.
- **File upload:** After selecting a file, Tab to the submit button and press Enter. Upload progress is indicated by the page loading a new result.
- **Severity badges:** In the audit report, severity levels are shown as colored badges. The text content is always present (not color-only), so screen readers announce "Critical", "High", etc.
- **Help links:** External help links open in new tabs and are announced as such.
- **Back to top:** Each section on the Guidelines and Guide pages has a "Back to table of contents" link for quick navigation.

---

## 13. Frequently Asked Questions

### Is my document stored on the server?

No. Documents are processed in memory and deleted immediately after your results are returned. No files are stored, and no accounts are required.

### What is the maximum file size?

500 MB. If your document is larger, try compressing images within the document first (Word: File, Compress Pictures).

### Can I audit multiple documents at once?

The web tool processes one document at a time. For batch processing, use the [desktop application](https://github.com/accesswatch/acb-large-print-toolkit) which supports folder-level audits.

### Why does the fix not change my headings?

Heading hierarchy corrections require understanding your document's intended structure, which only you can determine. The fix tool corrects heading formatting (font, size, bold) but does not change heading levels. Review your heading structure manually using the report's guidance.

### What is the difference between ACB and MSAC rules?

**ACB Large Print** rules come from the American Council of the Blind's Board of Publications. They cover visual formatting: font, size, spacing, emphasis, alignment, and margins.

**MS Accessibility Checker (MSAC)** rules are aligned with the Microsoft Office Accessibility Checker and WCAG 2.1. They cover structural accessibility: alt text, table headers, reading order, hyperlink text, document properties.

Both categories work together for comprehensive compliance. Run with both enabled for best results.

### What about DAISY Pipeline conversions?

DAISY Ace is bundled with the web application and always runs during ePub audits. DAISY Pipeline (for advanced format conversions like Word to EPUB, HTML to DAISY 2.02) requires Java and is an optional server component. Pipeline conversions appear automatically when installed by the server administrator. For the desktop application, install Node.js and Ace (`npm install -g @daisy/ace`) for full ePub audit support.

### Can I use this tool for documents in languages other than English?

Yes. The ACB formatting rules (font, size, spacing) apply regardless of language. The tool audits document structure and formatting, not content. Set the document language property (Rule: ACB-DOC-LANGUAGE) to the correct language code for proper screen reader pronunciation.

### Is there a desktop version?

Yes. The [ACB Large Print Toolkit](https://github.com/accesswatch/acb-large-print-toolkit) includes a desktop application with a graphical wizard interface, command-line tools, and batch processing support. It runs on Windows without requiring an internet connection.

### Where can I read the ACB Large Print Guidelines?

The full guidelines are available at [acb.org/large-print-guidelines](https://acb.org/large-print-guidelines) (revised May 6, 2025). A reference copy is included in this repository at `docs/ACB Large Print Guidelines, revised 5-6-25.docx`. The web application includes a [Guidelines page](https://lp.csedesigns.com/guidelines) with the complete rule reference and related audit rule mappings.

---

## 14. Getting Help

- **Full ACB Large Print Guidelines Reference** -- available on the web app Guidelines page or at [acb.org/large-print-guidelines](https://acb.org/large-print-guidelines)
- **Submit Feedback** -- use the Feedback page in the web app to report bugs, request features, or share your experience
- **About This Project** -- mission, organizations, standards, and open source dependencies on the web app About page
- **GitHub Issues** -- [report bugs or request features](https://github.com/accesswatch/acb-large-print-toolkit/issues) on the open source repository
- **DAISY Knowledge Base** -- [remediation guidance](https://kb.daisy.org/publishing/) for ePub accessibility issues
- **Microsoft Accessibility Checker Guide** -- [Microsoft's guide](https://support.microsoft.com/en-us/office/improve-accessibility-with-the-accessibility-checker-a16f6de0-2f39-4a2b-8bd8-5ad801426c7f) to the Office accessibility checker
