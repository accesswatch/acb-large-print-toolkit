"""Flask application factory."""

from __future__ import annotations

import logging
import os
import socket
from datetime import UTC, datetime
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFError, CSRFProtect

from .rules import get_help_urls_map, get_rules_by_category, get_rules_by_severity

csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120 per minute"],
    storage_uri="memory://",
)


def create_app(config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    # Resolve instance path: honour FLASK_INSTANCE_PATH env var so the
    # feedback SQLite database lands in the Docker volume (/app/instance)
    # instead of Flask's default which resolves to site-packages/instance/
    # (not writable by the container's non-root user).
    # Default: CWD-relative "instance/" -- in Docker (WORKDIR /app) this
    # resolves to /app/instance, which matches the compose volume mount.
    _instance_path = os.environ.get(
        "FLASK_INSTANCE_PATH",
        os.path.join(os.getcwd(), "instance"),
    )
    app = Flask(__name__, instance_path=_instance_path)
    app.url_map.strict_slashes = False

    # Defaults
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB
    secret = os.environ.get("SECRET_KEY", "")
    if not secret:
        secret = os.urandom(32).hex()
        app.logger.warning(
            "SECRET_KEY not set -- using random key. "
            "Sessions and CSRF tokens will not survive restarts."
        )
    app.config["SECRET_KEY"] = secret

    # Session timeout: default 4 hours for long document processing workflows
    # Users can adjust via SESSION_TIMEOUT_MINUTES env var
    timeout_minutes = int(os.environ.get("SESSION_TIMEOUT_MINUTES", "240"))
    app.config["PERMANENT_SESSION_LIFETIME"] = timeout_minutes * 60
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True

    if config:
        app.config.update(config)

    # Extensions
    csrf.init_app(app)
    limiter.init_app(app)

    # Logging
    _configure_logging(app)

    # Request timing (set before each request so after_request can compute duration)
    import time as _time

    @app.before_request
    def _record_request_start():
        from flask import g as _g
        _g._request_start = _time.monotonic()

    @app.after_request
    def _log_request(response):
        from flask import g as _g, request as _req
        duration_ms = round((_time.monotonic() - getattr(_g, '_request_start', _time.monotonic())) * 1000)
        # Skip noisy health poll logs unless they fail or are slow
        if _req.path == '/health' and response.status_code == 200 and duration_ms < 2000:
            return response
        app.logger.info(
            'REQUEST %s %s -> %s (%dms) ua=%s',
            _req.method,
            _req.full_path.rstrip('?'),
            response.status_code,
            duration_ms,
            (_req.user_agent.string or '')[:80],
        )
        return response

    # Make rule metadata available in all templates
    @app.context_processor
    def inject_rules():
        from importlib.metadata import version as pkg_version

        try:
            web_ver = pkg_version("acb-large-print-web")
        except Exception:
            web_ver = "1.0.0"
        try:
            desktop_ver = pkg_version("acb-large-print")
        except Exception:
            desktop_ver = "1.0.0"

        if web_ver == desktop_ver:
            release_ver = web_ver
        else:
            release_ver = f"web {web_ver} / desktop {desktop_ver}"
        return {
            "rules_by_severity": get_rules_by_severity(),
            "rules_by_category": get_rules_by_category(),
            "help_urls_map": get_help_urls_map(),
            "web_version": web_ver,
            "desktop_version": desktop_ver,
            "release_version": release_ver,
        }

    # Jinja2 filter: render lightweight Markdown to safe HTML for AI answers.
    # Covers the subset Ollama/Llama3 actually produces: headings, bold,
    # inline code, unordered/ordered lists, horizontal rules, and paragraphs.
    # Uses markupsafe (already a Flask dependency) for escaping.
    import re as _re
    from markupsafe import Markup, escape as _esc

    def _markdown_to_html(text: str) -> Markup:
        if not text:
            return Markup("")
        lines = text.splitlines()
        out: list[str] = []
        in_ul = in_ol = False
        ol_counter = 0

        def close_lists():
            nonlocal in_ul, in_ol, ol_counter
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if in_ol:
                out.append("</ol>")
                in_ol = False
                ol_counter = 0

        def inline(s: str) -> str:
            # Bold (**text** or __text__)
            s = _re.sub(r"\*\*(.+?)\*\*", lambda m: f"<strong>{_esc(m.group(1))}</strong>", str(_esc(s)))
            s = _re.sub(r"__(.+?)__", lambda m: f"<strong>{m.group(1)}</strong>", s)
            # Inline code
            s = _re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", s)
            return s

        for line in lines:
            raw = line.rstrip()
            # ATX headings
            m = _re.match(r"^(#{1,6})\s+(.*)", raw)
            if m:
                close_lists()
                level = len(m.group(1))
                out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
                continue
            # Horizontal rule
            if _re.match(r"^[-*_]{3,}\s*$", raw):
                close_lists()
                out.append("<hr>")
                continue
            # Unordered list item
            m = _re.match(r"^[-*+]\s+(.*)", raw)
            if m:
                if in_ol:
                    out.append("</ol>")
                    in_ol = False
                    ol_counter = 0
                if not in_ul:
                    out.append("<ul>")
                    in_ul = True
                out.append(f"<li>{inline(m.group(1))}</li>")
                continue
            # Ordered list item
            m = _re.match(r"^\d+\.\s+(.*)", raw)
            if m:
                if in_ul:
                    out.append("</ul>")
                    in_ul = False
                if not in_ol:
                    out.append("<ol>")
                    in_ol = True
                out.append(f"<li>{inline(m.group(1))}</li>")
                continue
            # Blank line
            if not raw:
                close_lists()
                out.append("")
                continue
            # Normal paragraph line
            close_lists()
            out.append(f"<p>{inline(raw)}</p>")

        close_lists()
        return Markup("\n".join(out))

    app.jinja_env.filters["markdown"] = _markdown_to_html

    # Register blueprints
    from .routes.main import main_bp
    from .routes.audit import audit_bp
    from .routes.fix import fix_bp
    from .routes.template import template_bp
    from .routes.export import export_bp
    from .routes.guidelines import guidelines_bp
    from .routes.feedback import feedback_bp
    from .routes.about import about_bp
    from .routes.convert import convert_bp
    from .routes.docs_pages import guide_bp, changelog_bp, prd_bp, faq_bp
    from .routes.settings import settings_bp
    from .routes.privacy import privacy_bp
    from .routes.whisperer import whisperer_bp
    from .routes.consent import consent_bp, consent_required
    from .routes.process import process_bp
    from .routes.chat import chat_bp
    from .routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(consent_bp, url_prefix="/consent")
    app.register_blueprint(process_bp, url_prefix="/process")
    app.register_blueprint(audit_bp, url_prefix="/audit")
    app.register_blueprint(fix_bp, url_prefix="/fix")
    app.register_blueprint(template_bp, url_prefix="/template")
    app.register_blueprint(export_bp, url_prefix="/export")
    app.register_blueprint(convert_bp, url_prefix="/convert")
    app.register_blueprint(whisperer_bp, url_prefix="/whisperer")
    app.register_blueprint(guidelines_bp, url_prefix="/guidelines")
    app.register_blueprint(guide_bp, url_prefix="/guide")
    app.register_blueprint(changelog_bp, url_prefix="/changelog")
    app.register_blueprint(prd_bp, url_prefix="/prd")
    app.register_blueprint(faq_bp, url_prefix="/faq")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(feedback_bp, url_prefix="/feedback")
    app.register_blueprint(about_bp, url_prefix="/about")
    app.register_blueprint(privacy_bp, url_prefix="/privacy")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Startup ready log -- emitted once per worker process launch
    try:
        from importlib.metadata import version as _pkg_version
        _web_ver = _pkg_version("acb-large-print-web")
        _core_ver = _pkg_version("acb-large-print")
    except Exception:
        _web_ver = _core_ver = "unknown"
    app.logger.info(
        "GLOW startup: web=%s core=%s maintenance=%s log_level=%s",
        _web_ver,
        _core_ver,
        os.environ.get("MAINTENANCE_MODE", "0"),
        os.environ.get("LOG_LEVEL", "INFO"),
    )

    # Maintenance mode: gate all requests except /health when MAINTENANCE_MODE=1
    # This allows safe deployment-time downtime while keeping health checks working
    @app.before_request
    def check_maintenance_mode():
        from flask import request as req
        maintenance_mode = os.environ.get("MAINTENANCE_MODE", "0") == "1"
        if maintenance_mode and req.path != "/health":
            return render_template("maintenance.html"), 503

    # Consent gate: redirect first-time visitors to the agreement page.
    # Skipped in test mode so existing tests don't need consent cookies.
    @app.before_request
    def require_consent():
        if app.testing:
            return None
        from flask import redirect, request as req, url_for as _url_for
        if consent_required(req):
            return redirect(
                _url_for("consent.consent_form", next=req.full_path.rstrip("?"))
            )

    # Health check
    @app.route("/health")
    def health():
        from .gating import get_capacity_metrics
        from acb_large_print.converter import whisper_available
        import time as _htime
        _hstart = _htime.monotonic()

        pipeline_url = os.environ.get("PIPELINE_URL", "http://pipeline:8181/ws")
        ollama_url = os.environ.get("OLLAMA_HOST", "http://ollama:11434")

        pipeline_status = _check_tcp_endpoint(pipeline_url)
        ollama_status = _check_http_endpoint(f"{ollama_url.rstrip('/')}/api/tags")
        ollama_models = _get_ollama_models(ollama_url)
        capacity = get_capacity_metrics()

        services = {
            "web": {"status": "ok", "detail": "service responding"},
            "pipeline": pipeline_status,
            "ollama": ollama_status,
        }

        has_llama3 = any("llama3" in model for model in ollama_models)
        has_llava = any("llava" in model for model in ollama_models)

        whisper_ready = whisper_available()

        readiness = {
            "chat": {
                "status": "ready" if has_llama3 else "not-ready",
                "model_required": "llama3",
                "model_present": has_llama3,
            },
            "vision": {
                "status": "ready" if has_llava else "not-ready",
                "model_required": "llava",
                "model_present": has_llava,
            },
            "whisperer": {
                "status": "ready" if whisper_ready else "not-ready",
                "dependency_required": "faster-whisper",
                "dependency_present": whisper_ready,
            },
        }

        services_ok = all(service.get("status") == "ok" for service in services.values())
        features_ready = all(item.get("status") == "ready" for item in readiness.values())
        all_ok = services_ok and features_ready

        _hduration_ms = round((_htime.monotonic() - _hstart) * 1000)
        app.logger.info(
            "HEALTH status=%s services=%s readiness=%s models=%s duration_ms=%d",
            "ok" if all_ok else "degraded",
            {k: v.get("status") for k, v in services.items()},
            {k: v.get("status") for k, v in readiness.items()},
            ollama_models,
            _hduration_ms,
        )

        return (
            jsonify(
                {
                    "status": "ok" if all_ok else "degraded",
                    "services": services,
                    "readiness": readiness,
                    "models": {
                        "ollama": ollama_models,
                    },
                    "capacity": capacity,
                    "timestamp_utc": datetime.now(UTC).isoformat(),
                }
            ),
            200,
        )

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return _render_error(
            "Session Expired",
            "Your form session has expired. Please go back, refresh the page, "
            "and try again.",
            400,
        )

    # Error handlers
    @app.errorhandler(413)
    def too_large(e):
        return _render_error(
            "File Too Large",
            "The uploaded file exceeds the 500 MB size limit. "
            "Please upload a smaller file.",
            413,
        )

    @app.errorhandler(404)
    def not_found(e):
        return _render_error(
            "Page Not Found",
            "The page you requested does not exist.",
            404,
        )

    @app.errorhandler(403)
    def forbidden(e):
        return _render_error(
            "Access Denied",
            "You do not have permission to access this page.",
            403,
        )

    @app.errorhandler(500)
    def server_error(e):
        return _render_error(
            "Server Error",
            "Something went wrong while processing your request. " "Please try again.",
            500,
        )

    # Cleanup stale uploads on startup
    @app.before_request
    def cleanup_stale_uploads():
        """Clean up old temporary uploads on each request (lightweight, once per min)."""
        from . import upload
        import time
        
        # Store last cleanup time in app config
        now = time.time()
        last_cleanup = app.config.get("_last_cleanup", 0)
        
        # Run cleanup once per minute (3600 seconds = 1 hour between full scans)
        if now - last_cleanup > 60:
            max_age = int(os.environ.get("UPLOAD_MAX_AGE_HOURS", "1"))
            upload.cleanup_stale_uploads(max_age_hours=max_age)
            app.config["_last_cleanup"] = now

    return app


def _configure_logging(app: Flask) -> None:
    """Set up structured logging."""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Also configure the package-level logger
    pkg_logger = logging.getLogger("acb_large_print_web")
    pkg_logger.handlers.clear()
    pkg_logger.addHandler(handler)
    pkg_logger.setLevel(getattr(logging, log_level, logging.INFO))


def _render_error(title: str, message: str, code: int):
    """Render an error page."""
    from flask import render_template

    return render_template("error.html", title=title, message=message), code


def _check_tcp_endpoint(url: str, timeout: float = 2.0) -> dict[str, str | int]:
    """Check host:port reachability for internal services."""
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port

    if not host:
        return {"status": "down", "error": f"invalid URL: {url}"}

    if port is None:
        port = 443 if parsed.scheme == "https" else 80

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"status": "ok", "host": host, "port": port}
    except OSError as exc:
        return {"status": "down", "host": host, "port": port, "error": str(exc)}


def _check_http_endpoint(url: str, timeout: float = 2.0) -> dict[str, str | int]:
    """Check HTTP endpoint status code for internal services."""
    from urllib.request import Request, urlopen

    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310
            code = getattr(resp, "status", 200)
            if 200 <= code < 400:
                return {"status": "ok", "url": url, "http_status": code}
            return {"status": "down", "url": url, "http_status": code}
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        return {"status": "down", "url": url, "error": str(exc)}


def _get_ollama_models(ollama_url: str, timeout: float = 2.0) -> list[str]:
    """Return a normalized list of loaded Ollama model names from /api/tags."""
    from urllib.request import Request, urlopen
    import json

    url = f"{ollama_url.rstrip('/')}/api/tags"
    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310
            body = resp.read().decode("utf-8")
            payload = json.loads(body)
            models = payload.get("models", [])
            return [str(m.get("name", "")).lower() for m in models if m.get("name")]
    except Exception:
        return []
