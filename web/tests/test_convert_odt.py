from __future__ import annotations

import io
from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web.app import create_app
import acb_large_print_web.routes.convert as convert_route


@pytest.fixture()
def app(tmp_path: Path) -> Flask:
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "MAX_CONTENT_LENGTH": 50 * 1024 * 1024,
        }
    )
    application.instance_path = str(tmp_path / "instance")
    Path(application.instance_path).mkdir(parents=True, exist_ok=True)
    return application


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def test_convert_to_odt_direction_returns_result_page(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(convert_route, "pandoc_available", lambda: True)

    def _fake_convert_to_odt(src_path: Path, output_path: Path | None = None, *, title: str | None = None):
        out = output_path or src_path.with_suffix(".odt")
        out.write_bytes(b"PK\x03\x04fake-odt")
        return out, out.stat().st_size

    monkeypatch.setattr(convert_route, "convert_to_odt", _fake_convert_to_odt)

    res = client.post(
        "/convert/",
        data={
            "direction": "to-odt",
            "document": (io.BytesIO(b"# Heading\n\nBody text"), "sample.md"),
            "title": "Sample",
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "sample.odt" in body
    assert "Download" in body


def test_convert_to_odt_respects_feature_flag(client, monkeypatch: pytest.MonkeyPatch):
    original_get_all_flags = convert_route.get_all_flags

    def _flags_disabled() -> dict:
        flags = original_get_all_flags()
        flags["GLOW_ENABLE_CONVERT_TO_ODT"] = False
        return flags

    monkeypatch.setattr(convert_route, "get_all_flags", _flags_disabled)
    monkeypatch.setattr(convert_route, "pandoc_available", lambda: True)

    res = client.post(
        "/convert/",
        data={
            "direction": "to-odt",
            "document": (io.BytesIO(b"# Heading\n\nBody text"), "sample.md"),
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 400
    body = res.get_data(as_text=True)
    assert "disabled on this server" in body
