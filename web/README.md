# ACB Document Accessibility Web Application

A Flask web application that provides browser-based access to the ACB Document Accessibility Tool. Upload a Word, Excel, PowerPoint, Markdown, PDF, or ePub document, choose an operation (audit, fix, template, export, convert), and get results immediately -- no installation required.

## Features

- **Audit** -- check a .docx, .xlsx, .pptx, .md, .pdf, or .epub file against accessibility rules with Full, Quick, or Custom mode. Rules adapt automatically to each file format.
- **Fix** -- auto-fix compliance issues in Word documents and download the corrected file. Other formats receive a detailed audit with manual fix guidance.
- **Template** -- generate a pre-configured ACB-compliant Word template (.dotx)
- **Export** -- convert a .docx to accessible HTML (standalone ZIP or CMS fragment)
- **Convert** -- transform documents between formats via six conversion directions: Markdown (MarkItDown), HTML (Pandoc), Word (Pandoc), EPUB 3 (Pandoc), PDF (Pandoc + WeasyPrint), and EPUB/DAISY (DAISY Pipeline)
- **Guidelines** -- browse the full ACB Large Print specification and WCAG 2.2 supplement
- **About** -- project mission, organizations, standards, open source dependencies, and acknowledgments
- **Feedback** -- collect user feedback with SQLite storage and password-protected review

## Supported Formats

| Format | Audit | Auto-Fix | Template | Export | Convert |
|--------|-------|----------|----------|--------|---------|
| Word (.docx) | Full (30+ ACB + MSAC rules) | Yes | Yes (.dotx) | Yes (HTML) | To Markdown, To HTML, To EPUB 3 |
| Excel (.xlsx) | Full (MSAC rules: sheet names, table headers, merged cells, alt text, hidden content, color-only) | Planned | -- | -- | To Markdown |
| PowerPoint (.pptx) | Full (MSAC rules: slide titles, reading order, alt text, font sizes, speaker notes, charts) | Planned | -- | -- | To Markdown |
| Markdown (.md) | Basic (ACB emphasis, headings, images, lists) | Planned | -- | -- | To HTML, To Word, To EPUB 3, To PDF |
| PDF (.pdf) | Basic (page-level structure and text extraction) | Planned | -- | -- | To Markdown |
| HTML (.html) | -- | -- | -- | -- | To Word, To EPUB 3, To PDF |
| ePub (.epub) | Full (EPUB Accessibility 1.1: title, language, nav, headings, alt text, tables, links, metadata) | Planned | -- | -- | To Markdown, To HTML, To PDF, To DAISY 2.02, To DAISY 3 |

## Architecture

The web app is a thin Flask layer over the existing `acb_large_print` Python library. It calls the same public API that the CLI and GUI use -- zero modifications to the core library.

```
web/
  src/
    acb_large_print_web/
      app.py              Application factory (CSRF, rate limiting, logging)
      upload.py           File validation, temp directory management
      rules.py            Rule metadata helpers for templates
      wsgi.py             Gunicorn entry point
      routes/
        main.py           GET / landing page
        audit.py          GET/POST /audit
        fix.py            GET/POST /fix
        template.py       GET/POST /template
        export.py         GET/POST /export
        convert.py        GET/POST /convert
        guidelines.py     GET /guidelines
        about.py          GET /about
        feedback.py       GET/POST /feedback, GET /feedback/review
      templates/          Jinja2 HTML templates
      static/             CSS and favicon
  tests/
    test_app.py           28 tests (smoke, error, feedback, accessibility, integration)
  Dockerfile
  docker-compose.yml
  pyproject.toml
  requirements.txt
```

## Quick Start (Development)

```bash
cd web
pip install -e ".[dev]"
pip install -e "../desktop"

flask --app acb_large_print_web.app:create_app run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Running Tests

```bash
cd web
python -m pytest tests/ -v
```

## Docker

Build and run locally:

```bash
cd web
docker compose up --build
```

The app is served on port 8000. For production deployment with Caddy (auto-TLS), see [docs/deployment.md](../docs/deployment.md).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Random per-start | Flask session secret. Set a fixed value in production. |
| `FEEDBACK_PASSWORD` | (unset) | Set to enable `/feedback/review?key=<password>`. Disabled when unset. |
| `LOG_LEVEL` | `INFO` | Python logging level (DEBUG, INFO, WARNING, ERROR). |
| `MAX_CONTENT_LENGTH` | 500 MB | Maximum upload file size. |

## Security

- CSRF protection on all POST forms (Flask-WTF)
- Rate limiting: 120 requests/minute per IP (Flask-Limiter)
- Upload validation: .docx, .xlsx, .pptx, .md, .pdf extension whitelist, `secure_filename()`, path traversal prevention
- 500 MB upload size limit enforced by Flask before handlers run
- Temp files deleted in `finally` blocks -- guaranteed cleanup on success or exception
- Docker: non-root user, health check, tmpfs for temp files

## Accessibility (WCAG 2.2 AA)

- `lang="en"` on all pages
- Skip navigation link
- Landmark regions: header, nav, main, footer
- All form controls have associated labels
- Error messages linked via `aria-describedby` and `aria-invalid`
- Flash messages include text prefixes (Error/Success/Warning/Note) -- not color alone
- Severity badges, format pills, and format tags all have visible text labels -- color is supplementary
- All text and interactive-component contrast meets WCAG 2.2 AA thresholds
- Visible focus indicators (3px solid outline) on all interactive elements including nav links
- Native `<details>/<summary>` for contextual help (no JavaScript)
- `aria-current="page"` on active nav item
- ACB Large Print CSS applied to the tool itself
- Works without JavaScript enabled

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Web framework | Flask 3.x |
| WSGI server | Gunicorn 23.x |
| Python | 3.13 |
| Core library | acb_large_print (local) |
| Document conversion | MarkItDown (Microsoft) |
| CSRF | Flask-WTF |
| Rate limiting | Flask-Limiter |
| Feedback storage | SQLite (WAL mode) |
| Container | Docker + Compose |
| Reverse proxy | Caddy 2.x (production) |
