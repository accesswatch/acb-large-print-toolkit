"""AI usage endpoint -- session-scoped request and token counts for the sidebar meter."""

from __future__ import annotations

from flask import Blueprint, jsonify, session

from acb_large_print_web.ai_gateway import get_quota_status, make_session_hash
from acb_large_print_web.credentials import (
    get_user_ollama_model,
    is_ollama_configured,
)

ai_usage_bp = Blueprint("ai_usage", __name__)


@ai_usage_bp.route("/", methods=["GET"])
def ai_usage():
    """Return AI usage counts for the current session as JSON.

    Shape:
        {
            "provider": "ollama" | "openrouter" | "none",
            "ollama_model": "llama3.2" | null,
            "session_requests_today": 4,
            "session_tokens_today": 12400,
            "chat_remaining_today": 46,   // null when Ollama (unlimited)
            "budget_pct_remaining": 84,   // null when Ollama (not our budget)
        }

    Designed to be polled from the sidebar meter after each AI action.
    Returns quickly -- reads only the SQLite ledger, never calls an AI API.
    """
    sess_id = session.get("_id", "")
    sess_hash = make_session_hash(sess_id) if sess_id else "anonymous"

    if is_ollama_configured():
        # For Ollama, count from the ledger but surface as request counts only --
        # Ollama billing is GPU-time based and we have no way to query their quota.
        quota = get_quota_status(sess_hash)
        return jsonify({
            "provider": "ollama",
            "ollama_model": get_user_ollama_model(),
            "session_requests_today": quota.get("chat_today", 0),
            "session_tokens_today": _session_tokens_today(sess_hash),
            "chat_remaining_today": None,
            "budget_pct_remaining": None,
        })

    # OpenRouter / server key path
    quota = get_quota_status(sess_hash)
    from acb_large_print_web.ai_gateway import get_monthly_spend, get_runtime_config
    cfg = get_runtime_config()
    monthly_budget = float(cfg.get("monthly_budget_usd", 20.0))
    spend = get_monthly_spend()
    pct_remaining = max(0, round(100 * (1 - spend / monthly_budget))) if monthly_budget else 100

    return jsonify({
        "provider": "openrouter",
        "ollama_model": None,
        "session_requests_today": quota.get("chat_today", 0),
        "session_tokens_today": _session_tokens_today(sess_hash),
        "chat_remaining_today": quota.get("chat_remaining_today"),
        "budget_pct_remaining": pct_remaining,
    })


def _session_tokens_today(session_hash: str) -> int:
    """Return the total tokens used by this session today from the SQLite ledger."""
    try:
        from acb_large_print_web.ai_gateway import _db
        from datetime import UTC, datetime
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        with _db() as conn:
            row = conn.execute(
                """SELECT COALESCE(SUM(input_tokens + output_tokens), 0)
                   FROM ai_cost_ledger
                   WHERE session_hash = ? AND request_at LIKE ?""",
                (session_hash, f"{today}%"),
            ).fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return 0
