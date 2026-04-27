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
- ``GLOW_ENABLE_AI_CHAT``: gate Document Chat. Defaults to enabled.
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

from .ai_gateway import is_ai_configured
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
    """Return True when AI is configured and globally enabled.

    Defaults are conservative: AI features are OFF unless explicitly enabled
    via environment variables or persisted flags.
    """
    return is_ai_configured() and _env_flag("GLOW_ENABLE_AI", False)


def _feature_enabled(env_name: str) -> bool:
    """Return True when the master and feature gates are both enabled."""
    return _master_ai_enabled() and _env_flag(env_name, True)


def ai_chat_enabled() -> bool:
    """Chat tab and all chat routes are visible and functional."""
    return _feature_enabled("GLOW_ENABLE_AI_CHAT")


def ai_whisperer_enabled() -> bool:
    """Return whether the BITS Whisperer UI and routes are available."""
    return _feature_enabled("GLOW_ENABLE_AI_WHISPERER")


def ai_heading_fix_enabled() -> bool:
    """AI-powered heading detection in the Fix workflow is available."""
    return _feature_enabled("GLOW_ENABLE_AI_HEADING_FIX")


def ai_alt_text_enabled() -> bool:
    """AI-powered alt-text generation for images is available."""
    return _feature_enabled("GLOW_ENABLE_AI_ALT_TEXT")


def ai_markitdown_llm_enabled() -> bool:
    """Return whether MarkItDown LLM enhancements are available."""
    return _feature_enabled("GLOW_ENABLE_AI_MARKITDOWN_LLM")


def get_all_flags() -> dict[str, bool]:
    """Return all AI feature flags as a dict for template injection."""
    configured = _master_ai_enabled()
    return {
        "ai_configured": configured,
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
    }
    fn = flag_map.get(feature)
    if fn is None or not fn():
        raise AIFeatureDisabled(feature)
