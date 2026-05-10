"""Tests for the Ollama Cloud gateway path and settings routes."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
        import requests as req_lib

        monkeypatch.setattr(ai_gateway, "get_user_ollama_key", lambda: "ollama_badkey")
        monkeypatch.setattr(ai_gateway, "get_ollama_cloud_url", lambda: "https://ollama.com/api")

        bad_resp = MagicMock()
        bad_resp.status_code = 401
        bad_resp.raise_for_status = MagicMock()

        with patch("acb_large_print_web.ai_gateway.requests.post", return_value=bad_resp):
            with pytest.raises(RuntimeError, match="invalid or has been revoked"):
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

    def test_save_rejects_bad_prefix(self, settings_client) -> None:
        resp = settings_client.post(
            "/settings/ai/key",
            data={"ollama_api_key": "sk-openai-notollama", "ollama_model": "llama3.2"},
        )
        assert resp.status_code == 400
        assert "ollama_" in resp.get_json()["error"]

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
        assert "llama3.2" in data["models"]

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
