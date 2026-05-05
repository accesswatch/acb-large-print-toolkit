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


def test_convert_to_txt_direction_returns_result_page(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(convert_route, "pandoc_available", lambda: True)

    def _fake_convert_to_txt(src_path: Path, output_path: Path | None = None, *, title: str | None = None):
        out = output_path or src_path.with_suffix(".txt")
        out.write_text("Plain text output", encoding="utf-8")
        return out, out.stat().st_size

    monkeypatch.setattr(convert_route, "convert_to_txt", _fake_convert_to_txt)

    res = client.post(
        "/convert/",
        data={
            "direction": "to-txt",
            "document": (io.BytesIO(b"# Heading\n\nBody text"), "sample.md"),
            "title": "Sample",
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "sample.txt" in body
    assert "Download" in body


def test_convert_to_rtf_direction_returns_result_page(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(convert_route, "pandoc_available", lambda: True)

    def _fake_convert_to_rtf(src_path: Path, output_path: Path | None = None, *, title: str | None = None):
        out = output_path or src_path.with_suffix(".rtf")
        out.write_bytes(b"{\\rtf1\\ansi Fake RTF}")
        return out, out.stat().st_size

    monkeypatch.setattr(convert_route, "convert_to_rtf", _fake_convert_to_rtf)

    res = client.post(
        "/convert/",
        data={
            "direction": "to-rtf",
            "document": (io.BytesIO(b"# Heading\n\nBody text"), "sample.md"),
            "title": "Sample",
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "sample.rtf" in body
    assert "Download" in body


def test_convert_to_txt_respects_feature_flag(client, monkeypatch: pytest.MonkeyPatch):
    original_get_all_flags = convert_route.get_all_flags

    def _flags_disabled() -> dict:
        flags = original_get_all_flags()
        flags["GLOW_ENABLE_CONVERT_TO_TXT"] = False
        return flags

    monkeypatch.setattr(convert_route, "get_all_flags", _flags_disabled)
    monkeypatch.setattr(convert_route, "pandoc_available", lambda: True)

    res = client.post(
        "/convert/",
        data={
            "direction": "to-txt",
            "document": (io.BytesIO(b"# Heading\n\nBody text"), "sample.md"),
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 400
    body = res.get_data(as_text=True)
    assert "disabled on this server" in body


def test_convert_to_rtf_respects_feature_flag(client, monkeypatch: pytest.MonkeyPatch):
    original_get_all_flags = convert_route.get_all_flags

    def _flags_disabled() -> dict:
        flags = original_get_all_flags()
        flags["GLOW_ENABLE_CONVERT_TO_RTF"] = False
        return flags

    monkeypatch.setattr(convert_route, "get_all_flags", _flags_disabled)
    monkeypatch.setattr(convert_route, "pandoc_available", lambda: True)

    res = client.post(
        "/convert/",
        data={
            "direction": "to-rtf",
            "document": (io.BytesIO(b"# Heading\n\nBody text"), "sample.md"),
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 400
    body = res.get_data(as_text=True)
    assert "disabled on this server" in body
