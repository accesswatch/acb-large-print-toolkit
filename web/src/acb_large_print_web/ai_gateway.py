"""OpenRouter AI gateway with budget enforcement and quota tracking.

Single control plane for all AI inference in the GLOW web app.
Replaces on-device Ollama/faster-whisper with privacy-first open models.

Architecture
------------
Default path  : Privacy-reviewed OpenRouter models with ZDR + no-data-collection routing
Escalation    : Paid fallback model via OpenRouter (only when confidence < threshold)
Audio         : OpenRouter audio transcription endpoint (same OPENROUTER_API_KEY -- no extra key)
Budget        : $20/month hardcap tracked in SQLite cost ledger
Quotas        : 50 chat turns/day per anonymous session; 100 audio min/month

Server-side environment variables (NOT user-facing)
----------------------------------------------------
OPENROUTER_API_KEY      Required. Single key for all AI: chat, vision, and audio transcription.
AI_MONTHLY_BUDGET_USD   Hard cap USD (default 20.00)
AI_CHAT_DAILY_LIMIT     Chat turns per session per day (default 50)
AI_AUDIO_MONTHLY_MIN    Audio minutes per session per month (default 100)
AI_DEFAULT_MODEL        Primary OpenRouter model or comma list of models
AI_FALLBACK_MODEL       Escalation model or comma list of models
AI_VISION_MODEL         Vision-capable OpenRouter model for image analysis
AI_ESCALATION_THRESH    Confidence 0.0-1.0 below which escalation fires (default 0.7)

Privacy notes
-------------
- Requests are routed with provider-side privacy controls enabled whenever possible.
- GLOW uses OpenRouter provider filters (`dataCollection: deny`, `zdr: true`) for text requests.
- GLOW logs: metadata only -- no document text, no user content ever logged.
- All temp upload files deleted within 1 hour of job completion.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from .credentials import get_openrouter_api_key

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (resolved once at import time from environment)
# ---------------------------------------------------------------------------

_MONTHLY_BUDGET: float = float(os.environ.get("AI_MONTHLY_BUDGET_USD", "20.00"))
_CHAT_DAILY_LIMIT: int = int(os.environ.get("AI_CHAT_DAILY_LIMIT", "50"))
_AUDIO_MONTHLY_MIN: int = int(os.environ.get("AI_AUDIO_MONTHLY_MIN", "100"))
_DEFAULT_MODEL: str = os.environ.get(
    "AI_DEFAULT_MODEL", "openai/gpt-4o-mini"
)
_FALLBACK_MODEL: str = os.environ.get("AI_FALLBACK_MODEL", "openai/gpt-4o")
_VISION_MODEL: str = os.environ.get("AI_VISION_MODEL", "openai/gpt-4o-mini")
_ESCALATION_THRESH: float = float(os.environ.get("AI_ESCALATION_THRESH", "0.70"))
_WHISPER_MODEL: str = os.environ.get("WHISPER_MODEL", "openai/whisper-large-v3")

_DEFAULTS = {
    "monthly_budget_usd": _MONTHLY_BUDGET,
    "chat_daily_limit": _CHAT_DAILY_LIMIT,
    "audio_monthly_min": _AUDIO_MONTHLY_MIN,
    "default_model": _DEFAULT_MODEL,
    "fallback_model": _FALLBACK_MODEL,
    "vision_model": _VISION_MODEL,
    "escalation_thresh": _ESCALATION_THRESH,
    "whisper_model": _WHISPER_MODEL,
}

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_OPENROUTER_AUDIO_URL = f"{_OPENROUTER_BASE}/audio/transcriptions"
_OPENROUTER_CHAT_URL = f"{_OPENROUTER_BASE}/chat/completions"
_REQUEST_TIMEOUT = 60  # seconds
_OPENROUTER_MAX_RETRIES = int(os.environ.get("OPENROUTER_MAX_RETRIES", "2"))
_OPENROUTER_RETRY_BASE_SECONDS = float(os.environ.get("OPENROUTER_RETRY_BASE_SECONDS", "1.0"))

# Cost table: USD per 1 million tokens (input / output)
_COST_TABLE: dict[str, dict[str, float]] = {
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    # gpt-audio-mini: audio tokens billed at text-token equivalents via OpenRouter
    "openai/gpt-audio-mini": {"input": 0.15, "output": 0.60},
    # Legacy free models (kept for accounts that set these via AI_DEFAULT_MODEL env var)
    "meta-llama/llama-3-8b-instruct:free": {"input": 0.0, "output": 0.0},
    "mistralai/mistral-7b-instruct:free": {"input": 0.0, "output": 0.0},
}

# Phrases that signal the model is uncertain → trigger escalation
_UNCERTAINTY_MARKERS = frozenset(
    [
        "i'm not sure",
        "i don't know",
        "i cannot determine",
        "unclear",
        "i'm unable to",
        "i cannot",
        "not enough information",
        "cannot be determined",
        "i don't have enough",
        "i am not sure",
        "uncertain",
        "i'm unsure",
    ]
)


# ---------------------------------------------------------------------------
# Public availability checks
# ---------------------------------------------------------------------------


def is_ai_configured() -> bool:
    """Return True if the OpenRouter API key is set (AI features enabled)."""
    return bool(get_openrouter_api_key())


def is_whisper_configured() -> bool:
    """Return True if OpenRouter is configured (BITS Whisperer uses the same key)."""
    return is_ai_configured()


# ---------------------------------------------------------------------------
# SQLite cost ledger and quota tracking
# ---------------------------------------------------------------------------


def _db_path() -> Path:
    """Resolve instance path for the AI cost/quota database."""
    instance_path = Path(os.environ.get("FLASK_INSTANCE_PATH", "instance"))
    instance_path.mkdir(parents=True, exist_ok=True)
    return instance_path / "ai_quota.db"


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_cost_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_hash TEXT NOT NULL,
            request_at TEXT NOT NULL,
            workload TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            audio_seconds INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0,
            escalated INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_quota_sessions (
            session_hash TEXT NOT NULL,
            date TEXT NOT NULL,
            chat_turns INTEGER DEFAULT 0,
            audio_seconds INTEGER DEFAULT 0,
            PRIMARY KEY (session_hash, date)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def get_runtime_config() -> dict[str, Any]:
    """Return runtime config, with DB overrides on top of environment defaults."""
    cfg = dict(_DEFAULTS)
    try:
        with _db() as conn:
            rows = conn.execute("SELECT key, value FROM ai_settings").fetchall()
        for row in rows:
            k = row["key"]
            v = row["value"]
            if k in {"monthly_budget_usd", "escalation_thresh"}:
                cfg[k] = float(v)
            elif k in {"chat_daily_limit", "audio_monthly_min"}:
                cfg[k] = int(v)
            else:
                cfg[k] = v
    except Exception:
        pass
    return cfg


def update_runtime_config(updates: dict[str, Any]) -> None:
    """Persist runtime config updates from admin UI."""
    allowed = {
        "monthly_budget_usd",
        "chat_daily_limit",
        "audio_monthly_min",
        "default_model",
        "fallback_model",
        "vision_model",
        "escalation_thresh",
        "whisper_model",
    }
    now = datetime.now(UTC).isoformat()
    with _db() as conn:
        for k, v in updates.items():
            if k not in allowed:
                continue
            conn.execute(
                """
                INSERT INTO ai_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (k, str(v), now),
            )
        conn.commit()


def _compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a text completion."""
    rates = _COST_TABLE.get(model, {"input": 0.15, "output": 0.60})
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


def _record_usage(
    session_hash: str,
    workload: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    audio_seconds: int = 0,
    escalated: bool = False,
) -> float:
    """Write a usage record and return the cost incurred."""
    cost = _compute_cost(model, input_tokens, output_tokens)
    now = datetime.now(UTC).isoformat()
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    with _db() as conn:
        conn.execute(
            """
            INSERT INTO ai_cost_ledger
                (session_hash, request_at, workload, model, input_tokens,
                 output_tokens, audio_seconds, cost_usd, escalated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_hash,
                now,
                workload,
                model,
                input_tokens,
                output_tokens,
                audio_seconds,
                cost,
                int(escalated),
            ),
        )
        if workload == "chat":
            conn.execute(
                """
                INSERT INTO ai_quota_sessions (session_hash, date, chat_turns, audio_seconds)
                VALUES (?, ?, 1, 0)
                ON CONFLICT(session_hash, date) DO UPDATE SET chat_turns = chat_turns + 1
                """,
                (session_hash, today),
            )
        elif workload == "audio":
            conn.execute(
                """
                INSERT INTO ai_quota_sessions (session_hash, date, chat_turns, audio_seconds)
                VALUES (?, ?, 0, ?)
                ON CONFLICT(session_hash, date) DO UPDATE SET audio_seconds = audio_seconds + ?
                """,
                (session_hash, today, audio_seconds, audio_seconds),
            )
        conn.commit()

    log.info(
        "AI usage: session=%s workload=%s model=%s tokens=%d/%d cost=$%.4f escalated=%s",
        session_hash,
        workload,
        model,
        input_tokens,
        output_tokens,
        cost,
        escalated,
    )
    return cost


# ---------------------------------------------------------------------------
# Budget and quota checks
# ---------------------------------------------------------------------------


def get_monthly_spend() -> float:
    """Return total AI spend in USD for the current calendar month."""
    month = datetime.now(UTC).strftime("%Y-%m")
    try:
        with _db() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(cost_usd), 0.0) FROM ai_cost_ledger WHERE request_at LIKE ?",
                (f"{month}%",),
            ).fetchone()
            return float(row[0])
    except Exception:
        return 0.0


def is_budget_exhausted() -> bool:
    """Return True if the monthly hard cap has been reached."""
    cfg = get_runtime_config()
    return get_monthly_spend() >= float(cfg["monthly_budget_usd"])


def get_quota_status(session_hash: str) -> dict[str, Any]:
    """Return current quota state for a session (used in UI and admin)."""
    cfg = get_runtime_config()
    monthly_budget = float(cfg["monthly_budget_usd"])
    chat_daily_limit = int(cfg["chat_daily_limit"])
    audio_monthly_min = int(cfg["audio_monthly_min"])
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    month = datetime.now(UTC).strftime("%Y-%m")
    monthly_spend = get_monthly_spend()

    try:
        with _db() as conn:
            row = conn.execute(
                "SELECT chat_turns, audio_seconds FROM ai_quota_sessions WHERE session_hash=? AND date=?",
                (session_hash, today),
            ).fetchone()
            chat_today = int(row["chat_turns"]) if row else 0

            audio_row = conn.execute(
                """
                SELECT COALESCE(SUM(audio_seconds), 0) as total
                FROM ai_quota_sessions
                WHERE session_hash=? AND date LIKE ?
                """,
                (session_hash, f"{month}%"),
            ).fetchone()
            audio_month_seconds = int(audio_row["total"]) if audio_row else 0
    except Exception:
        chat_today = 0
        audio_month_seconds = 0

    audio_month_minutes = audio_month_seconds // 60

    return {
        "ai_configured": is_ai_configured(),
        "whisper_configured": is_whisper_configured(),
        "budget_usd": monthly_budget,
        "spent_usd": round(monthly_spend, 4),
        "budget_remaining_usd": round(max(0.0, monthly_budget - monthly_spend), 4),
        "budget_pct": round(min(100.0, monthly_spend / max(monthly_budget, 0.01) * 100), 1),
        "budget_exhausted": monthly_spend >= monthly_budget,
        "chat_turns_today": chat_today,
        "chat_daily_limit": chat_daily_limit,
        "chat_remaining_today": max(0, chat_daily_limit - chat_today),
        "chat_available": chat_today < chat_daily_limit and monthly_spend < monthly_budget,
        "audio_minutes_month": audio_month_minutes,
        "audio_monthly_limit": audio_monthly_min,
        "audio_remaining_min": max(0, audio_monthly_min - audio_month_minutes),
        "audio_available": audio_month_minutes < audio_monthly_min and monthly_spend < monthly_budget,
    }


def make_session_hash(flask_session_id: str) -> str:
    """Create a short stable anonymous hash from the Flask session identifier."""
    return hashlib.sha256(flask_session_id.encode()).hexdigest()[:24]


# ---------------------------------------------------------------------------
# Chat via OpenRouter
# ---------------------------------------------------------------------------


def _detect_uncertainty(text: str) -> bool:
    """Return True if the response appears uncertain (may benefit from escalation)."""
    lowered = text.lower()
    hits = sum(1 for marker in _UNCERTAINTY_MARKERS if marker in lowered)
    return hits >= 2


def _model_list(value: str) -> list[str]:
    """Normalize a comma-separated model config into a non-empty list."""
    return [item.strip() for item in value.split(",") if item.strip()]


def _provider_preferences(*, require_parameters: bool = False) -> dict[str, Any]:
    """Return OpenRouter provider routing preferences for privacy-sensitive workloads."""
    prefs: dict[str, Any] = {
        "dataCollection": "deny",
        "zdr": True,
        "allowFallbacks": True,
        "sort": "latency",
    }
    if require_parameters:
        prefs["requireParameters"] = True
    return prefs


def _openrouter_completion(
    model: str,
    messages: list[dict],
    user_id: str,
    max_tokens: int = 1200,
) -> tuple[str, int, int, str]:
    """Call OpenRouter chat completions.

    Returns (text, input_tokens, output_tokens, resolved_model).
    """
    api_key = get_openrouter_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://glow.bits-acb.org",
        "X-Title": "GLOW Accessibility Toolkit",
        "Content-Type": "application/json",
    }
    model_candidates = _model_list(model)
    payload: dict[str, Any] = {
        "model": model_candidates[0],
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "provider": _provider_preferences(require_parameters=False),
    }
    if len(model_candidates) > 1:
        payload["models"] = model_candidates
    if user_id:
        payload["user"] = user_id[:64]
    data = _openrouter_post_chat(payload, headers)
    text = data["choices"][0]["message"]["content"] or ""
    usage = data.get("usage", {})
    return (
        text,
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
        data.get("model") or model_candidates[0],
    )


def _openrouter_post_chat(payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    """POST OpenRouter chat completion with bounded retries on throttling/server faults."""
    attempts = max(0, _OPENROUTER_MAX_RETRIES)
    last_exc: Exception | None = None

    # Some providers reject advanced routing fields in otherwise valid requests.
    # Keep privacy routing as the default, but retry once with a compatibility
    # payload (no provider/models) when we receive 400/404 errors.
    compat_payload = dict(payload)
    compat_payload.pop("provider", None)
    compat_payload.pop("models", None)
    can_try_compat = compat_payload != payload

    for attempt in range(attempts + 1):
        try:
            resp = requests.post(
                f"{_OPENROUTER_BASE}/chat/completions",
                json=payload,
                headers=headers,
                timeout=_REQUEST_TIMEOUT,
            )
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < attempts:
                delay = _OPENROUTER_RETRY_BASE_SECONDS * (2**attempt)
                log.warning(
                    "OpenRouter transient status %s; retrying in %.2fs (attempt %d/%d)",
                    resp.status_code,
                    delay,
                    attempt + 1,
                    attempts,
                )
                time.sleep(delay)
                continue
            if resp.status_code in (400, 404) and can_try_compat:
                log.warning(
                    "OpenRouter returned %s with advanced routing fields; retrying with compatibility payload",
                    resp.status_code,
                )
                compat_resp = requests.post(
                    f"{_OPENROUTER_BASE}/chat/completions",
                    json=compat_payload,
                    headers=headers,
                    timeout=_REQUEST_TIMEOUT,
                )
                if compat_resp.ok:
                    return compat_resp.json()
                # Preserve the most relevant error context if compatibility also fails.
                compat_resp.raise_for_status()
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_exc = exc
            if attempt >= attempts:
                break
            delay = _OPENROUTER_RETRY_BASE_SECONDS * (2**attempt)
            log.warning(
                "OpenRouter request failed: %s; retrying in %.2fs (attempt %d/%d)",
                exc,
                delay,
                attempt + 1,
                attempts,
            )
            time.sleep(delay)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("OpenRouter request failed without exception details.")


def chat(
    question: str,
    system_prompt: str,
    session_hash: str,
    document_text: str = "",
    conversation_history: list[dict] | None = None,
) -> tuple[str, bool]:
    """Run a chat completion through the AI gateway.

    Returns:
        (answer_text, was_escalated)

    Raises:
        RuntimeError: if AI is not configured or budget/quota is exhausted.
    """
    if not is_ai_configured():
        raise RuntimeError("AI is not configured on this server.")

    if is_budget_exhausted():
        raise RuntimeError(
            "The monthly AI budget has been reached. AI features will resume next month."
        )

    cfg = get_runtime_config()
    default_model = str(cfg["default_model"])
    fallback_model = str(cfg["fallback_model"])

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history)
    if document_text:
        messages.append(
            {
                "role": "user",
                "content": f"Document excerpt (first 4000 chars):\n{document_text[:4000]}",
            }
        )
    messages.append({"role": "user", "content": question})

    # --- Try default (free) model first ---
    try:
        answer, in_tok, out_tok, resolved_model = _openrouter_completion(
            default_model,
            messages,
            session_hash,
        )
    except Exception as exc:
        log.warning("Default model failed (%s), escalating: %s", default_model, exc)
        answer, in_tok, out_tok, resolved_model = _openrouter_completion(
            fallback_model,
            messages,
            session_hash,
        )
        _record_usage(session_hash, "chat", resolved_model, in_tok, out_tok, escalated=True)
        return answer, True

    # --- Escalate if uncertain ---
    escalated = False
    if _detect_uncertainty(answer):
        try:
            escalated_answer, in_tok2, out_tok2, resolved_fallback_model = _openrouter_completion(
                fallback_model,
                messages,
                session_hash,
            )
            _record_usage(
                session_hash, "chat", resolved_model, in_tok, out_tok, escalated=False
            )
            _record_usage(
                session_hash, "chat", resolved_fallback_model, in_tok2, out_tok2, escalated=True
            )
            return escalated_answer, True
        except Exception as exc:
            log.warning("Escalation to %s failed: %s", fallback_model, exc)

    _record_usage(session_hash, "chat", resolved_model, in_tok, out_tok, escalated=False)
    return answer, escalated


def describe_image(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    session_hash: str,
) -> str:
    """Describe image content using a vision-capable OpenRouter model."""
    if not is_ai_configured():
        raise RuntimeError("AI is not configured on this server.")

    if is_budget_exhausted():
        raise RuntimeError(
            "The monthly AI budget has been reached. Vision analysis will resume next month."
        )

    cfg = get_runtime_config()
    vision_model = str(cfg.get("vision_model") or _VISION_MODEL)
    api_key = get_openrouter_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://glow.bits-acb.org",
        "X-Title": "GLOW Accessibility Toolkit",
        "Content-Type": "application/json",
    }

    encoded = base64.b64encode(image_bytes).decode("ascii")
    data_uri = f"data:{mime_type};base64,{encoded}"
    payload: dict[str, Any] = {
        "model": vision_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an accessibility assistant. Describe visible content accurately, "
                    "extract readable text when possible, and call out accessibility-relevant "
                    "elements such as headings, charts, labels, and figure meaning."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            },
        ],
        "max_tokens": 700,
        "temperature": 0.2,
        "provider": _provider_preferences(require_parameters=False),
        "user": session_hash[:64],
    }

    data = _openrouter_post_chat(payload, headers)
    text = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
    usage = data.get("usage", {})
    model_used = data.get("model") or vision_model
    _record_usage(
        session_hash,
        "vision",
        model_used,
        int(usage.get("prompt_tokens", 0) or 0),
        int(usage.get("completion_tokens", 0) or 0),
        escalated=False,
    )
    return text


# ---------------------------------------------------------------------------
# Audio transcription via OpenAI Whisper API
# ---------------------------------------------------------------------------


def transcribe(
    audio_path: Path,
    language: str | None,
    session_hash: str,
) -> str:
    """Transcribe audio using OpenRouter.

    Primary path: chat/completions with input_audio (openai/gpt-audio-mini).
    This path is resilient and token-cost-tracked.

    Fallback path: /audio/transcriptions (openai/whisper-large-v3).
    Used only when the primary path fails; cost estimated from file size.

    Returns the transcript as plain text.

    Raises:
        RuntimeError: if Whisper is not configured, budget is exhausted,
            a 402 balance error is returned, or both paths fail.
    """
    if not is_whisper_configured():
        raise RuntimeError("Audio transcription is not configured on this server.")

    if is_budget_exhausted():
        raise RuntimeError(
            "The monthly AI budget has been reached. Audio transcription will resume next month."
        )

    cfg = get_runtime_config()
    whisper_model = str(cfg.get("whisper_model", _WHISPER_MODEL))
    api_key = get_openrouter_api_key()

    transcript: str | None = None
    input_audio_error: str | None = None
    audio_model_used: str = "openai/gpt-audio-mini"
    audio_in_tokens: int = 0
    audio_out_tokens: int = 0
    path_used: str = "input_audio"

    # --- Primary path: chat/completions + input_audio (gpt-audio-mini) ---
    # Preferred because: token-cost-tracked, stable, no upstream 5xx HTML errors.
    try:
        transcript, audio_in_tokens, audio_out_tokens = _transcribe_via_input_audio(
            audio_path=audio_path,
            api_key=api_key,
            language=language,
            session_hash=session_hash,
        )
        path_used = "input_audio"
    except requests.HTTPError as exc:
        resp_obj = exc.response
        input_audio_error = _extract_openrouter_error(resp_obj)
        if resp_obj is not None and resp_obj.status_code == 402:
            raise RuntimeError(
                "OpenRouter audio transcription requires a minimum account balance. "
                "Top up your OpenRouter account (at least $0.50) to enable BITS Whisperer."
            ) from exc
        log.warning(
            "Audio input_audio path failed (HTTP %s): %s -- trying direct endpoint",
            resp_obj.status_code if resp_obj is not None else "n/a",
            input_audio_error,
        )
    except requests.RequestException as exc:
        input_audio_error = str(exc)
        log.warning("Audio input_audio path failed: %s -- trying direct endpoint", exc)

    # --- Fallback path: /audio/transcriptions (whisper-large-v3) ---
    # Used when primary fails due to provider issues (e.g. upstream 5xx).
    if transcript is None:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://glow.bits-acb.org",
            "X-Title": "GLOW Accessibility Toolkit",
        }
        try:
            with open(audio_path, "rb") as f:
                files = {"file": (audio_path.name, f, "audio/mpeg")}
                form_data: dict[str, Any] = {"model": whisper_model, "response_format": "text"}
                if language:
                    form_data["language"] = language
                resp = requests.post(
                    _OPENROUTER_AUDIO_URL,
                    headers=headers,
                    files=files,
                    data=form_data,
                    timeout=300,
                )
            if resp.ok:
                transcript = resp.text.strip()
                audio_model_used = whisper_model
                path_used = "direct"
            else:
                direct_error = _extract_openrouter_error(resp)
                if resp.status_code == 500 and "<!DOCTYPE" in (resp.text or ""):
                    raise RuntimeError(
                        "OpenRouter audio transcription is currently unavailable "
                        "(upstream provider error on direct endpoint, and the "
                        f"primary audio path also failed: {input_audio_error or 'unknown'}). "
                        "Please try again later."
                    )
                raise RuntimeError(
                    f"OpenRouter audio transcription failed. "
                    f"Primary path: {input_audio_error or 'n/a'}. "
                    f"Fallback path: {direct_error}."
                )
        except RuntimeError:
            raise
        except requests.RequestException as exc:
            raise RuntimeError(
                "OpenRouter audio transcription failed on both paths. "
                f"Primary (input_audio) error: {input_audio_error or 'n/a'}. "
                f"Fallback (direct) error: {exc}."
            ) from exc

    # --- Cost and quota tracking ---
    if path_used == "input_audio":
        # Token-based cost (same rate as gpt-4o-mini for now)
        _record_usage(
            session_hash,
            "audio",
            audio_model_used,
            audio_in_tokens,
            audio_out_tokens,
            escalated=False,
        )
        estimated_seconds = max(1, audio_in_tokens // 10)  # rough audio-token-to-seconds
    else:
        # Size-based estimate for direct Whisper endpoint (no token response)
        try:
            size_bytes = audio_path.stat().st_size
            estimated_seconds = max(1, size_bytes // 16_000)
        except Exception:
            estimated_seconds = 60
        cost = (estimated_seconds / 60) * 0.006
        now = datetime.now(UTC).isoformat()
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        try:
            with _db() as conn:
                conn.execute(
                    """
                    INSERT INTO ai_cost_ledger
                        (session_hash, request_at, workload, model, audio_seconds, cost_usd, escalated)
                    VALUES (?, ?, 'audio', ?, ?, ?, 0)
                    """,
                    (session_hash, now, audio_model_used, estimated_seconds, cost),
                )
                conn.execute(
                    """
                    INSERT INTO ai_quota_sessions (session_hash, date, chat_turns, audio_seconds)
                    VALUES (?, ?, 0, ?)
                    ON CONFLICT(session_hash, date) DO UPDATE SET audio_seconds = audio_seconds + ?
                    """,
                    (session_hash, today, estimated_seconds, estimated_seconds),
                )
                conn.commit()
        except Exception as exc:
            log.warning("Failed to record audio usage: %s", exc)

    log.info(
        "Whisper transcription: session=%s path=%s model=%s seconds~=%d",
        session_hash,
        path_used,
        audio_model_used,
        estimated_seconds,
    )
    return transcript


def _extract_openrouter_error(resp: requests.Response | None) -> str:
    """Extract a useful error string from OpenRouter JSON or HTML responses."""
    if resp is None:
        return "No response received"
    try:
        payload = resp.json()
        if isinstance(payload, dict):
            err = payload.get("error")
            if isinstance(err, dict) and err.get("message"):
                return str(err["message"])
        return str(payload)
    except Exception:
        body = (resp.text or "").strip().replace("\n", " ")
        return f"HTTP {resp.status_code}: {body[:300]}"


def _transcribe_via_input_audio(
    audio_path: Path,
    api_key: str,
    language: str | None,
    session_hash: str,
) -> tuple[str, int, int]:
    """Primary transcription via chat/completions + input_audio (openai/gpt-audio-mini).

    Documented by OpenRouter's multimodal audio guide:
    https://openrouter.ai/docs/guides/overview/multimodal/audio

    Returns:
        (transcript_text, input_tokens, output_tokens)

    Raises:
        requests.HTTPError: on non-2xx responses (caller inspects status code).
    """
    ext = audio_path.suffix.lower().lstrip(".") or "mp3"
    if ext not in {"mp3", "wav", "m4a", "ogg", "flac", "aac", "opus", "webm", "mp4", "mpeg", "mpga"}:
        ext = "mp3"

    encoded_audio = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    system_prompt = (
        "You are a transcription assistant. Return only the transcript text. "
        "Do not add summaries, speaker labels, or extra commentary."
    )
    user_prompt = "Transcribe this audio to plain text."
    if language:
        user_prompt += f" Language hint: {language}."

    payload: dict[str, Any] = {
        "model": "openai/gpt-audio-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encoded_audio,
                            "format": ext,
                        },
                    },
                ],
            },
        ],
        "max_tokens": 4000,
        "temperature": 0,
        "user": session_hash[:64],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://glow.bits-acb.org",
        "X-OpenRouter-Title": "GLOW Accessibility Toolkit",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        _OPENROUTER_CHAT_URL,
        headers=headers,
        json=payload,
        timeout=300,
    )
    resp.raise_for_status()
    data = resp.json()
    text = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
    usage = data.get("usage", {})
    return text, int(usage.get("prompt_tokens", 0) or 0), int(usage.get("completion_tokens", 0) or 0)


# ---------------------------------------------------------------------------
# Admin telemetry queries
# ---------------------------------------------------------------------------


def get_admin_stats() -> dict[str, Any]:
    """Return aggregated stats for the admin quota dashboard."""
    cfg = get_runtime_config()
    monthly_budget = float(cfg["monthly_budget_usd"])
    month = datetime.now(UTC).strftime("%Y-%m")
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    try:
        with _db() as conn:
            # Monthly totals
            monthly = conn.execute(
                """
                SELECT
                    COUNT(*) as requests,
                    COALESCE(SUM(cost_usd), 0) as spend,
                    COALESCE(SUM(CASE WHEN escalated=1 THEN 1 ELSE 0 END), 0) as escalations,
                    COALESCE(SUM(CASE WHEN workload='chat' THEN 1 ELSE 0 END), 0) as chat_count,
                    COALESCE(SUM(CASE WHEN workload='audio' THEN 1 ELSE 0 END), 0) as audio_count,
                    COALESCE(SUM(audio_seconds), 0) as audio_seconds
                FROM ai_cost_ledger WHERE request_at LIKE ?
                """,
                (f"{month}%",),
            ).fetchone()

            # Daily spend trend (last 14 days)
            daily_rows = conn.execute(
                """
                SELECT
                    substr(request_at, 1, 10) as day,
                    COALESCE(SUM(cost_usd), 0) as spend,
                    COUNT(*) as requests
                FROM ai_cost_ledger
                WHERE request_at >= date('now', '-13 days')
                GROUP BY day ORDER BY day
                """,
            ).fetchall()

            # Today totals
            today_row = conn.execute(
                """
                SELECT COUNT(*) as requests, COALESCE(SUM(cost_usd), 0) as spend
                FROM ai_cost_ledger WHERE request_at LIKE ?
                """,
                (f"{today}%",),
            ).fetchone()

            # Unique sessions this month
            session_count = conn.execute(
                "SELECT COUNT(DISTINCT session_hash) FROM ai_cost_ledger WHERE request_at LIKE ?",
                (f"{month}%",),
            ).fetchone()[0]

    except Exception as exc:
        log.warning("Admin stats query failed: %s", exc)
        return {}

    monthly_spend = float(monthly["spend"])
    return {
        "month": month,
        "today": today,
        "budget_usd": monthly_budget,
        "monthly_spend": round(monthly_spend, 4),
        "budget_remaining": round(max(0.0, monthly_budget - monthly_spend), 4),
        "budget_pct": round(min(100.0, monthly_spend / max(monthly_budget, 0.01) * 100), 1),
        "budget_exhausted": monthly_spend >= monthly_budget,
        "monthly_requests": int(monthly["requests"]),
        "monthly_escalations": int(monthly["escalations"]),
        "monthly_chat": int(monthly["chat_count"]),
        "monthly_audio": int(monthly["audio_count"]),
        "monthly_audio_minutes": int(monthly["audio_seconds"]) // 60,
        "today_requests": int(today_row["requests"]),
        "today_spend": round(float(today_row["spend"]), 4),
        "unique_sessions_month": int(session_count),
        "escalation_rate_pct": round(
            int(monthly["escalations"]) / max(int(monthly["requests"]), 1) * 100, 1
        ),
        "default_model": str(cfg["default_model"]),
        "fallback_model": str(cfg["fallback_model"]),
        "vision_model": str(cfg.get("vision_model", _VISION_MODEL)),
        "chat_daily_limit": int(cfg["chat_daily_limit"]),
        "audio_monthly_limit_min": int(cfg["audio_monthly_min"]),
        "daily_trend": [
            {"day": r["day"], "spend": round(float(r["spend"]), 4), "requests": int(r["requests"])}
            for r in daily_rows
        ],
    }


def get_model_catalog() -> list[dict[str, Any]]:
    """Fetch OpenRouter model catalog with pricing metadata.

    Returns a simplified list suitable for admin dropdowns and cost projection.
    """
    if not is_ai_configured():
        return []
    api_key = get_openrouter_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://glow.bits-acb.org",
        "X-Title": "GLOW Accessibility Toolkit",
    }
    try:
        resp = requests.get(f"{_OPENROUTER_BASE}/models", headers=headers, timeout=20)
        resp.raise_for_status()
        raw = resp.json().get("data", [])
        out: list[dict[str, Any]] = []
        for m in raw:
            pricing = m.get("pricing", {}) or {}
            in_price = float(pricing.get("prompt", 0) or 0)
            out_price = float(pricing.get("completion", 0) or 0)
            out.append(
                {
                    "id": m.get("id", ""),
                    "name": m.get("name") or m.get("id", ""),
                    "context_length": m.get("context_length", 0),
                    "input_per_million": round(in_price * 1_000_000, 6),
                    "output_per_million": round(out_price * 1_000_000, 6),
                }
            )
        out.sort(key=lambda x: (x["input_per_million"], x["output_per_million"], x["id"]))
        return out
    except Exception as exc:
        log.warning("OpenRouter model catalog fetch failed: %s", exc)
        # Fallback to known baseline entries
        return [
            {
                "id": "meta-llama/llama-3-8b-instruct:free",
                "name": "Llama 3 8B (free)",
                "context_length": 8192,
                "input_per_million": 0.0,
                "output_per_million": 0.0,
            },
            {
                "id": "openai/gpt-4o-mini",
                "name": "GPT-4o mini",
                "context_length": 128000,
                "input_per_million": 0.15,
                "output_per_million": 0.60,
            },
        ]


def project_monthly_cost(
    model_id: str,
    monthly_requests: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
) -> float:
    """Project monthly spend from simple traffic assumptions."""
    rates = _COST_TABLE.get(model_id, {"input": 0.15, "output": 0.60})
    total_in = monthly_requests * avg_input_tokens
    total_out = monthly_requests * avg_output_tokens
    return round((total_in * rates["input"] + total_out * rates["output"]) / 1_000_000, 4)
