from __future__ import annotations

import io
from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web import ai_features
from acb_large_print_web.app import create_app


@pytest.fixture()
def app(tmp_path: Path) -> Flask:
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "MAX_CONTENT_LENGTH": 500 * 1024 * 1024,
        }
    )
    application.instance_path = str(tmp_path / "instance")
    Path(application.instance_path).mkdir(parents=True, exist_ok=True)
    return application


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def test_get_all_flags_respects_master_and_per_feature_env(monkeypatch):
    monkeypatch.setattr(ai_features, "is_ai_configured", lambda: True)
    monkeypatch.setenv("GLOW_ENABLE_AI", "1")
    monkeypatch.setenv("GLOW_ENABLE_AI_CHAT", "0")
    monkeypatch.setenv("GLOW_ENABLE_AI_WHISPERER", "0")
    monkeypatch.setenv("GLOW_ENABLE_AI_HEADING_FIX", "1")

    flags = ai_features.get_all_flags()

    assert flags["ai_configured"] is True
    assert flags["ai_chat_enabled"] is False
    assert flags["ai_whisperer_enabled"] is False
    assert flags["ai_heading_fix_enabled"] is True


def test_get_all_flags_master_off_disables_everything(monkeypatch):
    monkeypatch.setattr(ai_features, "is_ai_configured", lambda: True)
    monkeypatch.setenv("GLOW_ENABLE_AI", "0")
    monkeypatch.setenv("GLOW_ENABLE_AI_CHAT", "1")
    monkeypatch.setenv("GLOW_ENABLE_AI_WHISPERER", "1")

    flags = ai_features.get_all_flags()

    assert flags["ai_configured"] is False
    assert flags["ai_chat_enabled"] is False
    assert flags["ai_whisperer_enabled"] is False
    assert flags["ai_heading_fix_enabled"] is False


def test_process_available_actions_hide_ai_when_gated(monkeypatch):
    from acb_large_print_web.routes import process as process_route

    monkeypatch.setattr(process_route, "ai_chat_enabled", lambda: False)
    monkeypatch.setattr(process_route, "ai_whisperer_enabled", lambda: False)

    docx_actions = process_route._get_available_actions(".docx")
    audio_actions = process_route._get_available_actions(".mp3")

    assert docx_actions["chat"]["enabled"] is False
    assert audio_actions["whisperer"]["enabled"] is False


def test_process_submit_rejects_audio_when_whisperer_is_gated(
    client, monkeypatch
):
    from acb_large_print_web.routes import process as process_route

    monkeypatch.setattr(process_route, "ai_whisperer_enabled", lambda: False)

    response = client.post(
        "/process/",
        data={"file": (io.BytesIO(b"fake audio"), "sample.mp3")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert b"not supported" in response.data.lower()


def test_home_hides_gated_ai_entry_points(client, monkeypatch):
    monkeypatch.setattr(ai_features, "is_ai_configured", lambda: True)
    monkeypatch.setenv("GLOW_ENABLE_AI", "1")
    monkeypatch.setenv("GLOW_ENABLE_AI_CHAT", "0")
    monkeypatch.setenv("GLOW_ENABLE_AI_WHISPERER", "0")

    response = client.get("/")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "BITS Whisperer" not in html
    assert "Document Chat" not in html


def test_whisperer_form_returns_404_when_feature_is_gated(client, monkeypatch):
    monkeypatch.setattr(ai_features, "ai_whisperer_enabled", lambda: False)

    response = client.get("/whisperer/")

    assert response.status_code == 404


def test_fix_parse_form_options_disables_ai_when_heading_fix_is_gated(
    app, monkeypatch
):
    from werkzeug.datastructures import MultiDict

    from acb_large_print_web.routes.fix import _parse_form_options

    monkeypatch.setattr(ai_features, "ai_heading_fix_enabled", lambda: False)

    with app.app_context():
        opts = _parse_form_options(
            MultiDict({"detect_headings": "on", "use_ai": "on"})
        )

    assert opts["detect_headings"] is True
    assert opts["use_ai"] is False
