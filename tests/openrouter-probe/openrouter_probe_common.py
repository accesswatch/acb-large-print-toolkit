from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "web" / "src"))

from acb_large_print_web.credentials import get_openrouter_api_key
from acb_large_print_web.ai_gateway import _extract_openrouter_error, _transcribe_via_input_audio


CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
AUDIO_URL = "https://openrouter.ai/api/v1/audio/transcriptions"


def require_api_key() -> str:
    key = get_openrouter_api_key()
    if not key:
        raise RuntimeError("No OpenRouter key found via server.credentials")
    return key


def request_headers(api_key: str, title: str, content_type_json: bool = False) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://glow.bits-acb.org",
        "X-OpenRouter-Title": title,
    }
    if content_type_json:
        headers["Content-Type"] = "application/json"
    return headers


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def response_payload(resp: requests.Response) -> dict[str, Any]:
    try:
        return resp.json()
    except Exception:
        return {
            "status_code": resp.status_code,
            "content_type": resp.headers.get("Content-Type"),
            "body": (resp.text or "")[:4000],
        }


__all__ = [
    "AUDIO_URL",
    "CHAT_URL",
    "PROBE_ROOT",
    "REPO_ROOT",
    "_extract_openrouter_error",
    "_transcribe_via_input_audio",
    "request_headers",
    "require_api_key",
    "response_payload",
    "write_json",
    "write_text",
]
