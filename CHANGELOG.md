# Changelog

All notable changes to the ACB Document Accessibility Toolkit are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Releases are tagged in the [GitHub repository](https://github.com/accesswatch/acb-large-print-toolkit). Dates are in Pacific Time (UTC-7).

---

## [Unreleased]

### Added

- **Synthetic heading stress corpus** (`desktop/src/acb_large_print/stress_profiles.py`, `desktop/tests/test_heading_stress_corpus.py`): reproducible randomized corpus with 1,000 heading scenarios across 1,000 generated Word documents. Covers paste-heavy and layout-heavy families including notepad, email, web paste, agendas, policies, newsletters, legal outlines, appendices, and flyers. Includes sample-run tests plus `pytest -m stress` full-corpus generation and fixer verification.
- **Web help: stress-testing transparency** (`web/src/acb_large_print_web/routes/guide.py`, `web/src/acb_large_print_web/routes/about.py`, `web/src/acb_large_print_web/templates/guide.html`, `web/src/acb_large_print_web/templates/about.html`): guide and About pages now explain the stress harness, why it exists, which scenario families are covered, and how failures are folded back into audit rules and fixer behavior.

- **AI heading detection engine** (`heading_detector.py`, `ai_provider.py`, `ai_providers/ollama_provider.py`): two-tier faux heading detection system. Tier 1 scores paragraphs on 10 heuristic signals (font size, bold, short length, caps, position, whitespace, isolation, run count, style name, proximity to known headings) on a 0-100 scale. Tier 2 optionally refines borderline candidates via Ollama (phi4-mini model) running locally. No data leaves the machine.
- **Heading detection CLI** (`cli.py`): new `detect-headings` subcommand for standalone heading analysis with `--ai`, `--ai-model`, `--ai-endpoint`, `--ai-prompt` (custom prompt file), `--threshold`, `--apply`, `--json` options. Also `--detect-headings` and `--ai` flags on `fix` and `batch` subcommands.
- **Heading conversion fixer pre-pass** (`fixer.py`): when `detect_headings=True`, runs heading detection before other fixes and converts faux headings to real Heading 1/2/3 styles. Clears conflicting direct formatting after conversion.
- **ACB-FAUX-HEADING audit rule** (`constants.py`, `auditor.py`): new HIGH severity auto-fixable rule detects paragraphs that look like headings but use non-heading styles. Wired into `audit_document()` via `_check_faux_headings()`.
- **FixRecord dataclass** (`constants.py`): structured fix tracking with `rule_id`, `category`, `description`, and `location` fields. Seven category constants: Headings, Font, Alignment, Emphasis, Spacing, Page Setup, Document Properties.
- **Detailed fix reports** (`fixer.py`, `reporter.py`): every fix function now records individual `FixRecord` entries. `fix_document()` returns a 5-tuple including the records list. `generate_fix_summary()` displays fixes grouped by category.
- **Fix result accordion UI** (`fix_result.html`): new "Fix Details" section with collapsible `<details>` elements grouped by category, showing rule ID, description, and location for each fix applied.
- **Heading detection web UI** (`fix_form.html`, `routes/fix.py`): new "Heading Detection" fieldset with enable checkbox, AI toggle (requires Ollama), and confidence threshold slider. Fix route parses form fields and passes to fixer.
- **Ollama Docker service** (`docker-compose.prod.yml`): new `ollama` service using `ollama/ollama:latest` image with health check, persistent volume (`ollama_data`), and `OLLAMA_HOST` env var on the web service.
- **Ollama dependency** (`requirements.txt`): added `ollama>=0.4.0` to both desktop and web requirements.
- **TypeScript constants synced** (`office-addin/src/constants.ts`, `word-addin/src/constants.ts`): `HEADING_CONFIDENCE_THRESHOLD`, `HEADING_HIGH_CONFIDENCE`, and `ACB-FAUX-HEADING` rule added.
- **User guide: heading detection** (`user-guide.md`): new section documenting heuristic detection, AI refinement, web UI usage, and CLI commands with examples.
- **Interactive heading review** (`fix_review_headings.html`, `routes/fix.py`): when heading detection finds candidates in a .docx upload, users see a review table with paragraph text, heuristic signals, confidence scores, AI reasoning (if used), and a heading level dropdown (H1-H6 or "Skip") for each candidate before fixes are applied. New `fix_confirm` POST route at `/fix/confirm` processes confirmed selections.
- **Fix route refactor** (`routes/fix.py`): extracted `_parse_form_options()` and `_run_fix_and_render()` helpers shared by submit and confirm routes, reducing duplication and supporting the two-step heading review flow.
- **AI auto-detection** (`ai_provider.py`, `fix_form.html`, `gui.py`): new `is_ai_available()` function probes Ollama at localhost:11434 with a 2-second HEAD request. Web fix form and desktop GUI auto-check the AI checkbox when Ollama is reachable.
- **Desktop GUI: heading detection controls** (`gui.py`): Step 3 Options panel adds paragraph indent checkbox, heading detection checkbox, and AI toggle. AI checkbox defaults to checked when `is_ai_available()` returns True and restores availability on re-enable.
- **Confirmed headings support** (`fixer.py`): `fix_document()` accepts a `confirmed_headings` parameter (list of paragraph index, level, text tuples). When provided, the fixer uses these directly instead of re-running detection, enabling the web interactive review workflow.

- **Configurable list indentation** (`constants.py`, `auditor.py`, `fixer.py`, `template.py`): new `ACB-LIST-INDENT` audit rule (Medium severity, auto-fixable) checks list item indentation against a configurable target. Default is flush-left (0.0 inch) per ACB alignment guidelines. Two presets: `LIST_INDENT_FLUSH` (0.0/0.0) and `LIST_INDENT_STANDARD` (0.5/0.25).
- **Desktop GUI: list indent controls** (`gui.py`): Step 3 Options panel adds a "Flush all lists to the left margin" checkbox (checked by default) with left indent and hanging indent spin controls. Unchecking reverts to standard Word indentation (0.50/0.25 inch). Custom values supported.
- **CLI: list indent options** (`cli.py`): `fix`, `template`, and `batch` subcommands accept `--flush-lists` / `--no-flush-lists` flags and `--list-indent` / `--list-hanging` for custom values.
- **Web app: list indent form controls** (`fix_form.html`, `fix.py`): "List Indentation" fieldset with flush-left checkbox and custom indent fields. Values are validated and clamped to safe range (0.0 -- 2.0 inches).
- **TypeScript constants synced** (`office-addin/src/constants.ts`, `word-addin/src/constants.ts`): `LIST_INDENT_IN` and `LIST_HANGING_IN` updated to 0.0, `LIST_INDENT_FLUSH` and `LIST_INDENT_STANDARD` presets added, `ACB-LIST-INDENT` rule added to `AUDIT_RULES`.
- **SPA tab controller** (`tabs.js`): new client-side script for true ARIA tab pattern with keyboard navigation (Arrow Left/Right, Home, End), lazy content loading via fetch, response caching, inline script re-execution, browser history (pushState/popstate), and document title updates on tab switch. Falls back to normal link navigation without JavaScript.
- **AI heading detection plan** (`docs/plan-ai-heading-detection.md`): comprehensive 6-phase plan for detecting faux headings in unstyled documents using heuristic scoring (Tier 1) and optional AI refinement (Tier 2) via GitHub Models, Ollama, or Hugging Face.

- **Non-list paragraph indentation audit and fix (Phase 5)**: new rules detect and auto-fix stray paragraph indentation that violates ACB flush-left requirements.
  - 4 new audit rules: `ACB-PARA-INDENT` (High, auto-fixable), `ACB-FIRST-LINE-INDENT` (High, auto-fixable), `ACB-BLOCKQUOTE-INDENT` (Medium, auto-fixable), `EPUB-TEXT-INDENT` (Medium, not auto-fixable).
  - 4 new constants: `PARA_INDENT_IN`, `FIRST_LINE_INDENT_IN`, `PARA_INDENT_FLUSH`, `PARA_INDENT_BLOCKQUOTE`.
  - **Auditor** (`auditor.py`): checks non-list, non-heading paragraphs for left indent and first-line indent violations, with blockquote detection for indents > 0.25 inch on body-length text.
  - **Fixer** (`fixer.py`): resets paragraph left indent and first-line indent to configured values.
  - **ePub auditor** (`epub_auditor.py`): detects CSS `text-indent` and `margin-left` on body text elements in ePub HTML content.
  - **CLI** (`cli.py`): `--flush-paragraphs` / `--no-flush-paragraphs`, `--para-indent`, `--first-line-indent` flags on `fix` and `batch` subcommands.
  - **Web app** (`fix_form.html`, `routes/fix.py`): "Paragraph Indentation" fieldset with flush checkbox and custom indent fields, matching the list indentation pattern.
  - **TypeScript** (`office-addin/src/constants.ts`, `word-addin/src/constants.ts`): synced all 4 constants and 4 audit rules.

- **Word, EPUB, and PDF conversion** (`pandoc_converter.py`, `convert.py`, `convert_form.html`): three new output formats on the Convert page. Word (.docx) via Pandoc, EPUB 3 via Pandoc with embedded ACB CSS, and PDF via Pandoc + WeasyPrint with ACB BOP print formatting (Arial 18pt, 1.15 line spacing, 1-inch margins, @page rules). PDF supports binding margin option (extra 0.5-inch left). Convert page now offers six directions: plain text, HTML, Word, EPUB 3, PDF, and DAISY Pipeline.
- **WeasyPrint integration** (`requirements.txt`, `Dockerfile`, `pandoc_converter.py`): added `weasyprint>=62.0` to web dependencies. Dockerfile installs Pango, Cairo, GDK-Pixbuf, libffi, shared-mime-info, and Liberation Sans font (metrically identical to Arial) for PDF rendering. The `weasyprint_available()` function allows graceful fallback when not installed.
- **ACB print CSS for PDF** (`pandoc_converter.py`): dedicated `_ACB_PDF_CSS` stylesheet with ACB BOP print-optimized rules -- Arial/Liberation Sans font stack, 18pt body, 22pt headings, 20pt subheadings, 1.15 line spacing, 1-inch margins, underline-only emphasis, flush-left alignment, @page size letter. Binding-margin variant adds 0.5-inch extra on the left.
- **Convert form: new radio options** (`convert_form.html`): Word document, EPUB 3 e-book (via Pandoc), and Accessible PDF radio buttons with descriptions of each engine, accepted formats, and what you get back. Options are disabled with explanatory text when Pandoc or WeasyPrint is not installed.
- **Convert form: expanded help** (`convert_form.html`): "How do I decide?" section updated with all six output options. Accepted file types accordion now lists formats for each direction (HTML, Word, EPUB, PDF, Pipeline, Markdown). Tips and chaining workflow sections updated to reference all new formats.
- **About page: WeasyPrint attribution** (`about.html`): added WeasyPrint (BSD, CourtBouillon) to core dependencies table and updated Pandoc description to mention Word, EPUB, and PDF output alongside HTML. Acknowledgments section updated.
- **User guide: convert section expanded** (`user-guide.md`): three new subsections for Word, EPUB 3, and PDF conversion with accepted formats, options, and guidance. "How do I decide" and chaining sections updated. Workflow D updated to include Pandoc EPUB option alongside Pipeline.
- **Announcement updated** (`announcement-web-app.md`): convert section rewritten with all six directions. Format support table expanded with Word, EPUB 3 (via Pandoc), and PDF columns. WeasyPrint credited in the Same Engine section. Pipeline section clarified as one of six options.
- **PRD updated** (`prd-flask-web-app.md`): implementation status table updated with Word/EPUB/PDF conversion rows. Convert route description expanded to six directions. Tech stack table updated with WeasyPrint. Dependencies section expanded.
- **Web README updated** (`web/README.md`): features list and format support table updated with Word, EPUB, and PDF convert columns.
- **Root README updated** (`README.md`): format support table convert column updated. "What this toolkit does" section expanded.

### Changed

- **Stress validation and lessons-learned documentation expanded** (`README.md`, `desktop/README.md`, `web/README.md`, `docs/user-guide.md`, `web/src/acb_large_print_web/templates/guide.html`, `web/src/acb_large_print_web/templates/about.html`): documentation now explains, in plain language, what heading and document-repair scenarios were stress-tested, what failures were discovered during learning, how the platform was adapted, what the final measured outcomes were, and what confidence limits still remain for cross-platform runtime proof.

- **Paragraph indentation enforcement tightened** (`desktop/src/acb_large_print/auditor.py`, `desktop/src/acb_large_print/fixer.py`, `desktop/src/acb_large_print/constants.py`, `office-addin/src/constants.ts`, `word-addin/src/constants.ts`): non-list paragraph left indent and first-line indent checks now enforce the configured target exactly, catching negative hanging indents and outdents in addition to positive indents. Rule descriptions now reflect the configurable target with flush-left as the default.

- **True SPA tab control** (`base.html`, `tabs.js`, `forms.css`): navigation tabs now switch content without a full page reload. Clicking a tab fetches the target page, extracts the main content, and swaps it in-place. Cached after first load for instant subsequent switches. Browser back/forward buttons work via pushState history.
- **Removed redundant ARIA landmark roles** (`base.html`): removed `role="banner"` from `<header>` and `role="contentinfo"` from `<footer>` since these are the implicit roles of those HTML5 elements.
- **Tab ARIA improvements** (`base.html`): each tab link now has a unique `id` attribute and `aria-controls="main"`; tablist has `aria-label="Document tools"`; removed redundant `aria-current="page"` from tab links (superseded by `aria-selected`). Roving tabindex managed by `tabs.js` for proper keyboard interaction.
- **Loading state** (`forms.css`): `main[aria-busy="true"]` style dims content and disables pointer events during SPA tab fetches.
- **Navigation structure** (`base.html`): main nav reduced from 9 items to 6 tabs (Audit, Fix, Template, Export, Convert, Guidelines). The brand link now also gets `aria-current="page"` when on the home page. Secondary links (User Guide, About, Changelog, Feedback) relocated to footer.
- **Tab bar contrast and touch targets** (`forms.css`): active tab uses `#0055cc` with 3px bottom border; inactive tabs use `#444` text (meets WCAG AA 4.5:1 on white); all tabs have 44px minimum height/width for touch targets.
- **Convert test** (`test_app.py`): `test_convert_to_html_md_file` now sends `acb_format=on` to match the new form behavior where ACB formatting is a checkbox.
- **User guide updated** (`user-guide.md`): heading detection section expanded with interactive review workflow steps for web, desktop GUI instructions, AI auto-detection notes, and updated FAQ entry for faux heading detection.
- **PRD updated** (`prd-flask-web-app.md`): implementation status table expanded with interactive heading review, AI auto-detection, and desktop GUI heading detection rows.
- **Documentation consolidated**: removed `docs/acb-large-print-toolkit.md` (superseded by `copilot-instructions.md` repo layout and PRD) and `docs/plan-ai-heading-detection.md` (fully implemented). README docs listing updated.

### Fixed

- **Changelog path resolution**: `changelog.py` now walks parent directories to find `CHANGELOG.md` (works in both dev checkout and Docker site-packages install), with `/app/CHANGELOG.md` as Docker fallback.

---

## [0.3.0] -- 2026-04-12

### ePub Accessibility Auditing

- Added `epub_auditor.py` with 15 EPUB Accessibility 1.1 rules:
  - **EPUB-TITLE** -- ePub must have a title in OPF metadata
  - **EPUB-LANGUAGE** -- ePub must declare a language
  - **EPUB-NAV-DOCUMENT** -- ePub must include a navigation document (nav or NCX)
  - **EPUB-HEADING-HIERARCHY** -- heading levels must not skip
  - **EPUB-MISSING-ALT-TEXT** -- images must have alt text
  - **EPUB-TABLE-HEADERS** -- tables must use th elements
  - **EPUB-ACCESSIBILITY-METADATA** -- ePub should include schema.org metadata
  - **EPUB-LINK-TEXT** -- links must have descriptive text
  - **EPUB-ACCESSIBILITY-HAZARD** -- ePub should declare hazard metadata
  - **EPUB-ACCESS-MODE-SUFFICIENT** -- ePub should declare sufficient access modes
  - **EPUB-PAGE-LIST** -- ePub should include a page list for navigation
  - **EPUB-PAGE-SOURCE** -- ePub with page list should declare a page source
  - **EPUB-MATHML-ALT** -- MathML elements should have alt text or annotation
  - **ACE-EPUB-CHECK** -- DAISY Ace ePub-level check results
  - **ACE-AXE-CHECK** -- DAISY Ace axe-core HTML check results

### DAISY Ace Integration

- Added `ace_runner.py` integrating the DAISY Ace EPUB accessibility checker
- Ace provides 100+ axe-core rules applied to EPUB content documents
- Results mapped to ACE-EPUB-CHECK and ACE-AXE-CHECK rule IDs
- Graceful degradation when Ace is not installed (skips Ace checks)
- Vendored DAISY Ace source in `vendor/daisy-ace/` for offline builds and auditing

### W3C Accessibility Metadata Display

- Added `epub_meta_display.py` implementing the [W3C Accessibility Metadata Display Guide 2.0](https://w3c.github.io/publ-a11y/a11y-meta-display-guide/2.0/draft/techniques/epub-metadata/)
- Extracts and renders human-readable accessibility statements from EPUB metadata
- Sections: Access, Sufficient Access Modes, Features, Hazards, Conformance, Summary
- Vendored DAISY a11y-meta-viewer reference implementation in `vendor/daisy-a11y-meta-viewer/`
- Audit report renders metadata sections with details/summary accordions

### Online Help System

- Added `/guide` route with 14-section user guide:
  - Quick-start walkthrough (audit, fix, re-audit in 3 steps)
  - Per-feature step-by-step instructions (audit, fix, template, export, convert)
  - Understanding results (severity levels, scores, grades)
  - Common issues and how to fix them
  - Tips by document format
  - Recommended workflows
  - DAISY accessibility tools overview
  - Keyboard and screen reader tips
  - Frequently asked questions
  - Getting help
- Added contextual help on every form via `<details>` accordions and `aria-describedby`
- Added `_help_links.html` partial for per-rule Learn More links (ACB, WebAIM, WCAG Understanding, Microsoft, DAISY)
- Added `_help_rules.html` partial for severity-grouped rule checkboxes with attached help links
- Added `_workflow_tip.html` partial for contextual next-step banners between pages
- `rules.py` maps every rule ID to curated help URLs plus auto-generated WCAG Understanding doc links
- `help_urls_map` injected globally via Flask context processor

### Directory Restructure

- Renamed `word-addon/` to `desktop/` (Python desktop app and CLI)
- Renamed `word-addin/` to `office-addin/` (Office.js Word add-in)
- Updated all cross-references: CI workflow, Dockerfile, `.dockerignore`, deploy scripts, README, `copilot-instructions.md`

### Upload Limit

- Raised `MAX_CONTENT_LENGTH` from 100 MB to 500 MB
- Updated all form templates, user guide, FAQ, README, deployment docs, and error messages

### Docker

- Dockerfile now installs Node.js and DAISY Ace globally (`npm install -g @daisy/ace`)
- Added `pymupdf>=1.24.0` to web requirements

### Tests

- Added desktop tests: `epub_auditor`, `epub_meta_display`, `ace_runner`, integration
- 74 web tests passing

---

## [0.2.3] -- 2026-04-12

### UI and Accessibility Polish

- Fixed guidelines Expand/Collapse All button not working (inline `onclick` blocked by CSP; moved to external `guidelines.js`)
- Added `script-src 'self'` to Caddyfile CSP; added one-time `update-csp.sh` migration script
- Fixed 11 UI and accessibility issues across web templates:
  - Fixed openpyxl link pointing to Mammoth URL on About page (copy-paste error)
  - Added back-to-top links to all 7 About page sections
  - Version numbers now pulled from package metadata instead of hardcoded
  - Added `.card-convert` accent border (purple) and format pill styles for MD, PDF
  - Guidelines JS: sync Expand/Collapse button text on manual details toggle; force-open all `<details>` on `beforeprint`, restore on `afterprint`
  - Feedback form: added `aria-describedby` linking help text to textarea; added `required` on rating and task radio groups; added "Error:" prefix to error box
  - Audit report: added "What's Next?" guidance for Markdown and PDF formats
  - Context processor injects `web_version` and `desktop_version` into all templates

### Convert Page Rewrite

- Replaced jargon (MarkItDown, Pandoc, RST, ODT) with plain-language descriptions
- Added "Which option should I choose?" expandable guide with use cases
- Step 1/Step 2 fieldset labels to guide users through the form
- Explained difference between Export and Convert pages
- Added privacy note (file deleted immediately after conversion)

---

## [0.2.2] -- 2026-04-12

### Pandoc HTML Conversion

- Added `pandoc_converter.py` for Markdown, reStructuredText, OpenDocument, RTF, and Word to ACB-compliant HTML conversion via Pandoc
- Added CLI `convert-html` subcommand with `--title`, `--css`, `--lang` options
- Added GUI checkbox for Pandoc HTML export in save step
- Web convert route: two-way conversion (to-Markdown or to-ACB-HTML)
- Convert form: radio group for direction, updated help text

### Docker Build Optimization

- Dockerfile now installs Pandoc for server-side HTML conversion
- Root `.dockerignore` massively reduces build context (excludes CLI, GUI, build files, installer, TypeScript add-in, docs, scripts)
- Upload validation: added `CONVERT_EXTENSIONS` superset with optional `allowed_extensions` parameter

### Form Improvements

- Audit and fix forms: wrapped custom rules in `<details>` (collapsed by default) to reduce form length
- 69 total tests passing (4 new Pandoc conversion tests)

---

## [0.2.1] -- 2026-04-12

### Markdown and PDF Auditing

- Added `md_auditor.py` with Markdown-specific rules: heading hierarchy, emphasis violations (italic, bold-as-emphasis), link text, alt text, emoji, em-dashes, tables
- Added `pdf_auditor.py` with PDF rules: metadata (title, language), tagged structure, font sizes, font families, scanned page detection, bookmarks (via PyMuPDF)
- Added `converter.py` wrapping Microsoft MarkItDown for document-to-Markdown conversion
- Web audit and fix routes dispatch to format-specific auditors for `.md` and `.pdf`

### Help URL Data Layer

- Added `rules.py` with per-rule help URLs: curated links to ACB spec, WebAIM, Microsoft Office docs, WCAG Understanding docs
- Auto-generates WCAG Understanding doc URLs from `acb_reference` strings
- Added `_help_links.html` partial for rendering help links in findings tables
- All audit and fix reports now show clickable "Learn More" per finding

### About Page

- New `/about` route with mission, organizations, standards, dependency attributions (core libraries, optional, infrastructure), and project info
- Base template navigation updated with About and Convert links

### Convert Route

- New `/convert` route with file download
- CLI `convert` subcommand and GUI Convert tab added

### Dependencies

- Added `markitdown[pdf,docx,xlsx,pptx]>=0.1.5` and `pymupdf>=1.25` to desktop
- Added `markitdown` and `pymupdf` to web requirements

### Tests

- 65 tests passing (28 new): about page, convert route, MD/PDF audit, help URLs, upload validation

---

## [0.2.0] -- 2026-04-12

### Multi-Format Support (Excel and PowerPoint)

- Added `xlsx_auditor.py` with 6 MSAC rules for Excel workbooks: sheet names, table headers, merged cells, alt text, color-only data, hyperlink text
- Added `pptx_auditor.py` with 6 MSAC rules for PowerPoint presentations: slide titles, reading order, alt text, font sizes, speaker notes, chart descriptions
- Added `DocFormat` enum to `constants.py` with `formats` field on every `AuditRule`
- Added 12 new MSAC rule IDs across both formats
- Web upload validation accepts `.docx`, `.xlsx`, `.pptx` with magic-byte checks
- Audit route dispatches to format-specific auditors
- Fix route returns audit guidance for Excel/PowerPoint (no auto-fix yet)
- Landing page shows format pills and per-format capability badges
- Format tags in rule lists indicate which formats each rule applies to
- CLI audit, fix, and batch commands accept all three Office formats
- GUI file picker includes all three formats; wizard skips HTML export for non-Word
- TypeScript `constants.ts` synced with new `DocFormat` enum and MSAC rule definitions

### Accessibility Improvements

- Flash messages use text prefixes (Error/Success/Warning/Note) not color alone
- All severity badges, format pills, and tags have visible text labels
- Nav link focus indicators (3px solid outline) on all interactive elements
- Contrast meets AA thresholds for all new UI elements

### Documentation

- PRD updated to v2.0 with multi-format status and implementation notes
- Deployment guide expanded to comprehensive production reference
- All READMEs updated for multi-format support

### Tests

- 40 tests passing (12 new multi-format tests)

---

## [0.1.5] -- 2026-04-11

### Production Deployment Infrastructure

- Added `docker-compose.prod.yml` with Caddy reverse proxy for auto-HTTPS
- Added `Caddyfile.example` configuring `csedesigns.com` (static) and `lp.csedesigns.com` (Flask proxy)
- Made wxPython optional via `[gui]` extra in pyproject.toml so Docker builds succeed without GTK/X11
- Added deployment shell scripts: `bootstrap-server.sh`, `deploy-app.sh`, `backup-feedback.sh`, `restore-feedback.sh`, `post-deploy-check.sh`
- Fixed: include `templates/` and `static/` in web package data
- Fixed: silence Gunicorn home directory and Flask-Limiter storage warnings
- Fixed: create writable `.gunicorn` directory for control socket

### Security Hardening

- Warn when `SECRET_KEY` is not set (random key won't survive restarts)
- Replaced deprecated `FLASK_ENV` with `FLASK_DEBUG` in docker-compose
- Added `Cache-Control: no-store` to feedback review endpoint
- Replaced `innerHTML` with DOM API in `taskpane.ts` (XSS prevention)
- Resolved 3 Dependabot vulnerabilities in word-addin:
  - Upgraded copy-webpack-plugin to ^14 (fixes serialize-javascript RCE + DoS)
  - Added npm overrides for `serialize-javascript >=7.0.5` and `tmp >=0.2.4`
  - GHSA-5c6j-r48x-rmvq (high), GHSA-qj8w-gfj5-8c6v (high), GHSA-52f5-9888-hmc6 (low)

---

## [0.1.4] -- 2026-04-11

### Server Documentation

- Added Phase 6: SSL/TLS configuration (verification, custom certs, troubleshooting, staging)
- Added Phase 8: SFTP file access (commands, GUI clients, chroot option)
- Added Phase 1 hardening: fail2ban for SSH brute-force protection, swap file for OOM prevention
- Added Docker json-file log rotation (10 MB x 3 files) to `docker-compose.yml`
- Added Caddy Content-Security-Policy and HSTS headers to all Caddyfile examples
- Added automated daily backup script with 30-day retention
- Added Docker image pinning guidance for reproducible builds
- Added `.prettierignore` to protect Jinja2 templates from formatter damage
- Fixed Caddyfile `reverse_proxy` references (`app` to `web`)
- Removed deploy-word-addin GitHub Actions workflow (replaced by Flask web app)

---

## [0.1.3] -- 2026-04-11

### Flask Web Application

- New `web/` directory with Flask 3.x web application
- Routes: `/` (landing), `/audit`, `/fix`, `/template`, `/export`, `/guidelines`, `/feedback`
- CSRF protection via Flask-WTF on all forms
- Rate limiting via Flask-Limiter (10/minute on upload endpoints)
- SQLite feedback storage with WAL mode and password-protected review
- Docker + Gunicorn deployment with non-root `app` user and `/health` endpoint
- Full WCAG 2.2 AA compliance: skip link, landmarks, `aria-current`, focus styles
- Path traversal protection on fix download (`secure_filename` + resolve check)
- Feedback input validation (rating allowlist, 5000-character message limit)
- Inline styles moved to CSS classes

### Word Add-in (Office.js)

- New `word-addin/` directory with Office.js TypeScript port
- Audit, fix, and template functionality as a Word ribbon integration
- `constants.ts` mirroring Python `constants.py` for cross-implementation sync
- `auditor.ts`, `fixer.ts`, `template.ts` implementing core logic
- Webpack build, manifest files for sideloading

### Documentation

- Added Flask web app PRD (`docs/prd-flask-web-app.md`)
- Added comprehensive deployment guide (`docs/deployment.md`)
- Updated `copilot-instructions.md` with cross-implementation sync table
- Created `web/README.md` with architecture and quick start
- 28 tests passing

---

## [0.1.2] -- 2026-04-09

### CLI Improvements

- Bumped version to 0.1.2 (was stuck at 0.1.0 across v0.1.0 and v0.1.1 tags)
- Added `--dry-run/-n` to fix command (shows what would change without modifying)
- Added `--dry-run/-n` to batch fix (shows per-file fixable vs manual counts)
- Added batch progress output: "Processing 1/5: file.docx"
- Added `completions` subcommand (bash, zsh, fish, powershell)
- Respect `NO_COLOR` environment variable ([no-color.org](https://no-color.org))
- Added `exitCode` field to JSON audit report output
- Added `--recursive/-r` to batch for subdirectory scanning
- Batch accepts directories as file arguments
- Sort batch files for deterministic output
- Wired `--quiet/-q` to suppress info messages (`logging.WARNING`)
- Wired `--verbose/-v` for debug output (`logging.DEBUG`)
- Fixed version: 1.0.0 to 0.1.0 to match pre-release tags

### CLI Short Flags

- Global: `-V` (version), `-q` (quiet), `-v` (verbose)
- audit: `-f` (format), `-o` (output)
- fix: `-o` (output), `-b` (bound)
- template: `-b` (bound), `-n` (no-sample), `-t` (title), `-i` (install)
- batch: `-f` (format), `-d` (output-dir), `-b` (bound)
- export: `-o` (output), `-c` (cms), `-t` (title)
- Documented exit codes: 0=success, 1=error, 2=non-compliant

---

## [0.1.1] -- 2026-04-09

### Build System

- Switched PyInstaller from `--onefile` to `--onedir` to eliminate `[PYI-32340:WARNING]` temp directory cleanup noise on Windows
- Build now produces `.zip` archives for portable distribution
- Inno Setup installer updated: GUI to `{app}`, CLI to `{app}\cli`
- CLI PATH registration points to `{app}\cli` for command-line use
- Fixed absolute imports in entry points for PyInstaller compatibility
- Removed `--clean` flag so second PyInstaller build does not delete first

### Packaging

- Separate CLI and GUI executables:
  - CLI: `acb-large-print-cli-{os}-{arch}` (console, no wxPython dependency)
  - GUI: `acb-large-print-{os}-{arch}` (windowed, includes wxPython)
- macOS builds packaged into `.dmg` disk image
- CI simplified to 2-platform matrix: Windows x64 + macOS ARM64

---

## [0.1.0] -- 2026-04-09

### Initial Release

The first public release of the ACB Document Accessibility Toolkit.

#### VS Code Agent Toolkit

- Large Print Formatter agent with 9 operating modes:
  - **Audit** -- check open HTML/CSS file against ACB Large Print rules
  - **Generate** -- create new ACB-compliant HTML from scratch
  - **Convert** -- transform existing HTML to ACB compliance
  - **Template** -- generate Word document templates with ACB styles
  - **CSS Embed** -- inject ACB CSS into existing HTML documents
  - **Word Setup** -- generate PowerShell COM script to configure Word styles
  - **Markdown Audit** -- check Markdown files for ACB emphasis, heading, and list issues
  - **Markdown Fix** -- auto-fix Markdown files for ACB compliance
  - **Markdown-to-HTML** -- convert Markdown to ACB-compliant HTML with document shell and CSS
- Markdown Accessibility assistant agent (WCAG audit orchestrator)
- Markdown Scanner, Markdown Fixer, and Markdown CSV Reporter sub-agents
- Slash commands: `/acb-audit`, `/acb-convert`, `/acb-md-audit`, `/acb-md-convert`, `/acb-word-setup`
- Auto-attach instructions for HTML/CSS editing
- Pattern library, severity scoring, emoji maps, and fix templates

#### Reference Files

- `acb-large-print.css` -- drop-in CSS stylesheet (rem-based, WCAG 2.2 AA, `@media print` overrides for ACB 1.15 line-height)
- `acb-large-print-boilerplate.html` -- semantic HTML skeleton with headings, lists, TOC leader dots, table, figure with caption, and endnotes

#### Desktop Tool (Python)

- CLI with subcommands: `audit`, `fix`, `template`, `export`, `batch`
- GUI: accessible 7-step wxPython wizard
- Word document auditor enforcing ACB Large Print Guidelines:
  - Font family (Arial), body size (18pt), heading sizes (22pt/20pt)
  - No italic, bold restricted to headings, underline emphasis
  - Flush left alignment, line spacing, margins, widow/orphan control
  - No hyphenation, page numbers, heading hierarchy
  - Document title, document language (WCAG 2.4.2, 3.1.1)
  - Alt text, table headers, hyperlink text (Microsoft Accessibility Checker rules)
- Word document fixer: auto-corrects fonts, sizes, spacing, alignment, emphasis
- Word template builder: generates `.dotx` with all ACB styles pre-configured
- HTML exporter via Mammoth: standalone pages and CMS-embeddable fragments
- Cross-platform PyInstaller builds (Windows x64, macOS ARM64)
- Inno Setup installer for Windows distribution

#### CI/CD

- GitHub Actions workflow for automated builds on push/tag/PR
- Artifact upload for all platform executables
- Release automation on version tags

#### Documentation

- Comprehensive toolkit documentation (`docs/acb-large-print-toolkit.md`)
- Project announcement (`docs/announcement.md`)
- ACB Large Print Guidelines source document (`docs/`)
