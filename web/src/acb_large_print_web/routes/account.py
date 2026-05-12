"""Account/profile routes for authenticated users."""

from __future__ import annotations

import json
import os
import shutil

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from ..db import db
from ..models import UserAISettings, UserAuditHistory, UserPrivacyConsent, UserUIPreferences

account_bp = Blueprint("account", __name__)


@account_bp.route("/")
@login_required
def dashboard():
    history = db.session.execute(
        db.select(UserAuditHistory)
        .where(UserAuditHistory.user_id == current_user.id)
        .order_by(UserAuditHistory.created_at.desc())
        .limit(50)
    ).scalars().all()
    consent = current_user.get_privacy_consent()
    display_name_value = current_user.display_name or ""
    if display_name_value.strip().lower() == (current_user.email or "").strip().lower():
        display_name_value = ""
    return render_template(
        "account/dashboard.html",
        history=history,
        consent=consent,
        display_name_value=display_name_value,
    )


@account_bp.route("/privacy", methods=["GET", "POST"])
@login_required
def privacy():
    consent = current_user.get_privacy_consent()
    if request.method == "POST":
        consent.sync_ai_keys = bool(request.form.get("sync_ai_keys"))
        consent.sync_ai_features = bool(request.form.get("sync_ai_features"))
        consent.sync_ai_prompts = bool(request.form.get("sync_ai_prompts"))
        consent.sync_ai_runtime = bool(request.form.get("sync_ai_runtime"))
        consent.sync_audit_history = bool(request.form.get("sync_audit_history"))
        consent.sync_ui_preferences = bool(request.form.get("sync_ui_preferences"))
        consent.sync_rule_profile = bool(request.form.get("sync_rule_profile"))
        db.session.commit()
        flash("Privacy settings saved.", "success")
        return redirect(url_for("account.privacy"))
    return render_template("account/privacy.html", consent=consent)


@account_bp.route("/profile", methods=["POST"])
@login_required
def profile_update():
    display_name = (request.form.get("display_name") or "").strip()
    current_user.display_name = display_name[:120]
    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("account.dashboard"))


@account_bp.route("/ui-prefs", methods=["POST"])
@login_required
def ui_prefs():
    payload = request.get_json(silent=True) or {}
    prefs = UserUIPreferences.for_user(current_user.id)
    theme = str(payload.get("theme") or "").strip().lower()
    cognitive_mode = str(payload.get("cognitive_mode") or "").strip().lower()
    if theme in {"light", "dark", "auto"}:
        prefs.theme = theme
    if cognitive_mode in {"on", "off"}:
        prefs.cognitive_mode = cognitive_mode
    db.session.commit()
    return jsonify({"ok": True})


@account_bp.route("/export-data")
@login_required
def export_data():
    ai_settings = db.session.get(UserAISettings, current_user.id)
    consent = current_user.get_privacy_consent()
    prefs = db.session.get(UserUIPreferences, current_user.id)
    history = db.session.execute(
        db.select(UserAuditHistory).where(UserAuditHistory.user_id == current_user.id)
    ).scalars().all()

    payload = {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "display_name": current_user.display_name,
            "auth_provider": current_user.auth_provider,
            "is_email_verified": current_user.is_email_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "privacy_consent": {
            "sync_ai_keys": consent.sync_ai_keys,
            "sync_ai_features": consent.sync_ai_features,
            "sync_ai_prompts": consent.sync_ai_prompts,
            "sync_ai_runtime": consent.sync_ai_runtime,
            "sync_audit_history": consent.sync_audit_history,
            "sync_ui_preferences": consent.sync_ui_preferences,
            "sync_rule_profile": consent.sync_rule_profile,
        },
        "ai_settings": {
            "feature_flags": ai_settings.feature_flags if ai_settings else {},
            "feature_models": ai_settings.feature_models if ai_settings else {},
            "runtime_settings": ai_settings.runtime_settings if ai_settings else {},
            "prompt_settings": ai_settings.prompt_settings if ai_settings else {},
            "rule_profile": ai_settings.rule_profile if ai_settings else {},
        },
        "ui_preferences": {
            "theme": prefs.theme if prefs else "auto",
            "cognitive_mode": prefs.cognitive_mode if prefs else "off",
        },
        "audit_history": [
            {
                "filename": h.filename,
                "file_ext": h.file_ext,
                "score": h.score,
                "severity_counts": h.severity_counts,
                "report_path": h.report_path,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ],
    }

    tmp_path = os.path.join(current_app.instance_path, f"user-export-{current_user.id}.json")
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return send_file(tmp_path, as_attachment=True, download_name=f"glow-user-export-{current_user.id}.json")


@account_bp.route("/data", methods=["DELETE", "POST"])
@login_required
def delete_data():
    user_id = current_user.id
    reports_dir = os.path.join(current_app.instance_path, "user_reports", str(user_id))

    # delete child rows first
    db.session.execute(db.delete(UserAuditHistory).where(UserAuditHistory.user_id == user_id))
    db.session.execute(db.delete(UserAISettings).where(UserAISettings.user_id == user_id))
    db.session.execute(db.delete(UserPrivacyConsent).where(UserPrivacyConsent.user_id == user_id))
    db.session.execute(db.delete(UserUIPreferences).where(UserUIPreferences.user_id == user_id))

    # delete user row (cascade handles OAuth/provider keys)
    db.session.delete(current_user)
    db.session.commit()

    if os.path.isdir(reports_dir):
        shutil.rmtree(reports_dir, ignore_errors=True)

    from flask_login import logout_user
    logout_user()
    flash("Your account and stored data were deleted.", "info")
    return redirect(url_for("main.index"))
