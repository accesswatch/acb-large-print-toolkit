import base64
import json
import sys
from pathlib import Path

import fitz
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "web" / "src"))
from acb_large_print_web.credentials import get_openrouter_api_key


def main() -> None:
    key = get_openrouter_api_key()
    if not key:
        raise RuntimeError("No OpenRouter key found via server.credentials")

    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://glow.bits-acb.org",
        "X-OpenRouter-Title": "GLOW Vision Audio Probe",
    }
    json_headers = {**headers, "Content-Type": "application/json"}

    base = Path(__file__).resolve().parent
    png = base / "vision_text.png"
    pdf = base / "vision_text.pdf"
    mp3 = base / "reagan-30s.mp3"

    png_b64 = base64.b64encode(png.read_bytes()).decode("ascii")
    image_payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Read the visible text in this image. Return the text you can see."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png_b64}"}},
                ],
            }
        ],
        "max_tokens": 300,
        "temperature": 0,
    }
    image_resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=json_headers,
        data=json.dumps(image_payload),
        timeout=60,
    )
    print("IMAGE_STATUS", image_resp.status_code)
    image_resp.raise_for_status()
    print("IMAGE_REPLY", image_resp.json()["choices"][0]["message"]["content"][:1200])

    doc = fitz.open(pdf)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=160)
    pdf_png = pix.tobytes("png")
    pdf_b64 = base64.b64encode(pdf_png).decode("ascii")
    pdf_payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "This is a rendered PDF page. Extract all readable text."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{pdf_b64}"}},
                ],
            }
        ],
        "max_tokens": 300,
        "temperature": 0,
    }
    pdf_resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=json_headers,
        data=json.dumps(pdf_payload),
        timeout=60,
    )
    print("PDF_STATUS", pdf_resp.status_code)
    pdf_resp.raise_for_status()
    print("PDF_REPLY", pdf_resp.json()["choices"][0]["message"]["content"][:1200])

    with mp3.open("rb") as handle:
        audio_resp = requests.post(
            "https://openrouter.ai/api/v1/audio/transcriptions",
            headers=headers,
            files={"file": (mp3.name, handle, "audio/mpeg")},
            data={
                "model": "openai/whisper-large-v3",
                "response_format": "text",
                "language": "en",
            },
            timeout=300,
        )
    print("AUDIO_STATUS", audio_resp.status_code)
    audio_resp.raise_for_status()
    print("AUDIO_REPLY", audio_resp.text[:1600])


if __name__ == "__main__":
    main()
