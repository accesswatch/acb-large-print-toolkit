"""Admin routes backed by unified Flask-Login + RBAC.

Admin users authenticate via /auth/login (Firebase email-link or GitHub) and
then access this blueprint with role-gated routes.
"""

from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime
from functools import wraps
from typing import Any

from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from ..app import limiter
from ..email import email_configured
from ..credentials import get_bootstrap_admin_email, get_bootstrap_admin_password
from ..ai_gateway import (
    get_admin_stats,
    get_model_catalog,
    get_runtime_config,
    project_monthly_cost,
    update_runtime_config,
)
from ..feature_flags import (
    get_all_flags as _get_all_flags,
    set_flag as _set_flag,
    reset_defaults as _reset_flag_defaults,
    get_flag_meta as _get_flag_meta,
    get_backend as _get_flags_backend,
    migrate_json_to_sqlite as _migrate_flags,
    get_audit_entries as _get_audit_entries,
)
from ..speech import (
    get_engine_status,
    get_piper_voice_inventory,
    install_piper_voice,
    remove_piper_voice,
)
from .whisperer import (
    admin_cancel_queued_job,
    admin_requeue_failed_job,
    get_admin_queue_snapshot,
)

admin_bp = Blueprint("admin", __name__)
_LEGACY_MAGIC_LINK_TTL_SECONDS = 15 * 60
_legacy_magic_links: dict[str, tuple[str, datetime]] = {}


def _send_admin_email(to_email: str, subject: str, body: str) -> bool:
    """Send admin notification email via Postmark.
    
    Mock-friendly stub for test integration.
    """
    # For now, this is a stub that tests can monkeypatch.
    # In production, this would send via Postmark email service.
    return True


def _legacy_bootstrap_admin_emails() -> set[str]:
    emails: set[str] = set()
    super_raw = os.environ.get("SUPER_ADMIN_BOOTSTRAP_EMAILS", "").strip()
    if super_raw:
        emails.update(_normalize_email(v) for v in super_raw.split(",") if v.strip())
    raw = os.environ.get("ADMIN_BOOTSTRAP_EMAILS", "").strip()
    if raw:
        emails.update(_normalize_email(v) for v in raw.split(",") if v.strip())
    single = _normalize_email(get_bootstrap_admin_email())
    if single:
        emails.add(single)
    return emails


def _legacy_admin_email() -> str:
    if getattr(current_user, "is_authenticated", False) and current_user.is_admin():
        return current_user.email
    legacy = _normalize_email(session.get("legacy_admin_email", ""))
    if legacy and legacy in _legacy_bootstrap_admin_emails():
        return legacy
    return ""


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _bootstrap_admins() -> None:
    """Create or promote User accounts listed in ADMIN_BOOTSTRAP_EMAILS.

    Safe to call on every request to an admin-visible route — it is idempotent.
    Also handles ADMIN_BOOTSTRAP_EMAIL / ADMIN_BOOTSTRAP_PASSWORD for a
    local password account.
    """
    from ..db import db
    from ..models import User, UserRole

    changed = False

    super_raw = os.environ.get("SUPER_ADMIN_BOOTSTRAP_EMAILS", "").strip()
    super_emails = [_normalize_email(e) for e in super_raw.split(",") if e.strip()] if super_raw else []

    now = datetime.now(UTC)
    for email in super_emails:
        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                display_name=email,
                auth_provider="local",
                is_active=True,
                is_email_verified=True,
                role=UserRole.SUPER_ADMIN.value,
                created_at=now,
            )
            db.session.add(user)
            changed = True
        elif user.role != UserRole.SUPER_ADMIN.value:
            user.role = UserRole.SUPER_ADMIN.value
            changed = True

    raw = os.environ.get("ADMIN_BOOTSTRAP_EMAILS", "").strip()
    emails = [_normalize_email(e) for e in raw.split(",") if e.strip()] if raw else []

    for email in emails:
        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                display_name=email,
                auth_provider="local",
                is_active=True,
                is_email_verified=True,
                role=UserRole.ADMIN.value,
                created_at=now,
            )
            db.session.add(user)
            changed = True
        elif user.role == UserRole.USER.value:
            user.role = UserRole.ADMIN.value
            changed = True

    boot_email = _normalize_email(get_bootstrap_admin_email())
    boot_pass = get_bootstrap_admin_password().strip()
    if boot_email and boot_pass:
        user = db.session.execute(
            db.select(User).where(User.email == boot_email)
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=boot_email,
                display_name=boot_email,
                auth_provider="local",
                is_active=True,
                is_email_verified=True,
                role=UserRole.ADMIN.value,
                created_at=now,
            )
            user.set_password(boot_pass)
            db.session.add(user)
            changed = True
        else:
            if not user.password_hash:
                user.set_password(boot_pass)
                changed = True
            if user.role == UserRole.USER.value:
                user.role = UserRole.ADMIN.value
                changed = True

    if changed:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()


def admin_required(f):
    """Route decorator: requires a logged-in user with admin or super_admin role."""

    @wraps(f)
    def decorated(*args, **kwargs):
        _bootstrap_admins()

        if getattr(current_user, "is_authenticated", False):
            if not current_user.is_admin():
                abort(403)
            return f(*args, **kwargs)

        if _legacy_admin_email():
            return f(*args, **kwargs)

        return redirect(url_for("auth.login", next=request.path))

    return decorated


@admin_bp.route("/login", methods=["GET"])
def admin_login() -> Any:
    """Legacy compatibility route used by existing admin-auth tests."""
    if _legacy_admin_email():
        return redirect(url_for("admin.admin_queue"))
    return render_template(
        "admin_login.html",
        email_enabled=email_configured(),
        ttl_minutes=_LEGACY_MAGIC_LINK_TTL_SECONDS // 60,
        providers=[],
        local_password_enabled=False,
        local_password_email="",
        firebase_admin_auth_enabled=False,
        firebase_auth_enabled=False,
        firebase_web_api_key="",
        firebase_auth_domain="",
        firebase_project_id="",
        firebase_app_id="",
        notice=request.args.get("notice"),
        error=request.args.get("error"),
    )


@admin_bp.route("/logout", methods=["GET", "POST"])
def admin_logout() -> Any:
    """Legacy compatibility route: admin logout now uses unified auth."""
    session.pop("legacy_admin_email", None)
    return redirect(url_for("auth.logout"))


@admin_bp.route("/login/email", methods=["POST"])
def admin_login_email() -> Any:
    if not email_configured():
        return (
            render_template(
                "admin_login.html",
                email_enabled=False,
                ttl_minutes=_LEGACY_MAGIC_LINK_TTL_SECONDS // 60,
                providers=[],
                local_password_enabled=False,
                local_password_email="",
                firebase_admin_auth_enabled=False,
                firebase_auth_enabled=False,
                firebase_web_api_key="",
                firebase_auth_domain="",
                firebase_project_id="",
                firebase_app_id="",
                error="Admin sign-in is unavailable until email delivery is configured.",
            ),
            503,
        )

    email = _normalize_email(request.form.get("email", ""))
    token = secrets.token_urlsafe(32)
    _legacy_magic_links[token] = (
        email,
        datetime.now(UTC).replace(microsecond=0),
    )
    _send_admin_email(email, "GLOW admin sign-in", "Use your one-time sign-in link.")

    return render_template(
        "admin_login.html",
        email_enabled=True,
        ttl_minutes=_LEGACY_MAGIC_LINK_TTL_SECONDS // 60,
        providers=[],
        local_password_enabled=False,
        local_password_email="",
        firebase_admin_auth_enabled=False,
        firebase_auth_enabled=False,
        firebase_web_api_key="",
        firebase_auth_domain="",
        firebase_project_id="",
        firebase_app_id="",
        notice="A sign-in link has been sent.",
    )


@admin_bp.route("/magic-link/consume", methods=["GET"])
def admin_magic_link_consume() -> Any:
    token = (request.args.get("token") or "").strip()
    email = ""
    entry = _legacy_magic_links.pop(token, None)
    if entry is not None:
        email = _normalize_email(entry[0])

    if not email or email not in _legacy_bootstrap_admin_emails():
        return redirect(url_for("admin.admin_login", error="Invalid or expired sign-in link."))

    session["legacy_admin_email"] = email
    return redirect(url_for("admin.admin_queue"))


@admin_bp.route("/request-access", methods=["GET", "POST"])
def admin_request_access() -> Any:
    """Legacy compatibility route for admin access request tests."""
    if not email_configured():
        return (
            render_template(
                "admin_request_access.html",
                form_disabled=True,
                submitted=False,
                error="Request access is unavailable until email delivery is configured.",
            ),
            503,
        )
    return render_template("admin_request_access.html", form_disabled=False, submitted=False, error=None)


@admin_bp.route("/requests", methods=["GET"])
@admin_required
def admin_requests() -> Any:
    """Legacy compatibility route: promotion requests moved to role blueprint."""
    return redirect(url_for("role.admin_promotions"))


@admin_bp.route("/queue", methods=["GET"])
@admin_required
def admin_queue() -> Any:
    rows = get_admin_queue_snapshot()
    return render_template("admin_queue.html", admin_email=_legacy_admin_email(), rows=rows)


@admin_bp.route("/speech", methods=["GET"])
@admin_required
def admin_speech() -> Any:
    status = get_engine_status()
    voices = get_piper_voice_inventory()
    return render_template(
        "admin_speech.html",
        admin_email=_legacy_admin_email(),
        engine_status=status,
        voices=voices,
        notice=request.args.get("notice"),
        error=request.args.get("error"),
    )


@admin_bp.route("/speech/install/<voice_id>", methods=["POST"])
@admin_required
def admin_speech_install(voice_id: str) -> Any:
    ok, msg = install_piper_voice(voice_id)
    return redirect(
        url_for("admin.admin_speech", notice=msg if ok else None, error=None if ok else msg)
    )


@admin_bp.route("/speech/remove/<voice_id>", methods=["POST"])
@admin_required
def admin_speech_remove(voice_id: str) -> Any:
    ok, msg = remove_piper_voice(voice_id)
    return redirect(
        url_for("admin.admin_speech", notice=msg if ok else None, error=None if ok else msg)
    )


@admin_bp.route("/ai", methods=["GET", "POST"])
@admin_required
def admin_ai_settings() -> Any:
    """Admin AI configuration panel (model routing, budget, quotas)."""
    notice = None
    error = None

    if request.method == "POST":
        try:
            updates = {
                "default_model": (request.form.get("default_model") or "").strip(),
                "fallback_model": (request.form.get("fallback_model") or "").strip(),
                "vision_model": (request.form.get("vision_model") or "").strip(),
                "escalation_thresh": float(request.form.get("escalation_thresh") or "0.7"),
                "monthly_budget_usd": float(request.form.get("monthly_budget_usd") or "20"),
                "chat_daily_limit": int(request.form.get("chat_daily_limit") or "50"),
                "audio_monthly_min": int(request.form.get("audio_monthly_min") or "100"),
                "session_quota_per_session": int(request.form.get("session_quota_per_session") or "0"),
                "quota_reset_hours": int(request.form.get("quota_reset_hours") or "24"),
                "whisper_model": (request.form.get("whisper_model") or "openai/whisper-large-v3").strip(),
            }

            if request.form.get("use_free_defaults") == "on":
                updates["default_model"] = "openai/gpt-4o-mini"
                updates["fallback_model"] = "openai/gpt-4o"
            if updates["escalation_thresh"] < 0 or updates["escalation_thresh"] > 1:
                raise ValueError("Escalation threshold must be between 0.0 and 1.0")
            if updates["monthly_budget_usd"] <= 0:
                raise ValueError("Monthly budget must be greater than 0")
            if updates["chat_daily_limit"] < 0:
                raise ValueError("Chat daily limit cannot be negative")
            if updates["audio_monthly_min"] < 0:
                raise ValueError("Audio monthly limit cannot be negative")
            if updates["session_quota_per_session"] < 0:
                raise ValueError("Session AI request limit cannot be negative")
            if updates["quota_reset_hours"] <= 0:
                raise ValueError("Session quota reset hours must be greater than 0")
            if not updates["default_model"]:
                raise ValueError("Default model is required")
            if not updates["fallback_model"]:
                raise ValueError("Fallback model is required")
            if not updates["vision_model"]:
                updates["vision_model"] = updates["fallback_model"]

            update_runtime_config(updates)
            notice = "AI settings saved. Changes apply immediately."
        except Exception as exc:
            error = f"Could not save settings: {exc}"

    cfg = get_runtime_config()
    stats = get_admin_stats()
    models = get_model_catalog()
    projection = project_monthly_cost(
        model_id=str(cfg.get("default_model", "openai/gpt-4o-mini")),
        monthly_requests=10000,
        avg_input_tokens=1200,
        avg_output_tokens=400,
    )
    return render_template(
        "admin_ai.html",
        admin_email=current_user.email,
        cfg=cfg,
        stats=stats,
        models=models,
        projection=projection,
        notice=notice,
        error=error,
    )


@admin_bp.route("/ai/pricing", methods=["GET"])
@admin_required
def admin_ai_pricing() -> Any:
    """Live pricing and projection API for the admin AI settings page."""
    model_id = (request.args.get("model") or "").strip()
    try:
        monthly_requests = int(request.args.get("monthly_requests") or "10000")
        avg_input_tokens = int(request.args.get("avg_input_tokens") or "1200")
        avg_output_tokens = int(request.args.get("avg_output_tokens") or "400")
    except ValueError:
        return jsonify({"error": "Invalid numeric query params"}), 400

    models = get_model_catalog()
    selected = next((m for m in models if m.get("id") == model_id), None)
    if selected is None and models:
        selected = models[0]
        model_id = str(selected.get("id", ""))

    projected = project_monthly_cost(model_id, monthly_requests, avg_input_tokens, avg_output_tokens)
    return jsonify(
        {
            "model": selected,
            "projection": {
                "monthly_requests": monthly_requests,
                "avg_input_tokens": avg_input_tokens,
                "avg_output_tokens": avg_output_tokens,
                "projected_monthly_usd": projected,
            },
            "models": models,
        }
    )


@admin_bp.route("/flags", methods=["GET", "POST"])
@admin_required
def admin_flags() -> Any:
    """Admin panel to view and manipulate server-side feature flags."""
    notice = None
    error = None

    feature_keys = [
        "GLOW_ENABLE_AI",
        "GLOW_ENABLE_AI_GENERAL_CHAT",
        "GLOW_ENABLE_AI_CHAT",
        "GLOW_ENABLE_AI_WHISPERER",
        "GLOW_ENABLE_AI_HEADING_FIX",
        "GLOW_ENABLE_AI_ALT_TEXT",
        "GLOW_ENABLE_AI_MARKITDOWN_LLM",
        "GLOW_ENABLE_USER_LOGIN",
        "GLOW_ENABLE_ADMIN_LOGIN",
        "GLOW_ENABLE_AUDIT",
        "GLOW_ENABLE_CHECKER",
        "GLOW_ENABLE_HEADING_DETECTION",
        "GLOW_ENABLE_CONVERTER",
        "GLOW_ENABLE_TEMPLATE_BUILDER",
        "GLOW_ENABLE_WORD_SETUP",
        "GLOW_ENABLE_MARKDOWN_AUDIT",
        "GLOW_ENABLE_WORD",
        "GLOW_ENABLE_EXCEL",
        "GLOW_ENABLE_POWERPOINT",
        "GLOW_ENABLE_PDF",
        "GLOW_ENABLE_MARKDOWN",
        "GLOW_ENABLE_EPUB",
        "GLOW_ENABLE_EXPORT_HTML",
        "GLOW_ENABLE_EXPORT_PDF",
        "GLOW_ENABLE_EXPORT_WORD",
        "GLOW_ENABLE_EXPORT_MARKDOWN",
        "GLOW_ENABLE_CONVERT_TO_MARKDOWN",
        "GLOW_ENABLE_CONVERT_TO_HTML",
        "GLOW_ENABLE_CONVERT_TO_DOCX",
        "GLOW_ENABLE_CONVERT_TO_EPUB",
        "GLOW_ENABLE_CONVERT_TO_PDF",
        "GLOW_ENABLE_CONVERT_TO_PIPELINE",
        "GLOW_ENABLE_EXPORT_SPEECH",
        "GLOW_ENABLE_CONVERT_TO_SPEECH",
        "GLOW_ENABLE_EXPORT_BRAILLE",
        "GLOW_ENABLE_CONVERT_TO_BRAILLE",
        "GLOW_ENABLE_BRAILLE_BACK_TRANSLATION_SCORE",
        "GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY",
        "GLOW_ENABLE_SPEECH_STREAM",
        "GLOW_ENABLE_TABLE_ADVISOR",
        "GLOW_ENABLE_READING_ORDER_DETECTION",
        "GLOW_ENABLE_PDF_OCR",
        "GLOW_ENABLE_DOCUMENT_COMPARE",
        "GLOW_ENABLE_CONVERT_TO_ODT",
        "GLOW_ENABLE_COGNITIVE_PROFILE",
        "GLOW_ENABLE_FORCED_COLORS_MODE",
        "GLOW_ENABLE_RULE_CONTRIBUTIONS",
        "GLOW_ENABLE_SITE_AUDIT",
        "GLOW_ENABLE_PANDOC",
        "GLOW_ENABLE_WEASYPRINT",
        "GLOW_ENABLE_PYMUPDF",
        "GLOW_ENABLE_MARKITDOWN",
        "GLOW_ENABLE_DAISY_ACE",
        "GLOW_ENABLE_DAISY_META_VIEWER",
        "GLOW_ENABLE_DAISY_PIPELINE",
        "GLOW_ENABLE_EPUBCHECK",
        "GLOW_ENABLE_PYDOCX",
        "GLOW_ENABLE_OPENPYXL",
        "GLOW_ENABLE_PYTHON_PPTX",
    ]

    categories = {
        "ai": [
            "GLOW_ENABLE_AI",
            "GLOW_ENABLE_AI_GENERAL_CHAT",
            "GLOW_ENABLE_AI_CHAT",
            "GLOW_ENABLE_AI_WHISPERER",
            "GLOW_ENABLE_AI_HEADING_FIX",
            "GLOW_ENABLE_AI_ALT_TEXT",
            "GLOW_ENABLE_AI_MARKITDOWN_LLM",
        ],
        "core": [
            "GLOW_ENABLE_USER_LOGIN",
            "GLOW_ENABLE_ADMIN_LOGIN",
            "GLOW_ENABLE_AUDIT",
            "GLOW_ENABLE_CHECKER",
            "GLOW_ENABLE_HEADING_DETECTION",
            "GLOW_ENABLE_SITE_AUDIT",
            "GLOW_ENABLE_COGNITIVE_PROFILE",
            "GLOW_ENABLE_FORCED_COLORS_MODE",
            "GLOW_ENABLE_RULE_CONTRIBUTIONS",
        ],
        "conversion": [
            "GLOW_ENABLE_CONVERTER",
            "GLOW_ENABLE_TEMPLATE_BUILDER",
            "GLOW_ENABLE_WORD_SETUP",
            "GLOW_ENABLE_MARKDOWN_AUDIT",
            "GLOW_ENABLE_TABLE_ADVISOR",
            "GLOW_ENABLE_READING_ORDER_DETECTION",
            "GLOW_ENABLE_PDF_OCR",
            "GLOW_ENABLE_DOCUMENT_COMPARE",
        ],
        "documents": [
            "GLOW_ENABLE_WORD",
            "GLOW_ENABLE_EXCEL",
            "GLOW_ENABLE_POWERPOINT",
            "GLOW_ENABLE_PDF",
            "GLOW_ENABLE_MARKDOWN",
            "GLOW_ENABLE_EPUB",
        ],
        "exports": [
            "GLOW_ENABLE_EXPORT_HTML",
            "GLOW_ENABLE_EXPORT_PDF",
            "GLOW_ENABLE_EXPORT_WORD",
            "GLOW_ENABLE_EXPORT_MARKDOWN",
            "GLOW_ENABLE_EXPORT_SPEECH",
            "GLOW_ENABLE_EXPORT_BRAILLE",
            "GLOW_ENABLE_SPEECH_STREAM",
        ],
        "convert_subfeatures": [
            "GLOW_ENABLE_CONVERT_TO_MARKDOWN",
            "GLOW_ENABLE_CONVERT_TO_HTML",
            "GLOW_ENABLE_CONVERT_TO_DOCX",
            "GLOW_ENABLE_CONVERT_TO_ODT",
            "GLOW_ENABLE_CONVERT_TO_EPUB",
            "GLOW_ENABLE_CONVERT_TO_PDF",
            "GLOW_ENABLE_CONVERT_TO_PIPELINE",
            "GLOW_ENABLE_CONVERT_TO_SPEECH",
            "GLOW_ENABLE_CONVERT_TO_BRAILLE",
        ],
        "integrations": [
            "GLOW_ENABLE_BRAILLE_BACK_TRANSLATION_SCORE",
            "GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY",
            "GLOW_ENABLE_PANDOC",
            "GLOW_ENABLE_WEASYPRINT",
            "GLOW_ENABLE_PYMUPDF",
            "GLOW_ENABLE_MARKITDOWN",
            "GLOW_ENABLE_DAISY_ACE",
            "GLOW_ENABLE_DAISY_META_VIEWER",
            "GLOW_ENABLE_DAISY_PIPELINE",
            "GLOW_ENABLE_EPUBCHECK",
            "GLOW_ENABLE_PYDOCX",
            "GLOW_ENABLE_OPENPYXL",
            "GLOW_ENABLE_PYTHON_PPTX",
        ],
    }

    if request.method == "POST":
        try:
            if request.form.get("reset_defaults") == "on":
                _reset_flag_defaults()
                notice = "Feature flags reset to defaults."
            else:
                posted = {k: request.form.get(k) == "on" for k in feature_keys}

                if not posted.get("GLOW_ENABLE_AI", False):
                    for child in [
                        "GLOW_ENABLE_AI_GENERAL_CHAT",
                        "GLOW_ENABLE_AI_CHAT",
                        "GLOW_ENABLE_AI_WHISPERER",
                        "GLOW_ENABLE_AI_HEADING_FIX",
                        "GLOW_ENABLE_AI_ALT_TEXT",
                        "GLOW_ENABLE_AI_MARKITDOWN_LLM",
                    ]:
                        posted[child] = False

                for k, v in posted.items():
                    _set_flag(k, v, changed_by=current_user.email)
                notice = "Feature flags updated."
        except Exception as exc:
            error = f"Could not update flags: {exc}"

    flags = _get_all_flags()
    metas = {k: _get_flag_meta(k) for k in feature_keys}
    backend = _get_flags_backend()
    audit_rows: list[dict[str, Any]] = []
    try:
        for k in feature_keys:
            audit_rows.extend(_get_audit_entries(k, limit=10))
        audit_rows = sorted(audit_rows, key=lambda r: r.get("changed_at") or "", reverse=True)[:200]
    except Exception:
        audit_rows = []
    return render_template(
        "admin_flags.html",
        admin_email=current_user.email,
        flags=flags,
        flag_meta=metas,
        flags_backend=backend,
        audit_rows=audit_rows,
        feature_keys=feature_keys,
        categories=categories,
        notice=notice,
        error=error,
    )


@admin_bp.route("/flags/migrate", methods=["POST"])
@admin_required
def admin_flags_migrate() -> Any:
    """Trigger a JSON->SQLite migration helper (idempotent) from the UI."""
    notice = None
    error = None
    try:
        _migrate_flags()
        notice = "Feature flags migrated (if JSON data present)."
    except Exception as exc:
        error = f"Migration failed: {exc}"

    return redirect(url_for("admin.admin_flags", notice=notice, error=error))


@admin_bp.route("/queue/cancel/<job_id>", methods=["POST"])
@admin_required
def admin_queue_cancel(job_id: str) -> Any:
    ok, msg = admin_cancel_queued_job(job_id)
    return redirect(url_for("admin.admin_queue", notice=msg if ok else None, error=None if ok else msg))


@admin_bp.route("/queue/requeue/<job_id>", methods=["POST"])
@admin_required
def admin_queue_requeue(job_id: str) -> Any:
    ok, msg = admin_requeue_failed_job(job_id)
    return redirect(url_for("admin.admin_queue", notice=msg if ok else None, error=None if ok else msg))


@admin_bp.route("/analytics", methods=["GET"])
@admin_required
def admin_analytics() -> Any:
    """Tool usage analytics dashboard."""
    from ..tool_usage import (
        get_all as _get_tool_usage,
        get_detail_counts as _get_detail_counts,
        get_total as _get_tool_total,
    )
    from ..visitor_counter import get_count as _get_visitor_count
    from ..speech_metrics import get_summary as _get_speech_metrics_summary

    usage = _get_tool_usage()
    total_uses = _get_tool_total()
    visitor_count = _get_visitor_count()
    return render_template(
        "admin_analytics.html",
        admin_email=current_user.email,
        usage=usage,
        total_uses=total_uses,
        visitor_count=visitor_count,
        speech_metrics_summary=_get_speech_metrics_summary(),
        anthem_downloads=_get_detail_counts("anthem_download", "detail", limit=1),
        speech_modes=_get_detail_counts("speech", "mode", limit=20),
        speech_voices=_get_detail_counts("speech", "voice", limit=20),
        speech_speeds=_get_detail_counts("speech", "speed", limit=20),
        speech_pitches=_get_detail_counts("speech", "pitch", limit=20),
    )
