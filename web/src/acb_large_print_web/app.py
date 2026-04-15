"""Flask application factory."""

from __future__ import annotations

import logging
import os
import socket
from datetime import UTC, datetime
from urllib.parse import urlparse

from flask import Flask, jsonify
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
    app = Flask(__name__)
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
    from .routes.guide import guide_bp
    from .routes.changelog import changelog_bp
    from .routes.settings import settings_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(audit_bp, url_prefix="/audit")
    app.register_blueprint(fix_bp, url_prefix="/fix")
    app.register_blueprint(template_bp, url_prefix="/template")
    app.register_blueprint(export_bp, url_prefix="/export")
    app.register_blueprint(convert_bp, url_prefix="/convert")
    app.register_blueprint(guidelines_bp, url_prefix="/guidelines")
    app.register_blueprint(guide_bp, url_prefix="/guide")
    app.register_blueprint(changelog_bp, url_prefix="/changelog")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(feedback_bp, url_prefix="/feedback")
    app.register_blueprint(about_bp, url_prefix="/about")

    # Health check
    @app.route("/health")
    def health():
        pipeline_url = os.environ.get("PIPELINE_URL", "http://pipeline:8181/ws")
        ollama_url = os.environ.get("OLLAMA_HOST", "http://ollama:11434")

        pipeline_status = _check_tcp_endpoint(pipeline_url)
        ollama_status = _check_http_endpoint(f"{ollama_url.rstrip('/')}/api/tags")

        services = {
            "web": {"status": "ok", "detail": "service responding"},
            "pipeline": pipeline_status,
            "ollama": ollama_status,
        }
        all_ok = all(service.get("status") == "ok" for service in services.values())

        return (
            jsonify(
                {
                    "status": "ok" if all_ok else "degraded",
                    "services": services,
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
            max_age = int(os.environ.get("UPLOAD_MAX_AGE_HOURS", "24"))
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
