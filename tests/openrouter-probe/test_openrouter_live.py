from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import fitz
import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "web" / "src"))

from acb_large_print_web.credentials import get_openrouter_api_key
from acb_large_print_web.ai_gateway import _transcribe_via_input_audio


API_KEY = get_openrouter_api_key()

pytestmark = pytest.mark.skipif(
    not API_KEY,
    reason="No OpenRouter key found via server.credentials",
)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://glow.bits-acb.org",
        "X-OpenRouter-Title": "GLOW OpenRouter Live Tests",
    }


def _asset(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def test_chat_roundtrip() -> None:
    headers = {**_headers(), "Content-Type": "application/json"}
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": "Reply with exactly OPENROUTER_OK"}],
        "max_tokens": 20,
        "temperature": 0,
    }
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload),
        timeout=60,
    )
    assert resp.status_code == 200, resp.text[:600]
    content = resp.json()["choices"][0]["message"]["content"]
    assert "OPENROUTER_OK" in content


def test_image_ocr_roundtrip() -> None:
    headers = {**_headers(), "Content-Type": "application/json"}
    b64 = base64.b64encode(_asset("vision_text.png").read_bytes()).decode("ascii")
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Read all visible text from this image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 400,
        "temperature": 0,
    }
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload),
        timeout=60,
    )
    assert resp.status_code == 200, resp.text[:600]
    content = resp.json()["choices"][0]["message"]["content"]
    assert "VISION_TEXT_OK" in content


def test_pdf_ocr_roundtrip() -> None:
    headers = {**_headers(), "Content-Type": "application/json"}
    doc = fitz.open(_asset("vision_text.pdf"))
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=160)
    b64 = base64.b64encode(pix.tobytes("png")).decode("ascii")
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all readable text from this rendered PDF page image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 400,
        "temperature": 0,
    }
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload),
        timeout=60,
    )
    assert resp.status_code == 200, resp.text[:600]
    content = resp.json()["choices"][0]["message"]["content"]
    assert "VISION_TEXT_OK" in content


def test_audio_fallback_path() -> None:
    audio = _asset("reagan-30s.mp3")
    try:
        text, in_tokens, out_tokens = _transcribe_via_input_audio(
            audio_path=audio,
            api_key=API_KEY,
            language="en",
            session_hash="openrouter-live-test",
        )
        assert isinstance(text, str)
        assert isinstance(in_tokens, int)
        assert isinstance(out_tokens, int)
    except requests.HTTPError as exc:
        # A known live failure mode is 402 when account balance is below audio minimum.
        if exc.response is not None and exc.response.status_code == 402:
            pytest.skip("OpenRouter audio requires >= $0.50 balance for input_audio models")
        raise
