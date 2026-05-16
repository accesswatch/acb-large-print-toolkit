from __future__ import annotations

from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web.app import create_app
from acb_large_print_web.workshop_store import add_feedback, ensure_session, save_submission, upsert_conference_code


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
    explore_idx = body.find('id="nav-group-explore"')
    workshop_idx = body.find("Workshop Follow-Through")
    beta_idx = body.find('id="nav-group-beta"')
    assert explore_idx != -1 and workshop_idx != -1
    assert explore_idx < workshop_idx
    if beta_idx != -1:
        assert workshop_idx < beta_idx


def test_workshop_activity_structured_form_and_save_next(client, app: Flask):
    with app.app_context():
        ensure_session("magic75", title="Magical Workshop Session")

    page = client.get("/workshop/session/magic75/activity/journey_check_in")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "Interactive Activity Form" in html
    assert "Workshop Progress Passport" in html

    save_next = client.post(
        "/workshop/session/magic75/activity/journey_check_in",
        data={
            "display_name": "Jordan",
            "work_type": "I coach faculty on course content accessibility.",
            "partner_blockers": "People do not know where to start with headings and links.",
            "champion_shift": "Teams would fix issues earlier and reuse checklists.",
            "bonus_note": "Bring this into onboarding.",
            "submit_action": "save_next",
        },
    )
    assert save_next.status_code in (302, 303)
    assert "/workshop/session/magic75/activity/problem_statement" in save_next.headers.get("Location", "")

    gallery = client.get("/workshop/session/magic75/gallery")
    assert gallery.status_code == 200
    gallery_html = gallery.get_data(as_text=True)
    assert "Activity: Accessibility Journey Check-In" in gallery_html
    assert "Bring this into onboarding." in gallery_html


def test_workshop_code_lookup_then_name_join_and_my_content(client, app: Flask):
    with app.app_context():
        upsert_conference_code(
            "AHG2026",
            session_code="ahg2026",
            session_title="AHG Workshop Session",
            event_name="Accessing Higher Ground",
            active=True,
        )

    lookup = client.post(
        "/workshop/",
        data={"action": "lookup", "access_code": "AHG2026"},
        follow_redirects=True,
    )
    assert lookup.status_code == 200
    lookup_html = lookup.get_data(as_text=True)
    assert "Step 2: Confirm participant identity" in lookup_html
    assert "AHG Workshop Session" in lookup_html

    joined = client.post(
        "/workshop/",
        data={"action": "join", "session_code": "ahg2026", "display_name": "Pat"},
        follow_redirects=False,
    )
    assert joined.status_code in (302, 303)
    assert "/workshop/session/ahg2026/activity/journey_check_in" in joined.headers.get("Location", "")
    assert "glow_workshop_participant=" in joined.headers.get("Set-Cookie", "")

    start = client.get(joined.headers.get("Location", ""))
    assert start.status_code == 200
    start_html = start.get_data(as_text=True)
    assert "Participant:</strong> Pat" in start_html
    assert "My content" in start_html

    client.post(
        "/workshop/session/ahg2026/activity/journey_check_in",
        data={
            "display_name": "Pat",
            "work_type": "Accessibility office support.",
            "partner_blockers": "Confidence and process gaps.",
            "champion_shift": "More shared ownership across departments.",
            "bonus_note": "Need onboarding checklist.",
            "submit_action": "save",
        },
    )

    my_page = client.get("/workshop/session/ahg2026/me")
    assert my_page.status_code == 200
    my_html = my_page.get_data(as_text=True)
    assert "My Workshop Content" in my_html
    assert "Need onboarding checklist." in my_html


def test_workshop_launchpad_tokens_and_samples(client, app: Flask):
    with app.app_context():
        ensure_session("launch75", title="Launchpad Session")

    resp = client.get("/workshop/session/launch75/launchpad")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Magical Exercise Launchpad" in html
    assert "GLOW:AUDIT" in html
    assert "workshop_return=" in html
    assert "/workshop/session/launch75/samples/board-agenda-docx" in html


def test_workshop_return_banner_only_for_workshop_participants(client, app: Flask):
    # Not in workshop: banner should stay hidden even if query params are present.
    resp = client.get("/?workshop_return=/workshop/session/demo75/launchpad&workshop_label=Return%20to%20Workshop%20(demo75)")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Workshop flow:" not in body

    # After joining a workshop session, the banner should render.
    with app.app_context():
        ensure_session("demo75", title="Demo Session")
    joined = client.post(
        "/workshop/",
        data={"action": "join", "session_code": "demo75", "display_name": "Pat"},
        follow_redirects=False,
    )
    assert joined.status_code in (302, 303)

    resp2 = client.get("/?workshop_return=/workshop/session/demo75/launchpad&workshop_label=Return%20to%20Workshop%20(demo75)")
    assert resp2.status_code == 200
    body2 = resp2.get_data(as_text=True)
    assert "Workshop flow:" in body2
    assert "Return to Workshop (demo75)" in body2
