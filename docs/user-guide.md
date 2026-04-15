# GLOW Accessibility Toolkit -- User Guide

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

**Quick links to new features:**
- [Quick Rule Exceptions](#quick-rule-exceptions)
- [Preserve centered headings](#preserve-centered-headings)
- [Per-level list indentation](#per-level-list-indentation)
- [FAQ page](/faq/) (also accessible from the web app footer)

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

### Recent Fix workflow updates

- If you uncheck **Detect and convert faux headings**, `ACB-FAUX-HEADING` is now suppressed from post-fix scoring so you are not penalized for a rule you intentionally disabled.
- Fix Results now shows a page-growth warning when your source appears to use body text below 18pt, since normalization to the ACB minimum can increase page count.
- List indentation controls are always visible under **List Indentation** and are disabled while **Flush all lists to the left margin** is checked.
- Legacy Word VML shapes with `alt=""` are treated as decorative and no longer trigger missing-alt findings.

### Quick Rule Exceptions

On the Fix and Audit forms, a new **Quick Rule Exceptions** section lets you suppress specific findings per operation without changing your default settings. This is useful when you want to ignore certain rules for one document without affecting your usual workflow.

**Available exceptions:**

- **Suppress ambiguous link text** (`ACB-LINK-TEXT`) -- ignore links that are not descriptive (e.g., "click here", "more info", "read more"). Use this when you know your links are contextually clear or when you are gathering feedback and do not want link-text errors to distract from other issues.
- **Suppress missing alt text** (`ACB-MISSING-ALT-TEXT`) -- ignore images without alt text. Use this when you are working on structural issues first and will add alt text in a later pass.
- **Suppress faux heading detection** (`ACB-FAUX-HEADING`) -- ignore bold, large text that looks like headings but are not styled as heading styles. Use this when you intentionally want to preserve visual "pseudo-headings" for design reasons and do not want them flagged.

**How to use:**

1. On the Fix or Audit form, expand the **Quick Rule Exceptions** section.
2. Check the rules you want to suppress for this operation only.
3. Submit the form normally.
4. The audit/fix results will not include findings for the suppressed rules, and a note will appear showing which rules were suppressed and why.

### Preserve centered headings

By default, the fixer normalizes all paragraph alignment to flush-left (ragged-right) per ACB requirements. However, you may want to preserve intentional heading center-alignment for design reasons.

The **Preserve centered headings** option on the Fix form skips alignment override for paragraphs identified as headings (those using Heading 1, Heading 2, or Heading 3 styles). Non-heading paragraphs are still normalized to flush-left.

**How to use:**

1. On the Fix form, find the **Heading Alignment Handling** option.
2. Check **Preserve centered headings** to leave heading alignment unchanged.
3. Uncheck it (default) to normalize all paragraphs including headings to flush-left.
4. Submit the form. Headings will retain their original alignment if the option is enabled.

### Per-level list indentation

By default, the fixer applies a uniform left indent to all list items regardless of their nesting depth. The new **Per-level list indentation** option lets you specify different indent values for Level 1, Level 2, and Level 3 list items.

This is useful when:
- Your document has multiple indentation levels and you want each level to use a specific indent value
- You want tighter spacing for nested lists (e.g., Level 1 at 0.25", Level 2 at 0.50", Level 3 at 0.75")
- You are working with bulleted or numbered lists that need consistent per-depth formatting

**How to use:**

1. On the Fix form, find the **List Indentation** section.
2. Check **Use per-level list indentation**.
3. Uncheck **Flush all lists to the left margin** if it is checked (the two options work together).
4. Enter indent values (in inches) for Level 1, Level 2, and Level 3.
5. Submit the form. The auditor and fixer apply per-level indents based on the paragraph's detected list style level.

Tip: Leave a level blank or set it to 0 if your document does not have that depth.

### Heading Detection (Word documents)

Many Word documents use bold, large text to simulate headings instead of using real heading styles (Heading 1, Heading 2, Heading 3). This causes accessibility problems because screen readers cannot navigate by headings, and the document has no logical structure.

The fixer can detect these "faux headings" and convert them to proper heading styles automatically.

**How it works:**

1. **Heuristic detection** -- The tool scores each paragraph on 10 signals: font size, bold formatting, short length, capitalization patterns, position in the document, and more. Paragraphs scoring above the confidence threshold (default 50 out of 100) are identified as likely headings.

2. **AI refinement (optional)** -- If Ollama is available, the tool can send borderline candidates to a local AI model (phi4-mini) for a second opinion. The AI considers surrounding context to improve accuracy. No data leaves your machine.

3. **Heading level assignment** -- Detected headings are assigned to Heading 1, 2, or 3 based on font size and document position. The first high-confidence heading is typically Heading 1, with subsequent headings assigned based on relative formatting.

### Heading detection accuracy modes

To balance speed and precision, the Fix workflow supports three accuracy modes:

- **Conservative** -- Heuristics-only with stricter filtering. Best when you want to minimize false positives such as names, times, or single-word labels (for example, "Agenda").
- **Balanced** (default) -- Heuristics plus optional AI refinement (when enabled). Best for most documents.
- **Thorough** -- More inclusive candidate capture with AI refinement when available. Best when you want to catch subtle headings and are willing to review more candidates.

Practical guidance:

- If names, times, or short labels are being flagged too often, switch to **Conservative**.
- If true headings are being missed, switch to **Thorough**.
- Keep **Balanced** for routine office documents.

**Using heading detection on the web:**

1. On the Fix page, check "Detect and convert faux headings to real heading styles."
2. Optionally check "Refine with AI" if Ollama is running on the server. The checkbox auto-checks when Ollama is detected.
3. Adjust the confidence threshold if needed (higher means fewer but more certain conversions).
4. Choose a heading detection accuracy level:
   - Conservative (fewer false positives)
   - Balanced (recommended default)
   - Thorough (captures more candidates)
5. Click Fix Document.
5. If candidates are found, you are taken to an **interactive heading review page**. This page shows a table listing every detected heading candidate with:
   - The paragraph text along with font size and bold/caps formatting info
   - The heuristic signals that fired and their point values
   - A confidence score and confidence level (High or Medium)
   - A heading level dropdown (H1 through H6) pre-set to the suggested level, plus a "Skip" option to exclude a candidate
   - If AI was used, the AI's reasoning is shown alongside the heuristic signals
6. Review each candidate. Change heading levels or set any false positives to "Skip."
7. Click "Apply Selections and Fix" to proceed. The confirmed headings are converted to real heading styles, then the normal fix pipeline runs.
8. The fix report details section shows every heading that was converted.

If no candidates are found above the confidence threshold, the fix proceeds directly without the review step.

**Using heading detection on the desktop GUI:**

1. Open the GLOW Accessibility Toolkit desktop application.
2. In the fix wizard (Step 3: Options), look for the Heading Detection section.
3. Check "Detect and convert faux headings to real heading styles."
4. Check "Refine with AI" if you have Ollama installed locally. The checkbox auto-checks when Ollama is detected.
5. Adjust the confidence threshold using the slider or spin control.
6. Complete the wizard to run the fix. Detected headings are converted before other fixes are applied.

**Using heading detection on the CLI:**

```shell
# Heuristic only
acb-lp fix document.docx --detect-headings

# With AI refinement
acb-lp fix document.docx --detect-headings --ai

# Standalone detection (report only, no fix)
acb-lp detect-headings document.docx

# With custom prompt file and threshold
acb-lp detect-headings document.docx --ai --ai-prompt my-prompt.txt --threshold 75
```

### How We Tested This Feature And What We Learned

We did not rely on a few hand-made examples. We built a synthetic Word-document stress harness to imitate the kinds of files people actually upload.

What the test set included:

- Meeting agendas
- Policy manuals
- Newsletters
- Legal outlines
- Appendices and flyers
- Email-style content
- Plain-text paste with no heading styles
- Mixed-font and font-size drift
- Centered and justified text that had to be repaired
- Multilingual section labels and numbering patterns

What those 1,000 documents were meant to represent in everyday use:

- A meeting agenda someone pasted out of email
- A newsletter copied from a website with mixed fonts and centered headings
- A policy manual built from older templates with indentation drift
- A legal-outline document with numbering that has to stay structurally correct
- A training handout where short prompts may or may not be real headings
- An appendix or report supplement with short labels, notes, and reference items

In other words, the documents were designed to behave like realistic user uploads, not toy examples. Each one placed the potential heading inside a fuller document context so the platform had to make a realistic decision and then repair the result to match ACB rules.

What we measured:

1. Whether the detector found real headings
2. Whether it avoided common false positives
3. Whether the fixer converted those headings cleanly
4. Whether the repaired document passed ACB audit rules afterward

What we learned:

1. Short lines are not automatically headings. Signature lines, reminders, and similar short phrases must be treated carefully.
2. Real documents often combine several problems at once. A heading may be visually strong while the surrounding document still has bad alignment, bad indentation, or font drift.
3. Heading detection and ACB enforcement are connected. A heading can be detected correctly and still need further cleanup so the final document does not violate rules such as no ALL CAPS or no skipped heading levels.

How the platform changed because of those lessons:

- We strengthened false-positive handling for signature-like and callout-style text.
- We expanded the random corpus to include plain-text/no-style negatives, font-only heading cues, and multilingual variants.
- We added a heading-normalization pass in the fixer so converted headings are cleaned up after detection, including heading hierarchy repair and ALL CAPS cleanup.

What the latest validation showed:

- Full heading stress suite passed
- Larger randomized comparisons showed zero false positives and zero false negatives in the measured runs
- Full fix-then-audit validation showed zero remaining ACB findings across the 1,000-document corpus after the latest fixes

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

Note: For legacy Word VML shapes, explicit `alt=""` is treated as decorative by the auditor.

### "I turned heading detection off. Why did my score still change?"

If **Detect and convert faux headings** is unchecked, fix results now suppress `ACB-FAUX-HEADING` in post-fix scoring. The results page also lists suppressed rules so you can verify exactly what was excluded.

### "Why did my document get longer after fix?"

Page growth is expected when source body text is below 18pt. For example, increasing 16pt body text to 18pt can significantly increase line count in long newsletters. Fix Results now warns when this condition is detected so the pagination change is expected rather than surprising.

### "Where are list indentation controls on the Fix page?"

The **List Indentation** fields are always visible. They are disabled while **Flush all lists to the left margin** is checked, and enabled when you uncheck it to use custom left/hanging indents.

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

Uploaded files are stored in an isolated temporary workspace long enough to complete audit/fix/download flows, including interactive heading review. Temporary files are automatically cleaned up and never retained as account data.

By default:

- Active sessions can continue for extended review workflows.
- Stale upload workspaces are automatically removed after 24 hours.

### What is the maximum file size?

500 MB. If your document is larger, try compressing images within the document first (Word: File, Compress Pictures).

### Can I audit multiple documents at once?

The web tool processes one document at a time. For batch processing, use the [desktop application](https://github.com/accesswatch/acb-large-print-toolkit) which supports folder-level audits.

### Why does the fix not change my headings?

The fix tool can now detect "faux headings" -- paragraphs that look like headings (bold, large font, short text) but use a Normal style instead of a real Heading style. Enable "Detect and convert faux headings" on the Fix page to use this feature. On the web, you review detected candidates in an interactive table before they are applied. On the CLI, use `--detect-headings`.

If false positives are common (for example names, times, "Agenda" labels), use the heading detection accuracy control and switch to **Conservative**. If valid headings are being missed, use **Thorough**.

For heading hierarchy corrections (changing an H3 to an H2, for example), the fix tool corrects heading formatting (font, size, bold) but does not change heading levels. Review your heading structure manually using the report's guidance.

### Why did decorative images get flagged as missing alt text?

Use Word's **Mark as decorative** option for non-informational visuals. The auditor now correctly treats legacy VML shapes with `alt=""` as decorative. Images without decorative intent or meaningful alt text are still reported.

### What is the difference between ACB and MSAC rules?

**ACB Large Print** rules come from the American Council of the Blind's Board of Publications. They cover visual formatting: font, size, spacing, emphasis, alignment, and margins.

**MS Accessibility Checker (MSAC)** rules are aligned with the Microsoft Office Accessibility Checker and WCAG 2.1. They cover structural accessibility: alt text, table headers, reading order, hyperlink text, document properties.

Both categories work together for comprehensive compliance. Run with both enabled for best results.

### What about DAISY Pipeline conversions?

DAISY Ace is bundled with the web application and always runs during ePub audits. DAISY Pipeline (for advanced format conversions like Word to EPUB, HTML to DAISY 2.02) requires Java and is an optional server component. Pipeline conversions appear automatically when installed by the server administrator. For the desktop application, install Node.js and Ace (`npm install -g @daisy/ace`) for full ePub audit support.

### Can I use this tool for documents in languages other than English?

Yes. The ACB formatting rules (font, size, spacing) apply regardless of language. The tool audits document structure and formatting, not content. Set the document language property (Rule: ACB-DOC-LANGUAGE) to the correct language code for proper screen reader pronunciation.

### Is there a desktop version?

Yes. The [GLOW Accessibility Toolkit](https://github.com/accesswatch/acb-large-print-toolkit) includes a desktop application with a graphical wizard interface, command-line tools, and batch processing support. It runs on Windows without requiring an internet connection.

### Where can I read the ACB Large Print Guidelines?

The full guidelines are available at [acb.org/large-print-guidelines](https://acb.org/large-print-guidelines) (revised May 6, 2025). A reference copy is included in this repository at `docs/ACB Large Print Guidelines, revised 5-6-25.docx`. The web application includes a [Guidelines page](https://glow.bits-acb.org/guidelines) with the complete rule reference and related audit rule mappings.

---

## 14. Getting Help

- **Full ACB Large Print Guidelines Reference** -- available on the web app Guidelines page or at [acb.org/large-print-guidelines](https://acb.org/large-print-guidelines)
- **Project overview and release highlights** -- [README.md](../README.md)
- **Web app operations and deployment notes** -- [web/README.md](../web/README.md)
- **Web app product requirements and implementation log** -- [docs/prd-flask-web-app.md](prd-flask-web-app.md)
- **Submit Feedback** -- use the Feedback page in the web app to report bugs, request features, or share your experience
- **About This Project** -- mission, organizations, standards, and open source dependencies on the web app About page
- **GitHub Issues** -- [report bugs or request features](https://github.com/accesswatch/acb-large-print-toolkit/issues) on the open source repository
- **DAISY Knowledge Base** -- [remediation guidance](https://kb.daisy.org/publishing/) for ePub accessibility issues
- **Microsoft Accessibility Checker Guide** -- [Microsoft's guide](https://support.microsoft.com/en-us/office/improve-accessibility-with-the-accessibility-checker-a16f6de0-2f39-4a2b-8bd8-5ad801426c7f) to the Office accessibility checker
