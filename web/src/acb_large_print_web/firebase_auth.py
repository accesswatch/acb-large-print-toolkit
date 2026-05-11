"""Firebase Authentication helpers.

Supports verifying Firebase ID tokens from web/mobile clients and mapping them
to local GLOW user accounts.

Configuration (env vars):
- FIREBASE_AUTH_ENABLED=1
- FIREBASE_PROJECT_ID=<your firebase project id>
- FIREBASE_CREDENTIALS_JSON=<raw service account json> OR
  FIREBASE_CREDENTIALS_PATH=/app/instance/firebase-service-account.json
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

_firebase_ready = False
_firebase_init_error = ""


def is_enabled() -> bool:
    return (os.environ.get("FIREBASE_AUTH_ENABLED", "0").strip() == "1")


def get_init_error() -> str:
    return _firebase_init_error


def ensure_initialized() -> bool:
    """Initialize Firebase Admin SDK once. Returns True when ready."""
    global _firebase_ready, _firebase_init_error

    if not is_enabled():
        _firebase_init_error = "Firebase auth is disabled."
        return False
    if _firebase_ready:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            _firebase_ready = True
            return True

        creds_json = (os.environ.get("FIREBASE_CREDENTIALS_JSON") or "").strip()
        creds_path = (os.environ.get("FIREBASE_CREDENTIALS_PATH") or "").strip()
        project_id = (os.environ.get("FIREBASE_PROJECT_ID") or "").strip()

        cred_obj = None
        if creds_json:
            parsed = json.loads(creds_json)
            cred_obj = credentials.Certificate(parsed)
        elif creds_path:
            cred_obj = credentials.Certificate(creds_path)
        else:
            # ADC fallback if running in GCP/GKE/Cloud Run with workload identity.
            cred_obj = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred_obj, {"projectId": project_id} if project_id else None)
        _firebase_ready = True
        _firebase_init_error = ""
        return True
    except Exception as exc:
        _firebase_ready = False
        _firebase_init_error = str(exc)
        log.exception("Firebase init failed")
        return False


def verify_id_token(id_token: str) -> dict[str, Any]:
    """Verify Firebase ID token and return decoded claims."""
    if not ensure_initialized():
        raise RuntimeError(f"Firebase is not initialized: {_firebase_init_error}")

    from firebase_admin import auth as fb_auth

    # check_revoked=False keeps this fast for per-request sign-in endpoint.
    decoded = fb_auth.verify_id_token(id_token, check_revoked=False)
    return decoded
