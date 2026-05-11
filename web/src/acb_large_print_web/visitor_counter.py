"""Persistent unique-session visitor counter backed by SQLAlchemy.

Each Flask session is counted at most once (tracked via a session flag).
The counter uses the main application database (SQLite or PostgreSQL).
"""
from __future__ import annotations

from .db import db
from .models import VisitorCounter


def increment_and_get() -> int:
    """Atomically increment the visitor count and return the new value."""
    try:
        count = VisitorCounter.increment_and_get()
        db.session.commit()
        return count
    except Exception:
        db.session.rollback()
        return 0


def get_count() -> int:
    """Return the current visitor count without incrementing."""
    try:
        return VisitorCounter.get_count()
    except Exception:
        return 0
