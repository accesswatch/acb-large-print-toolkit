from __future__ import annotations

import io
from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web.app import create_app


@pytest.fixture()
def app(tmp_path: Path) -> Flask:
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
        }
    )
    application.instance_path = str(tmp_path / "instance")
    Path(application.instance_path).mkdir(parents=True, exist_ok=True)
    return application


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def test_pdf_forms_disabled_by_default_returns_404(client, monkeypatch):
    from acb_large_print_web.routes import pdf_forms as pdf_forms_routes
    monkeypatch.setattr(pdf_forms_routes, "_beta_enabled", lambda: False)
    resp = client.get("/pdf-forms/")
    assert resp.status_code == 404


def test_pdf_forms_home_renders_when_enabled(client, monkeypatch):
    from acb_large_print_web.routes import pdf_forms as pdf_forms_routes
    monkeypatch.setattr(pdf_forms_routes, "_beta_enabled", lambda: True)
    resp = client.get("/pdf-forms/")
    assert resp.status_code == 200
    assert "PDF Forms Beta" in resp.get_data(as_text=True)


def test_pdf_forms_api_inspect_returns_json_when_enabled(client, monkeypatch):
    from acb_large_print_web.routes import pdf_forms as pdf_forms_routes
    monkeypatch.setattr(pdf_forms_routes, "_beta_enabled", lambda: True)

    monkeypatch.setattr(
        pdf_forms_routes,
        "inspect_pdf_form",
        lambda _path: {
            "classification": {
                "class": "acroform_supported",
                "round_trip_support": "yes",
                "supported": True,
                "reason": "ok",
            },
            "warnings": [],
            "fields": [],
            "summary": {"total_fields": 0, "field_type_counts": {}, "low_confidence_fields": 0},
            "file_path": "x.pdf",
        },
    )

    resp = client.post(
        "/pdf-forms/api/inspect",
        data={"file": (io.BytesIO(b"%PDF-1.4\n1 0 obj\n"), "sample.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload is not None
    assert payload["classification"]["class"] == "acroform_supported"
