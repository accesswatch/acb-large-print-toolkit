"""Lightweight file-backed cache for shareable audit reports.

Shares expire after SHARE_TTL_SECONDS and are stored in a dedicated
subdirectory of UPLOAD_TEMP_BASE to isolate them from upload temp dirs.
The share token is a separate UUID unrelated to the upload token, so
sharing a report never exposes the uploaded document.
"""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path

from .upload import UPLOAD_TEMP_BASE

SHARE_TTL_SECONDS: int = 3600  # 1 hour

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_SHARE_BASE: Path = UPLOAD_TEMP_BASE / "shares"


def _share_dir(share_token: str) -> Path:
    return _SHARE_BASE / share_token


def save_report(share_token: str, html: str) -> None:
    """Save rendered report HTML to the share cache under the given token."""
    share_dir = _share_dir(share_token)
    share_dir.mkdir(parents=True, exist_ok=True)
    (share_dir / "report.html").write_text(html, encoding="utf-8")
    (share_dir / "expires.txt").write_text(
        str(time.time() + SHARE_TTL_SECONDS), encoding="utf-8"
    )


def load_report(share_token: str) -> str | None:
    """Load a cached report by token. Returns None if missing or expired."""
    if not _UUID_RE.match(share_token or ""):
        return None
    share_dir = _share_dir(share_token)
    expires_file = share_dir / "expires.txt"
    report_file = share_dir / "report.html"
    if not expires_file.exists() or not report_file.exists():
        return None
    try:
        expires_at = float(expires_file.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None
    if time.time() > expires_at:
        try:
            shutil.rmtree(share_dir, ignore_errors=True)
        except Exception:
            pass
        return None
    return report_file.read_text(encoding="utf-8")


def remaining_minutes(share_token: str) -> int:
    """Return minutes remaining until expiry, or 0 if expired/not found."""
    if not _UUID_RE.match(share_token or ""):
        return 0
    expires_file = _share_dir(share_token) / "expires.txt"
    if not expires_file.exists():
        return 0
    try:
        expires_at = float(expires_file.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return 0
    remaining = expires_at - time.time()
    return max(0, int(remaining // 60))
