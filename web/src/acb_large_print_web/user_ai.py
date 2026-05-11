"""Session-scoped user AI provider helpers.

This module tracks user-supplied provider keys, cached model catalogs, per-feature
provider/model bindings, and provider lease windows. It preserves compatibility
with the original Ollama-only session keys so existing sessions continue to work.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

_PROVIDERS_KEY = "user_ai_providers"
_FEATURE_MODELS_KEY = "user_ai_feature_models"
_FEATURE_FLAGS_KEY = "user_ai_features"
_RUNTIME_SETTINGS_KEY = "user_ai_runtime_settings"
_PROMPT_SETTINGS_KEY = "user_ai_prompt_settings"
_VALIDATED_KEYS_KEY = "user_ai_validated_keys"
_LEGACY_OLLAMA_KEY = "ollama_api_key"
_LEGACY_OLLAMA_MODEL = "ollama_model"
_LEGACY_OLLAMA_EXPIRY = "ollama_key_expires_at"
_SESSION_MINUTES = int(
    os.environ.get("USER_AI_SESSION_MINUTES", os.environ.get("SESSION_TIMEOUT_MINUTES", "240"))
)
_EXTEND_MINUTES = int(os.environ.get("USER_AI_SESSION_EXTEND_MINUTES", str(_SESSION_MINUTES)))
_MIN_SESSION_MINUTES = 15
_MAX_SESSION_MINUTES = 24 * 60
MODEL_REF_SEPARATOR = "::"

DEFAULT_ALT_TEXT_PROMPT = (
    "You are writing alternative text for an accessibility-focused document workflow. "
    "Generate one concise alt text suggestion for a non-decorative image. Focus on the meaning the image conveys, "
    "include visible text when it is important to understanding the image, avoid leading phrases like 'image of' or 'picture of', "
    "and usually keep the result under 125 characters unless essential clarity requires slightly more detail. "
    "If the image appears decorative, return 'Decorative image.'"
)

DEFAULT_MARKITDOWN_IMAGE_PROMPT = (
    "You are an accessibility specialist helping MarkItDown describe images extracted from documents. "
    "Write a concise description that preserves important visible text, labels, chart meaning, and document context for downstream editing. "
    "Do not add commentary outside the description."
)

USER_AI_PROVIDER_DEFINITIONS: dict[str, dict[str, object]] = {
    "ollama": {
        "label": "Ollama Cloud",
        "default_model": "gemma3:4b",
        "supports_streaming": True,
        "supports_audio": False,
        "supports_vision": False,
        "key_url": "https://ollama.com/settings/keys",
        "description": "Fast personal inference with account-specific model access.",
    },
    "openrouter": {
        "label": "OpenRouter",
        "default_model": "openai/gpt-4o-mini",
        "supports_streaming": False,
        "supports_audio": True,
        "supports_vision": True,
        "key_url": "https://openrouter.ai/keys",
        "description": "Single key for many providers with rich model catalog and pricing metadata.",
    },
    "openai": {
        "label": "OpenAI",
        "default_model": "gpt-4o-mini",
        "supports_streaming": False,
        "supports_audio": False,
        "supports_vision": True,
        "key_url": "https://platform.openai.com/api-keys",
        "description": "OpenAI-hosted GPT models with simple key-based setup.",
    },
    "gemini": {
        "label": "Google Gemini",
        "default_model": "gemini-2.5-flash",
        "supports_streaming": False,
        "supports_audio": False,
        "supports_vision": True,
        "key_url": "https://aistudio.google.com/app/apikey",
        "description": "Google Gemini models with large context windows and multimodal support.",
    },
}

_PROVIDER_PRIORITY = ["ollama", "openai", "openrouter", "gemini"]
_FEATURE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "heading_fix": ("text",),
    "markitdown": ("text",),
    "playground": ("text",),
    "chat": ("text", "long_context"),
    "alt_text": ("vision",),
    "whisperer": ("audio_transcription",),
}

USER_AI_FEATURE_DEFAULTS: dict[str, bool] = {
    "heading_fix": True,
    "markitdown": True,
    "playground": True,
    "alt_text": True,
    "whisperer": True,
    "chat": False,
}

USER_AI_FEATURE_LABELS: dict[str, str] = {
    "heading_fix": "AI Heading Detection",
    "markitdown": "AI Document Formatting (MarkItDown)",
    "playground": "AI Playground",
    "alt_text": "Alternative Text Suggestions",
    "whisperer": "BITS Whisperer",
    "chat": "Document Chat",
}


def _empty_capabilities() -> dict[str, bool]:
    return {
        "text": False,
        "vision": False,
        "audio_transcription": False,
        "long_context": False,
        "reasoning": False,
        "streaming": False,
    }


def infer_model_capabilities(
    provider: str,
    model_id: str,
    *,
    model_name: str = "",
    context_length: int = 0,
    raw: dict[str, object] | None = None,
) -> dict[str, bool]:
    """Infer capability flags for a model using provider metadata and heuristics."""
    provider = str(provider or "").strip().lower()
    model_key = f"{model_id} {model_name}".lower()
    caps = _empty_capabilities()
    caps["streaming"] = bool(provider_metadata(provider).get("supports_streaming", False))

    if provider in {"ollama", "openrouter", "openai", "gemini"}:
        caps["text"] = True

    if provider == "ollama":
        caps["long_context"] = any(token in model_key for token in ("70b", "32b", "27b", "qwen3", "gpt-oss", "12b"))
        caps["reasoning"] = any(token in model_key for token in ("qwen", "gpt-oss", "reason", "thinking", "glm", "deepseek"))
        return caps

    raw = raw or {}
    architecture = raw.get("architecture") if isinstance(raw, dict) else {}
    if not isinstance(architecture, dict):
        architecture = {}
    modalities = " ".join(
        str(value).lower()
        for value in (
            architecture.get("modality"),
            architecture.get("input_modality"),
            architecture.get("output_modality"),
            raw.get("modality"),
        )
        if value
    )
    supported_methods = [str(item).lower() for item in (raw.get("supportedGenerationMethods") or []) if item]

    if provider == "openrouter":
        caps["vision"] = ("image" in modalities) or any(token in model_key for token in ("vision", "vl", "gpt-4o", "gemini", "claude-3"))
        caps["audio_transcription"] = any(token in model_key for token in ("whisper", "audio", "transcribe"))
        caps["long_context"] = int(context_length or 0) >= 64000 or any(token in model_key for token in ("claude", "gemini", "gpt-4o", "sonnet", "opus"))
        caps["reasoning"] = any(token in model_key for token in ("o1", "o3", "reason", "thinking", "deepseek", "claude", "gemini"))
        return caps

    if provider == "openai":
        caps["vision"] = any(token in model_key for token in ("gpt-4o", "gpt-4.1", "vision"))
        caps["audio_transcription"] = False
        caps["long_context"] = any(token in model_key for token in ("gpt-4o", "gpt-4.1", "o1", "o3"))
        caps["reasoning"] = any(token in model_key for token in ("o1", "o3", "reason"))
        return caps

    if provider == "gemini":
        caps["vision"] = True
        caps["audio_transcription"] = False
        caps["long_context"] = int(context_length or 0) >= 64000 or any(token in model_key for token in ("2.5", "1.5-pro", "pro"))
        caps["reasoning"] = any(token in model_key for token in ("2.5", "thinking", "pro"))
        if supported_methods:
            caps["text"] = "generatecontent" in {item.replace(" ", "") for item in supported_methods}
        return caps

    return caps


def model_supports_feature(model: dict[str, object], feature: str) -> bool:
    requirements = _FEATURE_REQUIREMENTS.get(feature, ("text",))
    caps = model.get("capabilities") if isinstance(model, dict) else {}
    if not isinstance(caps, dict):
        return False
    return all(bool(caps.get(requirement, False)) for requirement in requirements)


def provider_model_supports_feature(provider: str, model_id: str, feature: str) -> bool:
    for model in get_user_provider_models(provider):
        if str(model.get("id") or "") == model_id:
            return model_supports_feature(model, feature)
    pseudo_model = {
        "id": model_id,
        "name": model_id,
        "capabilities": infer_model_capabilities(provider, model_id, model_name=model_id),
    }
    return model_supports_feature(pseudo_model, feature)


def provider_supports_feature(provider: str, feature: str) -> bool:
    for model in get_user_provider_models(provider):
        if model_supports_feature(model, feature):
            return True
    default_model = get_user_provider_default_model(provider)
    if not default_model:
        return False
    pseudo_model = {
        "id": default_model,
        "name": default_model,
        "capabilities": infer_model_capabilities(provider, default_model),
    }
    return model_supports_feature(pseudo_model, feature)


def any_user_provider_supports_feature(feature: str) -> bool:
    for provider in USER_AI_PROVIDER_DEFINITIONS:
        if is_user_provider_configured(provider) and provider_supports_feature(provider, feature):
            return True
    return False


def feature_recommendation_note(feature: str) -> str:
    notes = {
        "heading_fix": "Use a fast text model to keep audits responsive.",
        "markitdown": "Use a balanced text model with solid formatting and extraction quality.",
        "playground": "Use any general chat model; low-latency models feel best here.",
        "chat": "Use larger long-context models for document-aware chat.",
        "alt_text": "Choose a vision-capable model so image descriptions do not fail at runtime.",
        "whisperer": "Choose an audio transcription-capable provider/model. OpenRouter is the strongest path today.",
    }
    return notes.get(feature, "Choose a model that supports this workflow.")


def _session_or_none():
    try:
        from flask import has_request_context, session

        if not has_request_context():
            return None

        return session
    except RuntimeError:
        return None


def user_ai_session_minutes() -> int:
    settings = get_user_ai_runtime_settings()
    return int(settings["session_minutes"])


def user_ai_extend_minutes() -> int:
    settings = get_user_ai_runtime_settings()
    return int(settings["extend_minutes"])


def _normalize_runtime_minutes(value: object, fallback: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except (TypeError, ValueError):
        parsed = fallback
    return max(_MIN_SESSION_MINUTES, min(_MAX_SESSION_MINUTES, parsed))


def get_user_ai_runtime_settings() -> dict[str, int]:
    session_data = _session_or_none()
    defaults = {
        "session_minutes": _normalize_runtime_minutes(_SESSION_MINUTES, _SESSION_MINUTES),
        "extend_minutes": _normalize_runtime_minutes(_EXTEND_MINUTES, _EXTEND_MINUTES),
    }
    if session_data is None:
        return defaults
    stored = session_data.get(_RUNTIME_SETTINGS_KEY) or {}
    if not isinstance(stored, dict):
        return defaults
    return {
        "session_minutes": _normalize_runtime_minutes(stored.get("session_minutes"), defaults["session_minutes"]),
        "extend_minutes": _normalize_runtime_minutes(stored.get("extend_minutes"), defaults["extend_minutes"]),
    }


def save_user_ai_runtime_settings(session_minutes: object, extend_minutes: object) -> dict[str, int]:
    session_data = _session_or_none()
    cleaned = {
        "session_minutes": _normalize_runtime_minutes(session_minutes, _SESSION_MINUTES),
        "extend_minutes": _normalize_runtime_minutes(extend_minutes, _EXTEND_MINUTES),
    }
    if session_data is None:
        return cleaned
    session_data[_RUNTIME_SETTINGS_KEY] = cleaned
    session_data.modified = True
    return cleaned


def default_user_ai_prompt_settings() -> dict[str, str]:
    return {
        "alt_text_prompt": DEFAULT_ALT_TEXT_PROMPT,
        "markitdown_image_prompt": DEFAULT_MARKITDOWN_IMAGE_PROMPT,
    }


def get_user_ai_prompt_settings() -> dict[str, str]:
    session_data = _session_or_none()
    defaults = default_user_ai_prompt_settings()
    if session_data is None:
        return defaults
    stored = session_data.get(_PROMPT_SETTINGS_KEY) or {}
    if not isinstance(stored, dict):
        return defaults
    return {
        key: str(stored.get(key) or defaults[key]).strip() or defaults[key]
        for key in defaults
    }


def save_user_ai_prompt_settings(values: dict[str, object]) -> dict[str, str]:
    session_data = _session_or_none()
    defaults = default_user_ai_prompt_settings()
    cleaned = {
        key: str(values.get(key) or defaults[key]).strip() or defaults[key]
        for key in defaults
    }
    if session_data is None:
        return cleaned
    session_data[_PROMPT_SETTINGS_KEY] = cleaned
    session_data.modified = True
    return cleaned


def build_alt_text_prompt(
    *,
    document_name: str = "",
    image_index: int | None = None,
    total_images: int | None = None,
    current_alt_text: str = "",
    surrounding_text: list[str] | None = None,
    extra_instruction: str = "",
) -> str:
    prompts = get_user_ai_prompt_settings()
    parts: list[str] = [prompts["alt_text_prompt"].strip()]

    context_lines: list[str] = []
    if document_name:
        context_lines.append(f"Document: {document_name}")
    if image_index is not None:
        if total_images is not None and total_images > 0:
            context_lines.append(f"Image position: {image_index + 1} of {total_images}")
        else:
            context_lines.append(f"Image position: {image_index + 1}")
    if current_alt_text.strip():
        context_lines.append(f"Existing alt text: {current_alt_text.strip()}")
    if surrounding_text:
        for item in surrounding_text:
            text = str(item or "").strip()
            if text:
                context_lines.append(text)

    if context_lines:
        parts.append("Context:\n- " + "\n- ".join(context_lines))
    if extra_instruction.strip():
        parts.append(extra_instruction.strip())
    parts.append("Return only the suggested alt text, with no quotation marks, labels, or explanation.")
    return "\n\n".join(part for part in parts if part)


def get_markitdown_image_prompt() -> str:
    return get_user_ai_prompt_settings()["markitdown_image_prompt"]


def format_model_ref(provider: str, model: str) -> str:
    return f"{provider}{MODEL_REF_SEPARATOR}{model}"


def parse_model_ref(value: str | None) -> tuple[str | None, str]:
    raw = str(value or "").strip()
    if MODEL_REF_SEPARATOR in raw:
        provider, model = raw.split(MODEL_REF_SEPARATOR, 1)
        provider = provider.strip().lower()
        return (provider if provider in USER_AI_PROVIDER_DEFINITIONS else None, model.strip())
    return None, raw


def _coerce_expiry(raw: object) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        expires_at = datetime.fromisoformat(text)
    except ValueError:
        return None
    if expires_at.tzinfo is None:
        return expires_at.replace(tzinfo=UTC)
    return expires_at.astimezone(UTC)


def provider_metadata(provider: str) -> dict[str, object]:
    return dict(USER_AI_PROVIDER_DEFINITIONS.get(provider, {}))


def all_provider_metadata() -> list[dict[str, object]]:
    return [
        {"id": provider, **provider_metadata(provider)}
        for provider in USER_AI_PROVIDER_DEFINITIONS
    ]


def _legacy_ollama_config(session_data) -> dict[str, object] | None:
    api_key = str(session_data.get(_LEGACY_OLLAMA_KEY, "") or "").strip()
    if not api_key:
        return None
    return {
        "api_key": api_key,
        "default_model": str(session_data.get(_LEGACY_OLLAMA_MODEL, "gemma3:4b") or "gemma3:4b"),
        "expires_at": str(session_data.get(_LEGACY_OLLAMA_EXPIRY, "") or ""),
        "models": [],
    }


def _provider_store(copy_items: bool = True) -> dict[str, dict[str, object]]:
    session_data = _session_or_none()
    if session_data is None:
        return {}
    raw = session_data.get(_PROVIDERS_KEY) or {}
    out: dict[str, dict[str, object]] = {}
    if isinstance(raw, dict):
        for provider, cfg in raw.items():
            if provider in USER_AI_PROVIDER_DEFINITIONS and isinstance(cfg, dict):
                out[provider] = dict(cfg) if copy_items else cfg
    if "ollama" not in out:
        legacy = _legacy_ollama_config(session_data)
        if legacy:
            out["ollama"] = legacy
    return out


def _write_provider_store(store: dict[str, dict[str, object]]) -> None:
    session_data = _session_or_none()
    if session_data is None:
        return
    session_data[_PROVIDERS_KEY] = store
    session_data.modified = True


def _validated_key_store() -> dict[str, str]:
    session_data = _session_or_none()
    if session_data is None:
        return {}
    raw = session_data.get(_VALIDATED_KEYS_KEY) or {}
    return dict(raw) if isinstance(raw, dict) else {}


def set_validated_key_hash(provider: str, key_hash: str) -> None:
    session_data = _session_or_none()
    if session_data is None:
        return
    store = _validated_key_store()
    store[provider] = key_hash
    session_data[_VALIDATED_KEYS_KEY] = store
    session_data.modified = True


def get_validated_key_hash(provider: str) -> str:
    return _validated_key_store().get(provider, "")


def clear_validated_key_hash(provider: str) -> None:
    session_data = _session_or_none()
    if session_data is None:
        return
    store = _validated_key_store()
    store.pop(provider, None)
    session_data[_VALIDATED_KEYS_KEY] = store
    session_data.modified = True


def get_provider_expiry(provider: str) -> datetime | None:
    store = _provider_store()
    cfg = store.get(provider) or {}
    return _coerce_expiry(cfg.get("expires_at"))


def get_provider_seconds_remaining(provider: str) -> int:
    expires_at = get_provider_expiry(provider)
    if not expires_at:
        return 0
    return max(0, int((expires_at - datetime.now(UTC)).total_seconds()))


def set_provider_expiry(provider: str, expires_at: datetime) -> datetime | None:
    session_data = _session_or_none()
    if session_data is None:
        return None
    store = _provider_store()
    cfg = dict(store.get(provider) or {})
    normalized = expires_at.astimezone(UTC) if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
    cfg["expires_at"] = normalized.isoformat()
    store[provider] = cfg
    _write_provider_store(store)
    if provider == "ollama":
        session_data[_LEGACY_OLLAMA_EXPIRY] = normalized.isoformat()
        session_data.modified = True
    return normalized


def refresh_provider_expiry(provider: str) -> datetime | None:
    return set_provider_expiry(provider, datetime.now(UTC) + timedelta(minutes=user_ai_session_minutes()))


def extend_provider_expiry(provider: str) -> datetime | None:
    current = get_provider_expiry(provider)
    base = current if current and current > datetime.now(UTC) else datetime.now(UTC)
    return set_provider_expiry(provider, base + timedelta(minutes=user_ai_extend_minutes()))


def _cleanup_expired_provider(provider: str) -> None:
    if get_provider_seconds_remaining(provider) > 0:
        return
    remove_user_provider(provider)


def get_user_provider_configs(include_inactive: bool = False) -> dict[str, dict[str, object]]:
    store = _provider_store()
    out: dict[str, dict[str, object]] = {}
    for provider, cfg in store.items():
        expiry = _coerce_expiry(cfg.get("expires_at"))
        if expiry and expiry <= datetime.now(UTC):
            if not include_inactive:
                _cleanup_expired_provider(provider)
                continue
        item = dict(cfg)
        item["provider"] = provider
        item["expires_at"] = expiry.isoformat() if expiry else ""
        item["seconds_remaining"] = get_provider_seconds_remaining(provider) if expiry else 0
        out[provider] = item
    return out


def save_user_provider(
    provider: str,
    api_key: str,
    default_model: str,
    models: list[dict[str, object]] | None = None,
) -> None:
    session_data = _session_or_none()
    if session_data is None:
        return
    provider = provider.strip().lower()
    if provider not in USER_AI_PROVIDER_DEFINITIONS:
        raise ValueError(f"Unsupported AI provider: {provider}")
    store = _provider_store()
    cfg = dict(store.get(provider) or {})
    cfg["api_key"] = api_key.strip()
    cfg["default_model"] = default_model.strip() or str(provider_metadata(provider).get("default_model") or "")
    cfg["models"] = list(models or cfg.get("models") or [])
    store[provider] = cfg
    _write_provider_store(store)
    refresh_provider_expiry(provider)
    if provider == "ollama":
        session_data[_LEGACY_OLLAMA_KEY] = api_key.strip()
        session_data[_LEGACY_OLLAMA_MODEL] = cfg["default_model"]
    session_data.permanent = True
    session_data.modified = True


def remove_user_provider(provider: str) -> None:
    session_data = _session_or_none()
    if session_data is None:
        return
    store = _provider_store()
    store.pop(provider, None)
    _write_provider_store(store)
    clear_validated_key_hash(provider)
    if provider == "ollama":
        for key in (_LEGACY_OLLAMA_KEY, _LEGACY_OLLAMA_MODEL, _LEGACY_OLLAMA_EXPIRY):
            session_data.pop(key, None)
        for key in ("ollama_features", "ollama_feature_models", "ollama_validated", "ollama_validated_key_hash"):
            session_data.pop(key, None)
    session_data.modified = True


def get_user_provider_key(provider: str) -> str:
    return str((get_user_provider_configs().get(provider) or {}).get("api_key") or "")


def get_user_provider_default_model(provider: str) -> str:
    cfg = get_user_provider_configs().get(provider) or {}
    return str(cfg.get("default_model") or provider_metadata(provider).get("default_model") or "")


def get_user_provider_models(provider: str) -> list[dict[str, object]]:
    cfg = get_user_provider_configs().get(provider) or {}
    models = cfg.get("models") or []
    return [dict(item) for item in models if isinstance(item, dict)]


def is_user_provider_configured(provider: str) -> bool:
    key = get_user_provider_key(provider)
    if not key:
        return False
    expires_at = get_provider_expiry(provider)
    if expires_at is None:
        refresh_provider_expiry(provider)
        return True
    if get_provider_seconds_remaining(provider) <= 0:
        _cleanup_expired_provider(provider)
        return False
    return True


def any_user_provider_configured() -> bool:
    for provider in USER_AI_PROVIDER_DEFINITIONS:
        if is_user_provider_configured(provider):
            return True
    return False


def get_user_active_providers() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for provider in _PROVIDER_PRIORITY:
        if provider not in USER_AI_PROVIDER_DEFINITIONS:
            continue
        if not is_user_provider_configured(provider):
            continue
        cfg = get_user_provider_configs().get(provider) or {}
        out.append({
            "id": provider,
            **provider_metadata(provider),
            "default_model": str(cfg.get("default_model") or provider_metadata(provider).get("default_model") or ""),
            "models": get_user_provider_models(provider),
            "seconds_remaining": get_provider_seconds_remaining(provider),
            "expires_at": str(cfg.get("expires_at") or ""),
        })
    return out


def get_user_ai_feature_flags() -> dict[str, bool]:
    session_data = _session_or_none()
    defaults = dict(USER_AI_FEATURE_DEFAULTS)
    if session_data is None:
        return defaults
    stored = session_data.get(_FEATURE_FLAGS_KEY)
    if not isinstance(stored, dict):
        stored = session_data.get("ollama_features", {})
    if not isinstance(stored, dict):
        return defaults
    return {key: bool(stored.get(key, default)) for key, default in defaults.items()}


def save_user_ai_feature_flags(values: dict[str, bool]) -> None:
    session_data = _session_or_none()
    if session_data is None:
        return
    cleaned = {
        key: bool(values.get(key, USER_AI_FEATURE_DEFAULTS.get(key, False)))
        for key in USER_AI_FEATURE_DEFAULTS
    }
    session_data[_FEATURE_FLAGS_KEY] = cleaned
    # Keep legacy Ollama feature storage for backward-compatible routes/templates.
    session_data["ollama_features"] = {
        key: cleaned[key]
        for key in ("heading_fix", "markitdown", "chat", "playground")
        if key in cleaned
    }
    session_data.modified = True


def is_user_ai_feature_enabled(feature: str) -> bool:
    return any_user_provider_configured() and get_user_ai_feature_flags().get(feature, False)


def get_user_ai_feature_models() -> dict[str, str]:
    session_data = _session_or_none()
    if session_data is None:
        return {}
    raw = session_data.get(_FEATURE_MODELS_KEY)
    if isinstance(raw, dict):
        return {str(key): str(value) for key, value in raw.items() if value}
    legacy = session_data.get("ollama_feature_models") or {}
    if isinstance(legacy, dict):
        return {
            str(key): format_model_ref("ollama", str(value))
            for key, value in legacy.items()
            if value
        }
    return {}


def save_user_ai_feature_models(values: dict[str, str]) -> None:
    session_data = _session_or_none()
    if session_data is None:
        return
    cleaned = {str(key): str(value).strip() for key, value in values.items() if str(value).strip()}
    session_data[_FEATURE_MODELS_KEY] = cleaned
    session_data.modified = True


def get_user_ai_provider_and_model_for(feature: str) -> tuple[str | None, str]:
    bindings = get_user_ai_feature_models()
    provider, model = parse_model_ref(bindings.get(feature, ""))
    if provider and model and is_user_provider_configured(provider) and provider_model_supports_feature(provider, model, feature):
        return provider, model

    for item in get_user_active_providers():
        provider_id = str(item.get("id") or "")
        if not provider_supports_feature(provider_id, feature):
            continue
        for model_item in get_user_provider_models(provider_id):
            model_id = str(model_item.get("id") or "")
            if model_id and model_supports_feature(model_item, feature):
                return provider_id, model_id
        default_model = str(item.get("default_model") or "")
        if default_model and provider_model_supports_feature(provider_id, default_model, feature):
            return provider_id, default_model
    return None, ""


def feature_model_options() -> list[dict[str, object]]:
    options: list[dict[str, object]] = []
    for item in get_user_active_providers():
        provider = str(item.get("id") or "")
        provider_label = str(item.get("label") or provider)
        models = item.get("models") or []
        if models:
            for model in models:
                model_id = str(model.get("id") or model.get("name") or "").strip()
                if not model_id:
                    continue
                options.append({
                    "value": format_model_ref(provider, model_id),
                    "provider": provider,
                    "provider_label": provider_label,
                    "model_id": model_id,
                    "label": str(model.get("name") or model_id),
                    "input_per_million": model.get("input_per_million"),
                    "output_per_million": model.get("output_per_million"),
                    "note": model.get("note") or "",
                    "capabilities": dict(model.get("capabilities") or {}),
                })
            continue
        default_model = str(item.get("default_model") or "")
        if default_model:
            options.append({
                "value": format_model_ref(provider, default_model),
                "provider": provider,
                "provider_label": provider_label,
                "model_id": default_model,
                "label": default_model,
                "input_per_million": None,
                "output_per_million": None,
                "note": "",
                "capabilities": infer_model_capabilities(provider, default_model, model_name=default_model),
            })
    return options


def feature_model_options_for(feature: str) -> list[dict[str, object]]:
    return [
        option
        for option in feature_model_options()
        if model_supports_feature({"capabilities": option.get("capabilities") or {}}, feature)
    ]


def primary_active_provider() -> dict[str, object] | None:
    providers = get_user_active_providers()
    return providers[0] if providers else None


def provider_session_payload(provider: str) -> dict[str, object]:
    expires_at = get_provider_expiry(provider)
    active = is_user_provider_configured(provider) and bool(expires_at) and get_provider_seconds_remaining(provider) > 0
    return {
        "ok": True,
        "provider": provider,
        "active": active,
        "duration_minutes": user_ai_session_minutes(),
        "extend_minutes": user_ai_extend_minutes(),
        "expires_utc": expires_at.isoformat() if active and expires_at else None,
        "seconds_remaining": get_provider_seconds_remaining(provider) if active else 0,
    }