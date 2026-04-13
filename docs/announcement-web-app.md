# BITS Launches Free Online Document Accessibility Checker -- No Software Required

**FOR IMMEDIATE RELEASE -- April 12, 2026**

***

The Blind Information Technology Solutions (BITS) organization today announced the launch of the ACB Document Accessibility Web Application, a free, browser-based tool that checks and fixes Office documents for compliance with the American Council of the Blind (ACB) Large Print Guidelines and WCAG 2.2 AA accessibility standards. The web app is live now at [lp.csedesigns.com](https://lp.csedesigns.com) and requires no account, no download, and no installation.

"The number one piece of feedback we heard from ACB chapters was: 'I don't want to install anything,'" said **Jeff Bishop, President of BITS**. "People would see our desktop tool and say, 'That looks great, but I just need to check one document.' The web app is the answer. Open your browser, upload your file, and you are done. It works on a phone, a Chromebook, a library computer -- anywhere you have a browser."

## How It Works: Three Steps

The web app is designed to be usable by anyone, regardless of technical experience. The entire workflow is three steps:

1. **Upload** -- drag or browse to select your document
2. **Choose an operation** -- audit, fix, create a template, export to HTML, or convert formats
3. **Get results** -- view the report in your browser or download the corrected file

There is nothing to configure, nothing to log in to, and nothing to install. The tool handles the ACB specification so you do not have to memorize it.

## What You Can Do

The web app provides six operations, each accessible from the home page:

### Audit a Document

Upload a Word, Excel, PowerPoint, Markdown, PDF, or ePub file and get a complete accessibility compliance report displayed directly in your browser. Findings are organized by severity -- Critical, High, Medium, and Low -- so you know what to fix first. Three audit modes are available:

- **Full Audit** checks every rule. This is the default and the best choice for first-time users.
- **Quick Audit** checks only Critical and High severity rules for a fast overview of major issues.
- **Custom Audit** lets you pick exactly which rules to check using grouped checkboxes.

Each finding includes a description of the problem, why it matters, and a link to the relevant ACB guideline section or WCAG success criterion so you can understand the rationale behind each rule.

### Fix a Document

Upload a Word document and download a corrected version with one click. The tool automatically fixes fonts, sizes, spacing, alignment, and emphasis to meet ACB standards. A before-and-after compliance score shows exactly how much the document improved. Three fix modes let you control how much the tool changes:

- **Full Fix** applies every auto-fixable rule for maximum compliance.
- **Essentials Fix** applies only Critical and High severity fixes, leaving smaller issues untouched.
- **Custom Fix** lets you select which fix categories to apply.

For Excel, PowerPoint, Markdown, PDF, and ePub files, the fix page runs a full audit and provides detailed manual-fix guidance for each finding, since those formats do not yet support automated correction.

### Create a Template

Generate a pre-configured Word template (`.dotx`) with all ACB-compliant styles built in -- Arial 18pt body, 22pt headings, 20pt subheadings, flush left alignment, correct spacing and margins. You can set a document title, choose whether to include sample content that demonstrates each style, and optionally add binding margins for print documents. Starting from the template means every new document is compliant from the first word you type.

### Export to HTML

Convert a Word document into accessible HTML with ACB-compliant CSS. Two output options are available:

- **Standalone** -- a complete HTML page with all styles included. Ready to host on any web server.
- **CMS Fragment** -- an HTML snippet with embedded CSS, designed to paste directly into WordPress, Drupal, or any content management system without breaking your site theme.

### Convert a Document

Three conversion engines, each suited to a different purpose:

- **Extract to Markdown** (via Microsoft MarkItDown) -- pull the text content from any Word, Excel (.xlsx and legacy .xls), PowerPoint, PDF, HTML, CSV, JSON, XML, or ePub document into a clean, readable Markdown file. Supports the widest range of input formats. Useful for repurposing existing content or preparing a source file for further conversion.
- **Convert to Accessible HTML** (via Pandoc) -- transform a Markdown, Word, reStructuredText, OpenDocument, Rich Text, or ePub file into a fully accessible web page with ACB Large Print formatting, WCAG 2.2 AA compliance, and optional binding margins and print stylesheet. Pandoc produces the highest quality HTML output with proper heading hierarchy, semantic lists, tables, and footnotes. Options include ACB formatting toggle, binding margin for printed/bound documents, and a print-ready stylesheet.
- **Convert to EPUB or DAISY** (via DAISY Pipeline 2) -- create accessible EPUB 3 e-books from Word or HTML files, or convert existing EPUBs to DAISY 2.02 talking book format or DAISY 3/DTBook format. Best for content destined for e-readers, refreshable braille displays, or dedicated DAISY playback devices. Powered by the DAISY Consortium's open-source Pipeline engine.

The convert page includes guided help that explains when each engine is the better choice and how to chain them together (for example, extracting a PDF to Markdown first, editing the result, then converting the Markdown to an accessible web page or EPUB for the best results).

### Browse the Guidelines

A dedicated Guidelines page presents the complete ACB Large Print specification and the WCAG 2.2 AA digital supplement as browsable, searchable reference content. Each guideline section expands to show the specific audit rules, severity levels, and descriptions. This page is useful for learning the standard, training staff, or settling questions about what the rules actually require.

## Supported Document Formats

| Format | Audit | Auto-Fix | Template | Export | Convert |
| --- | --- | --- | --- | --- | --- |
| Word (.docx) | Full (30+ ACB and Microsoft Accessibility Checker rules) | Yes | Yes (.dotx) | Yes (HTML) | To Markdown, To HTML, To EPUB 3 |
| Excel (.xlsx, .xls) | Full (sheet names, table headers, merged cells, alt text, hidden content, color-only data) | Planned | -- | -- | To Markdown |
| PowerPoint (.pptx) | Full (slide titles, reading order, alt text, font sizes, speaker notes, charts) | Planned | -- | -- | To Markdown |
| Markdown (.md) | ACB emphasis, headings, images, lists | Planned | -- | -- | To HTML |
| PDF (.pdf) | Structure, metadata, fonts, tagged content, scanned page detection | Planned | -- | -- | To Markdown |
| HTML (.html) | -- | -- | -- | -- | To EPUB 3 |
| ePub (.epub) | Full (15 EPUB Accessibility 1.1 rules plus DAISY Ace integration) | Planned | -- | -- | To Markdown, To HTML, To DAISY 2.02, To DAISY 3 |

## Built for Everyone

### No Technical Knowledge Required

The web app is designed for the people who actually produce documents in ACB chapters and affiliates -- newsletter editors, meeting coordinators, chapter officers, and volunteers. Every page includes expandable help sections that explain what each operation does, what options are available, and what the results mean, all in plain language. A built-in user guide walks through every feature step by step.

### Works on Any Device

The web app works in any modern browser on any platform -- Windows, Mac, Linux, Chromebook, iPhone, iPad, and Android. There is no app to download and no plugin to install. If your device has a web browser, you can use the tool.

### Fully Accessible

This is an accessibility tool, and it practices what it preaches. The web app meets WCAG 2.2 AA from day one:

- Full keyboard navigation with visible focus indicators on every interactive element
- Screen reader compatible with proper landmark regions, labeled form controls, and descriptive headings
- Works without JavaScript enabled -- every feature uses standard HTML forms and server-side processing
- Skip navigation link on every page
- Error messages linked to the form fields that caused them
- Status messages use clear text prefixes (Error, Success, Warning, Note) rather than relying on color alone
- The tool itself is styled using the same ACB Large Print CSS it enforces in documents

"I use a screen reader every day," Bishop said. "If I can not use the tool I built, it has no business existing. Every page, every form, every report -- it is all structured text that works with assistive technology."

### No Account Required

There is no registration, no login, and no email address to provide. Upload a document, get results, and leave. The tool is free and open to anyone.

## Privacy and Security

Document privacy is a core design principle:

- **Uploaded files are deleted immediately** after processing. No documents are stored on the server, ever.
- **No user tracking.** There are no analytics scripts, no cookies beyond the session-level security token, and no third-party trackers.
- **No accounts.** Nothing is stored that could associate a document with a person.
- **CSRF protection** on every form prevents cross-site request forgery attacks.
- **Rate limiting** prevents abuse (120 requests per minute per IP address).
- **The server runs as a non-root user** inside a Docker container with no write access outside the temporary processing directory.

"ACB chapters handle sensitive organizational documents -- budgets, personnel discussions, legal correspondence," Bishop said. "We designed the system so that documents exist on the server only for the seconds it takes to process them. There is nothing to leak because there is nothing stored."

## Same Engine, Zero Compromises

The web application runs on the exact same Python core library that powers the desktop application and the command-line tool. When a bug is fixed or a new rule is added to the core, it appears in the web app automatically with no extra work. There is one set of rules, one set of thresholds, and one source of truth -- the `constants.py` file that defines every audit rule, severity level, and ACB reference.

This also means audit results are identical across every interface. A document that scores 85% in the desktop app will score 85% in the web app. The rules do not change based on how you access the tool.

## Online Help System

The web app includes a comprehensive built-in help system:

- **User guide** -- a 14-section walkthrough covering every feature, from getting started to advanced workflows, with tips organized by document format
- **Contextual help** -- every form page includes expandable help sections that explain the operation, the options, and what the results mean
- **Learn More links** -- every audit finding links to the relevant ACB guideline, WCAG success criterion, or Microsoft support article
- **Guidelines reference** -- the complete ACB Large Print specification and WCAG 2.2 digital supplement, browsable on the site
- **Frequently Asked Questions** -- common questions about supported formats, scoring, privacy, and recommended workflows

All help content is built with native HTML `<details>` and `<summary>` elements -- no JavaScript required, fully keyboard and screen reader accessible.

## Who This Is For

- **ACB chapter officers and volunteers** producing meeting agendas, newsletters, reports, and correspondence
- **Newsletter editors** who need to verify their documents meet the ACB standard before distribution
- **Conference presenters and trainers** who want to point attendees to a URL rather than walk them through a software installation
- **Web content managers** who need accessible HTML versions of Word documents for their chapter websites
- **IT staff at ACB affiliates** who cannot install arbitrary software on managed systems
- **Students, researchers, and publishers** who want to ensure their materials are readable by people with low vision
- **Anyone on a mobile device or Chromebook** who was previously excluded by platform limitations

## What the ACB Large Print Guidelines Require

For readers unfamiliar with the standard, the ACB Large Print Guidelines specify formatting rules that make documents readable for people with low vision:

- **Font**: Arial only, 18-point minimum for body text
- **Headings**: 22-point bold for main headings, 20-point bold for subheadings
- **Alignment**: Flush left, ragged right (never justified)
- **Emphasis**: Underline only -- no italic anywhere, no bold for emphasis in body text
- **Spacing**: 1 blank line between paragraphs, no extra space between list items
- **Margins**: 1 inch on all sides
- **Other**: No hyphenation, no ALL CAPS formatting, no decorative fonts

For digital content, the toolkit adds WCAG 2.2 AA requirements: 4.5:1 minimum contrast ratio, support for 400% zoom without horizontal scrolling, and 1.5x line-height for screen readability.

## Part of the Larger Toolkit

The web app joins the existing ACB Document Accessibility Toolkit, which also includes:

- **Desktop application** -- a standalone Windows program with both a graphical wizard and a command-line interface, for users who prefer offline processing or need to audit large batches of documents
- **VS Code Copilot Chat agent** -- an AI-powered agent that audits, fixes, and generates compliant documents directly inside the code editor, with nine operating modes covering HTML, CSS, Markdown, and Word
- **Office Add-in** -- a Microsoft Word ribbon integration (in development) for checking documents directly inside Word

All four interfaces share the same core engine. A rule added to the core library is immediately enforced everywhere.

## Open Source

The ACB Document Accessibility Toolkit is open source and available on GitHub at [github.com/accesswatch/acb-large-print-toolkit](https://github.com/accesswatch/acb-large-print-toolkit). Contributions, bug reports, and feature requests are welcome.

The project is part of [Accessibility Agents](http://www.community-access.org), an open-source ecosystem that delivers accessibility guidance and remediation across web, mobile, desktop, and document formats.

## Try It Now

Visit [lp.csedesigns.com](https://lp.csedesigns.com), upload a document, and see the results in seconds. No sign-up, no download. Just accessible documents.

***

**About BITS:** The Blind Information Technology Solutions (BITS) is a special interest affiliate of the American Council of the Blind (ACB), dedicated to promoting the use of technology by and for people who are blind or have low vision.

**Contact:** Jeff Bishop, President, BITS -- [bits-acb.org](https://bits-acb.org)
