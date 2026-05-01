# v3.0.0 Release Summary: April 30, 2026

## Overview

GLOW Accessibility Toolkit v3.0.0 is the community-driven milestone release that unifies the major capabilities introduced through the 2.5, 2.6, 2.7, 2.8, and 2.9 development cycles into one production baseline.

This release delivers a complete Speech Studio platform, adaptive real-world timing telemetry, deeper analytics visibility, and seamless cross-workflow handoffs from Quick Start and Convert.

## Headline outcomes

- Full Speech Studio workflow (typed and uploaded document-to-speech)
- Convert tab now includes a direct Speech direction handoff
- Adaptive speech timing estimates based on real server telemetry
- Admin and About analytics now track anthem downloads and speech usage patterns
- One-click admin voice pack management for curated Piper voices
- Persisted speech defaults (voice, speed, pitch, text) integrated with Settings

## Major features in v3.0.0

### 1. Speech Studio: end-to-end document narration

Users can:

- type text and preview/download narration
- upload supported document formats and extract speech text
- preview first sentences from uploaded content
- download full document narration in MP3 (or WAV fallback)

### 2. Real-world adaptive estimate telemetry

Speech conversion timing is no longer only heuristic. GLOW now records real conversion telemetry on this deployment and blends historical throughput into future estimates.

Telemetry captured per conversion includes:

- word count
- character count
- source size bytes
- engine/voice/speed/pitch
- measured processing seconds
- generated audio seconds

Stored in:

- `instance/speech_metrics.db`

### 3. Seamless Convert -> Speech handoff

Convert now includes a `Speech audio` direction. Selecting it sends the current upload session token to Speech Studio and avoids re-uploading.

### 4. Usage analytics expansion

Analytics now include:

- Let it GLOW anthem download counts
- Speech usage patterns by mode, voice, speed, and pitch
- speech timing telemetry sample summary

Visible in:

- `/about/` usage section
- `/admin/analytics`

### 5. Admin speech operations

Admins can install/remove curated Piper voices from the admin dashboard without shell access.

## Files and docs updated for 3.0.0

- `CHANGELOG.md`
- `docs/prd.md`
- `docs/speech.md`
- `docs/user-guide.md`
- `docs/RELEASE-v3.0.0.md`
- `docs/announcement-v3.0.0-combined.md`
- `docs/announcement-v3.0.0-combined.html`

## Version alignment

Updated to `3.0.0`:

- `desktop/pyproject.toml`
- `desktop/src/acb_large_print/__init__.py`
- `office-addin/package.json`
- `web/pyproject.toml`
- `web/package.json`

## Notes

This release is intentionally framed as a community milestone. It tells the complete story for readers who did not follow each incremental release and presents the platform as a cohesive 3.0 baseline.
