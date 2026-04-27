from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import fitz
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "web" / "src"))

from acb_large_print_web.credentials import get_openrouter_api_key
from acb_large_print_web.ai_gateway import _transcribe_via_input_audio, _extract_openrouter_error


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://glow.bits-acb.org",
        "X-OpenRouter-Title": "GLOW OpenRouter Probe",
    }


def probe_chat(api_key: str) -> None:
    headers = {**_headers(api_key), "Content-Type": "application/json"}
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
    print("CHAT_STATUS", resp.status_code)
    if resp.ok:
        print("CHAT_REPLY", resp.json()["choices"][0]["message"]["content"])
    else:
        print("CHAT_ERROR", _extract_openrouter_error(resp))


def probe_image(api_key: str, image_path: Path) -> None:
    headers = {**_headers(api_key), "Content-Type": "application/json"}
    b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
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
    print("IMAGE_STATUS", resp.status_code)
    if resp.ok:
        print("IMAGE_REPLY", resp.json()["choices"][0]["message"]["content"][:1200])
    else:
        print("IMAGE_ERROR", _extract_openrouter_error(resp))


def probe_pdf_ocr(api_key: str, pdf_path: Path) -> None:
    headers = {**_headers(api_key), "Content-Type": "application/json"}
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=160)
    png_bytes = pix.tobytes("png")
    b64 = base64.b64encode(png_bytes).decode("ascii")

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
    print("PDF_OCR_STATUS", resp.status_code)
    if resp.ok:
        print("PDF_OCR_REPLY", resp.json()["choices"][0]["message"]["content"][:1200])
    else:
        print("PDF_OCR_ERROR", _extract_openrouter_error(resp))


def probe_audio_direct(api_key: str, audio_path: Path) -> None:
    headers = _headers(api_key)
    with audio_path.open("rb") as handle:
        resp = requests.post(
            "https://openrouter.ai/api/v1/audio/transcriptions",
            headers=headers,
            files={"file": (audio_path.name, handle, "audio/mpeg")},
            data={
                "model": "openai/whisper-large-v3",
                "response_format": "text",
                "language": "en",
            },
            timeout=300,
        )
    print("AUDIO_DIRECT_STATUS", resp.status_code)
    if resp.ok:
        print("AUDIO_DIRECT_REPLY", resp.text[:1200])
    else:
        print("AUDIO_DIRECT_ERROR", _extract_openrouter_error(resp))


def probe_audio_fallback(api_key: str, audio_path: Path) -> None:
    try:
        transcript = _transcribe_via_input_audio(
            audio_path=audio_path,
            api_key=api_key,
            language="en",
            session_hash="openrouter-probe",
        )
        print("AUDIO_FALLBACK_STATUS", 200)
        print("AUDIO_FALLBACK_REPLY", transcript[:1200])
    except requests.HTTPError as exc:
        resp = exc.response
        code = resp.status_code if resp is not None else "n/a"
        print("AUDIO_FALLBACK_STATUS", code)
        print("AUDIO_FALLBACK_ERROR", _extract_openrouter_error(resp))


def main() -> None:
    folder = Path(__file__).resolve().parent
    image_path = folder / "vision_text.png"
    pdf_path = folder / "vision_text.pdf"
    audio_path = folder / "reagan-30s.mp3"

    api_key = get_openrouter_api_key()
    if not api_key:
        raise RuntimeError("No OpenRouter key found via server.credentials")

    print("--- Chat ---")
    probe_chat(api_key)
    print("\n--- Image OCR ---")
    probe_image(api_key, image_path)
    print("\n--- PDF OCR (rendered first page image) ---")
    probe_pdf_ocr(api_key, pdf_path)
    print("\n--- Audio direct endpoint ---")
    probe_audio_direct(api_key, audio_path)
    print("\n--- Audio fallback (chat input_audio) ---")
    probe_audio_fallback(api_key, audio_path)


if __name__ == "__main__":
    main()
