"""Tests for the Ollama Cloud gateway path and settings routes."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from datetime import UTC, datetime, timedelta

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_ollama_response(content: str = "Test answer", model: str = "llama3.2") -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.ok = True
    resp.json.return_value = {
        "message": {"role": "assistant", "content": content},
        "model": model,
        "prompt_eval_count": 120,
        "eval_count": 40,
    }
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# _ollama_completion
# ---------------------------------------------------------------------------

class TestOllamaCompletion:
    def test_returns_text_and_token_counts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        monkeypatch.setattr(ai_gateway, "get_user_ollama_key", lambda: "ollama_testkey")
        monkeypatch.setattr(ai_gateway, "get_ollama_cloud_url", lambda: "https://ollama.com/api")

        with patch("acb_large_print_web.ai_gateway.requests.post", return_value=_fake_ollama_response("Hello")) as mock_post:
            text, in_tok, out_tok, model = ai_gateway._ollama_completion(
                model="llama3.2",
                messages=[{"role": "user", "content": "Hi"}],
                session_hash="abc123",
            )

        assert text == "Hello"
        assert in_tok == 120
        assert out_tok == 40
        assert model == "llama3.2"
        mock_post.assert_called_once()

    def test_raises_on_401(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        monkeypatch.setattr(ai_gateway, "get_user_ollama_key", lambda: "ollama_badkey")
        monkeypatch.setattr(ai_gateway, "get_ollama_cloud_url", lambda: "https://ollama.com/api")

        bad_resp = MagicMock()
        bad_resp.status_code = 401
        bad_resp.raise_for_status = MagicMock()

        with patch("acb_large_print_web.ai_gateway.requests.post", return_value=bad_resp):
            with pytest.raises(RuntimeError, match="not authorized for cloud inference"):
                ai_gateway._ollama_completion("llama3.2", [], "sess")

    def test_raises_on_403_with_plan_guidance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        monkeypatch.setattr(ai_gateway, "get_user_ollama_key", lambda: "ollama_key")
        monkeypatch.setattr(ai_gateway, "get_ollama_cloud_url", lambda: "https://ollama.com/api")

        bad_resp = MagicMock()
        bad_resp.status_code = 403
        bad_resp.json.return_value = {"error": "this model requires a subscription"}
        bad_resp.raise_for_status = MagicMock()

        with patch("acb_large_print_web.ai_gateway.requests.post", return_value=bad_resp):
            with pytest.raises(RuntimeError, match="requires a subscription"):
                ai_gateway._ollama_completion("glm-5", [], "sess")

    def test_raises_on_404_with_model_guidance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        monkeypatch.setattr(ai_gateway, "get_user_ollama_key", lambda: "ollama_key")
        monkeypatch.setattr(ai_gateway, "get_ollama_cloud_url", lambda: "https://ollama.com/api")

        bad_resp = MagicMock()
        bad_resp.status_code = 404
        bad_resp.json.return_value = {"error": "model 'llama3.2' not found"}
        bad_resp.raise_for_status = MagicMock()

        with patch("acb_large_print_web.ai_gateway.requests.post", return_value=bad_resp):
            with pytest.raises(RuntimeError, match="not available on this account"):
                ai_gateway._ollama_completion("llama3.2", [], "sess")

    def test_raises_on_429(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        monkeypatch.setattr(ai_gateway, "get_user_ollama_key", lambda: "ollama_key")
        monkeypatch.setattr(ai_gateway, "get_ollama_cloud_url", lambda: "https://ollama.com/api")

        bad_resp = MagicMock()
        bad_resp.status_code = 429
        bad_resp.raise_for_status = MagicMock()

        with patch("acb_large_print_web.ai_gateway.requests.post", return_value=bad_resp):
            with pytest.raises(RuntimeError, match="plan limit reached"):
                ai_gateway._ollama_completion("llama3.2", [], "sess")

    def test_raises_when_no_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        monkeypatch.setattr(ai_gateway, "get_user_ollama_key", lambda: "")

        with pytest.raises(RuntimeError, match="No Ollama API key"):
            ai_gateway._ollama_completion("llama3.2", [], "sess")


# ---------------------------------------------------------------------------
# is_ai_configured -- provider detection
# ---------------------------------------------------------------------------

class TestIsAiConfigured:
    def test_true_with_ollama_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        monkeypatch.setattr(ai_gateway, "is_ollama_configured", lambda: True)
        monkeypatch.setattr(ai_gateway, "get_openrouter_api_key", lambda: "")
        assert ai_gateway.is_ai_configured() is True

    def test_true_with_openrouter_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        monkeypatch.setattr(ai_gateway, "is_ollama_configured", lambda: False)
        monkeypatch.setattr(ai_gateway, "get_openrouter_api_key", lambda: "sk-test")
        assert ai_gateway.is_ai_configured() is True

    def test_false_with_no_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        monkeypatch.setattr(ai_gateway, "is_ollama_configured", lambda: False)
        monkeypatch.setattr(ai_gateway, "get_openrouter_api_key", lambda: "")
        assert ai_gateway.is_ai_configured() is False

    def test_whisper_requires_openrouter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_gateway

        # Even when Ollama is active, Whisperer needs OpenRouter
        monkeypatch.setattr(ai_gateway, "is_ollama_configured", lambda: True)
        monkeypatch.setattr(ai_gateway, "get_openrouter_api_key", lambda: "")
        assert ai_gateway.is_whisper_configured() is False


class TestCapabilityGating:
    def test_alt_text_requires_vision_capable_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_features

        monkeypatch.setattr(ai_features, "_env_flag", lambda name, default=False: True)
        monkeypatch.setattr(ai_features, "any_user_provider_supports_feature", lambda feature: feature == "alt_text")
        monkeypatch.setattr(ai_features, "is_ai_configured", lambda: False)
        monkeypatch.setattr(ai_features, "is_whisper_configured", lambda: False)

        assert ai_features.ai_alt_text_enabled() is True
        assert ai_features.ai_whisperer_enabled() is False

    def test_whisperer_requires_audio_capable_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from acb_large_print_web import ai_features

        monkeypatch.setattr(ai_features, "_env_flag", lambda name, default=False: True)
        monkeypatch.setattr(ai_features, "any_user_provider_supports_feature", lambda feature: feature == "whisperer")
        monkeypatch.setattr(ai_features, "is_ai_configured", lambda: False)
        monkeypatch.setattr(ai_features, "is_whisper_configured", lambda: False)

        assert ai_features.ai_whisperer_enabled() is True
        assert ai_features.ai_alt_text_enabled() is False


# ---------------------------------------------------------------------------
# Settings -- save/forget/validate routes
# ---------------------------------------------------------------------------

@pytest.fixture()
def settings_client(monkeypatch):
    """Flask test client with AI settings routes."""
    monkeypatch.setenv("GLOW_ENABLE_AI", "true")
    from acb_large_print_web.app import create_app
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret", "WTF_CSRF_ENABLED": False})
    app.config["SERVER_NAME"] = "localhost"
    with app.test_client() as client:
        yield client


class TestSettingsOllamaRoutes:
    def test_ai_page_has_canonical_route(self, settings_client) -> None:
        resp = settings_client.get("/ai/")
        assert resp.status_code == 200
        assert b"Enable AI Features" in resp.data
        assert resp.headers.get("X-Request-ID")

    def test_legacy_settings_ai_redirects_to_canonical_route(self, settings_client) -> None:
        resp = settings_client.get("/settings/ai")
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/ai/")

    def test_save_valid_key(self, settings_client) -> None:
        # Must validate first before save is accepted.
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "llama3.2"}]}

        with patch("acb_large_print_web.routes.settings.requests.get", return_value=mock_resp):
            validate_resp = settings_client.post(
                "/settings/ai/validate",
                data={"ollama_api_key": "ollama_abc123"},
            )

        assert validate_resp.status_code == 200
        assert validate_resp.get_json()["ok"] is True

        resp = settings_client.post(
            "/settings/ai/key",
            data={"ollama_api_key": "ollama_abc123", "ollama_model": "llama3.2"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["model"] == "llama3.2"

    def test_save_rejects_missing_key(self, settings_client) -> None:
        resp = settings_client.post("/settings/ai/key", data={"ollama_model": "llama3.2"})
        assert resp.status_code == 400

    def test_save_requires_prior_validation(self, settings_client) -> None:
        resp = settings_client.post(
            "/settings/ai/key",
            data={"ollama_api_key": "sk-openai-notollama", "ollama_model": "llama3.2"},
        )
        assert resp.status_code == 400
        assert "check your key first" in resp.get_json()["error"].lower()

    def test_forget_key(self, settings_client) -> None:
        # Save first
        settings_client.post(
            "/settings/ai/key",
            data={"ollama_api_key": "ollama_abc123", "ollama_model": "llama3.2"},
        )
        # Then forget
        resp = settings_client.delete("/settings/ai/key")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_validate_calls_ollama_tags(self, settings_client) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "llama3.2"}, {"name": "mistral"}]}

        with patch("acb_large_print_web.routes.settings.requests.get", return_value=mock_resp):
            resp = settings_client.post(
                "/settings/ai/validate",
                data={"ollama_api_key": "ollama_validkey"},
            )

        data = resp.get_json()
        assert data["ok"] is True
        assert any(model["id"] == "llama3.2" for model in data["models"])
        assert data["suggested_model"] == "mistral"

    def test_validate_surfaces_401(self, settings_client) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch("acb_large_print_web.routes.settings.requests.get", return_value=mock_resp):
            resp = settings_client.post(
                "/settings/ai/validate",
                data={"ollama_api_key": "ollama_badkey"},
            )

        data = resp.get_json()
        assert data["ok"] is False
        assert "rejected" in data["error"]

    def test_client_log_endpoint_accepts_browser_errors(self, settings_client) -> None:
        resp = settings_client.post(
            "/ai/client-log",
            json={
                "kind": "ai-fetch-failure",
                "action": "save-key",
                "request_id": "req-client-123",
                "message": "The request failed with status 500.",
                "detail": "<html>server error</html>",
            },
        )

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        assert resp.headers.get("X-Request-ID")

    def test_save_key_sets_ai_session_expiry(self, settings_client) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "gemma3:4b"}]}

        with patch("acb_large_print_web.routes.settings.requests.get", return_value=mock_resp):
            settings_client.post("/settings/ai/validate", data={"ollama_api_key": "ollama_abc123"})

        settings_client.post(
            "/settings/ai/key",
            data={"ollama_api_key": "ollama_abc123", "ollama_model": "gemma3:4b"},
        )

        with settings_client.session_transaction() as session_data:
            assert session_data.get("ollama_key_expires_at")

    def test_ollama_session_status_and_extend(self, settings_client) -> None:
        future = (datetime.now(UTC) + timedelta(minutes=30)).isoformat()
        with settings_client.session_transaction() as session_data:
            session_data["ollama_api_key"] = "ollama_abc123"
            session_data["ollama_model"] = "gemma3:4b"
            session_data["ollama_key_expires_at"] = future

        status_resp = settings_client.get("/ai/session")
        assert status_resp.status_code == 200
        status_data = status_resp.get_json()
        assert status_data["active"] is True
        assert status_data["seconds_remaining"] > 0

        extend_resp = settings_client.post("/ai/session/extend")
        assert extend_resp.status_code == 200
        extend_data = extend_resp.get_json()
        assert extend_data["active"] is True
        assert extend_data["seconds_remaining"] > status_data["seconds_remaining"]

    def test_expired_ollama_session_reports_inactive(self, settings_client) -> None:
        past = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
        with settings_client.session_transaction() as session_data:
            session_data["ollama_api_key"] = "ollama_abc123"
            session_data["ollama_model"] = "gemma3:4b"
            session_data["ollama_key_expires_at"] = past

        resp = settings_client.get("/ai/session")
        data = resp.get_json()
        assert data["active"] is False
        with settings_client.session_transaction() as session_data:
            assert "ollama_api_key" not in session_data


class TestAiUsageRoute:
    def test_ollama_usage_uses_chat_turns_today_field(self, settings_client, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("acb_large_print_web.routes.ai_usage.is_ollama_configured", lambda: True)
        monkeypatch.setattr(
            "acb_large_print_web.routes.ai_usage.primary_active_provider",
            lambda: {"id": "ollama", "label": "Ollama Cloud", "default_model": "gemma3:4b"},
        )
        monkeypatch.setattr("acb_large_print_web.routes.ai_usage.make_session_hash", lambda _value: "sess-hash")
        monkeypatch.setattr(
            "acb_large_print_web.routes.ai_usage.get_quota_status",
            lambda _value: {"chat_turns_today": 7},
        )
        monkeypatch.setattr("acb_large_print_web.routes.ai_usage._session_tokens_today", lambda _value: 42)

        resp = settings_client.get("/ai/usage/")

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["provider"] == "ollama"
        assert data["provider_model"] == "gemma3:4b"
        assert data["session_requests_today"] == 7
        assert data["session_tokens_today"] == 42


class TestPlaygroundRendering:
    def test_assistant_history_does_not_add_extra_ai_response_labels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GLOW_ENABLE_AI", "true")
        monkeypatch.setenv("GLOW_ENABLE_AI_GENERAL_CHAT", "true")
        from acb_large_print_web.app import create_app

        app = create_app({"TESTING": True, "SECRET_KEY": "test-secret", "WTF_CSRF_ENABLED": False})
        app.config["SERVER_NAME"] = "localhost"

        with app.test_client() as client:
            with client.session_transaction() as session_data:
                session_data["ollama_api_key"] = "ollama_test"
                session_data["ollama_model"] = "gemma3:4b"
                session_data["ollama_features"] = {
                    "heading_fix": True,
                    "markitdown": True,
                    "chat": False,
                    "playground": True,
                }
                session_data["playground_history"] = [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there"},
                ]

            resp = client.get("/beta/chat/")

        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert 'aria-label="AI response"' not in html
        assert 'aria-label="You said"' not in html
        assert 'Copy response' in html
        assert 'Model: gemma3:4b' in html
