"""Settings route -- user preference controls with opt-in persistence."""

import logging

import requests
from flask import Blueprint, jsonify, render_template, request, session

from acb_large_print_web.rules import get_all_rule_ids
from acb_large_print_web.credentials import (
    OLLAMA_FEATURE_DEFAULTS,
    OLLAMA_FEATURE_LABELS,
    OLLAMA_MODEL_RECOMMENDATIONS,
    get_ollama_cloud_url,
    get_user_ollama_features,
    get_user_ollama_key,
    get_user_ollama_model,
    is_ollama_configured,
)

log = logging.getLogger(__name__)
settings_bp = Blueprint("settings", __name__)

_OLLAMA_VALID_MODELS = {m["id"] for m in OLLAMA_MODEL_RECOMMENDATIONS}


@settings_bp.route("/", methods=["GET"])
def settings_page():
    return render_template(
        "settings.html",
        total_rules=len(get_all_rule_ids()),
    )


@settings_bp.route("/ai", methods=["GET"])
def settings_ai_page():
    """Dedicated page for Ollama AI key setup, model selection, and feature toggles."""
    features = get_user_ollama_features()
    return render_template(
        "settings_ai.html",
        ollama_active=is_ollama_configured(),
        ollama_model=get_user_ollama_model(),
        model_recommendations=OLLAMA_MODEL_RECOMMENDATIONS,
        ollama_features=features,
        ollama_feature_labels=OLLAMA_FEATURE_LABELS,
        ollama_feature_defaults=OLLAMA_FEATURE_DEFAULTS,
    )


@settings_bp.route("/ai/key", methods=["POST"])
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
def forget_ollama_key():
    """Remove the Ollama API key, model, and feature toggles from the session."""
    session.pop("ollama_api_key", None)
    session.pop("ollama_model", None)
    session.pop("ollama_features", None)
    session.modified = True
    return jsonify({"ok": True})


@settings_bp.route("/ai/features", methods=["POST"])
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
    session.modified = True

    enabled = [OLLAMA_FEATURE_LABELS.get(k, k) for k, v in updated.items() if v]
    return jsonify({"ok": True, "enabled": enabled})


@settings_bp.route("/ai/validate", methods=["POST"])
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
