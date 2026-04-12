"""Flask application factory."""

from __future__ import annotations

import logging
import os

from flask import Flask, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

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

    # Defaults
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    secret = os.environ.get("SECRET_KEY", "")
    if not secret:
        secret = os.urandom(32).hex()
        app.logger.warning(
            "SECRET_KEY not set -- using random key. "
            "Sessions and CSRF tokens will not survive restarts."
        )
    app.config["SECRET_KEY"] = secret

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
        return {
            "rules_by_severity": get_rules_by_severity(),
            "rules_by_category": get_rules_by_category(),
            "help_urls_map": get_help_urls_map(),
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

    app.register_blueprint(main_bp)
    app.register_blueprint(audit_bp, url_prefix="/audit")
    app.register_blueprint(fix_bp, url_prefix="/fix")
    app.register_blueprint(template_bp, url_prefix="/template")
    app.register_blueprint(export_bp, url_prefix="/export")
    app.register_blueprint(convert_bp, url_prefix="/convert")
    app.register_blueprint(guidelines_bp, url_prefix="/guidelines")
    app.register_blueprint(feedback_bp, url_prefix="/feedback")
    app.register_blueprint(about_bp, url_prefix="/about")

    # Health check
    @app.route("/health")
    def health():
        return "ok", 200

    # Error handlers
    @app.errorhandler(413)
    def too_large(e):
        return _render_error(
            "File Too Large",
            "The uploaded file exceeds the 16 MB size limit. "
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
            "Something went wrong while processing your request. "
            "Please try again.",
            500,
        )

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
