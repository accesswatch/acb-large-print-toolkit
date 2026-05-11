"""Symmetric encryption helpers for sensitive user data (API keys, etc.).

Design principles (privacy-first):
- Uses Fernet (AES-128-CBC + HMAC-SHA256) from the ``cryptography`` package.
- The encryption key is derived from Flask's SECRET_KEY via PBKDF2-HMAC-SHA256
  with a fixed per-application salt.  If SECRET_KEY is rotated, all encrypted
  values become undecryptable; users must re-enter their keys.  This is the
  correct trade-off: losing access to encrypted keys is far better than a
  key-rotation bypass that silently keeps old data readable.
- Plaintext API keys are NEVER logged, stored, or passed across the wire.
- Token format: URL-safe base64 (Fernet default) -- safe for DB TEXT columns.
- Graceful degradation: if ``cryptography`` is not installed, encryption/
  decryption raise ``RuntimeError`` so callers know the operation failed.
"""

from __future__ import annotations

import base64
import hashlib
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Fixed per-application KDF salt -- changing this rotates all user keys.
# Not a secret; its purpose is domain separation, not added entropy.
_KDF_SALT = b"glow-user-key-encryption-v1"
_KDF_ITERATIONS = 260_000  # OWASP 2024 PBKDF2-SHA256 recommendation


def _derive_fernet_key(secret_key: str) -> bytes:
    """Derive a 32-byte Fernet key from Flask's SECRET_KEY."""
    raw = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        raw,
        _KDF_SALT,
        iterations=_KDF_ITERATIONS,
        dklen=32,
    )
    return base64.urlsafe_b64encode(digest)


def _get_fernet():
    """Return a Fernet instance bound to the current Flask app's SECRET_KEY."""
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise RuntimeError(
            "cryptography package is required for API key encryption. "
            "Install it with: pip install cryptography"
        ) from exc
    from flask import current_app
    secret = current_app.config.get("SECRET_KEY", "")
    if not secret:
        raise RuntimeError("SECRET_KEY must be set before encrypting user data.")
    return Fernet(_derive_fernet_key(str(secret)))


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string.  Returns a URL-safe Fernet token string."""
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(token: str) -> str:
    """Decrypt a Fernet token.  Raises ``cryptography.fernet.InvalidToken``
    if the token is invalid, tampered with, or the key has changed."""
    fernet = _get_fernet()
    return fernet.decrypt(token.encode("ascii")).decode("utf-8")


def decrypt_safe(token: str, default: str = "") -> str:
    """Decrypt a Fernet token, returning *default* on any failure.

    Use this in read paths where a stale/invalid token should be treated as
    "no value" rather than an exception (e.g. after a SECRET_KEY rotation).
    """
    try:
        return decrypt(token)
    except Exception:
        return default


def is_encrypted(value: str) -> bool:
    """Return True if the string looks like a Fernet token (heuristic).

    Fernet tokens start with a version byte (0x80) encoded as gA in base64.
    """
    return bool(value) and value.startswith("gA")
