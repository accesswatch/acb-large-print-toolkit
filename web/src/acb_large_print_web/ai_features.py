"""AI feature visibility flags for the GLOW web app.

This module answers one question for every AI-dependent feature:
"Should this feature be shown to the user right now?"

Rules
-----
- If OPENROUTER_API_KEY is not set, ALL AI features are invisible.
  No error messages, no disabled buttons -- the feature simply does not exist.
- Deploy-time feature flags can additionally disable all AI or individual AI
    features without removing the OpenRouter key.
- If the monthly budget is exhausted, AI features show a
    "temporarily unavailable" message rather than disappearing
    (the feature exists, just paused until next month).
- BITS Whisperer uses the same OPENROUTER_API_KEY as all other AI features.

Environment flags
-----------------
- ``GLOW_ENABLE_AI``: master AI switch. Defaults to enabled.
- ``GLOW_ENABLE_AI_GENERAL_CHAT``: gate AI Playground (general chat).
- ``GLOW_ENABLE_AI_CHAT``: gate Document Chat.
- ``GLOW_ENABLE_AI_WHISPERER``: gate BITS Whisperer. Defaults to enabled.
- ``GLOW_ENABLE_AI_HEADING_FIX``: gate AI heading refinement in Fix.
- ``GLOW_ENABLE_AI_ALT_TEXT``: gate AI alt-text helpers.
- ``GLOW_ENABLE_AI_MARKITDOWN_LLM``: gate MarkItDown LLM enhancements.

This module is imported by:
  - app.py   (context_processor injects flags into every template)
  - routes   (to gate 404 vs 503 responses on unconfigured features)
  - base.html (conditional nav tabs)

Adding a new AI feature
-----------------------
1. Add a function here following the pattern below.
2. Inject it in the context_processor in app.py.
3. Use ``{% if ai_chat_enabled %}`` in templates.
4. In the route, call ``require_ai_feature('chat')`` at the top of
    POST handlers.
"""

from __future__ import annotations

import os

from .ai_gateway import is_ai_configured, is_whisper_configured
from .credentials import is_ollama_configured, is_ollama_feature_enabled
from . import feature_flags


def _env_flag(name: str, default: bool = False) -> bool:
    """Return a normalized boolean feature flag.

    Preference order:
    1. Environment variable
    2. Persisted server-side feature flag (instance/feature_flags.json)
    3. Provided default
    """
    # First, honor explicit environment variables when present
    value = os.environ.get(name)
    if value is not None:
        return value.strip().lower() in {"1", "true", "yes", "on"}

    # Then prefer persisted server-side flags when available
    try:
        return feature_flags.get_flag(name, default)
    except Exception:
        return bool(default)


def _master_ai_enabled() -> bool:
    """Return True when any AI provider is configured and globally enabled.

    A user-supplied Ollama key satisfies the provider check on its own;
    the server-side OpenRouter key is not required when Ollama is active.
    """
    return is_ai_configured() and _env_flag("GLOW_ENABLE_AI", False)


def _ollama_feature_enabled(env_name: str, ollama_feature: str) -> bool:
    """Return True when Ollama is active, the server env flag is on, AND the
    user has enabled this specific feature in their session settings.

    ``ollama_feature`` is one of the keys in OLLAMA_FEATURE_DEFAULTS
    (e.g. 'heading_fix', 'markitdown', 'chat').
    """
    return (
        is_ollama_configured()
        and _env_flag("GLOW_ENABLE_AI", False)
        and _env_flag(env_name, True)
        and is_ollama_feature_enabled(ollama_feature)
    )


def _openrouter_feature_enabled(env_name: str) -> bool:
    """Return True when OpenRouter is configured and the feature flag is on."""
    from .ai_gateway import is_whisper_configured as _wc
    return _wc() and _env_flag("GLOW_ENABLE_AI", False) and _env_flag(env_name, True)


def _feature_enabled(env_name: str) -> bool:
    """Return True when the master gate and feature flag are both on."""
    return _master_ai_enabled() and _env_flag(env_name, True)


def ai_chat_enabled() -> bool:
    """Chat tab and all chat routes are visible and functional."""
    return _feature_enabled("GLOW_ENABLE_AI_CHAT") or _ollama_feature_enabled("GLOW_ENABLE_AI_CHAT", "chat")


def ai_whisperer_enabled() -> bool:
    """Return whether the BITS Whisperer UI and routes are available.

    Whisperer requires audio transcription -- Ollama does not support this.
    Only OpenRouter is checked.
    """
    return _openrouter_feature_enabled("GLOW_ENABLE_AI_WHISPERER")


def ai_heading_fix_enabled() -> bool:
    """AI-powered heading detection in the Fix workflow is available."""
    return _feature_enabled("GLOW_ENABLE_AI_HEADING_FIX") or _ollama_feature_enabled("GLOW_ENABLE_AI_HEADING_FIX", "heading_fix")


def ai_alt_text_enabled() -> bool:
    """AI-powered alt-text generation for images is available."""
    return _feature_enabled("GLOW_ENABLE_AI_ALT_TEXT")


def ai_markitdown_llm_enabled() -> bool:
    """Return whether MarkItDown LLM enhancements are available."""
    return _feature_enabled("GLOW_ENABLE_AI_MARKITDOWN_LLM") or _ollama_feature_enabled("GLOW_ENABLE_AI_MARKITDOWN_LLM", "markitdown")


def ai_playground_enabled() -> bool:
    """Return whether the standalone Ollama playground is available."""
    return _feature_enabled("GLOW_ENABLE_AI_GENERAL_CHAT") and is_ollama_configured()


def get_all_flags() -> dict[str, bool]:
    """Return all AI feature flags as a dict for template injection."""
    configured = _master_ai_enabled()
    ollama_active = is_ollama_configured()
    ai_entry_enabled = _env_flag("GLOW_ENABLE_AI", True)
    return {
        "ai_entry_enabled": ai_entry_enabled,
        "ai_configured": configured,
        "ollama_active": ollama_active,
        "ai_ollama_active": ollama_active,
        "ai_playground_enabled": ai_playground_enabled(),
        "ai_chat_enabled": ai_chat_enabled(),
        "ai_whisperer_enabled": ai_whisperer_enabled(),
        "ai_heading_fix_enabled": ai_heading_fix_enabled(),
        "ai_alt_text_enabled": ai_alt_text_enabled(),
        "ai_markitdown_llm_enabled": ai_markitdown_llm_enabled(),
    }


class AIFeatureDisabled(Exception):
    """Raised when a route needs an AI feature that is currently disabled."""

    def __init__(self, feature: str) -> None:
        self.feature = feature
        super().__init__(
            f"AI feature '{feature}' is not available on this server."
        )


def require_ai_feature(feature: str) -> None:
    """Raise AIFeatureDisabled if the named feature is not currently available.

    Use at the top of POST route handlers for AI-dependent features.

    Example::

        from ..ai_features import require_ai_feature, AIFeatureDisabled

        @bp.route("/", methods=["POST"])
        def chat_submit():
            try:
                require_ai_feature("chat")
            except AIFeatureDisabled:
                abort(404)
            ...
    """
    flag_map = {
        "chat": ai_chat_enabled,
        "whisperer": ai_whisperer_enabled,
        "heading_fix": ai_heading_fix_enabled,
        "alt_text": ai_alt_text_enabled,
        "markitdown_llm": ai_markitdown_llm_enabled,
        "playground": ai_playground_enabled,
    }
    fn = flag_map.get(feature)
    if fn is None or not fn():
        raise AIFeatureDisabled(feature)
