"""Simple feature flag storage for the web app.

This file implements a minimal, server-side feature flag store using a
JSON file under the Flask `instance/` directory. The admin UI can read and
update flags via the admin blueprint. Defaults fall back to environment
variables for parity with existing behavior.

Note: This is intentionally lightweight — later we can swap to a DB or
remote flags provider without changing callers.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from flask import current_app
import sqlite3
from datetime import datetime, timezone
from typing import Optional

# Backends: 'json' (default) or 'sqlite'
_BACKEND = os.environ.get("FEATURE_FLAGS_BACKEND", "json").strip().lower()


def _sqlite_path() -> Path:
    p = Path(current_app.instance_path)
    p.mkdir(parents=True, exist_ok=True)
    return p / "feature_flags.db"


def _sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_sqlite_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS flags (name TEXT PRIMARY KEY, value INTEGER NOT NULL, updated_at TEXT)"
    )
    conn.commit()
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_DEFAULTS: dict[str, bool] = {
    # Master AI switch: default OFF for conservative deployments
    "GLOW_ENABLE_AI": False,
    # Individual AI features (all default OFF; master flag overrides)
    "GLOW_ENABLE_AI_CHAT": False,
    "GLOW_ENABLE_AI_WHISPERER": False,
    "GLOW_ENABLE_AI_HEADING_FIX": False,
    "GLOW_ENABLE_AI_ALT_TEXT": False,
    "GLOW_ENABLE_AI_MARKITDOWN_LLM": False,
    # Broad GLOW feature flags (non-AI features).
    # Defaults: non-AI features are enabled by default so typical
    # document processing (audit, convert, export) is available.
    "GLOW_ENABLE_AUDIT": True,
    "GLOW_ENABLE_CHECKER": True,
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
    "GLOW_ENABLE_DAISY_ACE": True,
    "GLOW_ENABLE_DAISY_META_VIEWER": True,
    "GLOW_ENABLE_DAISY_PIPELINE": True,
    "GLOW_ENABLE_PYDOCX": True,
    "GLOW_ENABLE_OPENPYXL": True,
    "GLOW_ENABLE_PYTHON_PPTX": True,
}


def _path() -> Path:
    p = Path(current_app.instance_path)
    p.mkdir(parents=True, exist_ok=True)
    return p / "feature_flags.json"


def _load() -> dict[str, Any]:
    try:
        if _BACKEND == "sqlite":
            conn = _sqlite_conn()
            rows = conn.execute("SELECT name, value FROM flags").fetchall()
            out = {r["name"]: bool(r["value"]) for r in rows}
            conn.close()
            return out
        p = _path()
        if not p.exists():
            return {}
        with p.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save(data: dict[str, Any]) -> None:
    if _BACKEND == "sqlite":
        conn = _sqlite_conn()
        for k, v in data.items():
            conn.execute(
                "INSERT INTO flags (name, value, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (k, int(bool(v)), _now_iso()),
            )
        conn.commit()
        conn.close()
        return

    p = _path()
    with p.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)


def get_flag(name: str, default: bool | None = None) -> bool:
    """Return the boolean value for a named flag.

    If the flag is not present in storage and a default is provided,
    the default is returned. If default is None, falls back to the
    compiled defaults in this module.
    """
    data = _load()
    if name in data:
        return bool(data[name])
    if default is not None:
        return bool(default)
    return bool(_DEFAULTS.get(name, False))


def _ensure_audit_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS flag_audit ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " name TEXT NOT NULL,"
        " old_value INTEGER,"
        " new_value INTEGER NOT NULL,"
        " changed_at TEXT NOT NULL,"
        " changed_by TEXT"
        ")"
    )
    conn.commit()


def _record_audit(name: str, old: bool | None, new: bool, changed_by: str | None = None) -> None:
    try:
        conn = _sqlite_conn()
        _ensure_audit_table(conn)
        conn.execute(
            "INSERT INTO flag_audit (name, old_value, new_value, changed_at, changed_by) VALUES (?, ?, ?, ?, ?)",
            (name, None if old is None else int(bool(old)), int(bool(new)), _now_iso(), changed_by),
        )
        conn.commit()
        conn.close()
    except Exception:
        # Audit should not block normal operation
        return


def _notify_webhook(name: str, old: bool | None, new: bool, changed_by: str | None = None) -> None:
    url = os.environ.get("FEATURE_FLAGS_WEBHOOK_URL", "").strip()
    if not url:
        return
    try:
        import requests

        payload = {
            "flag": name,
            "old_value": None if old is None else bool(old),
            "new_value": bool(new),
            "changed_by": changed_by,
            "changed_at": _now_iso(),
        }
        body = json.dumps(payload)
        headers = {"Content-Type": "application/json"}
        secret = os.environ.get("FEATURE_FLAGS_WEBHOOK_SECRET", "")
        if secret:
            import hmac
            import hashlib

            sig = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
            headers["X-FeatureFlags-Signature"] = f"sha256={sig}"

        # Best-effort notify; do not raise on failure
        requests.post(url, data=body, headers=headers, timeout=5)
    except Exception:
        return


def set_flag(name: str, value: bool, changed_by: str | None = None) -> None:
    """Persist a flag and record an audit entry and optional webhook.

    `changed_by` is optional (email or username) and used for auditing.
    """
    old_val = None
    # Read previous value regardless of backend
    try:
        data = _load()
        if name in data:
            old_val = bool(data[name])
    except Exception:
        old_val = None

    if _BACKEND == "sqlite":
        conn = _sqlite_conn()
        cur = conn.execute("SELECT value FROM flags WHERE name=?", (name,)).fetchone()
        if cur is not None:
            old_val = bool(cur[0])
        conn.execute(
            "INSERT INTO flags (name, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (name, int(bool(value)), _now_iso()),
        )
        conn.commit()
        conn.close()
    else:
        data = _load()
        data[name] = bool(value)
        _save(data)

    # Record audit and notify webhook (best-effort)
    try:
        _record_audit(name, old_val, bool(value), changed_by)
        _notify_webhook(name, old_val, bool(value), changed_by)
    except Exception:
        pass


def get_all_flags() -> dict[str, bool]:
    data = _load()
    out = {k: bool(v) for k, v in data.items()}
    # Fill in any defaults not explicitly stored
    for k, v in _DEFAULTS.items():
        out.setdefault(k, bool(v))
    return out


def get_flag_meta(name: str) -> dict[str, Optional[str]]:
    """Return metadata for a flag: updated_at and backend."""
    if _BACKEND == "sqlite":
        try:
            conn = _sqlite_conn()
            row = conn.execute("SELECT updated_at FROM flags WHERE name=?", (name,)).fetchone()
            conn.close()
            return {"updated_at": row["updated_at"] if row else None, "backend": "sqlite"}
        except Exception:
            return {"updated_at": None, "backend": "sqlite"}

    # json backend: file mtime
    try:
        p = _path()
        if p.exists():
            stat = p.stat()
            return {"updated_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(), "backend": "json"}
    except Exception:
        pass
    return {"updated_at": None, "backend": "json"}


def get_audit_entries(name: str, limit: int = 25) -> list[dict[str, Any]]:
    """Return recent audit entries for a flag (best-effort)."""
    out: list[dict[str, Any]] = []
    try:
        conn = _sqlite_conn()
        cur = conn.execute(
            "SELECT id, name, old_value, new_value, changed_at, changed_by FROM flag_audit WHERE name=? ORDER BY id DESC LIMIT ?",
            (name, int(limit)),
        ).fetchall()
        for r in cur:
            out.append({
                "id": r[0],
                "name": r[1],
                "old_value": None if r[2] is None else bool(r[2]),
                "new_value": bool(r[3]),
                "changed_at": r[4],
                "changed_by": r[5],
            })
        conn.close()
    except Exception:
        pass
    return out


def reset_defaults() -> None:
    # Reset persisted store to known defaults
    _save(dict(_DEFAULTS))


def migrate_json_to_sqlite() -> None:
    """Migrate an existing JSON-backed flags file into sqlite backend.

    This is a best-effort convenience helper invoked when switching backends.
    """
    try:
        js = {}
        p = _path()
        if p.exists():
            with p.open("r", encoding="utf-8") as fh:
                js = json.load(fh)
        if not js:
            return
        conn = _sqlite_conn()
        for k, v in js.items():
            conn.execute(
                "INSERT INTO flags (name, value, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (k, int(bool(v)), _now_iso()),
            )
        conn.commit()
        conn.close()
    except Exception:
        return


def get_backend() -> str:
    """Return the active backend name ('json' or 'sqlite')."""
    return _BACKEND
