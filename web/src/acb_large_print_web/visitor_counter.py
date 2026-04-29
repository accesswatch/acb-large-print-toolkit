"""Persistent unique-session visitor counter backed by SQLite.

Each Flask session is counted at most once (tracked via a session flag).
The counter is stored in ``instance/visitor_counter.db`` alongside the
other instance-level databases.  All reads and writes go through SQLite
with WAL mode so concurrent gunicorn workers do not corrupt the value.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import current_app


def _db_path() -> Path:
    p = Path(current_app.instance_path)
    p.mkdir(parents=True, exist_ok=True)
    return p / "visitor_counter.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS counter (id INTEGER PRIMARY KEY CHECK (id = 1), visits INTEGER NOT NULL DEFAULT 0)"
    )
    # Ensure the single row exists
    conn.execute("INSERT OR IGNORE INTO counter (id, visits) VALUES (1, 0)")
    conn.commit()
    return conn


def increment_and_get() -> int:
    """Atomically increment the visitor count and return the new value."""
    with _conn() as conn:
        conn.execute("UPDATE counter SET visits = visits + 1 WHERE id = 1")
        row = conn.execute("SELECT visits FROM counter WHERE id = 1").fetchone()
        return int(row[0]) if row else 1


def get_count() -> int:
    """Return the current visitor count without incrementing."""
    try:
        with _conn() as conn:
            row = conn.execute("SELECT visits FROM counter WHERE id = 1").fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return 0
