# version.py

# This file provides a single source of truth for the GLOW version.
# All products should read from this file to stay in sync.

from pathlib import Path


def _resolve_version_file() -> Path:
    """Find the repository VERSION file from this module path."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "VERSION"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("VERSION file not found in parent directories")


def get_version() -> str:
    return _resolve_version_file().read_text(encoding="utf-8").strip()
