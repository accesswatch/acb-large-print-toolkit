"""Flask application factory."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

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
        from .ai_features import get_all_flags as _get_ai_flags

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
        ctx = {
            "rules_by_severity": get_rules_by_severity(),
            "rules_by_category": get_rules_by_category(),
            "help_urls_map": get_help_urls_map(),
            "web_version": web_ver,
            "desktop_version": desktop_ver,
            "release_version": release_ver,
        }
        ctx.update(_get_ai_flags())
        return ctx

    # Jinja2 filter: render lightweight Markdown to safe HTML for AI answers.
    # Covers the subset typically produced: headings, bold,
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

    # Seed defaults for feature flags on first startup (if no persisted flags exist).
    try:
        from . import feature_flags as _feature_flags
        from pathlib import Path as _Path

        ff_path = _Path(app.instance_path) / "feature_flags.json"
        if not ff_path.exists():
            with app.app_context():
                app.logger.info("Seeding default feature flags into instance/feature_flags.json")
                _feature_flags.reset_defaults()
    except Exception:
        app.logger.debug("Failed to seed default feature flags (continuing)")

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
        from .ai_gateway import (
            get_admin_stats,
            is_ai_configured,
            is_budget_exhausted,
        )
        import time as _htime
        _hstart = _htime.monotonic()

        capacity = get_capacity_metrics()
        admin_stats = get_admin_stats()
        ai_configured = is_ai_configured()
        budget_ok = not is_budget_exhausted()

        # Live reachability probes (non-blocking, short timeout)
        openrouter_probe = _probe_openrouter() if ai_configured else {
            "status": "not-configured",
            "detail": "OPENROUTER_API_KEY not set -- AI features disabled",
        }
        whisper_probe = _probe_whisper() if ai_configured else {
            "status": "not-configured",
            "detail": "OPENROUTER_API_KEY not set -- BITS Whisperer disabled",
        }

        services = {
            "web": {"status": "ok", "detail": "service responding"},
            "openrouter": openrouter_probe,
            "whisper": whisper_probe,
        }

        readiness = {
            "chat": {
                "status": "ready" if ai_configured and budget_ok and openrouter_probe["status"] == "ok" else "not-ready",
                "provider": "openrouter",
                "key_set": ai_configured,
                "reachable": openrouter_probe["status"] == "ok",
                "budget_ok": budget_ok,
            },
            "vision": {
                "status": "ready" if ai_configured and budget_ok and openrouter_probe["status"] == "ok" else "not-ready",
                "provider": "openrouter",
                "key_set": ai_configured,
                "reachable": openrouter_probe["status"] == "ok",
                "budget_ok": budget_ok,
            },
            "whisperer": {
                "status": "ready" if ai_configured and whisper_probe["status"] == "ok" else "not-ready",
                "provider": "openrouter",
                "key_set": ai_configured,
                "reachable": whisper_probe["status"] == "ok",
            },
            "budget": {
                "status": "ok" if budget_ok else "exhausted",
                "monthly_budget_usd": admin_stats.get("budget_usd", 20.0),
                "monthly_spend_usd": admin_stats.get("monthly_spend", 0.0),
                "pct_used": round(
                    min(100.0, admin_stats.get("monthly_spend", 0.0)
                        / max(admin_stats.get("budget_usd", 20.0), 0.01) * 100),
                    1,
                ),
            },
        }

        # Overall status: web always ok; degrade only if a configured provider
        # is unreachable or budget is gone
        provider_ok = (
            (not ai_configured or openrouter_probe["status"] == "ok")
        )
        all_ok = provider_ok and budget_ok

        _hduration_ms = round((_htime.monotonic() - _hstart) * 1000)
        app.logger.info(
            "HEALTH status=%s openrouter=%s whisper=%s budget_pct=%.1f%% duration_ms=%d",
            "ok" if all_ok else "degraded",
            openrouter_probe["status"],
            whisper_probe["status"],
            readiness["budget"]["pct_used"],
            _hduration_ms,
        )

        return (
            jsonify(
                {
                    "status": "ok" if all_ok else "degraded",
                    "services": services,
                    "readiness": readiness,
                    "models": {
                        "chat_default": admin_stats.get("default_model", "n/a"),
                        "chat_fallback": admin_stats.get("fallback_model", "n/a"),
                        "vision": admin_stats.get("vision_model", "n/a"),
                        # audio_path_active reflects which path GLOW tries first:
                        # input_audio (gpt-audio-mini) is the primary; direct
                        # (whisper-large-v3) is only used if primary fails.
                        "whisper_fallback": admin_stats.get("whisper_model", "openai/whisper-large-v3"),
                        "audio_primary": "openai/gpt-audio-mini",
                        "audio_path_active": "input_audio",
                    },
                    "capacity": capacity,
                    "timestamp_utc": datetime.now(UTC).isoformat(),
                    "duration_ms": _hduration_ms,
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


def _probe_openrouter(timeout: float = 4.0) -> dict[str, str]:
    """Probe OpenRouter /models to verify the key is valid and the service is reachable.

    Returns a status dict with keys 'status' ("ok" | "unreachable" | "auth-error")
    and 'detail' for display in the health response.
    We hit /models (a cheap, read-only endpoint) with a short timeout.
    No content is sent -- this is purely a connectivity + auth check.
    """
    from .credentials import get_openrouter_api_key
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

    key = get_openrouter_api_key()
    if not key:
        return {"status": "not-configured", "detail": "OPENROUTER_API_KEY not set"}

    req = Request(
        "https://openrouter.ai/api/v1/models",
        headers={
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://glow.bits-acb.org",
            "X-Title": "GLOW Health Check",
        },
        method="GET",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310
            code = getattr(resp, "status", 200)
            if 200 <= code < 300:
                return {"status": "ok", "detail": f"reachable (HTTP {code})"}
            return {"status": "degraded", "detail": f"unexpected HTTP {code}"}
    except HTTPError as exc:
        if exc.code in (401, 403):
            return {"status": "auth-error", "detail": f"API key rejected (HTTP {exc.code})"}
        return {"status": "degraded", "detail": f"HTTP {exc.code} from OpenRouter"}
    except URLError as exc:
        return {"status": "unreachable", "detail": f"Network error: {exc.reason}"}
    except Exception as exc:  # pragma: no cover
        return {"status": "unreachable", "detail": str(exc)}


def _probe_whisper(timeout: float = 4.0) -> dict[str, str]:
    """Whisperer uses the same OpenRouter key -- delegate to the OpenRouter probe."""
    return _probe_openrouter(timeout=timeout)
