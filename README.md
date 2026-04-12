# ACB Document Accessibility Toolkit

A VS Code agent toolkit, desktop application, and web application for auditing and fixing Office documents for accessibility. Enforces the American Council of the Blind (ACB) Large Print Guidelines (revised May 6, 2025), Microsoft Accessibility Checker rules, and WCAG 2.2 AA digital accessibility standards.

## Supported Document Formats

| Format | Audit | Auto-Fix | Template | Export | Convert |
|--------|-------|----------|----------|--------|---------|
| Word (.docx) | 30+ ACB + MSAC rules | Yes -- fonts, spacing, emphasis, headings, margins | Yes (.dotx) | HTML (standalone or CMS) | To Markdown |
| Excel (.xlsx) | MSAC rules -- sheet names, table headers, merged cells, alt text, hidden content, color-only | Planned | -- | -- | To Markdown |
| PowerPoint (.pptx) | MSAC rules -- slide titles, reading order, alt text, font sizes, speaker notes, charts | Planned | -- | -- | To Markdown |
| Markdown (.md) | ACB emphasis, headings, images, lists | Planned | -- | -- | -- |
| PDF (.pdf) | Page-level structure and text extraction | Planned | -- | -- | To Markdown |
| ePub (.epub) | EPUB Accessibility 1.1 (title, language, nav, headings, alt text, tables, links, metadata) | Planned | -- | -- | To Markdown, To HTML |
| HTML/CSS | ACB + WCAG 2.2 AA (via VS Code agent) | Yes (via agent) | Yes | -- | To Markdown |

## Five ways to use it

| Interface | Who it is for | Install required? |
|-----------|---------------|-------------------|
| **Web app** | Anyone with a browser -- chapter officers, newsletter editors, conference attendees | No -- just open the URL |
| **Desktop GUI** | Users who prefer a native desktop wizard with file dialogs | Yes -- download a single executable |
| **CLI** | Developers and scripters who want batch processing | Yes -- `pip install` or download executable |
| **VS Code agent** | Developers using VS Code with Copilot Chat | Yes -- copy agent files to VS Code config |
| **Word Add-in** | Users who want ACB tools in the Word ribbon | Yes -- sideload the Office Add-in |

## What this toolkit does

- Audits Word (.docx), Excel (.xlsx), PowerPoint (.pptx), Markdown (.md), PDF (.pdf), ePub (.epub), HTML, and CSS files for accessibility
- Auto-fixes Word document compliance issues (fonts, spacing, emphasis, headings, margins)
- Provides detailed audit reports for Excel, PowerPoint, Markdown, PDF, and ePub with manual fix guidance
- Generates ACB-compliant Word templates (.dotx) with pre-configured styles
- Exports Word documents to accessible HTML (standalone or CMS-ready fragments)
- Converts documents to Markdown via Microsoft MarkItDown (.docx, .xlsx, .pptx, .pdf, .html, .csv, .json, .xml, .epub)
- Converts Markdown to ACB-compliant HTML with proper document structure
- Produces PowerShell scripts for configuring Word document styles
- Detects and uses external tools (markdownlint, Pandoc) when available

## Workspace structure

```
lp/
  .github/
    copilot-instructions.md              Repo-level Copilot context
    agents/
      large-print-formatter.agent.md     Main agent (9 operating modes)
      markdown-a11y-assistant.agent.md   WCAG markdown audit orchestrator
      markdown-scanner.agent.md          Internal: single-file scanner
      markdown-fixer.agent.md            Internal: auto-fix applicator
      markdown-csv-reporter.agent.md     Internal: CSV export
    prompts/
      acb-audit.prompt.md               /acb-audit slash command
      acb-convert.prompt.md             /acb-convert slash command
      acb-md-audit.prompt.md            /acb-md-audit slash command
      acb-md-convert.prompt.md          /acb-md-convert slash command
      acb-word-setup.prompt.md          /acb-word-setup slash command
    instructions/
      acb-large-print.instructions.md   Auto-attach on html/css files
    skills/
      markdown-accessibility/
        SKILL.md                         Pattern library, severity scoring, fix templates
  styles/
    acb-large-print.css                  Reference CSS (rem-based, print overrides)
  templates/
    acb-large-print-boilerplate.html     Semantic HTML skeleton
  docs/
    acb-large-print-toolkit.md           Detailed file inventory and history
    announcement.md                      Press release / announcement
    prd-flask-web-app.md                 Web app product requirements document
    deployment.md                        Step-by-step server deployment guide
  samples/
    *.md                                 Example Markdown source files
    *.html                               Converted HTML output files
    *-cms-embed.html                     CMS embed snippets (class-scoped)
  reference/
    ACB Large Print Guidelines, revised 5-6-25.docx   Source specification
  web/                                   Flask web application
    src/acb_large_print_web/             Application package
    tests/                               Test suite
    Dockerfile                           Production container image
    docker-compose.yml                   Compose file for deployment
  desktop/                               Desktop CLI + GUI (Python)
    src/acb_large_print/                 Core library (canonical source of truth)
  office-addin/                          Office.js Word Add-in (TypeScript)
    src/                                 TypeScript port of audit/fix/template
  vendor/                                Vendored third-party source
    daisy-ace/                           DAISY Ace source (MIT)
    daisy-a11y-meta-viewer/              DAISY a11y-meta-viewer source (CC BY-NC-SA 4.0)
```

## Quick start

### Use the web app (no install)

Open the web app in any browser. Upload a Word, Excel, PowerPoint, Markdown, or PDF file and choose an operation:

| Page | What it does |
|------|-------------|
| **Audit** | Check any supported document against accessibility rules (Full, Quick, or Custom mode) |
| **Fix** | Auto-fix Word documents; get audit-based fix guidance for other formats |
| **Template** | Generate an ACB-compliant Word template (.dotx) |
| **Export** | Convert a .docx to accessible HTML (standalone or CMS fragment) |
| **Convert** | Transform any supported document to Markdown via Microsoft MarkItDown |
| **Guidelines** | Browse the full ACB specification and WCAG 2.2 supplement |
| **About** | Project mission, organizations, standards, open source dependencies, and acknowledgments |

### Run the web app locally

```bash
cd web
pip install -e ".[dev]"
pip install -e "../desktop"
flask --app acb_large_print_web.app:create_app run --debug
```

### Deploy with Docker

```bash
cd web
docker compose up --build
```

See [docs/deployment.md](docs/deployment.md) for full production deployment (Ubuntu VPS, Caddy, TLS).

### Install to VS Code (User-level)

Copy the agent, prompts, styles, templates, and instructions to your VS Code User config:

```powershell
$prompts = "$env:APPDATA\Code\User\prompts"
$agents  = "$env:APPDATA\Code\User\agents"

# Main agent and bundled markdown agents
Copy-Item .github\agents\*.agent.md $agents\ -Force

# Slash commands
Copy-Item .github\prompts\*.prompt.md $prompts\ -Force

# Auto-attach instructions
Copy-Item .github\instructions\acb-large-print.instructions.md $prompts\ -Force

# Reference CSS and HTML boilerplate
Copy-Item styles\acb-large-print.css $prompts\ -Force
Copy-Item templates\acb-large-print-boilerplate.html $prompts\ -Force
```

### Use the slash commands

Open the VS Code Chat panel (Ctrl+Shift+I) and type the command. The prompt files route to the correct agent automatically.

| Command | What it does |
|---|---|
| `/acb-audit` | Audit the open file for ACB compliance |
| `/acb-convert` | Fix the open file to ACB compliance |
| `/acb-md-audit` | Audit a Markdown file for ACB compliance |
| `/acb-md-convert` | Convert Markdown to ACB-compliant HTML |
| `/acb-word-setup` | Generate a Word styles configuration script |

## Using the agents

### Large Print Formatter (main agent)

Address `@large-print-formatter` in VS Code Chat. It supports 9 operating modes that activate based on your request.

#### Mode 1: Review / Audit -- check an HTML or CSS file

Reads the file, checks every ACB rule, and reports a PASS/FAIL checklist with a compliance score.

Sample prompts:

- `@large-print-formatter audit this HTML file for ACB compliance`
- `@large-print-formatter review the open file against ACB Large Print rules`
- `@large-print-formatter check if this CSS meets the ACB typography requirements`

#### Mode 2: Generate -- create new ACB-compliant content

Creates new HTML/CSS with all ACB rules applied from the start. Asks whether you want external CSS, embedded, or both.

Sample prompts:

- `@large-print-formatter generate a new ACB-compliant HTML page for a meeting agenda`
- `@large-print-formatter create an ACB-compliant newsletter template`

#### Mode 3: Convert / Reformat -- fix an existing file

Reads an existing HTML file, detects every deviation, and fixes it. Handles fragments (no DOCTYPE) by wrapping them in a complete document shell. Fixes bold abuse, fake headings, `<br>` separators, and italic misuse.

Sample prompts:

- `@large-print-formatter convert this HTML file to ACB compliance`
- `@large-print-formatter reformat the open file for large print`
- `@large-print-formatter fix this Pandoc output to meet ACB guidelines`

#### Mode 4: CSS / HTML Template -- get starter files

Generates a reference CSS file and semantic HTML boilerplate with all ACB + WCAG rules, including print media overrides.

Sample prompts:

- `@large-print-formatter generate an ACB-compliant CSS stylesheet`
- `@large-print-formatter create an HTML boilerplate with ACB large print styles`

#### Mode 5: CSS Embed -- inline the stylesheet

Takes the reference CSS and embeds it as a `<style>` block in an HTML file, removing any external `<link>` to avoid duplication.

Sample prompts:

- `@large-print-formatter embed the CSS directly into this HTML file`
- `@large-print-formatter inline the ACB stylesheet into the open file`

#### Mode 5a: CMS Embed Snippet -- scoped output for WordPress / Drupal / CMS

Produces a class-scoped version of the content: all CSS selectors are prefixed with `.acb-lp` and the HTML content is wrapped in `<div class="acb-lp">`. This prevents the ACB styles from clashing with the CMS theme. The output is a single file (no DOCTYPE/head/body) ready to paste into any CMS HTML editor.

Sample prompts:

- `@large-print-formatter create a WordPress embed snippet for this HTML`
- `@large-print-formatter generate a CMS-ready version of the meeting agenda`
- `@large-print-formatter convert this markdown to a CMS embed snippet`

When using `/acb-convert` or Mode 3/Mode 9, you can also select "CMS embed snippet" from the CSS delivery question to get this output alongside the standalone HTML.

#### Mode 6: Word Setup Script -- configure Microsoft Word

Generates a PowerShell COM automation script that configures Word styles (Normal, Heading 1, Heading 2, List Bullet) and page layout to ACB spec.

Sample prompts:

- `@large-print-formatter generate a Word setup script for ACB large print`
- `@large-print-formatter create a PowerShell script to configure Word for ACB compliance`

#### Mode 7: Markdown Audit -- check a .md file

Reads a Markdown file and checks ACB-specific rules: italic prohibition, heading hierarchy, emphasis conventions, ALL CAPS, lists, images, bare URLs.

Sample prompts:

- `@large-print-formatter audit this markdown file for ACB compliance`
- `@large-print-formatter check the open .md file against ACB rules`

#### Mode 8: Markdown Fix -- auto-repair a .md file

Runs the audit first, then auto-fixes what it can (italic removal, heading hierarchy, ALL CAPS) and asks about ambiguous cases.

Sample prompts:

- `@large-print-formatter fix this markdown file for ACB compliance`
- `@large-print-formatter auto-fix the ACB issues in the open .md file`

#### Mode 9: Markdown to HTML Conversion -- full pipeline

Converts Markdown to a complete ACB-compliant HTML document. Asks about CSS delivery, print intent, and output location. Uses Pandoc when available.

Sample prompts:

- `@large-print-formatter convert this markdown to ACB-compliant HTML`
- `@large-print-formatter convert meeting-agenda.md to large print HTML with embedded CSS`
- `@large-print-formatter convert the open .md file to HTML for print`

### Markdown Accessibility Assistant (bundled)

Address `@markdown-a11y-assistant` in VS Code Chat for general WCAG markdown auditing. This is a separate, interactive wizard that covers 9 accessibility domains beyond ACB formatting.

Sample prompts:

- `@markdown-a11y-assistant audit this markdown file`
- `@markdown-a11y-assistant check all .md files in the docs folder`
- `@markdown-a11y-assistant review the README for accessibility`

The assistant will ask you configuration questions before scanning (scope, emoji preference, Mermaid preference) and then orchestrate its sub-agents (`markdown-scanner`, `markdown-fixer`, `markdown-csv-reporter`) automatically.

#### Domains covered by the markdown accessibility agents

| Domain | What it checks | WCAG criteria |
|---|---|---|
| Descriptive links | Ambiguous text ("click here", "read more"), bare URLs, repeated identical text | 2.4.4, 2.4.9 |
| Image alt text | Missing, empty, filename-as-alt, generic placeholders | 1.1.1 |
| Heading hierarchy | Skipped levels, multiple H1s, bold-as-heading | 1.3.1, 2.4.6 |
| Table descriptions | Missing descriptions, empty headers, layout tables | 1.3.1 |
| Emoji | Decorative emoji, emoji bullets, consecutive emoji, emoji in headings | 1.3.3, Cognitive |
| Mermaid/ASCII diagrams | Diagrams without text alternatives | 1.1.1, 1.3.1 |
| Em-dash normalization | Unicode em/en-dashes, doubled hyphens | Cognitive |
| Anchor link validation | Broken `#anchor` links, GitHub anchor generation rules | 2.4.4 |
| Plain language | Sentence length, passive voice, emoji bullets | Cognitive |

### Combined ACB + WCAG workflow

For the most thorough audit of a Markdown file, run both agents in sequence:

1. `@large-print-formatter audit this markdown file for ACB compliance` -- catches ACB-specific formatting rules (italic prohibition, font requirements, print layout)
2. `@markdown-a11y-assistant audit the same file` -- catches general WCAG issues (emoji, Mermaid diagrams, ambiguous links, anchor validation)

The large-print-formatter has built-in handoff links. After an ACB audit, it can offer to hand off to `@markdown-a11y-assistant` for the broader WCAG sweep.

## If you already have the accessibility agents installed

The markdown accessibility agents are bundled here for completeness so this toolkit works standalone. **If you already have the [accessibility agents](https://github.com/accessibility-agents) repo cloned as a workspace or installed to your VS Code User config, use those copies as the source of truth.** Do not copy the bundled versions over newer ones. The accessibility agents repo receives updates to all agents, skills, and shared instructions that this standalone copy will not automatically pick up.

To check if you already have them:

```powershell
# Check User-level agents
Get-ChildItem "$env:APPDATA\Code\User\agents\markdown-*" -ErrorAction SilentlyContinue

# Check for the accessibility agents workspace
Get-ChildItem S:\code\agents\.github\agents\markdown-* -ErrorAction SilentlyContinue
```

If either location returns results, those are your source of truth and will receive updates from the accessibility agents project. The bundled copies in this repo are a frozen snapshot for standalone use only.

## CMS embedding (WordPress, Drupal, etc.)

When pasting ACB Large Print content into a CMS page, the standalone HTML file's bare selectors (`body`, `h1`, `p`) will conflict with the theme's CSS. The agent produces a **CMS embed snippet** that avoids this:

- All CSS selectors are scoped under a `.acb-lp` class prefix
- Content is wrapped in `<div class="acb-lp">...</div>`
- No document shell (`<!DOCTYPE>`, `<html>`, `<head>`, `<body>`) -- the CMS already provides these
- Output file uses a `-cms-embed.html` suffix

To get a CMS embed snippet:

1. Select "CMS embed snippet" when the agent asks about CSS delivery, **or**
2. Ask directly: `@large-print-formatter create a CMS embed snippet for this file`

The agent always produces the CMS embed as a separate file alongside the standalone HTML.

## External tool support

The agent detects and uses these tools when available:

| Tool | Purpose | Install |
|---|---|---|
| markdownlint | Structural Markdown linting before ACB audit | `npm install -g markdownlint-cli` |
| Pandoc | Reliable GFM to HTML5 conversion | [pandoc.org/installing](https://pandoc.org/installing.html) |

When tools are not installed, the agent performs equivalent checks manually.

## ACB Large Print rules (summary)

- Font: Arial only, 18pt body, 22pt headings, 20pt subheadings
- Alignment: flush left, ragged right (never justified)
- Emphasis: underline only (no bold for emphasis, no italic ever)
- Headings: proper hierarchy, no ALL CAPS, no skipped levels
- Lists: large solid bullets, no extra spacing between items
- Links: descriptive text (no bare URLs, no "click here")
- Spacing: 1 blank line between paragraphs, no blank lines between list items
- Digital supplement: WCAG 2.2 AA contrast (4.5:1), 400% zoom reflow, 1.5x line-height

## License

This toolkit implements the ACB Large Print Guidelines, a public specification from the American Council of the Blind. The toolkit code and configuration files are provided for organizational use.

## Web Application

The `web/` directory contains a Flask web application that provides browser-based access to all core operations. No installation or account required. Runs in Docker for production deployment. See [web/README.md](web/README.md) for full documentation.

## Desktop Tool

The `desktop/` directory contains a standalone desktop application (CLI and GUI) that audits, fixes, and exports Microsoft Word documents for ACB compliance. It builds as one-file executables for 6 platforms via PyInstaller and GitHub Actions. See [desktop/README.md](desktop/README.md) for full documentation.

## Office Add-in

The `office-addin/` directory contains an Office.js Web Add-in that integrates ACB Large Print audit, fix, and template tools directly into the Microsoft Word ribbon. TypeScript port of the Python core. Deployed to GitHub Pages automatically on push.
