"""Settings route -- user preference controls with opt-in persistence."""

import logging

import requests
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from acb_large_print_web.rules import get_all_rule_ids
from acb_large_print_web.credentials import (
    OLLAMA_FEATURE_DEFAULTS,
    OLLAMA_FEATURE_LABELS,
    OLLAMA_FEATURE_MODEL_DEFAULTS,
    OLLAMA_MODEL_RECOMMENDATIONS,
    get_ollama_cloud_url,
    get_user_ollama_features,
    get_user_ollama_key,
    get_user_ollama_model,
    get_user_ollama_model_for,
    is_ollama_configured,
)

log = logging.getLogger(__name__)
settings_bp = Blueprint("settings", __name__)
ai_bp = Blueprint("ai", __name__)

_OLLAMA_VALID_MODELS = {m["id"] for m in OLLAMA_MODEL_RECOMMENDATIONS}


def _trim_text(value: object, limit: int = 300) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit - 1]}..."


def _render_ai_settings_page():
    features = get_user_ollama_features()
    # Build per-feature model map for template
    feature_models = {
        feature: get_user_ollama_model_for(feature)
        for feature in OLLAMA_FEATURE_DEFAULTS
    }
    return render_template(
        "settings_ai.html",
        ollama_active=is_ollama_configured(),
        ollama_model=get_user_ollama_model(),
        model_recommendations=OLLAMA_MODEL_RECOMMENDATIONS,
        ollama_features=features,
        ollama_feature_labels=OLLAMA_FEATURE_LABELS,
        ollama_feature_defaults=OLLAMA_FEATURE_DEFAULTS,
        ollama_feature_model_defaults=OLLAMA_FEATURE_MODEL_DEFAULTS,
        ollama_feature_models=feature_models,
    )


@settings_bp.route("/", methods=["GET"])
def settings_page():
    return render_template(
        "settings.html",
        total_rules=len(get_all_rule_ids()),
    )


@settings_bp.route("/ai", methods=["GET"])
def settings_ai_redirect():
    """Legacy AI settings path kept for existing links and cached pages."""
    return redirect(url_for("ai.settings_ai_page"), code=302)


@ai_bp.route("/", methods=["GET"])
def settings_ai_page():
    """Dedicated page for Ollama AI key setup, model selection, and feature toggles."""
    return _render_ai_settings_page()


@settings_bp.route("/ai/key", methods=["POST"])
@ai_bp.route("/key", methods=["POST"])
def save_ollama_key():
    """Save the user's Ollama API key and chosen model to the session.

    The key is held only in server-side session storage and is never logged
    or written to disk. The session cookie is HttpOnly and Secure.
    """
    api_key = (request.form.get("ollama_api_key") or "").strip()
    model = (request.form.get("ollama_model") or "llama3.2").strip()

    if not api_key:
        return jsonify({"ok": False, "error": "API key is required."}), 400

    # Reject keys that look obviously wrong (Ollama keys start with "ollama_")
    if not api_key.startswith("ollama_"):
        return jsonify({
            "ok": False,
            "error": "That does not look like an Ollama API key. Keys begin with 'ollama_'.",
        }), 400

    # Validate model against known list; allow unknown models with a warning
    if model not in _OLLAMA_VALID_MODELS:
        log.info("User supplied unlisted Ollama model: %s", model)

    session["ollama_api_key"] = api_key
    session["ollama_model"] = model
    # Write feature defaults only when activating a key for the first time;
    # preserve existing user choices on key rotation.
    if "ollama_features" not in session:
        session["ollama_features"] = dict(OLLAMA_FEATURE_DEFAULTS)
    session.modified = True

    return jsonify({"ok": True, "model": model})


@settings_bp.route("/ai/key", methods=["DELETE"])
@ai_bp.route("/key", methods=["DELETE"])
def forget_ollama_key():
    """Remove the Ollama API key, model, and feature toggles from the session."""
    session.pop("ollama_api_key", None)
    session.pop("ollama_model", None)
    session.pop("ollama_features", None)
    session.modified = True
    return jsonify({"ok": True})


@settings_bp.route("/ai/features", methods=["POST"])
@ai_bp.route("/features", methods=["POST"])
def save_ollama_features():
    """Persist the user's per-feature Ollama enable choices to the session.

    Accepts form fields named ``feature_<key>`` (checkboxes -- present when
    checked, absent when unchecked). Only recognises keys declared in
    OLLAMA_FEATURE_DEFAULTS; unknown keys are ignored.
    """
    if not is_ollama_configured():
        return jsonify({"ok": False, "error": "No Ollama key active."}), 400

    updated: dict[str, bool] = {}
    for feature in OLLAMA_FEATURE_DEFAULTS:
        updated[feature] = request.form.get(f"feature_{feature}") == "1"

    session["ollama_features"] = updated

    # Persist per-feature model selections
    feature_models: dict[str, str] = {}
    valid_model_ids = {m["id"] for m in OLLAMA_MODEL_RECOMMENDATIONS}
    for feature in OLLAMA_FEATURE_DEFAULTS:
        chosen = (request.form.get(f"model_{feature}") or "").strip()
        if chosen and (chosen in valid_model_ids or len(chosen) <= 80):
            feature_models[feature] = chosen
        else:
            feature_models[feature] = OLLAMA_FEATURE_MODEL_DEFAULTS.get(feature, "llama3.2")

    session["ollama_feature_models"] = feature_models
    session.modified = True

    enabled = [OLLAMA_FEATURE_LABELS.get(k, k) for k, v in updated.items() if v]
    return jsonify({"ok": True, "enabled": enabled})


@settings_bp.route("/ai/validate", methods=["POST"])
@ai_bp.route("/validate", methods=["POST"])
def validate_ollama_key():
    """Validate an Ollama API key by making a lightweight /api/tags request.

    Returns JSON {ok: bool, models: [...], error: str}.
    The candidate key is read from the POST body, not yet saved to session.
    """
    api_key = (request.form.get("ollama_api_key") or "").strip()
    if not api_key:
        return jsonify({"ok": False, "error": "No key supplied."}), 400

    base_url = get_ollama_cloud_url()
    try:
        resp = requests.get(
            f"{base_url}/tags",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if resp.status_code == 401:
            return jsonify({"ok": False, "error": "Key rejected -- check it and try again."}), 200
        if resp.status_code == 429:
            return jsonify({"ok": False, "error": "Rate limited. Wait a moment and try again."}), 200
        resp.raise_for_status()
        data = resp.json()
        model_names = [m.get("name", "") for m in data.get("models", [])]
        return jsonify({"ok": True, "models": model_names[:20]})
    except requests.RequestException as exc:
        return jsonify({"ok": False, "error": f"Could not reach Ollama: {exc}"}), 200


@ai_bp.route("/client-log", methods=["POST"])
def client_log():
    """Accept structured browser-side diagnostics for AI page failures."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "JSON object required."}), 400

    entry = {
        "kind": _trim_text(payload.get("kind") or "client-error", 80),
        "message": _trim_text(payload.get("message") or "Unknown browser error", 600),
        "page": _trim_text(payload.get("page") or request.headers.get("Referer") or "", 200),
        "request_id": _trim_text(payload.get("request_id") or payload.get("requestId"), 80),
        "server_request_id": _trim_text(request.headers.get("X-Request-ID"), 80),
        "source": _trim_text(payload.get("source"), 120),
        "action": _trim_text(payload.get("action"), 120),
        "status": _trim_text(payload.get("status"), 40),
        "url": _trim_text(payload.get("url"), 200),
        "line": _trim_text(payload.get("line"), 20),
        "column": _trim_text(payload.get("column"), 20),
        "detail": _trim_text(payload.get("detail"), 1200),
        "stack": _trim_text(payload.get("stack"), 1500),
        "user_agent": _trim_text(request.user_agent.string, 200),
    }

    log.warning(
        "CLIENT_ERROR req=%s srv_req=%s kind=%s action=%s status=%s page=%s source=%s url=%s message=%s detail=%s stack=%s ua=%s",
        entry["request_id"],
        entry["server_request_id"],
        entry["kind"],
        entry["action"],
        entry["status"],
        entry["page"],
        entry["source"],
        entry["url"],
        entry["message"],
        entry["detail"],
        entry["stack"],
        entry["user_agent"],
    )
    return jsonify({"ok": True})
