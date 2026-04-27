from __future__ import annotations

import json
from pathlib import Path

import requests

from openrouter_probe_common import CHAT_URL, PROBE_ROOT, request_headers, require_api_key, response_payload, write_json, write_text


def main() -> None:
    api_key = require_api_key()
    out_dir = PROBE_ROOT / "chat"
    prompt_path = out_dir / "intent_prompt.txt"
    expected_path = out_dir / "expected_reply.txt"
    actual_path = out_dir / "latest_reply.txt"
    response_path = out_dir / "latest_response.json"

    prompt = prompt_path.read_text(encoding="utf-8").strip()
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 20,
        "temperature": 0,
    }
    resp = requests.post(
        CHAT_URL,
        headers=request_headers(api_key, "GLOW Chat Probe", content_type_json=True),
        data=json.dumps(payload),
        timeout=60,
    )
    write_json(response_path, response_payload(resp))
    if not resp.ok:
        raise RuntimeError(f"Chat probe failed: HTTP {resp.status_code}")

    actual = resp.json()["choices"][0]["message"]["content"].strip()
    write_text(actual_path, actual + "\n")

    print(f"Prompt: {prompt_path}")
    print(f"Expected: {expected_path}")
    print(f"Actual: {actual_path}")
    print(f"Raw response: {response_path}")


if __name__ == "__main__":
    main()
