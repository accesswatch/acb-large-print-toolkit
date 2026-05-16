from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web.app import create_app
from acb_large_print_web.chat_handler import ChatSession


@pytest.fixture()
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Flask:
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret",
        }
    )
    application.instance_path = str(tmp_path / "instance")
    Path(application.instance_path).mkdir(parents=True, exist_ok=True)

    from acb_large_print_web import feature_flags
    from acb_large_print_web import upload as upload_mod

    monkeypatch.setattr(upload_mod, "UPLOAD_TEMP_BASE", tmp_path / "uploads")
    upload_mod.UPLOAD_TEMP_BASE.mkdir(parents=True, exist_ok=True)
    with application.app_context():
        feature_flags.set_flag("GLOW_ENABLE_AI", True)
        feature_flags.set_flag("GLOW_ENABLE_AI_CHAT", True)
    return application


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def test_chat_submit_sanitizes_ai_payload(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from acb_large_print_web import upload as upload_mod
    from acb_large_print_web.routes import chat as chat_route

    token = str(uuid.uuid4())
    temp_dir = upload_mod.UPLOAD_TEMP_BASE / token
    temp_dir.mkdir(parents=True, exist_ok=True)
    (temp_dir / "notes.txt").write_text(
        "Reach me at owner@contoso.com for project details.", encoding="utf-8"
    )

    with client.session_transaction() as sess:
        sess["_id"] = "session-1"
        sess[f"chat_{token}"] = ChatSession(token, "notes.txt").to_dict()

    class _FakeTools:
        def __init__(self, _context):
            pass

        def dispatch_for_question(self, _question: str) -> str:
            return "[=== GLOW Document Analysis (pre-flight tool results) ===]\nContact owner@contoso.com"

        def get_document_summary(self) -> str:
            return "Summary: owner@contoso.com"

        def get_compliance_score(self) -> str:
            return "Score: 92"

        def get_what_passes(self) -> str:
            return "Passes: heading hierarchy"

    captured: dict[str, str] = {}

    def fake_sanitize(text: str, *, surface: str, strict=None):
        return text.replace("owner@contoso.com", "[REDACTED_EMAIL]"), {
            "enabled": True,
            "applied": True,
            "redacted": True,
            "entity_count": 1,
        }

    def fake_gateway_chat(**kwargs):
        captured["question"] = kwargs.get("question", "")
        captured["system_prompt"] = kwargs.get("system_prompt", "")
        captured["document_text"] = kwargs.get("document_text", "")
        return "Done.", False

    monkeypatch.setattr(chat_route, "require_ai_feature", lambda _feature: None)
    monkeypatch.setattr(chat_route, "get_quota_status", lambda _hash: {"chat_available": True, "session_available": True})
    monkeypatch.setattr(chat_route, "make_session_hash", lambda _sess_id: "hash-1")
    monkeypatch.setattr(chat_route, "ai_gate", lambda wait_seconds=None: __import__("contextlib").nullcontext())
    monkeypatch.setattr(chat_route, "ToolRegistry", _FakeTools)
    monkeypatch.setattr(chat_route, "sanitize_text_for_ai", fake_sanitize)
    monkeypatch.setattr(chat_route, "gateway_chat", fake_gateway_chat)

    response = client.post(
        "/chat/",
        data={"token": token, "question": "Please summarize owner@contoso.com contact details."},
    )

    assert response.status_code == 302
    assert "[REDACTED_EMAIL]" in captured["question"]
    assert "owner@contoso.com" not in captured["question"]
    assert "[REDACTED_EMAIL]" in captured["system_prompt"]
    assert "[REDACTED_EMAIL]" in captured["document_text"]
