from __future__ import annotations

import pytest

from acb_large_print_web.app import create_app
from acb_large_print_web.keycloak import build_oidc_settings


@pytest.fixture()
def client(tmp_path):
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    app.instance_path = str(tmp_path / "instance")
    return app.test_client()


def test_keycloak_health_route_not_configured(client):
    resp = client.get("/health/keycloak")
    assert resp.status_code == 503
    assert resp.get_json() == {"keycloak": "not-configured"}


def test_keycloak_oidc_settings_build_from_env(monkeypatch):
    monkeypatch.setenv("KEYCLOAK_BASE_URL", "https://keycloak.example.com")
    monkeypatch.setenv("KEYCLOAK_REALM", "glow")
    monkeypatch.setenv("KEYCLOAK_CLIENT_ID", "glow-web")
    monkeypatch.setenv("KEYCLOAK_CLIENT_SECRET", "secret")
    monkeypatch.setenv("KEYCLOAK_REDIRECT_URI", "https://lp.csedesigns.com/authorize")
    monkeypatch.setenv("OIDC_SCOPES", "openid email profile")

    settings = build_oidc_settings()

    assert settings is not None
    assert settings["OIDC_ENABLED"] is True
    assert settings["OIDC_SCOPES"] == "openid email profile"
    assert settings["OIDC_CLIENT_SECRETS"]["web"]["issuer"] == "https://keycloak.example.com/realms/glow"
    assert settings["OIDC_CLIENT_SECRETS"]["web"]["redirect_uris"] == ["https://lp.csedesigns.com/authorize"]
    assert settings["OIDC_OVERWRITE_REDIRECT_URI"] == "https://lp.csedesigns.com/authorize"


def test_keycloak_health_route_uses_configured_url(client, monkeypatch):
    monkeypatch.setenv("KEYCLOAK_BASE_URL", "https://keycloak.example.com")
    monkeypatch.setenv("KEYCLOAK_REALM", "glow")

    calls: list[str] = []

    class _Resp:
        status_code = 200

    def _fake_get(url, timeout):
        calls.append(url)
        return _Resp()

    monkeypatch.setattr("acb_large_print_web.routes.status.requests.get", _fake_get)

    resp = client.get("/health/keycloak")

    assert resp.status_code == 200
    assert resp.get_json() == {"keycloak": "ok"}
    assert calls == ["https://keycloak.example.com/realms/glow"]
