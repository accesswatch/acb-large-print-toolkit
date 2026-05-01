"""Speech conversion telemetry and adaptive estimation.

Tracks real document conversion runtimes so future estimates are based on this
server's actual observed throughput, not fixed heuristics.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from flask import current_app


def _db_path() -> Path:
    p = Path(current_app.instance_path)
    p.mkdir(parents=True, exist_ok=True)
    return p / "speech_metrics.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS document_conversions ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  created_at TEXT NOT NULL,"
        "  engine TEXT NOT NULL,"
        "  voice TEXT NOT NULL,"
        "  speed REAL NOT NULL,"
        "  pitch INTEGER NOT NULL,"
        "  word_count INTEGER NOT NULL,"
        "  char_count INTEGER NOT NULL,"
        "  source_size_bytes INTEGER NOT NULL,"
        "  processing_seconds REAL NOT NULL,"
        "  audio_seconds REAL NOT NULL"
        ")"
    )
    conn.commit()
    return conn


def record_document_conversion(
    *,
    engine: str,
    voice: str,
    speed: float,
    pitch: int,
    word_count: int,
    char_count: int,
    source_size_bytes: int,
    processing_seconds: float,
    audio_seconds: float,
) -> None:
    """Record one completed document-to-speech conversion."""
    try:
        now = datetime.now(UTC).isoformat()
        with _conn() as conn:
            conn.execute(
                "INSERT INTO document_conversions ("
                "created_at, engine, voice, speed, pitch, word_count, char_count, "
                "source_size_bytes, processing_seconds, audio_seconds"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    now,
                    str(engine or "unknown"),
                    str(voice or "unknown"),
                    float(speed),
                    int(pitch),
                    max(0, int(word_count)),
                    max(0, int(char_count)),
                    max(0, int(source_size_bytes)),
                    max(0.01, float(processing_seconds)),
                    max(0.0, float(audio_seconds)),
                ),
            )
    except Exception:
        # Telemetry must never break user workflow.
        return


def estimate_processing_seconds(
    *,
    engine: str,
    speed: float,
    word_count: int,
    char_count: int,
    source_size_bytes: int,
    baseline_seconds: float,
) -> tuple[float, str, int]:
    """Return adaptive estimate from historical records + baseline fallback.

    Returns: (estimated_seconds, estimate_source, sample_count)
    """
    try:
        with _conn() as conn:
            rows = conn.execute(
                "SELECT word_count, source_size_bytes, processing_seconds "
                "FROM document_conversions "
                "WHERE engine = ? AND speed BETWEEN ? AND ? "
                "ORDER BY id DESC LIMIT 250",
                (str(engine or "unknown"), float(speed) - 0.25, float(speed) + 0.25),
            ).fetchall()
    except Exception:
        rows = []

    sample_count = len(rows)
    if sample_count < 5:
        return max(1.0, float(baseline_seconds)), "baseline", sample_count

    per_word = []
    per_byte = []
    for r in rows:
        w = int(r[0] or 0)
        b = int(r[1] or 0)
        s = float(r[2] or 0)
        if s <= 0:
            continue
        if w > 0:
            per_word.append(s / w)
        if b > 0:
            per_byte.append(s / b)

    if not per_word:
        return max(1.0, float(baseline_seconds)), "baseline", sample_count

    est_by_word = median(per_word) * max(1, int(word_count))
    est = est_by_word

    if per_byte and source_size_bytes > 0:
        est_by_byte = median(per_byte) * int(source_size_bytes)
        est = (est_by_word * 0.75) + (est_by_byte * 0.25)

    # Confidence weighting: gradually trust historical model more as samples grow.
    # Caps at 70% model / 30% baseline.
    trust = min(0.7, sample_count / 80.0)
    blended = (float(baseline_seconds) * (1.0 - trust)) + (est * trust)
    return max(1.0, blended), "historical_blended", sample_count


def get_summary() -> dict:
    """High-level telemetry summary for admin/about surfaces."""
    try:
        with _conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*), AVG(processing_seconds), AVG(word_count), AVG(source_size_bytes) "
                "FROM document_conversions"
            ).fetchone()
        total = int(row[0] or 0)
        return {
            "samples": total,
            "avg_processing_seconds": float(row[1] or 0.0),
            "avg_words": float(row[2] or 0.0),
            "avg_source_size_bytes": float(row[3] or 0.0),
        }
    except Exception:
        return {
            "samples": 0,
            "avg_processing_seconds": 0.0,
            "avg_words": 0.0,
            "avg_source_size_bytes": 0.0,
        }
