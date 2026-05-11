"""Simple feature flag storage for the web app.

This file implements server-side feature flags using SQLAlchemy.
The admin UI can read and update flags via the admin blueprint.
Defaults fall back to environment variables for parity with existing behavior.
"""
from __future__ import annotations

import os
import json
from datetime import UTC, datetime
from typing import Any

from .db import db
from .models import FeatureFlag, FeatureFlagAudit


_DEFAULTS: dict[str, bool] = {
    # Master AI switch: enabled by default for Ollama-first deployments
    "GLOW_ENABLE_AI": True,
    # General chat (AI Playground) switch
    "GLOW_ENABLE_AI_GENERAL_CHAT": True,
    # Individual AI features (master flag still overrides)
    "GLOW_ENABLE_AI_CHAT": False,
    "GLOW_ENABLE_AI_WHISPERER": False,
    "GLOW_ENABLE_AI_HEADING_FIX": True,
    "GLOW_ENABLE_AI_ALT_TEXT": False,
    "GLOW_ENABLE_AI_MARKITDOWN_LLM": True,
    # Broad GLOW feature flags (non-AI features).
    # Defaults: non-AI features are enabled by default so typical
    # document processing (audit, convert, export) is available.
    "GLOW_ENABLE_AUDIT": True,
    "GLOW_ENABLE_CHECKER": True,
    "GLOW_ENABLE_HEADING_DETECTION": True,
    "GLOW_ENABLE_CONVERTER": True,
    "GLOW_ENABLE_TEMPLATE_BUILDER": True,
    "GLOW_ENABLE_WORD_SETUP": True,
    "GLOW_ENABLE_MARKDOWN_AUDIT": True,

    # Document-format specific flags
    "GLOW_ENABLE_WORD": True,
    "GLOW_ENABLE_EXCEL": True,
    "GLOW_ENABLE_POWERPOINT": True,
    "GLOW_ENABLE_PDF": True,
    "GLOW_ENABLE_MARKDOWN": True,
    "GLOW_ENABLE_EPUB": True,

    # Export / conversion capabilities
    "GLOW_ENABLE_EXPORT_HTML": True,
    "GLOW_ENABLE_EXPORT_PDF": True,
    "GLOW_ENABLE_EXPORT_WORD": True,
    "GLOW_ENABLE_EXPORT_MARKDOWN": True,

    # Convert route subfeatures (direction-level controls)
    "GLOW_ENABLE_CONVERT_TO_MARKDOWN": True,
    "GLOW_ENABLE_CONVERT_TO_HTML": True,
    "GLOW_ENABLE_CONVERT_TO_DOCX": True,
    "GLOW_ENABLE_CONVERT_TO_EPUB": True,
    "GLOW_ENABLE_CONVERT_TO_PDF": True,
    "GLOW_ENABLE_CONVERT_TO_PIPELINE": True,

    # Optional tool integrations (can be disabled if binary deps are not present)
    "GLOW_ENABLE_PANDOC": True,
    "GLOW_ENABLE_WEASYPRINT": True,
    "GLOW_ENABLE_PYMUPDF": True,
    "GLOW_ENABLE_MARKITDOWN": True,
    "GLOW_ENABLE_EPUBCHECK": True,
    "GLOW_ENABLE_DAISY_ACE": True,
    "GLOW_ENABLE_DAISY_META_VIEWER": True,
    "GLOW_ENABLE_DAISY_PIPELINE": True,
    "GLOW_ENABLE_PYDOCX": True,
    "GLOW_ENABLE_OPENPYXL": True,
    "GLOW_ENABLE_PYTHON_PPTX": True,

    # Server-side Speech Studio
    "GLOW_ENABLE_SPEECH": True,
    "GLOW_ENABLE_EXPORT_SPEECH": True,
    "GLOW_ENABLE_CONVERT_TO_SPEECH": True,

    # Braille Studio (requires louis / liblouis Python bindings)
    "GLOW_ENABLE_BRAILLE": True,
    "GLOW_ENABLE_EXPORT_BRAILLE": True,
    "GLOW_ENABLE_CONVERT_TO_BRAILLE": True,

    # 1.5 Back-translation quality scoring
    "GLOW_ENABLE_BRAILLE_BACK_TRANSLATION_SCORE": True,

    # 2.5 Pronunciation dictionary management
    "GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY": True,

    # 2.6 Real-time streaming speech preview
    "GLOW_ENABLE_SPEECH_STREAM": True,

    # 3.3 Table accessibility advisor
    "GLOW_ENABLE_TABLE_ADVISOR": True,

    # 3.4 Reading order detection and correction
    "GLOW_ENABLE_READING_ORDER_DETECTION": True,

    # 3.5 OCR for scanned PDFs
    "GLOW_ENABLE_PDF_OCR": True,

    # 3.6 Document comparison and change tracking
    "GLOW_ENABLE_DOCUMENT_COMPARE": True,

    # 4.3 OpenDocument Text export
    "GLOW_ENABLE_CONVERT_TO_ODT": True,

    # 7.3 Cognitive accessibility profile
    "GLOW_ENABLE_COGNITIVE_PROFILE": True,

    # 7.4 High-contrast and forced-colors mode
    "GLOW_ENABLE_FORCED_COLORS_MODE": True,

    # 9.1 Public rule contribution portal
    "GLOW_ENABLE_RULE_CONTRIBUTIONS": True,

    # User-facing website accessibility scanner
    "GLOW_ENABLE_SITE_AUDIT": True,
}


def get_flag(name: str, default: bool | None = None) -> bool:
    """Return the boolean value for a named flag.

    If the flag is not present in storage and a default is provided,
    the default is returned. If default is None, falls back to the
    compiled defaults in this module.
    """
    try:
        return FeatureFlag.get_flag(name, default=default)
    except Exception:
        if default is not None:
            return bool(default)
        return bool(_DEFAULTS.get(name, False))


def set_flag(name: str, value: bool, changed_by: str | None = None) -> None:
    """Persist a flag and record an audit entry and optional webhook.

    `changed_by` is optional (email or username) and used for auditing.
    """
    try:
        old_val = get_flag(name)
    except Exception:
        old_val = None

    try:
        FeatureFlag.set_flag(name, value)
        # Record audit entry
        FeatureFlagAudit.record_change(name, old_val, value, changed_by)
        db.session.commit()
        # Attempt webhook notification (best-effort)
        _notify_webhook(name, old_val, bool(value), changed_by)
    except Exception:
        db.session.rollback()


def get_all_flags() -> dict[str, bool]:
    """Return all flags with current/default values."""
    try:
        records = db.session.execute(db.select(FeatureFlag)).scalars().all()
        out = {r.name: bool(r.value) for r in records}
    except Exception:
        out = {}
    
    # Fill in any defaults not explicitly stored
    for k, v in _DEFAULTS.items():
        out.setdefault(k, bool(v))
    return out


def get_flag_meta(name: str) -> dict[str, Any]:
    """Return metadata for a flag: updated_at and backend."""
    try:
        record = db.session.execute(
            db.select(FeatureFlag).where(FeatureFlag.name == name)
        ).scalar_one_or_none()
        if record:
            return {
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                "backend": "sqlalchemy",
            }
    except Exception:
        pass
    return {"updated_at": None, "backend": "sqlalchemy"}


def reset_defaults() -> None:
    """Reset persisted store to known defaults."""
    try:
        for name, value in _DEFAULTS.items():
            FeatureFlag.set_flag(name, value)
        db.session.commit()
    except Exception:
        db.session.rollback()


def get_audit_entries(flag_name: str, limit: int = 10) -> list[dict[str, Any]]:
    """Return recent audit entries for a flag.

    Returns a list of dicts with keys: id, changed_by, changed_at (ISO8601), old_value, new_value.
    """
    try:
        entries = db.session.execute(
            db.select(FeatureFlagAudit)
            .where(FeatureFlagAudit.flag_name == flag_name)
            .order_by(FeatureFlagAudit.changed_at.desc())
            .limit(limit)
        ).scalars().all()
        return [
            {
                "id": e.id,
                "changed_by": e.changed_by,
                "changed_at": e.changed_at.isoformat() if e.changed_at else None,
                "old_value": e.old_value,
                "new_value": e.new_value,
            }
            for e in entries
        ]
    except Exception:
        return []


def _notify_webhook(name: str, old: bool | None, new: bool, changed_by: str | None = None) -> None:
    """Notify webhook if configured (best-effort)."""
    url = os.environ.get("FEATURE_FLAGS_WEBHOOK_URL", "").strip()
    if not url:
        return
    try:
        import requests
        import hmac
        import hashlib

        now = datetime.now(UTC).isoformat()
        payload = {
            "flag": name,
            "old_value": None if old is None else bool(old),
            "new_value": bool(new),
            "changed_by": changed_by,
            "changed_at": now,
        }
        body = json.dumps(payload)
        headers = {"Content-Type": "application/json"}
        secret = os.environ.get("FEATURE_FLAGS_WEBHOOK_SECRET", "")
        if secret:
            sig = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
            headers["X-FeatureFlags-Signature"] = f"sha256={sig}"

        # Best-effort notify; do not raise on failure
        requests.post(url, data=body, headers=headers, timeout=5)
    except Exception:
        return


def migrate_json_to_sqlite() -> None:
    """Import legacy JSON flags into the SQLAlchemy-backed flags table.

    Kept for backward compatibility with existing tooling and CI helpers.
    This function is best-effort and intentionally non-fatal.
    """
    try:
        from pathlib import Path
        from flask import current_app

        path_override = os.environ.get("FEATURE_FLAGS_JSON_PATH", "").strip()
        if path_override:
            json_path = Path(path_override)
        else:
            try:
                json_path = Path(current_app.instance_path) / "feature_flags.json"
            except Exception:
                json_path = Path("instance") / "feature_flags.json"

        if not json_path.exists():
            return

        with json_path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)

        if not isinstance(raw, dict):
            return

        for key, value in raw.items():
            if isinstance(key, str):
                FeatureFlag.set_flag(key, bool(value))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return


def get_backend() -> str:
    """Return the configured backend label for compatibility with admin UI/tests.

    The implementation is SQLAlchemy-backed. Historically this label was
    'json' or 'sqlite', so we preserve that surface API.
    """
    backend = os.environ.get("FEATURE_FLAGS_BACKEND", "sqlite").strip().lower()
    return backend if backend in {"json", "sqlite"} else "sqlite"
