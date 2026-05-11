"""AI usage endpoint -- session-scoped request and token counts for the sidebar meter."""

from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from acb_large_print_web.ai_gateway import estimate_request_cost, get_quota_status, make_session_hash
from acb_large_print_web.credentials import get_user_ollama_model, is_ollama_configured
from acb_large_print_web.user_ai import any_user_provider_configured, primary_active_provider

ai_usage_bp = Blueprint("ai_usage", __name__)


def _chat_turn_count(quota: dict) -> int:
    """Return the normalized chat-turn count from quota status payloads."""
    return int(quota.get("chat_turns_today", quota.get("chat_today", 0)) or 0)


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

    if any_user_provider_configured() or is_ollama_configured():
        quota = get_quota_status(sess_hash)
        provider = primary_active_provider() or {}
        return jsonify({
            "provider": str(provider.get("id") or ("ollama" if is_ollama_configured() else "personal")),
            "provider_label": str(provider.get("label") or "Personal AI"),
            "provider_model": str(provider.get("default_model") or ""),
            "ollama_model": str(provider.get("default_model") or ""),
            "session_requests_today": _chat_turn_count(quota),
            "session_tokens_today": _session_tokens_today(sess_hash),
            "chat_remaining_today": None,
            "budget_pct_remaining": None,
            "session_quota_enabled": quota.get("session_quota_enabled"),
            "session_requests_remaining": quota.get("session_requests_remaining"),
            "session_reset_seconds": quota.get("session_reset_seconds"),
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
        "session_requests_today": _chat_turn_count(quota),
        "session_tokens_today": _session_tokens_today(sess_hash),
        "chat_remaining_today": quota.get("chat_remaining_today"),
        "budget_pct_remaining": pct_remaining,
        "budget_remaining_usd": quota.get("budget_remaining_usd"),
        "session_quota_enabled": quota.get("session_quota_enabled"),
        "session_requests_remaining": quota.get("session_requests_remaining"),
        "session_reset_seconds": quota.get("session_reset_seconds"),
    })


@ai_usage_bp.route("/estimate", methods=["POST"])
def ai_estimate():
    """Return a rough token and cost estimate for a pending AI request."""
    payload = request.get_json(silent=True) or {}
    feature = str(payload.get("feature") or "chat").strip() or "chat"
    message = str(payload.get("message") or "")
    token_value = str(payload.get("token") or "")
    try:
        conversation_messages = int(payload.get("conversation_messages") or 0)
    except (TypeError, ValueError):
        conversation_messages = 0
    try:
        document_chars = int(payload.get("document_chars") or 0)
    except (TypeError, ValueError):
        document_chars = 0

    estimate = estimate_request_cost(
        feature=feature,
        message=message,
        token=token_value,
        conversation_messages=conversation_messages,
        document_chars=document_chars,
    )
    sess_id = session.get("_id", "")
    sess_hash = make_session_hash(sess_id) if sess_id else "anonymous"
    return jsonify({"ok": True, "estimate": estimate, "quota": get_quota_status(sess_hash)})


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
