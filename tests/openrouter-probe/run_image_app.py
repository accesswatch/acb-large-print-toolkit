from __future__ import annotations

import base64
import json

import requests

from openrouter_probe_common import CHAT_URL, PROBE_ROOT, request_headers, require_api_key, response_payload, write_json, write_text


def main() -> None:
    api_key = require_api_key()
    out_dir = PROBE_ROOT / "image"
    image_path = PROBE_ROOT / "vision_text.png"
    prompt_path = out_dir / "intent_prompt.txt"
    expected_path = out_dir / "expected_visible_text.txt"
    actual_path = out_dir / "latest_ocr_text.txt"
    response_path = out_dir / "latest_response.json"

    prompt = "Read all visible text from this image."
    write_text(prompt_path, prompt + "\n")

    b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 400,
        "temperature": 0,
    }
    resp = requests.post(
        CHAT_URL,
        headers=request_headers(api_key, "GLOW Image Probe", content_type_json=True),
        data=json.dumps(payload),
        timeout=60,
    )
    write_json(response_path, response_payload(resp))
    if not resp.ok:
        raise RuntimeError(f"Image probe failed: HTTP {resp.status_code}")

    actual = resp.json()["choices"][0]["message"]["content"].strip()
    write_text(actual_path, actual + "\n")

    print(f"Input image: {image_path}")
    print(f"Prompt: {prompt_path}")
    print(f"Expected: {expected_path}")
    print(f"Actual: {actual_path}")
    print(f"Raw response: {response_path}")


if __name__ == "__main__":
    main()
