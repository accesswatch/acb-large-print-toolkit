"""Speech conversion telemetry and adaptive estimation.

Tracks real document conversion runtimes so future estimates are based on this
server's actual observed throughput, not fixed heuristics.
"""

from __future__ import annotations

from datetime import UTC, datetime
from statistics import median

from sqlalchemy import func

from .db import db
from .models import SpeechConversionMetric


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
        record = SpeechConversionMetric(
            engine=str(engine or "unknown"),
            voice=str(voice or "unknown"),
            speed=float(speed),
            pitch=int(pitch),
            word_count=max(0, int(word_count)),
            char_count=max(0, int(char_count)),
            source_size_bytes=max(0, int(source_size_bytes)),
            processing_seconds=max(0.01, float(processing_seconds)),
            audio_seconds=max(0.0, float(audio_seconds)),
        )
        db.session.add(record)
        db.session.commit()
    except Exception:
        # Telemetry must never break user workflow.
        db.session.rollback()
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
        rows = db.session.execute(
            db.select(
                SpeechConversionMetric.word_count,
                SpeechConversionMetric.source_size_bytes,
                SpeechConversionMetric.processing_seconds,
            ).where(
                SpeechConversionMetric.engine == str(engine or "unknown"),
                SpeechConversionMetric.speed >= float(speed) - 0.25,
                SpeechConversionMetric.speed <= float(speed) + 0.25,
            ).order_by(SpeechConversionMetric.id.desc()).limit(250)
        ).all()
    except Exception:
        rows = []

    sample_count = len(rows)
    if sample_count < 5:
        return max(1.0, float(baseline_seconds)), "baseline", sample_count

    per_word = []
    per_byte = []
    for w, b, s in rows:
        word_count_val = int(w or 0)
        bytes_val = int(b or 0)
        seconds_val = float(s or 0)
        if seconds_val <= 0:
            continue
        if word_count_val > 0:
            per_word.append(seconds_val / word_count_val)
        if bytes_val > 0:
            per_byte.append(seconds_val / bytes_val)

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
        row = db.session.execute(
            db.select(
                func.count(SpeechConversionMetric.id),
                func.avg(SpeechConversionMetric.processing_seconds),
                func.avg(SpeechConversionMetric.word_count),
                func.avg(SpeechConversionMetric.source_size_bytes),
            )
        ).one()
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
