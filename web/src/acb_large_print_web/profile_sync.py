"""Profile sync: bidirectional bridge between Flask session and user DB profile.

On login  → ``load_profile_to_session(user)``  restores all consented settings.
On logout → ``save_session_to_profile(user)``  persists all consented settings.
On request → ``maybe_autosave(user)``           periodic save (every 5 minutes).

All operations are gated by UserPrivacyConsent so users remain in control of
exactly what data leaves their browser session and enters the database.

API key handling:
- Keys in session (user_ai_providers dict) are stored as plaintext in the
  encrypted Flask cookie only.  When saving to DB they are encrypted with
  Fernet before being written.  When loading from DB they are decrypted in-
  process and placed back into the session cookie (still encrypted in transit).
- The DB never holds a plaintext key.  The session cookie never holds a
  DB-encrypted Fernet token; it only holds the raw key (protected by the
  cookie HMAC signing via Flask's itsdangerous).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta

log = logging.getLogger(__name__)

# Minimum seconds between auto-saves to avoid excessive DB writes.
_AUTOSAVE_INTERVAL_S = 300  # 5 minutes
_AUTOSAVE_KEY = "_profile_last_save"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_profile_to_session(user) -> None:
    """Restore a logged-in user's consented profile data into the session.

    Called immediately after a successful login.  Existing session values are
    *not* overwritten -- the session (fresh browser data) wins.
    """
    from flask import session
    consent = user.get_privacy_consent()

    if consent.allows("ai_features") and user.ai_settings:
        _load_ai_features(user.ai_settings, session)

    if consent.allows("ai_runtime") and user.ai_settings:
        _load_ai_runtime(user.ai_settings, session)

    if consent.allows("ai_prompts") and user.ai_settings:
        _load_ai_prompts(user.ai_settings, session)

    if consent.allows("rule_profile") and user.ai_settings:
        _load_rule_profile(user.ai_settings, session)

    if consent.allows("ai_keys"):
        _load_provider_keys(user, session)

    if consent.allows("ui_preferences") and user.ui_preferences:
        _load_ui_preferences(user.ui_preferences, session)

    session[_AUTOSAVE_KEY] = datetime.now(UTC).isoformat()
    log.debug("profile: loaded profile for user %d", user.id)


def save_session_to_profile(user) -> None:
    """Persist the session's consented settings back to the user's DB profile.

    Called on logout, and periodically by ``maybe_autosave``.
    """
    from flask import session
    from .db import db

    consent = user.get_privacy_consent()

    if consent.allows("ai_features"):
        _save_ai_features(user, session)

    if consent.allows("ai_runtime"):
        _save_ai_runtime(user, session)

    if consent.allows("ai_prompts"):
        _save_ai_prompts(user, session)

    if consent.allows("rule_profile"):
        _save_rule_profile(user, session)

    if consent.allows("ai_keys"):
        _save_provider_keys(user, session)

    if consent.allows("ui_preferences"):
        _save_ui_preferences(user, session)

    try:
        db.session.commit()
        session[_AUTOSAVE_KEY] = datetime.now(UTC).isoformat()
        log.debug("profile: saved profile for user %d", user.id)
    except Exception:
        db.session.rollback()
        log.exception("profile: save failed for user %d", user.id)


def maybe_autosave(user) -> None:
    """Trigger a save if more than _AUTOSAVE_INTERVAL_S seconds have passed."""
    from flask import session
    raw = session.get(_AUTOSAVE_KEY, "")
    if raw:
        try:
            last = datetime.fromisoformat(raw)
            if (datetime.now(UTC) - last).total_seconds() < _AUTOSAVE_INTERVAL_S:
                return
        except ValueError:
            pass
    save_session_to_profile(user)


def record_audit_history(user, *, filename: str, file_ext: str,
                          score: float | None, severity_counts: dict,
                          report_data: dict | None = None) -> None:
    """Write an audit result to the user's history (if consented).

    If *report_data* is provided it is written to
    ``instance/user_reports/<user_id>/<timestamp>.json`` and the path
    is stored in the DB row.
    """
    from flask import current_app
    from .db import db
    from .models import UserAuditHistory

    consent = user.get_privacy_consent()
    if not consent.allows("audit_history"):
        return

    import os
    report_path = None
    if report_data:
        reports_dir = os.path.join(current_app.instance_path, "user_reports", str(user.id))
        os.makedirs(reports_dir, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        fname = f"{ts}_{_safe_stem(filename)}.json"
        abs_path = os.path.join(reports_dir, fname)
        with open(abs_path, "w", encoding="utf-8") as fh:
            json.dump(report_data, fh)
        # Store path relative to instance_path
        report_path = os.path.join("user_reports", str(user.id), fname)

    entry = UserAuditHistory(
        user_id=user.id,
        filename=filename,
        file_ext=file_ext,
        score=score,
        severity_counts_json=json.dumps(severity_counts or {}),
        report_path=report_path,
    )
    db.session.add(entry)

    # Prune old entries in the same transaction
    UserAuditHistory.prune_old_history(user.id)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        log.exception("profile: failed to record audit history for user %d", user.id)


# ---------------------------------------------------------------------------
# Private helpers -- load direction (DB → session)
# ---------------------------------------------------------------------------

def _load_ai_features(settings, session) -> None:
    flags = settings.feature_flags
    if flags and "user_ai_features" not in session:
        session["user_ai_features"] = flags

    models = settings.feature_models
    if models and "user_ai_feature_models" not in session:
        session["user_ai_feature_models"] = models


def _load_ai_runtime(settings, session) -> None:
    runtime = settings.runtime_settings
    if runtime and "user_ai_runtime_settings" not in session:
        session["user_ai_runtime_settings"] = runtime


def _load_ai_prompts(settings, session) -> None:
    prompts = settings.prompt_settings
    if prompts and "user_ai_prompt_settings" not in session:
        session["user_ai_prompt_settings"] = prompts


def _load_rule_profile(settings, session) -> None:
    profile = settings.rule_profile
    if profile and "glow_rule_profile" not in session:
        session["glow_rule_profile"] = profile


def _load_provider_keys(user, session) -> None:
    """Decrypt stored provider keys and restore them to the session."""
    from .encryption import decrypt_safe
    existing_providers: dict = session.get("user_ai_providers") or {}

    for key_record in user.provider_keys:
        provider = key_record.provider
        if provider in existing_providers:
            # Session already has a key for this provider -- session wins
            continue
        plaintext = key_record.get_plaintext_key()
        if not plaintext:
            continue  # Decryption failed (e.g. after SECRET_KEY rotation)

        # Reconstruct a minimal provider entry matching user_ai.py's structure
        try:
            models_list = json.loads(key_record.models_json or "[]")
        except (ValueError, TypeError):
            models_list = []

        existing_providers[provider] = {
            "api_key": plaintext,
            "default_model": key_record.default_model,
            "models": models_list,
            "validated": True,
            "validated_at": key_record.updated_at.isoformat() if key_record.updated_at else "",
        }

    if existing_providers:
        session["user_ai_providers"] = existing_providers
        # Also populate legacy Ollama keys if present
        if "ollama" in existing_providers:
            _sync_legacy_ollama_keys(existing_providers["ollama"], session)


def _load_ui_preferences(prefs, session) -> None:
    if "glow_theme" not in session:
        session["glow_theme"] = prefs.theme
    if "glow_cognitive_mode" not in session:
        session["glow_cognitive_mode"] = prefs.cognitive_mode


# ---------------------------------------------------------------------------
# Private helpers -- save direction (session → DB)
# ---------------------------------------------------------------------------

def _save_ai_features(user, session) -> None:
    from .models import UserAISettings
    settings = UserAISettings.for_user(user.id)
    flags = session.get("user_ai_features")
    if flags:
        settings.feature_flags = flags
    models = session.get("user_ai_feature_models")
    if models:
        settings.feature_models = models


def _save_ai_runtime(user, session) -> None:
    from .models import UserAISettings
    settings = UserAISettings.for_user(user.id)
    runtime = session.get("user_ai_runtime_settings")
    if runtime:
        settings.runtime_settings = runtime


def _save_ai_prompts(user, session) -> None:
    from .models import UserAISettings
    settings = UserAISettings.for_user(user.id)
    prompts = session.get("user_ai_prompt_settings")
    if prompts:
        settings.prompt_settings = prompts


def _save_rule_profile(user, session) -> None:
    from .models import UserAISettings
    settings = UserAISettings.for_user(user.id)
    profile = session.get("glow_rule_profile")
    if profile:
        settings.rule_profile = profile


def _save_provider_keys(user, session) -> None:
    """Encrypt session provider keys and upsert into UserProviderKey rows."""
    from .models import UserProviderKey
    providers: dict = session.get("user_ai_providers") or {}

    # Also capture legacy Ollama key if present
    legacy_key = session.get("ollama_api_key", "")
    legacy_model = session.get("ollama_model", "")
    if legacy_key and "ollama" not in providers:
        providers["ollama"] = {"api_key": legacy_key, "default_model": legacy_model, "models": []}

    for provider, data in providers.items():
        if not isinstance(data, dict):
            continue
        plaintext = str(data.get("api_key") or "").strip()
        if not plaintext:
            continue
        model = str(data.get("default_model") or "").strip()
        models_list = data.get("models") or []
        try:
            UserProviderKey.upsert(user.id, provider, plaintext, model, models_list)
        except Exception:
            log.exception("profile: failed to save key for provider %s (user %d)", provider, user.id)


def _save_ui_preferences(user, session) -> None:
    from .models import UserUIPreferences
    prefs = UserUIPreferences.for_user(user.id)
    theme = session.get("glow_theme", "")
    if theme in ("light", "dark", "auto"):
        prefs.theme = theme
    cognitive = session.get("glow_cognitive_mode", "")
    if cognitive in ("on", "off"):
        prefs.cognitive_mode = cognitive


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _safe_stem(filename: str) -> str:
    import re
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    return re.sub(r"[^\w\-]", "_", stem)[:40]


def _sync_legacy_ollama_keys(ollama_data: dict, session) -> None:
    """Keep legacy session keys in sync for backward compat with older code."""
    if not session.get("ollama_api_key"):
        session["ollama_api_key"] = ollama_data.get("api_key", "")
    if not session.get("ollama_model"):
        session["ollama_model"] = ollama_data.get("default_model", "")
