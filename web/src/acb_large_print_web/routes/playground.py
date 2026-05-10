"""AI Playground -- open-ended Ollama chat sandbox (Beta).

This route provides a standalone conversational interface for testing
Ollama AI capabilities without a document context.  It is intentionally
simple: no tool-calling, no agentic flow, no document upload.  The goal
is a clean surface for evaluating model behaviour before wiring it into
more complex GLOW workflows.

Routes
------
GET  /beta/chat/        -- Playground page
POST /beta/chat/send    -- Streaming-ready JSON chat endpoint
POST /beta/chat/clear   -- Clear server-side conversation history
"""

from __future__ import annotations

import hashlib
import logging

from flask import Blueprint, jsonify, render_template, request, session

from ..ai_features import AIFeatureDisabled, require_ai_feature
from ..app import limiter
from ..credentials import (
    OLLAMA_FEATURE_LABELS,
    OLLAMA_MODEL_RECOMMENDATIONS,
    get_user_ollama_model_for,
    is_ollama_configured,
)

log = logging.getLogger(__name__)

playground_bp = Blueprint("playground", __name__)

_PLAYGROUND_HISTORY_KEY = "playground_history"
_MAX_HISTORY_TURNS = 20       # keep last N user/assistant pairs in session
_MAX_QUESTION_LEN  = 3000
_SYSTEM_PROMPT = (
    "You are a helpful, friendly AI assistant embedded in GLOW -- an "
    "accessibility-focused document workflow tool for the blind and low-vision "
    "community.  Answer clearly and concisely.  When uncertain, say so.  "
    "You are running as an Ollama model supplied by the user for testing purposes."
)


def _session_hash() -> str:
    key = session.get("ollama_api_key", "anon")
    return hashlib.sha256(key.encode()).hexdigest()


def _get_history() -> list[dict]:
    return list(session.get(_PLAYGROUND_HISTORY_KEY, []))


def _set_history(history: list[dict]) -> None:
    # Trim to last N pairs (each pair = 2 messages)
    turns = _MAX_HISTORY_TURNS * 2
    session[_PLAYGROUND_HISTORY_KEY] = history[-turns:]
    session.modified = True


@playground_bp.route("/", methods=["GET"])
def playground_page():
    """Render the AI Playground page."""
    return render_template(
        "beta_chat.html",
        ollama_active=is_ollama_configured(),
        playground_model=get_user_ollama_model_for("playground"),
        model_recommendations=OLLAMA_MODEL_RECOMMENDATIONS,
        feature_label=OLLAMA_FEATURE_LABELS.get("playground", "AI Playground"),
        history=_get_history(),
    )


@playground_bp.route("/send", methods=["POST"])
@limiter.limit("30 per minute")
def playground_send():
    """Process a single chat turn and return the assistant reply as JSON.

    Request (JSON or form):
        message  str   The user's message

    Response (JSON):
        {ok: true,  reply: str, model: str}
        {ok: false, error: str}
    """
    # Gate: Ollama key must be active; playground feature must be enabled
    try:
        require_ai_feature("playground")
    except AIFeatureDisabled as exc:
        return jsonify({"ok": False, "error": str(exc)}), 403

    if not is_ollama_configured():
        return jsonify({"ok": False, "error": "The AI Playground requires your personal Ollama key."}), 403

    raw = request.get_json(silent=True) or {}
    message = (raw.get("message") or request.form.get("message") or "").strip()

    if not message:
        return jsonify({"ok": False, "error": "Message cannot be empty."}), 400
    if len(message) > _MAX_QUESTION_LEN:
        return jsonify({"ok": False, "error": f"Message too long (max {_MAX_QUESTION_LEN} characters)."}), 400

    from ..ai_gateway import chat as gateway_chat, make_session_hash

    history = _get_history()
    sess_hash = make_session_hash(session)

    try:
        reply, _ = gateway_chat(
            question=message,
            system_prompt=_SYSTEM_PROMPT,
            session_hash=sess_hash,
            conversation_history=history,
            feature="playground",
        )
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 503

    # Append this turn to history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    _set_history(history)

    model_used = get_user_ollama_model_for("playground")
    return jsonify({"ok": True, "reply": reply, "model": model_used})


@playground_bp.route("/clear", methods=["POST"])
def playground_clear():
    """Wipe the server-side conversation history for this session."""
    session.pop(_PLAYGROUND_HISTORY_KEY, None)
    session.modified = True
    return jsonify({"ok": True})
