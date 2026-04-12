# ACB Large Print Toolkit

## Files (all under VS Code User config)

### Agents
- `agents/large-print-formatter.agent.md` -- Main agent: 9 operating modes (audit, generate, convert, template, CSS embed, Word setup, MD audit, MD fix, MD-to-HTML). Tools: read, edit, search, execute, web, vscode_askQuestions. Handoffs to markdown-a11y-assistant and markdown-csv-reporter.
- `agents/markdown-a11y-assistant.agent.md` -- Bundled WCAG markdown audit orchestrator (from accessibility agents ecosystem). Interactive wizard covering 9 domains.
- `agents/markdown-scanner.agent.md` -- Internal sub-agent: scans a single file for accessibility issues across all 9 domains.
- `agents/markdown-fixer.agent.md` -- Internal sub-agent: applies auto-fixes and presents human-judgment fixes for approval.
- `agents/markdown-csv-reporter.agent.md` -- Internal sub-agent: exports findings to CSV with severity scoring, WCAG criteria, and help links.

### Prompts
- `prompts/acb-audit.prompt.md` -- `/acb-audit`: one-click compliance check on open file. Routes to large-print-formatter agent.
- `prompts/acb-convert.prompt.md` -- `/acb-convert`: auto-fix open file to ACB compliance. Asks CSS delivery preference via askQuestions.
- `prompts/acb-word-setup.prompt.md` -- `/acb-word-setup`: generates PowerShell COM script to configure Word styles.
- `prompts/acb-md-audit.prompt.md` -- `/acb-md-audit`: audit a Markdown file for ACB Large Print issues (emphasis, headings, images, lists).
- `prompts/acb-md-convert.prompt.md` -- `/acb-md-convert`: convert Markdown to ACB-compliant HTML with document shell and CSS.

### Templates and Reference Files
- `prompts/acb-large-print.css` -- Drop-in CSS (rem-based) with all ACB + WCAG 2.2 rules. Includes @media print overrides. Source: `styles/acb-large-print.css` in workspace.
- `prompts/acb-large-print-boilerplate.html` -- Semantic HTML skeleton: headings, lists, TOC leader dots, table, figure+caption, endnotes. Source: `templates/acb-large-print-boilerplate.html` in workspace.

### Instructions
- `prompts/acb-large-print.instructions.md` -- Auto-activates on *.html, *.css files. Quick-reference ACB/WCAG checklist.

## Flask Web Application (April 2026)

The `web/` directory contains a browser-based interface for all core toolkit operations. No installation, no accounts, no JavaScript required.

### Supported Document Formats

| Format | Audit | Auto-Fix | Template | Export |
|--------|-------|----------|----------|--------|
| Word (.docx) | Full (30+ ACB + MSAC rules) | Yes | Yes (.dotx) | Yes (HTML/ZIP) |
| Excel (.xlsx) | Full (MSAC: sheet names, table headers, merged cells, alt text, hidden content, color-only) | Planned | -- | -- |
| PowerPoint (.pptx) | Full (MSAC: slide titles, reading order, alt text, font sizes, speaker notes, charts) | Planned | -- | -- |

### Pages

| Route | Purpose |
|-------|---------|
| `GET /` | Landing page with format pills, operation cards, and descriptions |
| `GET/POST /audit` | Upload a .docx/.xlsx/.pptx, choose Full/Quick/Custom mode, view compliance report |
| `GET/POST /fix` | Upload a file, Word gets auto-fixed, Excel/PowerPoint get audit guidance |
| `GET/POST /template` | Configure and download an ACB-compliant Word template (.dotx) |
| `GET/POST /export` | Upload a .docx, export as standalone HTML (ZIP) or CMS fragment |
| `GET /guidelines` | Full ACB Large Print specification and WCAG 2.2 supplement |
| `GET/POST /feedback` | Submit feedback (rating, task, message) |
| `GET /feedback/review` | View feedback (password-protected via FEEDBACK_PASSWORD env var) |
| `GET /health` | Health check endpoint (returns 200) |

### Architecture

- Flask 3.x application factory pattern with blueprints
- Imports `acb_large_print` core library directly -- zero modifications to existing code
- CSRF protection (Flask-WTF), rate limiting (Flask-Limiter), structured logging
- SQLite for feedback storage (WAL mode, concurrent-safe)
- Docker container with non-root user and health check
- Caddy reverse proxy (production) for auto-TLS
- All help text and rule descriptions auto-generated from `constants.py`
- Native HTML `<details>/<summary>` for contextual help (no JavaScript)

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Random per-start | Flask session/CSRF secret. Set in production. |
| `FEEDBACK_PASSWORD` | (unset) | Enables `/feedback/review?key=<password>` |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Workspace for Testing
- `s:\code\lp` -- shared workspace with all toolkit files + test HTML
- Test file: `04 - April 8 2026 BITS Board Meeting Agenda.html` (BITS board meeting, ~730 lines, HTML fragment from Pandoc/Markdown conversion)

## First Audit Results (April 8, 2026)
- Score: 8/31 applicable rules = 26% (Grade F)
- File is an HTML fragment (no DOCTYPE, html, head, body)
- No CSS linked or embedded -- all typography/spacing rules fail
- Heavy `<strong>` misuse (entire paragraphs bolded) -- violates ACB emphasis rules
- `<em>` used for dates (italic violates ACB)
- Fake headings: `<p><strong>Impact</strong></p>` instead of `<h4>`
- `<br>` used as paragraph separators
- Broken Markdown artifacts: stray `**` in Fundraising section
- Heading hierarchy is well-structured (h1>h2>h3>h4>h5) -- one bright spot
- Semantic lists properly used (ul/ol/li)

## Agent Improvements Made After Testing
- Added "Document Shell Requirements" section -- detects/fixes HTML fragments
- Added "Common Content Anti-Patterns" section -- bold abuse, fake headings, br separators, Markdown artifacts, em italic misuse
- Convert Mode expanded to 8 steps: detect fragment, wrap in shell, fix anti-patterns, apply CSS, ask delivery preference
- New constraints: no strong on full paragraphs, no em/italic ever, no br as separator, no Markdown artifacts
- Added full Markdown support (April 2026): Markdown-Specific Rules section, 3 new modes (MD audit, MD fix, MD-to-HTML conversion)
- Markdown emphasis convention: `<u>text</u>` inline HTML since Markdown has no native underline
- Markdown constraints: no italic, no bold-as-emphasis, no skipped heading levels, no Setext headings, no blank lines between list items, no bare URLs

## Key Design Decisions
- HTML line-height: 1.5 (WCAG 1.4.12) overrides ACB's 1.15; @media print reverts to 1.15
- CSS uses rem units for zoom/reflow support
- Agent uses vscode_askQuestions for: CSS delivery (embed vs external vs CMS snippet), print intent, ACB/WCAG conflict resolution
- Emphasis on web: underline styled distinct from hyperlinks (thicker, offset)
- Agent file synced bidirectionally: User config is source of truth, workspace copy for sharing/testing

## Desktop Tool -- Multi-Format Support (April 2026)

All three interfaces (CLI, GUI, Web) now support .docx, .xlsx, and .pptx files:

| Format | Audit | Auto-Fix | Template | Export |
|--------|-------|----------|----------|--------|
| Word (.docx) | Full (30+ ACB + MSAC rules) | Yes | Yes (.dotx) | Yes (HTML) |
| Excel (.xlsx) | Full (MSAC rules) | Planned | -- | -- |
| PowerPoint (.pptx) | Full (MSAC rules) | Planned | -- | -- |

### CLI Changes
- `audit` command accepts .docx, .xlsx, .pptx
- `fix` command accepts all three formats (Word gets auto-fixed; Excel/PowerPoint get audit report with manual fix guidance)
- `batch` command scans directories for all three file types
- Format dispatch via `_audit_by_extension()` and `_fix_by_extension()` helpers

### GUI Changes
- File picker wildcard includes all three formats
- Welcome text updated for multi-format
- Validation accepts .docx, .xlsx, .pptx
- Audit and fix dispatched by extension
- HTML export options (CMS, standalone) only shown for Word files
- Save dialog uses the source file's extension

## CMS Embed Snippet
- Purpose: class-scoped output for pasting into WordPress, Drupal, or any CMS HTML editor
- CSS scoping: every selector prefixed with `.acb-lp` (e.g., `.acb-lp h1`, `.acb-lp p`) so ACB styles do not clash with the CMS theme
- Content wrapper: `<div class="acb-lp">...</div>` (no document shell -- CMS provides DOCTYPE, html, head, body)
- File naming: `-cms-embed.html` suffix (e.g., `meeting-agenda-cms-embed.html`)
- Agent mode: 5a (CMS Embed Snippet Mode), or select "CMS embed snippet" from the CSS delivery question in Convert / Generate / MD-to-HTML modes
- Always produced as a separate file alongside the standalone HTML -- never replaces the standalone version
- Sample file: `samples/wordpress-embed-snippet.html` (BITS board meeting agenda, scoped to `.acb-lp`)
