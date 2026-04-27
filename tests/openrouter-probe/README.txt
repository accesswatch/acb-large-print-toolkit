OpenRouter Probe Harness (root tests folder)

Purpose
- Reproduce and troubleshoot OpenRouter chat/vision/PDF-OCR/audio behavior with local artifacts.
- Use server.credentials automatically (no environment variable required).

Artifacts in this folder
- reagan-30s.mp3           30-second audio clip for transcription probes
- vision_text.png          image containing visible text
- vision_text.pdf          PDF built from the image for OCR probe

Review folders
- chat/                    prompt, expected reply, latest actual reply, raw JSON response
- image/                   prompt, expected OCR text, latest OCR text, raw JSON response
- pdf/                     prompt, expected OCR text, rendered page image, latest OCR text, raw JSON response
- audio/                   prompt/parameters, expected behavior notes, latest direct/fallback outputs

Python files
- generate_assets.py       creates/refreshes the clip/image/pdf artifacts
- probe_openrouter.py      one-shot probe runner (chat, image, pdf, audio direct, audio fallback)
- test_openrouter_live.py  pytest-style live tests (skip if no key)
- run_chat_app.py          standalone chat probe app
- run_image_app.py         standalone image OCR probe app
- run_pdf_app.py           standalone PDF OCR probe app
- run_audio_app.py         standalone audio probe app (direct + fallback)
- openrouter_probe_common.py shared helper utilities for the standalone apps

Run
1) Generate artifacts:
   python tests/openrouter-probe/generate_assets.py

2) Run one-shot probe:
   python tests/openrouter-probe/probe_openrouter.py

3) Run standalone apps individually:
   python tests/openrouter-probe/run_chat_app.py
   python tests/openrouter-probe/run_image_app.py
   python tests/openrouter-probe/run_pdf_app.py
   python tests/openrouter-probe/run_audio_app.py

4) Run pytest live tests:
   python -m pytest tests/openrouter-probe/test_openrouter_live.py -v -s

Notes
- This harness reads OPENROUTER_API_KEY from server.credentials via the app credentials helper.
- If audio direct fails with a 500 error, the direct OpenRouter audio endpoint is currently unstable in this environment.
- If audio fallback fails with a 402 error, OpenRouter account balance is too low for input_audio models.
- The intent of every probe is stored in a nearby intent_prompt.txt file, and the expected human-review target is stored in expected_*.txt or expected_behavior.txt.
- Running a standalone app overwrites only that app's latest_* output files, making before/after review easy.
