# ACB Large Print Web Application

A Flask web application that provides browser-based access to the ACB Large Print Tool. Upload a Word document, choose an operation (audit, fix, template, export), and get results immediately -- no installation required.

## Features

- **Audit** -- check a .docx file against 30+ ACB Large Print rules with Full, Quick, or Custom mode
- **Fix** -- auto-fix compliance issues and download the corrected document
- **Template** -- generate a pre-configured ACB-compliant Word template (.dotx)
- **Export** -- convert a .docx to accessible HTML (standalone ZIP or CMS fragment)
- **Guidelines** -- browse the full ACB Large Print specification and WCAG 2.2 supplement
- **Feedback** -- collect user feedback with SQLite storage and password-protected review

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
        guidelines.py     GET /guidelines
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
pip install -e "../word-addon"

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
| `MAX_CONTENT_LENGTH` | 16 MB | Maximum upload file size. |

## Security

- CSRF protection on all POST forms (Flask-WTF)
- Rate limiting: 120 requests/minute per IP (Flask-Limiter)
- Upload validation: .docx extension whitelist, `secure_filename()`, path traversal prevention
- 16 MB upload size limit enforced by Flask before handlers run
- Temp files deleted in `finally` blocks -- guaranteed cleanup on success or exception
- Docker: non-root user, health check, tmpfs for temp files

## Accessibility (WCAG 2.2 AA)

- `lang="en"` on all pages
- Skip navigation link
- Landmark regions: header, nav, main, footer
- All form controls have associated labels
- Error messages linked via `aria-describedby` and `aria-invalid`
- Native `<details>/<summary>` for contextual help (no JavaScript)
- ACB Large Print CSS applied to the tool itself
- Works without JavaScript enabled

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Web framework | Flask 3.x |
| WSGI server | Gunicorn 23.x |
| Python | 3.13 |
| Core library | acb_large_print (local) |
| CSRF | Flask-WTF |
| Rate limiting | Flask-Limiter |
| Feedback storage | SQLite (WAL mode) |
| Container | Docker + Compose |
| Reverse proxy | Caddy 2.x (production) |
