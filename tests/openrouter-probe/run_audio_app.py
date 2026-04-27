from __future__ import annotations

import requests

from openrouter_probe_common import (
    AUDIO_URL,
    PROBE_ROOT,
    _extract_openrouter_error,
    _transcribe_via_input_audio,
    request_headers,
    require_api_key,
    response_payload,
    write_json,
    write_text,
)


def main() -> None:
    api_key = require_api_key()
    out_dir = PROBE_ROOT / "audio"
    audio_path = PROBE_ROOT / "reagan-30s.mp3"
    prompt_path = out_dir / "intent_prompt.txt"
    behavior_path = out_dir / "expected_behavior.txt"
    direct_text_path = out_dir / "latest_direct_transcript.txt"
    direct_response_path = out_dir / "latest_direct_response.json"
    fallback_text_path = out_dir / "latest_fallback_transcript.txt"
    fallback_response_path = out_dir / "latest_fallback_response.json"

    write_text(
        prompt_path,
        "Direct endpoint parameters:\n"
        "- model: openai/whisper-large-v3\n"
        "- response_format: text\n"
        "- language: en\n\n"
        "Fallback prompt:\n"
        "Transcribe this audio to plain text. Language hint: en.\n",
    )

    with audio_path.open("rb") as handle:
        resp = requests.post(
            AUDIO_URL,
            headers=request_headers(api_key, "GLOW Audio Direct Probe"),
            files={"file": (audio_path.name, handle, "audio/mpeg")},
            data={
                "model": "openai/whisper-large-v3",
                "response_format": "text",
                "language": "en",
            },
            timeout=300,
        )
    write_json(direct_response_path, response_payload(resp))
    if resp.ok:
        write_text(direct_text_path, resp.text.strip() + "\n")
    else:
        write_text(direct_text_path, f"ERROR: {_extract_openrouter_error(resp)}\n")

    try:
        transcript, in_tokens, out_tokens = _transcribe_via_input_audio(
            audio_path=audio_path,
            api_key=api_key,
            language="en",
            session_hash="openrouter-audio-app",
        )
        write_text(fallback_text_path, transcript + "\n")
        write_json(
            fallback_response_path,
            {
                "status_code": 200,
                "content": transcript,
                "prompt_tokens": in_tokens,
                "completion_tokens": out_tokens,
            },
        )
    except requests.HTTPError as exc:
        write_json(fallback_response_path, response_payload(exc.response))
        write_text(
            fallback_text_path,
            f"ERROR: {_extract_openrouter_error(exc.response)}\n",
        )

    print(f"Input audio clip: {audio_path}")
    print(f"Prompt and parameters: {prompt_path}")
    print(f"Expected behavior: {behavior_path}")
    print(f"Direct transcript/error: {direct_text_path}")
    print(f"Direct raw response: {direct_response_path}")
    print(f"Fallback transcript/error: {fallback_text_path}")
    print(f"Fallback raw response: {fallback_response_path}")


if __name__ == "__main__":
    main()
