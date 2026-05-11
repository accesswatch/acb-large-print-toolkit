from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web.app import create_app


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
        feature_flags.set_flag("GLOW_ENABLE_AI_ALT_TEXT", True)
    return application


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def test_process_available_actions_offer_alt_text_for_visual_formats(monkeypatch: pytest.MonkeyPatch) -> None:
    from acb_large_print_web.routes import process as process_route

    monkeypatch.setattr(process_route, "ai_alt_text_enabled", lambda: True)
    monkeypatch.setattr(process_route, "ai_chat_enabled", lambda: False)
    monkeypatch.setattr(process_route, "ai_whisperer_enabled", lambda: False)

    assert process_route._get_available_actions(".png")["alt_text"]["enabled"] is True
    assert process_route._get_available_actions(".pdf")["alt_text"]["enabled"] is True
    assert process_route._get_available_actions(".pptx")["alt_text"]["enabled"] is True
    assert process_route._get_available_actions(".xlsx")["alt_text"]["enabled"] is True


def test_ai_estimate_endpoint_returns_estimate_and_quota(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from acb_large_print_web.routes import ai_usage as ai_usage_route

    monkeypatch.setattr(
        ai_usage_route,
        "estimate_request_cost",
        lambda **kwargs: {
            "feature": kwargs.get("feature"),
            "provider": "openrouter",
            "model": "openai/gpt-4o-mini",
            "estimated_total_tokens": 321,
            "estimated_cost_usd": 0.0042,
            "cost_available": True,
        },
    )
    monkeypatch.setattr(
        ai_usage_route,
        "get_quota_status",
        lambda _session_hash: {
            "budget_remaining_usd": 12.5,
            "session_quota_enabled": True,
            "session_requests_remaining": 7,
            "session_reset_seconds": 1800,
        },
    )

    response = client.post(
        "/ai/usage/estimate",
        json={"feature": "chat", "message": "Summarize section 2."},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["estimate"]["estimated_total_tokens"] == 321
    assert payload["quota"]["session_requests_remaining"] == 7


def test_enforce_session_quota_raises_when_window_is_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    from acb_large_print_web import ai_gateway

    monkeypatch.setattr(
        ai_gateway,
        "get_quota_status",
        lambda _session_hash: {
            "session_available": False,
            "session_reset_seconds": 600,
        },
    )

    with pytest.raises(RuntimeError, match="request limit"):
        ai_gateway.enforce_session_quota("session-1")


def test_alt_text_helper_renders_visual_items(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from acb_large_print_web import ai_features
    from acb_large_print_web.routes import alt_text as alt_text_route

    monkeypatch.setattr(ai_features, "ai_alt_text_enabled", lambda: True)
    token = str(uuid.uuid4())
    # Build a real temp session directory under the patched upload root.
    from acb_large_print_web import upload as upload_mod

    temp_dir = upload_mod.UPLOAD_TEMP_BASE / token
    temp_dir.mkdir(parents=True, exist_ok=True)
    (temp_dir / "slide-deck.pptx").write_bytes(b"PK")

    monkeypatch.setattr(
        alt_text_route,
        "extract_visual_items",
        lambda _path: [
            {
                "index": 0,
                "total_items": 1,
                "label": "Slide 1 chart",
                "location": "Slide 1",
                "source_type": "pptx-chart",
                "preview_data_uri": "",
                "mime_type": "",
                "width": None,
                "height": None,
                "current_alt_text": "",
                "context_lines": ["Slide title: Revenue trend"],
                "text_only": True,
            }
        ],
    )

    response = client.get(f"/alt-text/?token={token}")

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Alt-Text Helper" in html
    assert "Slide 1 chart" in html


def test_alt_text_suggest_uses_text_only_generation(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from acb_large_print_web import ai_features
    from acb_large_print_web import upload as upload_mod
    from acb_large_print_web.routes import alt_text as alt_text_route

    monkeypatch.setattr(ai_features, "ai_alt_text_enabled", lambda: True)
    token = str(uuid.uuid4())
    temp_dir = upload_mod.UPLOAD_TEMP_BASE / token
    temp_dir.mkdir(parents=True, exist_ok=True)
    (temp_dir / "charts.xlsx").write_bytes(b"PK")

    monkeypatch.setattr(
        alt_text_route,
        "extract_visual_items",
        lambda _path: [
            {
                "index": 0,
                "total_items": 1,
                "label": "Sheet 1 chart 1",
                "location": "Sheet 1",
                "source_type": "xlsx-chart",
                "mime_type": "",
                "image_bytes": b"",
                "preview_data_uri": "",
                "width": None,
                "height": None,
                "current_alt_text": "",
                "context_lines": ["Chart title: Quarterly revenue", "Series: North, South"],
                "text_only": True,
            }
        ],
    )
    monkeypatch.setattr(alt_text_route, "ai_gate", lambda wait_seconds=None: __import__("contextlib").nullcontext())
    monkeypatch.setattr(alt_text_route, "gateway_chat", lambda **kwargs: ("Quarterly revenue chart showing North ahead of South.", False))

    response = client.post(
        "/alt-text/suggest",
        data={"token": token, "item_index": "0", "extra_instruction": "Focus on the main trend."},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert "Quarterly revenue chart" in payload["suggestion"]
