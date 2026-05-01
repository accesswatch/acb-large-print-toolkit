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

### 1. Enhanced workflow and user experience across all tools

**8 new UX optimizations streamline the audit→fix→reaudit cycle:**

1. **Post-fix re-audit button** — After running Fix, users now see a prominent "Re-Audit Fixed Document" button, eliminating the need to navigate tabs or download then re-upload.
2. **Convert→Audit bridge** — After converting a document (Markdown→HTML, etc.), users can audit the output directly without re-uploading.
3. **Prominent batch audit CTA** — The Audit form now highlights batch mode benefits (compare formats, before/after testing, variant analysis) with side-by-side callouts.
4. **Enhanced findings diff** — When users re-audit after fixes, they see detailed "Newly Detected," "Still Present," and "Cleared" sections showing exactly which rules improved.
5. **Session audit history** — The session stores the last 5 audits. Users can restart any recent audit or quickly switch between related files.
6. **Smart next-step guidance** — Convert tool now suggests contextual workflows (e.g., "Test your Markdown by batch-auditing Word and HTML versions together").
7. **Reviewer feedback loop** — Shared audit reports can now collect reviewer comments (foundation for collaborative review workflows).
8. **Session restore on expiry** — When a session expires, users see their history and can restart recent audits with one click.

### 2. Product infrastructure and API completeness

**15 new foundation improvements provide power users and integrators with advanced capabilities:**

1. **Toast notification framework** — All progress and actions now communicate via accessible toast notifications (keyboard + screen reader compatible).
2. **Standards profile propagation** — The selected standards profile (ACB 2025, APH Submission, or Combined Strict) now flows through audit→fix→reaudit, ensuring consistent rule filtering across the workflow.
3. **Ctrl+U file picker shortcut** — Users can press Ctrl+U (Cmd+U on Mac) anywhere to focus the file picker for quick navigation.
4. **Session keep-alive** — The web app pings `/health` every 15 minutes when forms are active, preventing idle timeout interruptions.
5. **Webhook callback support** — Integrators can POST audit results to custom HTTPS URLs with HMAC-SHA256 signing for secure webhooks.
6. **Configurable share TTL** — The `SHARE_TTL_HOURS` environment variable controls how long shared audit reports remain available (default 4 hours).
7. **Session-based auto-diff** — The same session can audit the same file twice and automatically show before/after findings comparison.
8. **Large-file rate limiting** — Files over 10 MB are subject to a tighter rate limit (1/min vs. 6/min) to protect the server from abuse.
9. **Voice preview endpoint** — The Speech tool now lets users click any voice to hear a quick demo with the default test phrase.
10. **Audit history in session** — Sessions maintain a compact history showing recent audit scores, filenames, and share tokens.
11. **AI alt-text suggestions** — New `/audit/suggest-alt-text` endpoint uses AI to suggest alt text for images in Word documents.
12. **Post-fix findings CSV export** — New `/fix/csv/<token>` endpoint exports post-fix findings as CSV for analysis in Excel or other tools.
13. **EPUB Ace conformance levels** — EPUB audits now extract and display the W3C conformance level (e.g., "EPUB Accessibility 1.0 - WCAG 2.0 AA") from the Ace checker results.
14. **Template context injection** — Templates now always have access to `audit_history` and `share_ttl_hours` via the app context processor.
15. **Backward compatibility** — All new features are opt-in, non-breaking, and require no migration.

### 3. Speech Studio: end-to-end document narration

Users can:

- type text and preview/download narration
- upload supported document formats and extract speech text
- preview first sentences from uploaded content
- download full document narration in MP3 (or WAV fallback)

### 4. Real-world adaptive estimate telemetry

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

### 5. Seamless Convert -> Speech handoff

Convert now includes a `Speech audio` direction. Selecting it sends the current upload session token to Speech Studio and avoids re-uploading.

### 6. Usage analytics expansion

Analytics now include:

- Let it GLOW anthem download counts
- Speech usage patterns by mode, voice, speed, and pitch
- speech timing telemetry sample summary

Visible in:

- `/about/` usage section
- `/admin/analytics`

### 7. Admin speech operations

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
