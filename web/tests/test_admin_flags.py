from __future__ import annotations

import os

import pytest
from pathlib import Path

from acb_large_print_web import feature_flags
from tests.helpers import assert_flag_rendered, parse_iso_ts
from acb_large_print_web.app import create_app


@pytest.fixture(autouse=True)
def ensure_bootstrap_admin(monkeypatch):
    # Ensure an approved admin exists for tests and avoid interactive login
    monkeypatch.setenv("ADMIN_BOOTSTRAP_EMAILS", "test-admin@example.com")
    yield


@pytest.fixture()
def app(tmp_path: Path):
    application = create_app(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "MAX_CONTENT_LENGTH": 500 * 1024 * 1024}
    )
    application.instance_path = str(tmp_path / "instance")
    Path(application.instance_path).mkdir(parents=True, exist_ok=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def _login_as_admin(client):
    with client.session_transaction() as sess:
        sess["admin_email"] = "test-admin@example.com"


def test_admin_flags_page_shows_backend_and_flags(client, monkeypatch):
    monkeypatch.setenv("FEATURE_FLAGS_BACKEND", "json")
    _login_as_admin(client)

    res = client.get("/admin/flags")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Feature Flags" in html
    assert "Flags backend" in html
    assert "GLOW_ENABLE_AI" in html
    # The admin page should render a readable label and accessible input id
    assert_flag_rendered(html, "GLOW_ENABLE_AI")


def test_admin_update_flags_persists(app, client, monkeypatch):
    monkeypatch.setenv("FEATURE_FLAGS_BACKEND", "json")
    _login_as_admin(client)

    # Post with no checkbox for GLOW_ENABLE_AI to turn it off
    res = client.post("/admin/flags", data={}, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        assert feature_flags.get_flag("GLOW_ENABLE_AI") is False


def test_migrate_endpoint_invokes_helper(client, monkeypatch):
    monkeypatch.setenv("FEATURE_FLAGS_BACKEND", "sqlite")
    called = []

    def fake_migrate():
        called.append(True)

    # Patch the admin module binding (it imports the helper at module import time)
    from acb_large_print_web.routes import admin as admin_routes

    monkeypatch.setattr(admin_routes, "_migrate_flags", fake_migrate)
    _login_as_admin(client)

    res = client.post("/admin/flags/migrate", data={}, follow_redirects=True)
    assert res.status_code == 200
    assert called, "migrate_json_to_sqlite should have been called"


def test_admin_audit_log_shows_recent_changes(app, client, monkeypatch):
    """When flags change (sqlite backend), the admin Flags page shows audit entries."""
    monkeypatch.setenv("FEATURE_FLAGS_BACKEND", "sqlite")
    _login_as_admin(client)

    # Ensure sqlite backend is fresh
    with app.app_context():
        from acb_large_print_web import feature_flags as ff

        # Reset persisted store and then set a flag twice to generate audit rows
        ff.reset_defaults()
        ff.set_flag("GLOW_ENABLE_AUDIT", True, changed_by="tester@example.com")
        ff.set_flag("GLOW_ENABLE_AUDIT", False, changed_by="tester@example.com")

    # Request admin flags page and assert audit log contains our entries
    res = client.get("/admin/flags")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    # Check for the flag name and the changed_by identity
    assert "GLOW_ENABLE_AUDIT" in html
    assert "tester@example.com" in html


def test_admin_ai_cascade_persists_and_audit(app, client, monkeypatch):
    """Turning off master AI in the admin POST should cascade to AI subfeatures
    and create audit entries for the child flags (sqlite backend).
    """
    monkeypatch.setenv("FEATURE_FLAGS_BACKEND", "sqlite")
    _login_as_admin(client)

    # Prepare persisted store with AI features enabled
    with app.app_context():
        from acb_large_print_web import feature_flags as ff

        ff.reset_defaults()
        # Ensure master + children are enabled initially
        ff.set_flag("GLOW_ENABLE_AI", True, changed_by="setup@example.com")
        ff.set_flag("GLOW_ENABLE_AI_CHAT", True, changed_by="setup@example.com")
        ff.set_flag("GLOW_ENABLE_AI_WHISPERER", True, changed_by="setup@example.com")

    # Submit admin form with no checkboxes for AI (master omitted -> off)
    res = client.post("/admin/flags", data={}, follow_redirects=True)
    assert res.status_code == 200

    # Verify persisted flags were cascaded off and audit entries recorded
    with app.app_context():
        from acb_large_print_web import feature_flags as ff

        assert ff.get_flag("GLOW_ENABLE_AI") is False
        assert ff.get_flag("GLOW_ENABLE_AI_CHAT") is False
        assert ff.get_flag("GLOW_ENABLE_AI_WHISPERER") is False

        chat_audit = ff.get_audit_entries("GLOW_ENABLE_AI_CHAT", limit=10)
        whisper_audit = ff.get_audit_entries("GLOW_ENABLE_AI_WHISPERER", limit=10)

        assert any(e.get("changed_by") == "test-admin@example.com" for e in chat_audit), "Admin change should be audited for AI_CHAT"
        assert any(e.get("changed_by") == "test-admin@example.com" for e in whisper_audit), "Admin change should be audited for WHISPERER"

        # Verify audit entry fields include id, changed_at (ISO8601) and old/new values
        for name, audit_list in (
            ("GLOW_ENABLE_AI_CHAT", chat_audit),
            ("GLOW_ENABLE_AI_WHISPERER", whisper_audit),
        ):
            assert any(isinstance(e.get("id"), int) for e in audit_list), f"Expected numeric id in {name} audit"
            # changed_at should be present and parseable as ISO8601
            parsed = None
            for e in audit_list:
                parsed = parse_iso_ts(e.get("changed_at"))
                if parsed:
                    break
            assert parsed is not None, f"changed_at must be ISO8601 for {name} audit entries"

            # Ensure at least one audit row reflects the transition True -> False
            assert any((e.get("old_value") is True and e.get("new_value") is False) for e in audit_list), (
                f"Expected an audit row where {name} changed True -> False"
            )
