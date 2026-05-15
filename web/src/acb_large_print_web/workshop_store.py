"""Persistence helpers for Workshop Mode (7.3.0).

This module provides a lightweight SQLite store under instance/ so workshop
sessions, submissions, and peer feedback can be used in conference/training
environments without additional infrastructure.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app


_SESSION_CODE_RE = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db_path() -> Path:
    p = Path(current_app.instance_path)
    p.mkdir(parents=True, exist_ok=True)
    return p / "workshop_mode.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS workshop_sessions ("
        " session_code TEXT PRIMARY KEY,"
        " title TEXT NOT NULL,"
        " event_name TEXT,"
        " created_at_utc TEXT NOT NULL"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS workshop_submissions ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " session_code TEXT NOT NULL,"
        " activity_key TEXT NOT NULL,"
        " display_name TEXT NOT NULL,"
        " anonymity_mode INTEGER NOT NULL DEFAULT 0,"
        " content_text TEXT NOT NULL,"
        " created_at_utc TEXT NOT NULL,"
        " updated_at_utc TEXT NOT NULL,"
        " FOREIGN KEY(session_code) REFERENCES workshop_sessions(session_code)"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS workshop_feedback ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " session_code TEXT NOT NULL,"
        " submission_id INTEGER NOT NULL,"
        " reviewer_display_name TEXT NOT NULL,"
        " strength TEXT NOT NULL,"
        " risk_or_gap TEXT NOT NULL,"
        " recommended_safeguard TEXT NOT NULL,"
        " reuse_suggestion TEXT NOT NULL,"
        " created_at_utc TEXT NOT NULL,"
        " FOREIGN KEY(session_code) REFERENCES workshop_sessions(session_code),"
        " FOREIGN KEY(submission_id) REFERENCES workshop_submissions(id)"
        ")"
    )
    conn.commit()


def normalize_session_code(raw: str) -> str:
    value = (raw or "").strip()
    if not _SESSION_CODE_RE.match(value):
        raise ValueError("Session code must be 3-64 chars (letters, numbers, dash, underscore).")
    return value


def ensure_session(session_code: str, *, title: str = "GLOW Workshop Session", event_name: str = "") -> None:
    code = normalize_session_code(session_code)
    conn = _conn()
    conn.execute(
        "INSERT OR IGNORE INTO workshop_sessions (session_code, title, event_name, created_at_utc) VALUES (?, ?, ?, ?)",
        (code, title, event_name, _utc_now()),
    )
    conn.commit()
    conn.close()


def get_session(session_code: str) -> dict | None:
    code = normalize_session_code(session_code)
    conn = _conn()
    row = conn.execute(
        "SELECT session_code, title, event_name, created_at_utc FROM workshop_sessions WHERE session_code=?",
        (code,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_submission(
    session_code: str,
    activity_key: str,
    display_name: str,
    content_text: str,
    *,
    anonymity_mode: bool = False,
) -> int:
    code = normalize_session_code(session_code)
    now = _utc_now()
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO workshop_submissions (session_code, activity_key, display_name, anonymity_mode, content_text, created_at_utc, updated_at_utc) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (code, activity_key, (display_name or "Participant").strip() or "Participant", int(bool(anonymity_mode)), content_text, now, now),
    )
    conn.commit()
    new_id = int(cur.lastrowid)
    conn.close()
    return new_id


def list_submissions(session_code: str, *, activity_key: str | None = None) -> list[dict]:
    code = normalize_session_code(session_code)
    conn = _conn()
    if activity_key:
        rows = conn.execute(
            "SELECT id, session_code, activity_key, display_name, anonymity_mode, content_text, created_at_utc, updated_at_utc "
            "FROM workshop_submissions WHERE session_code=? AND activity_key=? ORDER BY updated_at_utc DESC",
            (code, activity_key),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, session_code, activity_key, display_name, anonymity_mode, content_text, created_at_utc, updated_at_utc "
            "FROM workshop_submissions WHERE session_code=? ORDER BY updated_at_utc DESC",
            (code,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_feedback(
    session_code: str,
    submission_id: int,
    reviewer_display_name: str,
    strength: str,
    risk_or_gap: str,
    recommended_safeguard: str,
    reuse_suggestion: str,
) -> int:
    code = normalize_session_code(session_code)
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO workshop_feedback (session_code, submission_id, reviewer_display_name, strength, risk_or_gap, recommended_safeguard, reuse_suggestion, created_at_utc) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            code,
            int(submission_id),
            (reviewer_display_name or "Peer Reviewer").strip() or "Peer Reviewer",
            strength,
            risk_or_gap,
            recommended_safeguard,
            reuse_suggestion,
            _utc_now(),
        ),
    )
    conn.commit()
    feedback_id = int(cur.lastrowid)
    conn.close()
    return feedback_id


def list_feedback_for_session(session_code: str) -> dict[int, list[dict]]:
    code = normalize_session_code(session_code)
    conn = _conn()
    rows = conn.execute(
        "SELECT id, submission_id, reviewer_display_name, strength, risk_or_gap, recommended_safeguard, reuse_suggestion, created_at_utc "
        "FROM workshop_feedback WHERE session_code=? ORDER BY created_at_utc DESC",
        (code,),
    ).fetchall()
    conn.close()

    grouped: dict[int, list[dict]] = {}
    for r in rows:
        item = dict(r)
        grouped.setdefault(int(item["submission_id"]), []).append(item)
    return grouped


def export_session_markdown(session_code: str, *, session_title: str = "GLOW Workshop Session") -> str:
    code = normalize_session_code(session_code)
    submissions = list_submissions(code)
    feedback = list_feedback_for_session(code)

    lines: list[str] = []
    lines.append(f"# {session_title}")
    lines.append("")
    lines.append(f"Session code: `{code}`")
    lines.append("")
    lines.append("## Submissions")
    lines.append("")

    if not submissions:
        lines.append("No submissions captured yet.")
        lines.append("")
        return "\n".join(lines)

    for s in submissions:
        submitter = "Anonymous participant" if int(s.get("anonymity_mode", 0)) else s.get("display_name", "Participant")
        lines.append(f"### {s.get('activity_key', 'unknown_activity')}")
        lines.append("")
        lines.append(f"- Submitter: {submitter}")
        lines.append(f"- Updated (UTC): {s.get('updated_at_utc', '')}")
        lines.append("")
        lines.append("```text")
        lines.append((s.get("content_text") or "").strip())
        lines.append("```")
        lines.append("")

        items = feedback.get(int(s.get("id", 0)), [])
        if items:
            lines.append("#### Peer Feedback")
            lines.append("")
            for f in items:
                lines.append(f"- Reviewer: {f.get('reviewer_display_name', 'Peer Reviewer')}")
                lines.append(f"  - Strength: {f.get('strength', '')}")
                lines.append(f"  - Risk or gap: {f.get('risk_or_gap', '')}")
                lines.append(f"  - Recommended safeguard: {f.get('recommended_safeguard', '')}")
                lines.append(f"  - Reuse suggestion: {f.get('reuse_suggestion', '')}")
            lines.append("")

    return "\n".join(lines)
