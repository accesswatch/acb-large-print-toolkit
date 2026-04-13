# PRD: ACB Document Accessibility Web Application

**Status:** Implemented (v2.0)
**Author:** Jeff Bishop, BITS
**Date:** April 12, 2026
**Target:** v2.0 release

---

## Implementation Status

The Flask web application has been built and is ready for deployment. All core features described in this PRD are implemented. The following table summarizes what shipped in v0.1:

| Feature | Status | Notes |
|---------|--------|-------|
| Audit page (Full / Quick / Custom modes) | Done | Rule filtering by severity, severity-grouped checkboxes |
| Fix page (Full / Essentials / Custom modes) | Done | Before/after scores, download fixed .docx, review-required warnings |
| Template generation | Done | Title, sample content, binding margin options |
| HTML export (Standalone ZIP + CMS fragment) | Done | Both modes working |
| Convert to Markdown (MarkItDown) | Done | .docx, .xlsx, .pptx, .pdf, .html, .csv, .json, .xml, .epub |
| Convert to HTML (Pandoc) | Done | .md, .docx, .rst, .odt, .rtf, .epub -- ACB formatting, binding margin, print stylesheet options |
| Convert to Word (Pandoc) | Done | .md, .rst, .odt, .rtf, .html, .epub -- produces .docx for editing or audit/fix |
| Convert to EPUB 3 (Pandoc) | Done | .md, .docx, .rst, .odt, .rtf, .html -- lightweight EPUB with ACB CSS |
| Convert to PDF (Pandoc + WeasyPrint) | Done | .md, .docx, .rst, .odt, .rtf, .epub, .html -- ACB print formatting, binding margin option |
| Convert to EPUB/DAISY (DAISY Pipeline) | Done | Word to EPUB 3, HTML to EPUB 3, EPUB to DAISY 2.02, EPUB to DAISY 3 |
| Markdown and PDF audit | Done | Basic page-level structure checks |
| About page | Done | Mission, organizations, standards, dependencies, acknowledgments |
| Guidelines reference page | Done | Full ACB spec + WCAG supplement from constants.py |
| Feedback page with SQLite storage | Done | Password-protected review page via FEEDBACK_PASSWORD env var |
| CSRF protection (Flask-WTF) | Done | All forms have hidden csrf_token |
| Rate limiting (Flask-Limiter) | Done | 120 requests/minute default |
| Structured logging | Done | Timestamp + level + logger name format, LOG_LEVEL env var |
| Favicon (SVG) | Done | "LP" monogram |
| Flash message support | Done | Category-based flash rendering in base template |
| Docker + Compose | Done | Non-root user, health check, feedback volume |
| Test suite | Done | Smoke tests, error handling, feedback, accessibility checks, integration |
| Contextual help (details/summary) | Done | Every form page has expandable help accordions |
| WCAG 2.2 AA compliance | Done | lang, landmarks, labels, contrast, skip nav, focus indicators |
| No JavaScript required | Done | All functionality works without JS |

### Deviations from Plan

- **Feedback system added** -- not in original PRD. SQLite-backed with password-protected review page.
- **Caddy not included in docker-compose.yml** -- shipped as a separate Caddyfile reference in deployment.md. The compose file exposes port 8000 directly; Caddy is added at deployment time.
- **Gunicorn workers reduced to 2** -- Docker default; override via environment variable at deployment.
- **Flash messages added** -- base template supports category-based flash rendering for future use.
- **Rate limiting added** -- 120 req/min default via Flask-Limiter (originally listed as out of scope).
- **CSRF protection added** -- Flask-WTF CSRFProtect on all forms (originally not specified).

---

## Problem Statement

The ACB Large Print Tool currently requires one of three things to use: VS Code with Copilot Chat (for the agent toolkit), a desktop Python install (for the CLI), or a PyInstaller executable (for the GUI wizard). All three assume local software installation. This means:

- Organizations that want to check a single document must download and install software first
- Non-technical staff (chapter presidents, newsletter editors, meeting coordinators) find the installation barrier too high
- IT departments at ACB affiliates may not allow installing arbitrary executables
- The tool cannot be demonstrated at conferences or training sessions without pre-configuring every attendee's machine
- Mobile and Chromebook users are completely excluded

Meanwhile, the core engine -- audit, fix, template builder, and HTML export -- is a clean Python library with no GUI dependency. Every function takes a file path in and returns data or a file path out. The business logic is ready to serve HTTP requests today.

## Solution

Build a Flask web application that wraps the existing `acb_large_print` Python library in a browser-accessible interface. Users upload a `.docx`, `.xlsx`, or `.pptx` file through a web form, choose an operation (audit, fix, create template, export to HTML), and receive results in the browser or as a file download. No installation. No accounts. No login.

The web app will:

- Accept `.docx`, `.xlsx`, and `.pptx` uploads (max 16 MB) and validate them server-side
- Provide all four core operations: audit (all three formats), fix (Word auto-fix; Excel/PowerPoint audit guidance), template creation (Word), and HTML export (Word)
- Display audit reports directly in the browser as accessible HTML
- Return fixed documents and templates as immediate file downloads
- Delete all uploaded and generated files immediately after the response is sent
- Meet WCAG 2.2 AA from day one -- this is an accessibility tool and must be accessible itself
- Coexist alongside the existing CLI, GUI, and VS Code agent -- the Flask app is a new interface, not a replacement
- Deploy via Docker for hosting flexibility (RackNerd VPS, Hetzner Cloud, or any Docker host)
- Provide rich contextual help via native HTML `<details>/<summary>` accordions on every page -- no JavaScript required, fully keyboard and screen reader accessible
- Let users control which rules are checked (audit) and which fixes are applied (fix) via three preset modes: Full, Quick/Essentials, and Custom (individual rule checkboxes grouped by severity)
- Include a dedicated `/guidelines` page with the complete ACB Large Print specification and WCAG 2.2 supplement as browsable, searchable reference content
- Auto-generate all help text and rule descriptions from the canonical `constants.py` rule metadata -- a single source of truth ensures the web UI stays in sync with the CLI, GUI, and VS Code agent

## User Stories

1. As a chapter newsletter editor, I want to upload my meeting agenda `.docx` and get an ACB compliance report in my browser, so that I can see what needs fixing without installing any software.
2. As a chapter newsletter editor, I want to upload a non-compliant `.docx` and download a fixed version with one click, so that I can produce compliant documents without understanding the ACB specification.
3. As a conference presenter, I want to point attendees to a URL where they can try the tool instantly, so that training sessions focus on the ACB rules rather than software installation.
4. As an ACB affiliate officer, I want to generate a pre-configured Word template from the web UI, so that future documents start compliant by default.
5. As a web content manager, I want to upload a `.docx` and download a standalone HTML version with ACB-compliant CSS, so that I can publish accessible content on our website.
6. As a web content manager, I want to export a CMS-ready HTML fragment with embedded CSS, so that I can paste it directly into WordPress or Drupal without breaking my site theme.
7. As a sighted user helping a blind colleague, I want the web UI to be fully keyboard-navigable with clear focus indicators, so that we can use it together on any device.
8. As a screen reader user, I want all form controls to have associated labels and all status messages to use ARIA live regions, so that I know what is happening at each step.
9. As a mobile user at a conference, I want the web app to work on my phone's browser, so that I can check a document without needing a laptop.
10. As a Chromebook user, I want to access all features through the browser, so that I am not excluded by platform limitations.
11. As the BITS president, I want uploaded documents to be deleted immediately after processing, so that sensitive organizational documents are not stored on third-party servers.
12. As the BITS president, I want the hosting cost to be under $80 per year, so that this is sustainable as a free community tool without ongoing fundraising.
13. As a developer contributing to the project, I want the Flask app to import the existing core library without modification, so that bug fixes and new rules flow through to the web UI automatically.
14. As a developer, I want the web app packaged as a Docker container, so that deployment is reproducible across any hosting provider.
15. As a user with low vision, I want the web UI styled with the same ACB Large Print CSS used for document output, so that the tool itself demonstrates the formatting it enforces.
16. As a user submitting a document, I want clear error messages when my upload fails (wrong file type, too large, corrupted), so that I know how to fix the problem.
17. As a user viewing an audit report, I want findings sorted by severity with clear visual and semantic grouping (critical, high, medium, low), so that I can prioritize fixes.
18. As a user requesting a template, I want to specify a document title, whether to include sample content, and whether to add binding margins, so that the template fits my needs.
19. As a user exporting to HTML, I want to choose between standalone (full HTML + CSS) and CMS fragment (embedded CSS), so that I get the right format for my publishing workflow.
20. As a system administrator, I want the Docker container to run as a non-root user with no write access outside the temp directory, so that the attack surface is minimized.
21. As a system administrator, I want the app to enforce upload size limits and MIME type validation at the application layer, so that malicious files are rejected before touching the processing pipeline.
22. As a returning user, I want to see brief explanations of each operation on the landing page, so that I remember which option to choose without re-reading documentation.
23. As a user who just completed an audit, I want a clear call-to-action to fix the document, so that the next step is obvious.
24. As a user processing a fix, I want to see a before/after compliance score, so that I understand the improvement.
25. As a user, I want the page to work without JavaScript, so that browser extensions, corporate proxies, and assistive technologies that disable scripts do not break functionality.
26. As a BITS board member, I want the tool branded as a BITS community project, so that users understand its origin and can report issues.
27. As a user on a slow connection, I want feedback during file upload and processing, so that I know the app has not frozen.
28. As a user, I want the audit report to link each finding to the relevant ACB guideline section, so that I can look up the rationale for each rule.
29. As a first-time user, I want contextual help on every page explaining what the operation does, what gets changed, and why, so that I understand each step without reading external documentation.
30. As an experienced user running an audit, I want to choose between Full Audit (all rules), Quick Audit (critical and high only), or Custom Audit (pick individual rules), so that I get the right level of detail for my workflow.
31. As an experienced user running a fix, I want to choose between Full Fix (all auto-fixable rules), Essentials Fix (critical and high only), or Custom Fix (pick individual fix categories), so that I control how much the tool changes in my document.
32. As a user exploring the Custom Audit/Fix option, I want rules grouped by severity (Critical, High, Medium, Low) inside expandable `<details>` accordions, so that I can quickly find and toggle related rules.
33. As a user learning the ACB specification, I want a dedicated Guidelines page on the web app that presents the complete ACB Large Print rules and WCAG 2.2 digital supplement, so that I can reference the standard without leaving the tool.
34. As a screen reader user, I want all help accordions to use native HTML `<details>/<summary>` elements rather than JavaScript widgets, so that my assistive technology announces expand/collapse states correctly.
35. As a user on the fix results page, I want to see which rules were applied and which were skipped (when using Essentials or Custom mode), so that I understand exactly what changed.

## Implementation Decisions

### Architecture

- The Flask web app lives in a new top-level `web/` directory alongside `desktop/` and `office-addin/`. It is a separate Python package (`acb_large_print_web`) that imports `acb_large_print` as a dependency.
- **Zero modifications** to the existing `acb_large_print` core library. The web app calls the same public API that the CLI and GUI use: `audit_document()`, `fix_document()`, `create_template()`, `export_standalone_html()`, `export_cms_fragment()`, and the reporter functions. Rule filtering happens in the web layer by post-filtering `AuditResult.findings` -- the core audit always runs all checks.
- The app uses the Flask application factory pattern (`create_app()`) for testability and configuration flexibility.

### Help Text and Documentation Strategy

Every page includes contextual help using native HTML `<details>/<summary>` accordion elements:

- **No JavaScript dependency** -- `<details>` is natively supported in all modern browsers, is keyboard-operable (Enter/Space to toggle), and is correctly announced by screen readers as "collapsed/expanded".
- **Help text is auto-generated from `constants.py`** -- the Jinja2 templates iterate over `AUDIT_RULES` to render rule descriptions, severity, ACB references, and auto-fixable status. This means a new rule added to the core library automatically appears in the web UI with zero template changes.
- **Accordions are grouped by severity** -- Critical, High, Medium, Low. Each severity group is a `<details>` accordion containing the rules in that group.
- **Every form page** (audit, fix, template, export) includes operation-specific help accordions explaining what the operation does, what options are available, and what the output will be.
- **A dedicated `/guidelines` page** presents the full ACB Large Print specification and WCAG 2.2 AA digital supplement as structured, browsable HTML with one `<details>` accordion per guideline section.

### Rule Selection (Audit and Fix)

Both the audit and fix pages offer three preset modes via radio buttons:

**Audit page:**
- **Full Audit** (default) -- runs all 16 rules. Recommended for first-time users.
- **Quick Audit** -- runs only Critical and High severity rules. Fast overview of major issues.
- **Custom Audit** -- expands a panel of checkboxes grouped by severity (`<details>` accordions: Critical, High, Medium, Low). Each checkbox corresponds to one rule from `AUDIT_RULES`. All are checked by default; the user unchecks any rules they want to skip.

**Fix page:**
- **Full Fix** (default) -- applies all auto-fixable rules. Brings the document to maximum compliance.
- **Essentials Fix** -- applies only Critical and High severity auto-fixes. Leaves Medium/Low issues untouched.
- **Custom Fix** -- same severity-grouped checkbox panel. User picks which fix categories to apply.

**Implementation:** The core library always runs all checks/fixes. The web layer:
- **Audit:** post-filters `AuditResult.findings` to include only the selected rule IDs before rendering the report.
- **Fix:** cannot partially fix (the core `fix_document()` applies everything). For Essentials/Custom modes, the web layer runs `fix_document()` with all fixes, then runs a post-fix audit and filters the report to show only the user's selected rules. The fix result page clearly states "All auto-fixable issues were corrected" regardless of mode, and the filtered report shows the user's focus area. This keeps KISS while giving the appearance of control -- the document is always fully fixed, which is the safest outcome.

### Modules

**Module 1: `app.py` -- Application Factory**

- `create_app(config=None) -> Flask`
- Registers blueprints, sets `MAX_CONTENT_LENGTH` (16 MB), configures temp directory, registers error handlers (413, 415, 500), registers `after_request` cleanup.
- Single function, no global state.

**Module 2: `upload.py` -- File Upload and Validation**

- `validate_upload(file) -> Path` -- accepts Flask `FileStorage`, validates extension (`.docx` only) and file size, saves to a `tempfile.TemporaryDirectory()`, returns the temp file path.
- `cleanup_tempdir(path) -> None` -- deletes the temporary directory and all contents.
- This is the **security boundary**. All uploaded file validation (extension, MIME type, magic bytes, path traversal prevention) happens here and nowhere else.

**Module 3: `routes/` -- Flask Blueprints**

Six thin blueprints. Each handles GET (show form) and POST (process upload), calling core functions directly:

| Blueprint | URL | Core API called | Response |
|-----------|-----|-----------------|----------|
| `main_bp` | `GET /` | None | Landing page with format pills, operation cards, and descriptions |
| `audit_bp` | `GET /audit`, `POST /audit` | `audit_document()` / `audit_workbook()` / `audit_presentation()` | Rendered audit report in browser (filtered by selected mode/rules) |
| `fix_bp` | `GET /fix`, `POST /fix` | `fix_document()` (Word) or audit-only (Excel/PowerPoint) | Fixed `.docx` download or audit guidance + before/after score |
| `template_bp` | `GET /template`, `POST /template` | `create_template()` | `.dotx` file download |
| `export_bp` | `GET /export`, `POST /export` | `export_standalone_html()` or `export_cms_fragment()` | HTML file download (standalone) or ZIP (standalone + CSS) |
| `guidelines_bp` | `GET /guidelines` | None (reads from `constants.py`) | Full ACB specification reference page |

Each POST route: validate upload -> save to temp dir -> call core function -> filter results by mode -> return response -> cleanup temp dir in `finally` block.

**Module 4: `templates/` -- Jinja2 HTML Templates**

- `base.html` -- layout: skip nav link, `<header>` landmark with BITS branding, `<nav>` with links to all pages, `<main>` landmark, `<footer>` landmark, heading hierarchy starting at `<h1>`.
- `index.html` -- landing page with cards for each operation, brief descriptions, and link to guidelines.
- `guidelines.html` -- full ACB Large Print specification and WCAG 2.2 digital supplement. One `<details>/<summary>` accordion per guideline section (Font, Headings, Emphasis, Alignment, Spacing, Margins, Pagination, Hyphenation, Page Numbers, Document Properties). Each section lists the relevant audit rules with severity and description.
- `audit_form.html` -- upload form with three radio buttons (Full / Quick / Custom), a `<details>` panel for Custom mode containing severity-grouped rule checkboxes, and contextual help accordions explaining the audit process.
- `audit_report.html` -- audit results rendered as accessible HTML table with severity badges. Includes a "What's Next" section with a link to the fix page.
- `fix_form.html` -- upload form with three radio buttons (Full Fix / Essentials Fix / Custom Fix), severity-grouped checkbox panel for Custom mode, contextual help accordions.
- `fix_result.html` -- before/after score comparison, list of applied/skipped rules, download link.
- `template_form.html` -- options form (title, sample content toggle, binding margin toggle) with help accordions for each option.
- `export_form.html` -- upload form with standalone/CMS radio toggle, title field, help accordions explaining each format.
- `error.html` -- error page with clear message and link back to the operation.
- `_help_rules.html` -- partial template (Jinja2 include) rendering severity-grouped rule checkboxes from `AUDIT_RULES`. Used by both audit and fix forms.

All templates use the ACB Large Print CSS for body text, headings, and spacing. Minimal supplemental CSS for form layout and `<details>` styling only.

**Module 5: `static/` -- CSS and Assets**

- Copies (not symlinks) `acb-large-print.css` from `styles/` into `web/static/`.
- A small `forms.css` for form-specific layout (input widths, button styles, file upload area).
- No JavaScript required. All forms use standard HTML `<form>` POST submissions. Optional progressive enhancement (upload progress indicator) if JS is available, but full functionality without it.

**Module 6: `wsgi.py` -- Production Entry Point**

- `app = create_app()` -- the WSGI callable for Gunicorn/uWSGI.

**Module 7: `Dockerfile` + `docker-compose.yml`**

- Base image: `python:3.13-slim`
- Non-root user (`appuser`)
- Install `acb_large_print` + `acb_large_print_web` + `gunicorn`
- Expose port 8000
- Gunicorn with 8 workers, 120s timeout (for large document processing)
- `docker-compose.yml`: two services -- Caddy reverse proxy (auto-HTTPS) + Flask app container
- Health check endpoint: `GET /health` returns 200
- Caddy persists TLS certificates in a Docker named volume
- See [docs/deployment.md](deployment.md) for step-by-step server setup and deployment commands

### File Handling and Security

- Uploaded files are saved to a new `tempfile.TemporaryDirectory()` per request.
- Temp directories are deleted in a `finally` block after the response is sent -- guaranteed cleanup even on exceptions.
- No files are ever written outside the temp directory.
- File extension whitelist: `.docx`, `.xlsx`, `.pptx` only.
- `MAX_CONTENT_LENGTH = 16 * 1024 * 1024` (16 MB) enforced by Flask before the upload handler runs.
- `werkzeug.utils.secure_filename()` applied to all uploaded filenames.
- The Docker container runs as non-root with a read-only filesystem except for `/tmp`.

### Accessibility (WCAG 2.2 AA)

- All pages have `lang="en"` on `<html>`.
- Skip navigation link as first focusable element.
- Landmark regions: `<header>`, `<nav>`, `<main>`, `<footer>`.
- Heading hierarchy: `<h1>` for page title, `<h2>` for sections, no skipped levels.
- All form controls have associated `<label>` elements.
- File input has help text via `aria-describedby` explaining accepted formats and size limit.
- Error messages linked to controls via `aria-describedby` and `aria-invalid`.
- Status messages (upload processing, success, failure) in `aria-live="polite"` region.
- Minimum 4.5:1 contrast ratio for all text.
- Focus indicators visible on all interactive elements.
- No reliance on color alone to convey information (severity uses text labels alongside color).
- All interactive elements have minimum 44x44px touch targets.
- Works without JavaScript enabled.

### Hosting Options (Docker-first, decide later)

The app ships as a Docker container. Any of these hosting options work:

| Option | Spec | Price | Notes |
|--------|------|-------|-------|
| **RackNerd 8 GB VPS (recommended)** | 6 vCPU, 8 GB RAM, 150 GB SSD, 20 TB transfer | **$62.49/year** (~$5.21/mo) | Black Friday promo -- locks in at renewal. Massive headroom for concurrent processing, room to host additional BITS services on the same VPS. Equivalent DigitalOcean Droplet would cost ~$576/year. |
| RackNerd 4 GB VPS | 3 vCPU, 4 GB RAM, 65 GB SSD, 6.5 TB transfer | $29.98/year | Good mid-tier if budget is tighter. |
| RackNerd 2.5 GB VPS | 2 vCPU, 2.5 GB RAM, 45 GB SSD, 3 TB transfer | $18.66/year | Minimum comfortable for this app alone. |
| DigitalOcean App Platform | 1 vCPU, 1 GB RAM, 100 GB transfer | $10/mo ($120/year) | Zero-ops managed platform (auto-deploy on git push, no SSH). Higher cost, less RAM, tight transfer limits. Best for teams wanting fully managed hosting. |
| Hetzner Cloud CX22 | 2 vCPU, 4 GB RAM, 40 GB SSD, 20 TB transfer | ~$54/year (~$4.49/mo) | EU GDPR, great API, hourly billing, US datacenter available (Ashburn VA). |
| Any Docker host | Varies | Varies | `docker compose up` works anywhere. |

**Recommended production stack (RackNerd 8 GB):**
- Ubuntu 24.04 LTS on the VPS
- Docker + Docker Compose for the app
- Caddy as reverse proxy (automatic Let's Encrypt TLS certificates)
- Gunicorn (8 workers -- 8 GB RAM supports it) as the WSGI server
- systemd service for auto-restart
- UptimeRobot free tier for uptime monitoring (pings `GET /health` every 5 minutes)
- Subdomain pointed via DNS A record to VPS IP
- Capacity for additional BITS services on the same VPS (150 GB SSD, 20 TB transfer)

**Deployment workflow:**
1. SSH into VPS
2. `git pull` (or `docker pull` from registry)
3. `docker compose up -d --build`
4. Caddy handles TLS automatically

For complete step-by-step commands starting from a bare server, see [docs/deployment.md](deployment.md).

### Concrete Technology Stack

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| OS | Ubuntu | 24.04 LTS | 5-year support, Docker-native, widely documented |
| Container runtime | Docker Engine + Compose | Latest stable | Reproducible builds, single `docker compose up` deploy |
| Reverse proxy / TLS | Caddy | 2.x | Automatic Let's Encrypt, zero-config HTTPS, single binary |
| WSGI server | Gunicorn | 23.x | Battle-tested, simple config, works with Flask out of the box |
| Web framework | Flask | 3.x | Minimal, no ORM/auth baggage, Jinja2 server-rendered HTML |
| Python | CPython | 3.13 | Latest stable, matches `python:3.13-slim` Docker image |
| Core library | acb_large_print | (local) | Existing audit/fix/template/export engine -- zero changes |
| Document converter | Pandoc | 3.1+ | Universal document converter: Markdown/Word/RST/ODT/RTF/ePub to HTML, Word, EPUB 3, and PDF (via WeasyPrint) |
| PDF renderer | WeasyPrint | 62.0+ | CSS-based PDF rendering with ACB print formatting (CourtBouillon). Requires Pango, Cairo, GDK-Pixbuf system libraries and Liberation Sans font. |
| Process manager | systemd | (OS built-in) | Auto-restart Docker on reboot, journald logging |
| Firewall | ufw | (OS built-in) | Simple allow/deny rules for SSH, HTTP, HTTPS |
| Monitoring | UptimeRobot | Free tier | 5-minute HTTP pings to `/health`, email/SMS alerts on downtime |

### Proposed Directory Structure

```
web/
  src/
    acb_large_print_web/
      __init__.py           # create_app() factory
      upload.py             # File validation and temp directory management
      wsgi.py               # Gunicorn entry point
      routes/
        __init__.py
        main.py             # GET / landing page
        audit.py            # GET/POST /audit (with rule filtering)
        fix.py              # GET/POST /fix (with mode filtering)
        template.py         # GET/POST /template
        export.py           # GET/POST /export
        guidelines.py       # GET /guidelines -- full ACB spec reference
      templates/
        base.html           # Layout with skip nav, landmarks, nav bar
        index.html          # Landing page with operation cards
        guidelines.html     # Full ACB spec + WCAG supplement reference
        audit_form.html     # Upload + Full/Quick/Custom radio + help
        audit_report.html   # Findings table + What's Next link
        fix_form.html       # Upload + Full/Essentials/Custom radio + help
        fix_result.html     # Before/after scores + applied rules + download
        template_form.html  # Options form + help accordions
        export_form.html    # Upload + standalone/CMS toggle + help
        error.html          # Error page
        _help_rules.html    # Partial: severity-grouped rule checkboxes
      static/
        acb-large-print.css # Copy of reference CSS
        forms.css           # Form layout, details styling, cards
  tests/
    conftest.py             # Flask test client fixture
    test_upload.py          # Upload validation unit tests
    test_audit_route.py     # Audit blueprint integration tests
    test_fix_route.py       # Fix blueprint integration tests
    test_template_route.py  # Template blueprint integration tests
    test_export_route.py    # Export blueprint integration tests
    test_guidelines.py      # Guidelines page rendering tests
    test_templates.py       # HTML template rendering tests (accessibility checks)
  Dockerfile
  docker-compose.yml
  Caddyfile
  pyproject.toml            # Package metadata, depends on acb-large-print
  requirements.txt
  README.md
```

## Testing Decisions

### What makes a good test

Tests verify **external behavior** through the Flask test client, not internal implementation details. A test uploads a real `.docx` fixture, hits a route, and asserts on the HTTP response (status code, content type, response body content). Tests do not mock core library functions -- they exercise the full stack from HTTP request to HTTP response.

### Modules to test

| Module | Test type | What to verify |
|--------|-----------|----------------|
| `upload.py` | Unit tests | Rejects non-`.docx` files, rejects oversized files, rejects empty uploads, accepts valid `.docx`, cleans up temp files after use |
| `routes/audit.py` | Integration tests | GET returns form with three mode radio buttons, POST with valid `.docx` returns HTML report containing findings, POST with Quick mode returns only Critical+High findings, POST with Custom mode filters to selected rules, POST with invalid file returns error |
| `routes/fix.py` | Integration tests | POST returns `.docx` download, response headers correct, before/after scores displayed, mode selection respected in result display |
| `routes/template.py` | Integration tests | POST with options returns `.dotx` download, title and bound options respected |
| `routes/export.py` | Integration tests | POST with standalone option returns ZIP, POST with CMS option returns HTML fragment |
| `routes/guidelines.py` | Rendering tests | GET returns 200, page contains all AUDIT_RULES rule IDs, each severity group is present, `<details>` elements are used |
| `templates/` | Rendering tests | All pages have `lang` attribute, all forms have labels, headings in order, landmarks present, `<details>/<summary>` elements used for help, rule checkboxes rendered from constants |

### Test fixtures

- A small valid `.docx` file (2-3 paragraphs with known ACB violations) committed to `tests/fixtures/`.
- A corrupt file for error handling tests.
- An oversized file (generated in test setup, not committed).

### Prior art

No existing tests in the repo. The test suite established here will set the pattern for future core library tests.

## Out of Scope

- **User accounts and authentication** -- the tool is completely open, no login required. If auth is needed later, it can be added as middleware without changing the route logic.
- **Batch processing (multi-file upload)** -- v2 handles one file at a time. Batch is a future enhancement.
- **PDF support** -- the core library only handles Office formats. PDF is a separate tool.
- **CI/CD pipeline** -- deployment is manual `docker compose up` for v2. GitHub Actions deployment can be added later.
- **Custom domain and DNS setup** -- the PRD covers the app. Domain configuration is an ops task done at deployment time.
- **Excel and PowerPoint auto-fix** -- audit is supported for all three formats, but auto-fix is Word-only. Excel and PowerPoint auto-fix is a future enhancement.

### Previously out of scope, now implemented

- **Database** -- SQLite added for feedback persistence (concurrent-safe with WAL mode).
- **Rate limiting** -- 120 requests/minute via Flask-Limiter (configurable).
- **CSRF protection** -- Flask-WTF CSRFProtect on all POST forms.
- **Multi-format support** -- .xlsx and .pptx audit support added across web, CLI, and GUI.
- **CLI and GUI multi-format support** -- CLI audit, fix, and batch commands accept .docx, .xlsx, and .pptx. GUI file picker and wizard flow updated for all three formats.

## Further Notes

### Why Flask over Django, FastAPI, or others

- Flask is the right weight for this app. There is no database, no ORM, no admin panel, no user model. Django brings all of that for free, but it is unused baggage here.
- FastAPI's async model adds complexity without benefit -- document processing is CPU-bound (python-docx, mammoth), not I/O-bound. Async would not improve throughput.
- Flask's Jinja2 templates produce server-rendered HTML that works without JavaScript, which is critical for the WCAG 2.2 AA requirement.
- The team already uses Python extensively. Flask requires no new language or paradigm.

### Why Docker

- Reproducible deployment regardless of hosting provider.
- Eliminates "works on my machine" for system-level dependencies.
- Makes hosting migration trivial -- move from RackNerd to Hetzner to Azure by changing where `docker compose up` runs.
- Security isolation: non-root user, read-only filesystem, no host access.

### Relationship to existing components

```
                        Users
                          |
         +-------+-------+-------+-------+
         |       |       |       |       |
      Web UI   CLI    GUI    VS Code   Word
      (Flask)  (cli)  (wx)   Agent    Add-in
         |       |       |       |       |
         +-------+-------+-------+       |
                 |                        |
          acb_large_print           office-addin
          (Python core)             (TypeScript)
```

All five interfaces share the same underlying rules and constants. Bug fixes to the core library automatically flow through to the web app with no additional work. The TypeScript Word Add-in maintains its own copy of the rules (kept in sync per the cross-implementation sync protocol documented in `copilot-instructions.md`).

The web UI adds a sixth blueprint (`/guidelines`) that reads from `constants.py` to render the full specification -- this page has no upload/processing logic, just documentation generated from the canonical rule definitions.

### Cost estimate

| Item | Annual cost |
|------|------------|
| RackNerd 8 GB VPS (Black Friday promo) | $62.49 |
| Domain (if new) | ~$10-15 (or $0 if using existing subdomain) |
| UptimeRobot monitoring | $0 (free tier) |
| Let's Encrypt TLS | $0 (auto via Caddy) |
| **Total** | **$62.49 to ~$78** |

At ~$5.21/month this is sustainable as an unfunded community tool indefinitely. The VPS has enough capacity to host additional BITS services without incremental cost.
