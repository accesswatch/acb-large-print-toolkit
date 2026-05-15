"""Keycloak OIDC configuration helpers."""

from __future__ import annotations

import os
from typing import Any


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def get_keycloak_issuer_url() -> str | None:
    base_url = _env("KEYCLOAK_BASE_URL")
    realm = _env("KEYCLOAK_REALM")
    if not base_url or not realm:
        return None
    return f"{base_url.rstrip('/')}/realms/{realm}"


def get_keycloak_health_url() -> str | None:
    return get_keycloak_issuer_url()


def _redirect_uri() -> str:
    return _env("KEYCLOAK_REDIRECT_URI") or _env("OIDC_OVERWRITE_REDIRECT_URI")


def build_oidc_client_secrets() -> dict[str, dict[str, Any]] | None:
    client_id = _env("KEYCLOAK_CLIENT_ID")
    client_secret = _env("KEYCLOAK_CLIENT_SECRET")
    redirect_uri = _redirect_uri()
    issuer = get_keycloak_issuer_url()

    if not client_id or not client_secret or not redirect_uri or not issuer:
        return None

    auth_base = f"{issuer}/protocol/openid-connect"
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": f"{auth_base}/auth",
            "token_uri": f"{auth_base}/token",
            "token_introspection_uri": f"{auth_base}/token/introspect",
            "userinfo_uri": f"{auth_base}/userinfo",
            "issuer": issuer,
            "redirect_uris": [redirect_uri],
        }
    }


def build_oidc_settings() -> dict[str, Any] | None:
    secrets = build_oidc_client_secrets()
    if secrets is None:
        return None

    scopes = _env("OIDC_SCOPES") or "openid email profile"
    redirect_uri = _redirect_uri()
    settings: dict[str, Any] = {
        "OIDC_CLIENT_SECRETS": secrets,
        "OIDC_ENABLED": True,
        "OIDC_RESOURCE_SERVER_ONLY": False,
        "OIDC_SCOPES": scopes,
    }
    if redirect_uri:
        settings["OIDC_OVERWRITE_REDIRECT_URI"] = redirect_uri
    return settings

