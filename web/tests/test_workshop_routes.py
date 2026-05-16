from __future__ import annotations

from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web.app import create_app
from acb_large_print_web.workshop_store import add_feedback, ensure_session, save_submission


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


def _seed_workshop(app: Flask, session_code: str = "demo75") -> str:
    with app.app_context():
        ensure_session(session_code, title="GLOW Workshop Demo", event_name="CSUN")
        submission_id = save_submission(
            session_code,
            "teach_vs_fix",
            "Alex",
            "Coach by clarifying the partner's barrier first.",
            anonymity_mode=False,
        )
        add_feedback(
            session_code,
            submission_id,
            "Sam",
            "Clear plain-language framing",
            "May skip policy requirement checks",
            "Add explicit policy review checkpoint",
            "Reuse this as a team checklist template",
        )
    return session_code


def test_workshop_facilitator_and_surfaces(client, app: Flask):
    code = _seed_workshop(app)

    dashboard = client.get(f"/workshop/session/{code}/facilitator")
    assert dashboard.status_code == 200
    html = dashboard.get_data(as_text=True)
    assert "Facilitator Dashboard" in html
    assert "Feedback coverage" in html

    coach = client.get(f"/workshop/session/{code}/coach")
    assert coach.status_code == 200
    assert "Coach Mode" in coach.get_data(as_text=True)

    review = client.get(f"/workshop/session/{code}/review")
    assert review.status_code == 200
    assert "Review Mode" in review.get_data(as_text=True)

    share = client.get(f"/workshop/session/{code}/share")
    assert share.status_code == 200
    assert "Share Mode" in share.get_data(as_text=True)


def test_workshop_export_formats(client, app: Flask):
    code = _seed_workshop(app, "exports75")

    md = client.get(f"/workshop/session/{code}/export/markdown")
    assert md.status_code == 200
    assert md.mimetype == "text/markdown"
    assert "GLOW Workshop Demo" in md.get_data(as_text=True)

    js = client.get(f"/workshop/session/{code}/export/json")
    assert js.status_code == 200
    assert js.mimetype == "application/json"
    assert '"session_code": "exports75"' in js.get_data(as_text=True)

    html = client.get(f"/workshop/session/{code}/export/html")
    assert html.status_code == 200
    assert html.mimetype == "text/html"
    assert "GLOW Workshop Demo" in html.get_data(as_text=True)

    docx = client.get(f"/workshop/session/{code}/export/docx")
    assert docx.status_code == 200
    assert docx.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert docx.data.startswith(b"PK")


def test_workshop_follow_through_flow(client, app: Flask):
    code = _seed_workshop(app, "follow75")

    page = client.get(f"/workshop/session/{code}/follow-through")
    assert page.status_code == 200
    assert "Workshop Follow-Through" in page.get_data(as_text=True)

    save_resp = client.post(
        f"/workshop/session/{code}/follow-through",
        data={
            "item_kind": "action_commitment",
            "item_title": "Run team follow-up",
            "owner_name": "Alex",
            "due_date": "2026-06-15",
            "item_details": "Check adoption and confidence with the partner team.",
        },
    )
    assert save_resp.status_code == 200
    body = save_resp.get_data(as_text=True)
    assert "Saved follow-through item." in body
    assert "Run team follow-up" in body

    status_resp = client.post(
        f"/workshop/session/{code}/follow-through/1/status",
        data={"status": "done"},
    )
    assert status_resp.status_code in (302, 303)

    export_resp = client.get(f"/workshop/session/{code}/follow-through/export/markdown")
    assert export_resp.status_code == 200
    export_body = export_resp.get_data(as_text=True)
    assert "Run team follow-up" in export_body
    assert "2026-06-15" in export_body
    assert "Status: done" in export_body


def test_homepage_surfaces_workshop_follow_through(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Workshop Follow-Through" in body
