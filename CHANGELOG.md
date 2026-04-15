# Changelog

All notable changes to the GLOW Accessibility Toolkit are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Releases are tagged in the [GitHub repository](https://github.com/accesswatch/acb-large-print-toolkit). Dates are in Pacific Time (UTC-7).

---

## [Unreleased]

### Fixed

- Web changelog page now builds its version list dynamically from `CHANGELOG.md` headings, so release `1.0.0` and future releases appear automatically without hardcoded template updates.
- Front page standards text now consistently references WCAG 2.2 AA (removed mixed WCAG 2.1 wording).
- Word fix workflow now preserves user-confirmed heading conversions through the heading review step even when form round-trip text normalization alters whitespace or punctuation.
- Added regression test coverage for confirmed heading application by paragraph index after review.
- Added community-driven project and feedback messaging to the web announcement content, including explicit note that extensive testing is producing strong results.
- Fix Results page now shows explicit score delta and weighted remaining-penalty breakdown (Critical/High/Medium/Low counts) to explain low grades when unresolved high-severity findings remain.
- Added heading-review telemetry logging in the fix confirm workflow to report confirmed heading selections received vs heading fixes applied.
- Fix Results page now displays heading review counts directly in the UI (`selected` vs `applied`) when interactive heading confirmation is used.
- Updated documentation links from `lp.csedesigns.com` to `glow.bits-acb.org` across announcement, deployment, and user guide content.
- Updated `web/Caddyfile.example` to support both `lp.csedesigns.com` and `glow.bits-acb.org`; operational scripts keep `lp.csedesigns.com` as the canonical default domain.
- Added a tracked `web/Caddyfile` with dual-domain app host support (`lp.csedesigns.com`, `glow.bits-acb.org`) for direct production deployment with Docker Compose.
- Deployment scripts now support optional alias-domain verification via `APP_ALIAS_DOMAIN` while keeping `APP_DOMAIN` defaulted to `lp.csedesigns.com`.

### Added

- Added a Playwright E2E regression harness under `web/e2e/` covering home, audit, fix, export, convert, template, and key static pages.
- Added upload-aware E2E tests using `E2E_UPLOAD_DOCX` (default `d:/code/test.docx`) for document workflow regression coverage.
- Added issue report generation (`web/e2e/scripts/generate-issue-report.mjs`) to summarize failed Playwright tests into `e2e/artifacts/ISSUES.md` alongside HTML/JSON/JUnit artifacts.
- Added Node test runner scaffolding in `web/package.json` and artifact ignores in `web/.gitignore` for repeatable local and CI-friendly regression execution.

---

## [1.0.0] -- 2026-04-14

### Core Platform

- Established the 1.0 release baseline across desktop and web toolchains, with synchronized rule metadata and cross-format audit/fix workflows.
- Introduced structured fix tracking with category-level reporting to make remediation output actionable for reviewers and administrators.
- Expanded supported workflows across Word, Excel, PowerPoint, Markdown, PDF, and ePub in a single toolkit.

### Product Identity and Guided Experience

- Rebranded the platform to **GLOW Accessibility Toolkit** (Guided Layout & Output Workflow) across web UI, desktop messaging, help content, and release surfaces.
- Added a clearer product identity with guided, user-friendly "magical" language while preserving standards-first behavior and compliance rigor.
- Kept release versioning at **1.0.0** while modernizing product naming and onboarding copy.

### Heading Intelligence and Structural Repair

- Added end-to-end faux heading detection and conversion in Word documents using heuristic scoring, optional AI refinement via Ollama, and interactive confirmation flows in the web UI.
- Added `ACB-FAUX-HEADING` and heading normalization behavior to improve semantic structure and post-fix heading hierarchy quality.
- Enabled heading detection by default in the web Fix workflow and clarified guidance for pasted and unstructured Word documents.

### ACB Layout Enforcement and Formatting Controls

- Added configurable list and paragraph indentation enforcement with flush-left defaults aligned to ACB large print policy.
- Added corresponding CLI, desktop GUI, and web controls so teams can apply strict defaults while still supporting policy-based overrides.
- Expanded automatic handling of emphasis, alignment, line spacing, page setup, language, and document-title repair.

### Conversion and Publishing

- Expanded conversion support to include Word, EPUB 3, and PDF outputs via Pandoc and WeasyPrint, in addition to existing text/HTML and DAISY pipeline flows.
- Added print-optimized ACB CSS generation for PDF workflows and improved conversion guidance in web UI and docs.

### Web Experience and Transparency

- Added full fix-details reporting in the web Fix results page with grouped remediation records.
- Clarified remaining-issues messaging to distinguish truly manual items from configurable optional behaviors.
- Added release version visibility in the global footer and About page so deployed environments clearly expose current release state.
- Enhanced health endpoint reporting to include web, pipeline, and ollama service status in one response.

### Documentation and Testing Program

- Added large synthetic stress corpus coverage for heading detection and repair validation, with scenario-family transparency documented in user-facing pages.
- Expanded guide/about/help surfaces to explain rule behavior, conversion pathways, and remediation workflows.
- Consolidated project docs and release-facing references to better support operations, onboarding, and compliance reporting.

### Security

- Added `pip-audit` to deployment requirements for continuous Python dependency vulnerability scanning. Integrated into release and deployment workflows to detect known CVEs in transitive dependencies.
- Resolved CVE-2026-40192 (pillow) and CVE-2026-40260 (pypdf) by upgrading to fixed versions: pillow >=12.2.0, pypdf >=6.10.0. All dependencies now pass pip-audit security checks.
- Fixed session timeout handling in web app: increased default session timeout to 4 hours for long document processing workflows, added automatic garbage collection of stale upload directories (24hr TTL by default), and improved error messages when sessions expire. Configurable via SESSION_TIMEOUT_MINUTES and UPLOAD_MAX_AGE_HOURS environment variables.

### Removed

- Removed in-progress noise and interim bugfix tracking from the 1.0 release narrative in favor of feature-grouped release notes.


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

The first public release of the GLOW Accessibility Toolkit.

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
