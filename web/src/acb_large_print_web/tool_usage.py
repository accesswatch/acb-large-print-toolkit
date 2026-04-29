"""Persistent tool-usage counters backed by SQLite.

Each call to ``record(tool)`` atomically increments the counter for that tool
and updates a ``last_used_at`` timestamp.  Stored in ``instance/tool_usage.db``.

Tools tracked:
    audit       -- document audit (single or batch)
    fix         -- document fix
    convert     -- document conversion
    template    -- template builder
    whisperer   -- audio transcription (BITS Whisperer)
    chat        -- document chat
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from flask import current_app


# Human-friendly display labels for each tool key
TOOL_LABELS: dict[str, str] = {
    "audit":     "Audit",
    "fix":       "Fix",
    "convert":   "Convert",
    "template":  "Template Builder",
    "whisperer": "BITS Whisperer",
    "chat":      "Document Chat",
}


def _db_path() -> Path:
    p = Path(current_app.instance_path)
    p.mkdir(parents=True, exist_ok=True)
    return p / "tool_usage.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS usage ("
        "  tool TEXT PRIMARY KEY,"
        "  count INTEGER NOT NULL DEFAULT 0,"
        "  last_used_at TEXT"
        ")"
    )
    conn.commit()
    return conn


def record(tool: str, detail: str | None = None) -> None:
    """Increment the counter for *tool*.  Silently swallows errors."""
    _ = detail  # reserved for future per-direction breakdown
    try:
        now = datetime.now(UTC).isoformat()
        with _conn() as conn:
            conn.execute(
                "INSERT INTO usage (tool, count, last_used_at) VALUES (?, 1, ?)"
                " ON CONFLICT(tool) DO UPDATE SET count = count + 1, last_used_at = ?",
                (tool, now, now),
            )
    except Exception:
        pass


def get_all() -> list[dict]:
    """Return all counters as a list of dicts sorted by count descending.

    Each dict has keys: ``tool``, ``label``, ``count``, ``last_used_at``.
    Tools that have never been used are included with count 0.
    """
    try:
        with _conn() as conn:
            rows = {
                row[0]: {"count": row[1], "last_used_at": row[2]}
                for row in conn.execute(
                    "SELECT tool, count, last_used_at FROM usage"
                ).fetchall()
            }
    except Exception:
        rows = {}

    result = []
    for tool, label in TOOL_LABELS.items():
        data = rows.get(tool, {})
        result.append(
            {
                "tool": tool,
                "label": label,
                "count": data.get("count", 0),
                "last_used_at": data.get("last_used_at"),
            }
        )
    return sorted(result, key=lambda r: r["count"], reverse=True)


def get_total() -> int:
    """Return the sum of all tool use counts."""
    return sum(r["count"] for r in get_all())
