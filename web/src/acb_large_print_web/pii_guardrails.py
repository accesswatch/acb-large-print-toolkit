"""PII guardrails for AI-bound text using Microsoft Presidio."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from flask import current_app

from . import feature_flags


def _flag_enabled(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is not None:
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return feature_flags.get_flag(name, default)


def pii_guardrails_enabled() -> bool:
    return _flag_enabled("GLOW_ENABLE_PII_GUARDRAILS", True)


def pii_guardrails_strict_mode_enabled() -> bool:
    return _flag_enabled("GLOW_ENABLE_PII_GUARDRAILS_STRICT_MODE", True)


@lru_cache(maxsize=1)
def _presidio_engines() -> tuple[Any, Any]:
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
    except ImportError as exc:
        raise RuntimeError(
            "PII guardrails are enabled but Presidio is not installed. "
            "Install presidio-analyzer and presidio-anonymizer."
        ) from exc
    return AnalyzerEngine(), AnonymizerEngine()


def _redact_text(text: str) -> tuple[str, int]:
    analyzer, anonymizer = _presidio_engines()
    entities = analyzer.analyze(text=text, language="en")
    if not entities:
        return text, 0
    anonymized = anonymizer.anonymize(text=text, analyzer_results=entities)
    return anonymized.text, len(entities)


def sanitize_text_for_ai(
    text: str,
    *,
    surface: str,
    strict: bool | None = None,
) -> tuple[str, dict[str, Any]]:
    """Return text sanitized for AI calls with metadata."""
    raw = str(text or "")
    enabled = pii_guardrails_enabled()
    if not raw or not enabled:
        return raw, {"enabled": enabled, "applied": False, "redacted": False, "entity_count": 0}

    strict_mode = pii_guardrails_strict_mode_enabled() if strict is None else bool(strict)
    try:
        sanitized, entity_count = _redact_text(raw)
    except RuntimeError as exc:
        if strict_mode:
            raise RuntimeError(str(exc)) from exc
        current_app.logger.warning("PII guardrails unavailable for %s: %s", surface, exc)
        return raw, {
            "enabled": True,
            "applied": False,
            "redacted": False,
            "entity_count": 0,
            "error": str(exc),
        }

    return sanitized, {
        "enabled": True,
        "applied": True,
        "redacted": sanitized != raw,
        "entity_count": entity_count,
    }
