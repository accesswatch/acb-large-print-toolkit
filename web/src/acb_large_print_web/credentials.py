"""Secure credential loading helpers for the web app.

Lookup order for secrets:
1) Environment variable (preferred for production)
2) Local server.credentials file (developer convenience)

The file path defaults to repository root server.credentials and can be overridden
with SERVER_CREDENTIALS_PATH. This module never logs secret values.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


def _credentials_path() -> Path:
    raw = os.environ.get("SERVER_CREDENTIALS_PATH", "").strip()
    if raw:
        return Path(raw)
    # repo root from web/src/acb_large_print_web -> ../../../.. /server.credentials
    return Path(__file__).resolve().parents[3] / "server.credentials"


@lru_cache(maxsize=1)
def _load_file_map() -> dict[str, str]:
    path = _credentials_path()
    out: dict[str, str] = {}
    if not path.exists():
        return out

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped and not stripped.startswith("http"):
            k, v = stripped.split("=", 1)
            out[k.strip().lower()] = v.strip()
            continue
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def secret(name: str, env_name: str | None = None) -> str:
    """Resolve a secret from env first, then server.credentials."""
    if env_name:
        v = os.environ.get(env_name, "").strip()
        if v:
            return v

    data = _load_file_map()
    aliases: dict[str, tuple[str, ...]] = {
        "openrouter_api_key": (
            "openrouter_api_key",
            "openrouter",
            "openrouter api key",
        ),
        "ssh_password": (
            "ssh_password",
            "password",
        ),
    }
    keys = aliases.get(name, (name,))
    for key in keys:
        v = data.get(key.lower(), "").strip()
        if v:
            return v
    return ""


def get_openrouter_api_key() -> str:
    return secret("openrouter_api_key", "OPENROUTER_API_KEY")


def get_bootstrap_admin_email() -> str:
    return os.environ.get("ADMIN_LOCAL_EMAIL", "jeff@jeffbishop.com").strip().lower()


def get_bootstrap_admin_password() -> str:
    # Support multiple env var names for a local bootstrap/admin password.
    # Priority: ADMIN_PASSWORD -> ADMIN_LOCAL_PASSWORD -> server.credentials ssh_password
    return (
        os.environ.get("ADMIN_PASSWORD", "").strip()
        or os.environ.get("ADMIN_LOCAL_PASSWORD", "").strip()
        or secret("ssh_password")
    )
