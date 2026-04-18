# Changelog

All notable changes to the GLOW Accessibility Toolkit are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Releases are tagged in the [GitHub repository](https://github.com/accesswatch/acb-large-print-toolkit). Dates are in Pacific Time (UTC-7).

---

## [Unreleased]

### Added

- **Web E2E: Whisperer sample-audio regression flow.** Added Playwright coverage in `web/e2e/tests/regression.spec.mjs` for `/whisperer`: consent handling, sample audio upload, explicit estimate refresh, proceed confirmation, transcription start, transcript download assertion, and saved artifact verification. Supports `E2E_UPLOAD_AUDIO` override and defaults to `S:/code/bw/Samples/ronaldreaganchallengeraddressatt3232.mp3`.
- **Web: Whisperer estimate troubleshooting diagnostics.** Added optional client-side estimate diagnostics in `whisperer_form.html` (enable with `?whispererDebug=1`) with event tracing for file selection, key/click triggers, fetch status, payload handling, and fallback paths. Added structured server-side estimate diagnostics in `routes/whisperer.py` with `WHISPERER_ESTIMATE` log lines plus optional debug payload support (`?debug=1` or `X-Whisperer-Debug: 1`).

### Fixed

- **Web: Whisperer estimate endpoint URL resolution.** `whisperer_form.html` now uses explicit backend URLs (`data-estimate-url`, `data-start-url`) instead of deriving endpoints from `form.action`, preventing broken estimate/start requests caused by path/URL variations.
- **Web: Whisperer metadata duration scaling with PyAV.** `_estimate_audio_duration_seconds()` now normalizes time-base conversion across PyAV variants so `container.duration` is interpreted in seconds correctly, avoiding extreme/invalid duration values.
- **Web: Whisperer estimate button keyboard activation reliability.** `whisperer_form.html` now handles `keydown`, `keyup`, and legacy `keypress` activation paths for Space/Enter on the estimate button with duplicate-trigger protection, improving behavior for browser and assistive-technology combinations that do not emit consistent click events.
- **Web: Whisperer estimate button real-time feedback.** The Calculate estimate button now shows "Calculating..." and disables during the estimate request, with live progress messaging ("Button pressed. Checking for audio file...", "Contacting server...") so users and screen-reader users get clear status updates about what the button is doing. Added exhaustive keyboard event telemetry to the button: logs all keydown/keyup/keypress events plus focus/blur state to the diagnostics panel and browser console for troubleshooting keyboard activation issues.
- **Web: Whisperer server-side estimate fallback step.** Added a no-JavaScript server-first flow using "Next: calculate estimate on server" and `/whisperer/estimate-page`, with two-stage rendering: initial page shows upload+Next only; after estimate, the same page shows estimate-confirmation and remaining transcription steps.
- **Web: Whisperer client-side confirm-estimate checkbox validation.** The JS submit handler now validates the required acknowledgement checkbox before posting to the server, showing a focused, accessible inline message and moving focus to the checkbox so users never reach the server with that input missing.
- **Web: Whisperer stage-2 error re-renders stay in stage 2.** When `whisperer_submit` catches a validation or runtime error it now preserves `estimate_ready=True` (when an `existing_token` is present), keeping the user on the estimate+options page so they can correct their input without re-uploading.
- **Web: Whisperer catch-all exception handler on both submit routes.** Unexpected exceptions in `whisperer_submit` and `whisperer_start_job` are now caught, logged with full tracebacks, and returned as user-friendly messages (HTML form re-render and JSON respectively) instead of propagating to the generic 500 error page.
- **Web: Whisperer model-load failure now reports the real cause.** `whisper_convert()` now maps common engine startup failures to specific user-facing errors, including insufficient disk space while downloading/loading the Whisper model and general model-load failures, instead of collapsing everything into a generic transcription-engine message.
- **Web: Whisperer client-side oversized-file precheck.** The form now uses the server-configured maximum audio size to warn and block oversized files immediately after selection (before upload), disabling estimate/proceed controls until a valid file is chosen.

### Changed

- **Web: Whisperer duration probe now prefers Mutagen metadata.** `_estimate_audio_duration_seconds()` now uses `mutagen` as the primary duration source and falls back to PyAV for additional codec/container coverage. Added `mutagen>=1.47.0` to `web/pyproject.toml` and `web/requirements.txt`.

## [2.0.0] - 2026-04-17

### Added

- **Ops: Deep deployment logging.** `scripts/deploy-app.sh` now writes every phase of a deployment to a timestamped log file in `~/deploy-logs/` (always teed to stdout). Each step emits an ISO-8601 timestamp. The health-wait loop logs per-attempt container `state=` / `health=` / `last_log=` for all four services at every interval. On health check failure the script dumps the last 40-80 lines from each service log, runs `docker inspect` to show container error and restart state, and probes `/health` JSON to print the full service + readiness breakdown. Rollback attempts are logged the same way. A `deploy-latest.log` symlink always points to the most recent run.
- **Web: `/health` deep readiness checks.** The `/health` endpoint now returns a `readiness` object alongside `services`. `readiness.chat` reports whether the Llama 3 model is loaded in Ollama. `readiness.vision` reports whether LLaVA is available. `readiness.whisperer` reports whether faster-whisper is installed. The top-level `status` field is `"degraded"` if any service is down or any readiness check is `"not-ready"`. The `models.ollama` array lists all currently loaded model names.
- **Web: `/health` probe logs service + readiness summary at INFO.** Every `/health` call now emits a structured log line: `HEALTH status=... services=... readiness=... models=... duration_ms=...`. Health poll calls that return 200 in under 2 seconds are suppressed to avoid log noise; slow or failing calls always log.
- **Web: Flask startup ready log.** On worker startup the app emits `GLOW startup: web=X core=Y maintenance=Z log_level=W` so deployment logs confirm the correct package versions are loaded.
- **Web: Per-request logging middleware.** Every request logs `REQUEST METHOD /path -> STATUS (Xms) ua=...` at INFO after the response is sent. Silent for fast successful `/health` polls.
- **Admin: Live System Health panel on admin queue dashboard.** `admin_queue.html` now shows a "System Health" table that fetches `/health` JSON on load and refreshes every 20 seconds alongside the queue refresh. Rows show web / pipeline / Ollama service status plus chat (Llama 3), vision (LLaVA), and Whisperer readiness.
- **Docker: Service log labels and increased retention.** All four Compose services now include a `tag` label (`glow-web/{{.Name}}`, `glow-pipeline/{{.Name}}`, `glow-ollama/{{.Name}}`, `glow-caddy/{{.Name}}`) for `docker logs` filtering. Log caps raised: web 5 files x 20 MB; pipeline and Ollama 5 files x 10 MB; Caddy 3 files x 5 MB (was 2 files x 5-10 MB). Web healthcheck timeout raised to 10 s and retries to 5 to accommodate slower starts. `process_form.html`, `template_form.html`, `fix_review_headings.html`, `admin_login.html`, `chat_form.html`, `feedback_form.html`, `admin_request_access.html`, `consent.html`, and `whisperer_retrieve.html` now disable their submit button and display a polite `aria-live` status paragraph immediately on submit. Prevents double-submission and gives screen readers and sighted users clear progress feedback.
- **Web: Download processing state on fix_result.** The "Download Fixed Document" button in `fix_result.html` shows "Preparing your download…" and disables for 4 seconds on click, preventing double-submission on slow connections.
- **Web: Document Chat card on home page.** `index.html` now includes Document Chat in the card grid and "What Each Tab Does" section. Users no longer need to discover Chat only by accident.
- **Web: Format-specific CTAs in batch audit report.** `audit_batch_report.html` per-file sections now show actionable next steps for every supported format (xlsx/pptx manual-fix guide, md convert flow, pdf Acrobat note, epub source-fix hint). "What's Next?" section expanded.
- **Web: Whisperer step numbering with Jinja namespace counter.** Step labels in `whisperer_form.html` use a `namespace(step=1)` counter so numbers stay sequential when the email background-notification fieldset is hidden.
- **Web: Settings page noscript fallback.** `settings.html` includes a `<noscript>` notice informing users that Settings requires JavaScript.
- **Web: Admin queue auto-refresh.** `admin_queue.html` auto-reloads every 20 seconds when any row shows `queued` or `processing` status. Refresh stops when the tab is hidden. Polite `aria-live` announcement precedes each reload with a timestamped caption.
- **Web: Fix review headings -- session expiry recovery hint.** `fix_review_headings.html` shows the session expiry time and recovery instructions near the submit button.
- **Web: Chat Ask Question submit state.** The Ask Question button disables and announces "Asking the AI… This can take up to 30 seconds" via `aria-live` during AI inference.
- **Web: Chat export emoji aria-hidden.** Decorative emoji on Export and Clear Conversation buttons are wrapped in `<span aria-hidden="true">`.
- **Web: process_choose empty-state fallback.** When no actions are available for a file type, `process_choose.html` shows a descriptive notice listing supported formats.
- **Web: process_choose action icon aria-hidden.** Decorative emoji icons on action cards in `process_choose.html` are wrapped with `aria-hidden="true"`.
- **Web: Admin request confirmation dialogs.** Approve and Deny buttons in `admin_requests.html` include `onclick="return confirm(…)"` guards naming the target email to prevent accidental approvals or denials.
- **Web: Admin queue action confirmation dialogs.** Cancel and Re-Queue buttons in `admin_queue.html` include confirm dialogs to prevent accidental queue operations.
- **Web: Privacy page consent-clear confirmation dialog.** The "Clear My Consent Record" button in `privacy.html` requires user confirmation before posting.
- **Web: `aria-describedby` on whisperer retrieve password input.** The retrieval password field in `whisperer_retrieve.html` now references its hint paragraph via `aria-describedby`.
- **Web: `aria-describedby` on whisperer password-confirm input.** The confirm password field in `whisperer_form.html` now has its own hint paragraph and `aria-describedby`.
- **Web: `autocomplete="name"` on display_name in admin_request_access.** Assists password managers and autofill.
- **Web: Styled `:disabled` state for `btn-primary` and `btn-secondary`.** `forms.css` now explicitly styles `button:disabled` and `[aria-disabled="true"]` for both button classes, providing consistent visual feedback across browsers rather than relying on browser defaults.
- **Web: HTTP 403 error handler.** `app.py` now registers a `@errorhandler(403)` that renders the styled `error.html` template (matching 404/500 behavior) instead of Flask's default unstyled 403 page. Triggered by `abort(403)` in feedback review, admin access checks, and OAuth flows.

### Changed

- **Web: fix_review_headings Apply button** now has an `id` and processing-state JS to prevent accidental double-submission.

### Added

- **Web: Real-time BITS Whisperer progress reporting.** Whisper transcription now runs as a background job with dedicated status and download endpoints (`/whisperer/start`, `/whisperer/progress/<job_id>`, `/whisperer/download/<job_id>`). The Whisperer page shows true server-reported conversion percentage instead of only elapsed-time estimates, including live status announcements for screen reader users.
- **Web: Whisperer preflight estimate + proceed confirmation.** Before transcription starts, the Whisperer form now shows an estimated conversion time from uploaded audio metadata and requires explicit user confirmation to proceed.
- **Web: Whisperer graceful length/size limits.** Added configurable guardrails (`WHISPER_MAX_AUDIO_MB`, `WHISPER_MAX_AUDIO_MINUTES`) with clear user-facing guidance to split/compress oversized recordings instead of failing silently.
- **Web: Active Whisperer job retention hardening.** In-progress audio jobs now refresh their temp workspace timestamps so stale-upload cleanup does not remove files needed for long-running conversions.
- **Web: Whisperer background queue + secure retrieval lifecycle.** Any audio job (any length) can opt into background processing with queueing, queued/started/completed lifecycle notifications, single-use secure retrieval links, retrieval password verification, and a final content-cleared email when unretrieved results expire. The background option is always visible when email is configured -- not gated on recording length -- so users are never stranded on a busy-server 503 without a queue path.
- **Ops: Deploy script backup + rollback safety.** `scripts/deploy-app.sh` now creates a pre-deploy feedback backup (by default) and performs a health-check-gated rollback to the previous Git commit when the new revision fails to become healthy.
- **Admin: Authentication and approval hub.** Added admin-only login and approval routes (`/admin/login`, `/admin/request-access`, `/admin/queue`, `/admin/requests`) with email magic-link login, configured SSO providers (Google, Apple, GitHub, Microsoft, Auth0, WordPress), bootstrap admin seeding, and approval-required access control.
- **Admin: Audio queue operations UI.** Added admin dashboard controls to inspect audio conversion queue state, cancel queued jobs, and re-queue failed jobs.
- **BITS Whisperer: On-server audio transcription.** New `/whisperer` route and tab. Transcribes audio files (MP3, WAV, M4A, OGG, FLAC, AAC, Opus) to Markdown (.md) or Word (.docx) using faster-whisper with the Whisper medium model and CTranslate2 int8 quantization. Audio is processed entirely on the GLOW server and never sent to any external service (no OpenAI, no cloud API). Supports language selection (auto-detect or choose from 50+ languages). Includes concurrency gating to protect CPU resources and a 503 Busy page with Retry-After headers when the inference queue is full.
- **Web: Consent and agreement gate (`/consent`).** First-time visitors are shown a one-page agreement explaining how GLOW handles data, what AI features are available locally, privacy protections, and cookie policies before accessing any tool. Agreement is stored in a secure `glow_consent_v1` cookie (HttpOnly, Strict SameSite, 365-day expiry). The consent gate is skipped in test mode so existing tests don't require cookie fixtures. Users can withdraw consent and reset the gate via the Privacy Policy page.
- **Web: Quick Start beginner path (`/process`).** New universal upload form + contextual action chooser. Users upload any document type and are shown available actions (Audit, Fix, Convert, Export, Template, BITS Whisperer) based on the file type. Reduces barrier to entry for accessibility newcomers while keeping the expert tab interface for power users. Both paths coexist.
- **Web: MarkItDown 0.2+ integration with enhanced capabilities.** Upgraded from MarkItDown 0.1.5 to 0.2+. Added support for image files (JPG, JPEG, PNG, GIF, WebP, BMP, TIFF). New `convert_with_llm_descriptions()` function passes local Ollama/Llama3 instance as LLM client to generate alt text descriptions for images in PowerPoint files and standalone image uploads -- fully local, no third-party API. New `youtube_to_markdown()` function fetches YouTube video transcripts (using YouTube's own caption data) and converts them to Markdown.
- **Web: Image file audit support.** Image files (.jpg, .jpeg, .png, .gif, .webp, .bmp, .tiff) are now accepted by Audit. Extracted EXIF metadata and any embedded text are included in the audit report.
- **Web: `/health` capacity metrics.** The health check endpoint now exposes `capacity` object with `active_jobs` (AI and audio inference jobs in flight), `max_concurrent_jobs`, and feature availability flags (`whisper_available`, `ai_available`). Consumed by the 503 busy logic to determine when to queue or reject.
- **Web: `convert_form.html` callout card for BITS Whisperer.** Below the standard Convert form, a prominent info card directs audio users to BITS Whisperer with a link to `/whisperer`.
- **Web: BITS Whisperer tab in main navigation.** Added between Convert and Guidelines tabs in base.html navigation.
- **Web: Settings link in footer.** Users can now access the Settings page (preference defaults) from the footer navigation.
- **Web: Audio concurrency gating and semaphore.** New `gating.py` module implements audio and AI task concurrency limiting via semaphore. Prevents CPU overload during Whisper transcription. Configurable via `GLOW_MAX_AUDIO_JOBS` (default 1) and `GLOW_MAX_AI_JOBS` (default 1) environment variables. When at capacity, a 503 Busy page is returned with `Retry-After: 60` header.
- **Web: Privacy Policy consent withdrawal controls.** New section in Privacy Policy (`/privacy`) allows users to clear their consent cookie via a button that POSTs to `/consent/withdraw`. Also documents cookie policy and the opt-in nature of consent.
- **Desktop: Image and YouTube support in converter.** Desktop CLI and GUI inherit the new `convert_with_llm_descriptions()` and `youtube_to_markdown()` functions from the shared converter module.
- **Dockerfile: Updated for latest MarkItDown + dependencies.** `requirements.txt` now pins `markitdown[all]>=0.2.0` (audio, image, YouTube capabilities). `Dockerfile` installs required system libraries for image/PDF processing via the updated MarkItDown dependencies.
- **Web: Vision-ready OCR path.** New `vision_gate()` context manager in `gating.py` serializes LLaVA vision-model sessions for scanned PDF and image-heavy document extraction via a local Ollama instance. Configurable via `GLOW_MAX_VISION_SESSIONS` (default 1). When at capacity the 503 Busy response is returned with `Retry-After: 60`. Vision capacity is reported in `/health` alongside audio and AI slots.
- **Web: Expanded Document Chat (`/chat`).** New multi-turn conversational interface for uploaded documents. Llama 3 running on-server drives 24 tool calls across five agent categories (Document, Compliance, Structure, Content, Remediation). Conversation history is organized by turn. Export to Markdown, Word, or PDF is available at any point in the session. All processing is local -- no data leaves the GLOW server.
- **Web: Accessibility-focused agent categories in Document Chat.** Tool registry exposes five named agent groups: Document (extract tables, search text, list headings, stats, summaries), Compliance Agent (run_accessibility_audit, get_compliance_score, critical/auto-fixable findings), Structure Agent (check_heading_hierarchy, find_faux_headings, check_list_structure, estimate_reading_order), Content Agent (check_emphasis_patterns, check_link_text, check_reading_level, check_alignment_hints), Remediation Agent (explain_rule, suggest_fix, prioritize_findings, estimate_fix_impact, check_image_alt_text).
- **Web: Chat Guided Question Cards and example prompts.** The chat page includes a Guided Question Cards section and Example Questions section for first-time users, covering compliance, structure, content, and remediation use cases. Cards are keyboard and screen-reader accessible. Conversation privacy notice informs users that sessions are local and deleted after one hour of inactivity.

### Changed

- **Docs: Complete rewrite of `docs/user-guide.md`.** Restructured from 9 inconsistently numbered sections to 17 sections with a corrected TOC. Expanded Quick Start with eight real-world scenarios and a step-by-step upload flow. Fully written BITS Whisperer section (standard mode, background mode, limits table, audio tips, privacy statement). Fully written Document Chat section (all five agent categories, 24 tools, starter prompts, conversation tips, export and privacy guidance). Removed version numbers embedded throughout; standardised language. All tables use proper accessible headers.
- **Web: Upload accepted file list expanded.** `CONVERT_EXTENSIONS` in `upload.py` now includes image files (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.tiff`).
- **Web: `/audit` form supports batch file upload (up to 3 files in one go).** Radio toggle between Single File and Batch modes. Queue UI with remove-before-submit. Output options: Combined Report (one scorecard with per-file collapsible findings) or Individual Reports (stacked per-file full reports).
- **Web: `/audit` POST endpoint has per-IP rate limit.** 6 requests per minute per IP to prevent abuse of the email delivery path. Limit applies to all POST submissions, email or not.
- **Web: Email report delivery on Audit pages (optional, Postmark integration).** Checkbox to request audit scorecard and findings CSV attachment be sent to an email address immediately after the run. Requires `POSTMARK_SERVER_TOKEN` env var. Server-side validation and graceful error handling. Email address is never stored.

### Fixed

- Fixed CSRF token handling in consent form so first-visit users can agree without pre-existing session.
- **Ops: `wait_for_health` bash syntax error caused rollback health check to crash.** `log_ts` writes to stdout; capturing `ROLLBACK_HEALTHY="$(wait_for_health "rollback")"` included all log lines in the variable, causing `[[ "$ROLLBACK_HEALTHY" -eq 1 ]]` to fail with `syntax error: operand expected`. Fixed by redirecting all `log_ts` calls inside `wait_for_health` to stderr so command substitution captures only the final `0` or `1`.
- **Web: `faster-whisper` missing from Docker image.** `faster-whisper>=1.0.3` was listed in `web/requirements.txt` but not in `web/pyproject.toml` `dependencies`. The Dockerfile installs via `pip install ./web` (pyproject.toml) and never runs `pip install -r requirements.txt`, so `faster-whisper` was never present in the image. BITS Whisperer transcription and the `/health` `readiness.whisperer` check always reported `not-ready` as a result. Fixed by adding `faster-whisper>=1.0.3` to `web/pyproject.toml`.
- **Web: Document Chat accessible from Audit and Fix result pages.** After running Audit, the uploaded file was immediately deleted by the `finally` cleanup before the user could pivot to Chat. The audit route now preserves the temp file and passes a `chat_token` to the result template. A "Chat about this document" link appears in the What's Next section on both `audit_report.html` and `fix_result.html` when the token is available.
- **Docs: User guide incorrectly instructed users to click a "Chat" tab.** No Chat tab exists in the navigation; Chat is token-gated and requires an uploaded document. Updated `docs/user-guide.md` Section 8 with the correct two-path instructions: via Quick Start, or from Audit/Fix result pages.

### Added

- **Web: Privacy Policy page (`/privacy`).** New `privacy.html` template and `privacy_bp` blueprint at `/privacy`. Covers document storage and retention (per workflow), AI usage and data protections, data rights (no training, no third-party sharing), accounts/cookies, and security practices. Accessible from the footer navigation on every page.
- **Web: AI used / not used disclosure on every result page.** Audit Report, Fix Results, and Fix Review Headings pages now display a "Data and Privacy" notice section showing whether AI was or was not used during that specific transaction. When AI was used, the notice clarifies that only a local Ollama model on the GLOW server was involved and no data was sent to any third party. When AI was not used, the notice confirms rule-based analysis only.
- **Web: Document availability expiry on Fix result pages.** Fix Results and Fix Review Headings pages now display the exact UTC date and time when the held document will be automatically deleted (approximately one hour after upload). This gives users a clear deadline to download their fixed file.
- **Web: `get_upload_expiry()` helper in `upload.py`.** Returns the UTC `datetime` when a token's temp directory expires, computed from the directory's modification time plus the configured retention window. Used by the fix route to pass expiry time to templates.

### Fixed

- **Web: Expired session error message updated.** The 24-hour reference in the fix confirm expired-session error was corrected to 1 hour to match the actual retention window.

### Changed

- **Web: Upload retention reduced from 24 hours to 1 hour.** The `UPLOAD_MAX_AGE_HOURS` environment variable default in `app.py` and the `cleanup_stale_uploads()` function signature in `upload.py` now default to `1` hour instead of `24`. This matches the retention commitment described in the Privacy Policy and in Jeff Bishop's ACB-Conversation response to Ron Brooks.
- **Web: Privacy Policy link added to footer navigation** in `base.html`, alongside the existing Feedback link.

 The audit form now offers a radio toggle between Single File and Batch (up to 3 files) upload modes. In batch mode, users build a queue via a file picker, can remove individual files before submission, then choose between a Combined report (one scorecard summarising all files with per-file findings in collapsible sections) or Individual reports (full separate report per file on one page). Submitting more than 3 files is handled gracefully -- the first 3 are audited and a polite note explains the rest were skipped; no 400 errors.
- **Web: `audit_batch_report.html` template.** New batch report page with aggregate scorecard (average score, total findings, pass count, severity breakdown), a per-file summary table, and either collapsible per-file findings (`<details>`) or stacked individual report sections, depending on the selected report style.
- **Web: File queue UI with remove-before-submit.** In batch mode, a JavaScript queue shows each selected file's name and size with an accessible Remove button (`aria-label` per file). The live region (`aria-live="polite"`) announces additions, removals, and over-limit notices without disrupting screen readers. A `DataTransfer`-based submit hook populates the hidden file input from the queue so only queued files are sent.
- **CLI: `--jobs N` flag on `batch audit/fix`.** Runs file processing in parallel using `concurrent.futures.ThreadPoolExecutor`. `--jobs 0` auto-detects CPU count. Serial mode (`--jobs 1`, default) is unchanged.
- **CLI: aggregate summary for `batch audit`.** After processing, the CLI prints a summary block: files processed, passing/failing count, average score, total findings, and a per-severity breakdown. JSON format (`-f json`) appends a `batch_summary` object at the end.
- **CLI: `--summary-only` flag for `batch audit`.** Suppresses per-file report output; prints only the aggregate summary. Intended for CI dashboards and scripted checks.
- **CLI: `--min-grade GRADE` flag for `batch audit`.** Exits with code 2 if the average score across all files falls below the specified grade threshold (A=90, B=80, C=70, D=60). Enables org-wide quality gates in CI pipelines.
- **Web: `notice-box`, file queue, batch scorecard, and individual report CSS** added to `forms.css` -- semantic colour tokens, accessible focus styles on Remove buttons, collapsible `<details>` triangles via `::before`, and responsive `flex-wrap` scorecard layout.
- **Web: `btn-secondary` CSS class** added to `forms.css` for secondary action buttons (e.g. "Fix this document" links in batch reports).
- **Web: Email Report option on audit form.** A new "Email Report" fieldset (visible for both single and batch audits) lets users optionally enter an email address to receive the audit scorecard and a findings CSV attachment immediately after the run. The email address is used only to deliver the report and is never stored. The checkbox reveals the email input via JavaScript; client-side validation checks for a valid address before submission. The entire fieldset is hidden unless `POSTMARK_SERVER_TOKEN` is configured -- no UI surface until the feature is ready.
- **Web: `email.py` -- Postmark transactional email integration.** New module at `web/src/acb_large_print_web/email.py`. Provides `send_audit_report_email()` (single file) and `send_batch_audit_report_email()` (batch -- one combined email with a merged findings CSV). Follows Postmark Skills guidance: uses the `transactional` Message Stream, implements correct per-status-code error handling (200 success, 400/401 no-retry, 422 validation, 429 rate-limit, 5xx/timeout surface to user), and encodes findings as a UTF-8 BOM CSV attachment for Excel compatibility. Configurable via `POSTMARK_SERVER_TOKEN` and `POSTMARK_FROM_EMAIL` environment variables; silently disabled if token is not set.
- **Web: email status banner on audit report pages.** `audit_report.html` and `audit_batch_report.html` display a green success banner or a blue informational notice at the top of the report page reflecting the outcome of the email send. Audit results are always visible on-screen regardless of email outcome.
- **Web: `success-box` CSS class** added to `forms.css` -- green-tinted banner for confirmed email delivery (parallels the existing `notice-box` blue-tinted informational banner).
- **Web: `requests>=2.32.0`** added to `web/requirements.txt` for Postmark API HTTP calls.
- **Web: Postmark env vars documented in `docker-compose.yml` and `docker-compose.prod.yml`.** Commented-out `POSTMARK_SERVER_TOKEN` and `POSTMARK_FROM_EMAIL` lines added to both compose files for easy activation.
- **Web: Server-side email address validation** added to `audit.py`. Submitted `report_email` values are validated against a format regex and a 254-character length cap before any Postmark API call is made. Invalid addresses produce an inline error banner on the report page without aborting the audit.
- **Web: Per-IP rate limit (6 per minute) on audit POST.** The `/audit` POST endpoint is now decorated with a Flask-Limiter rule to prevent the email delivery path from being abused as a send-quota burner. The rate limit applies to all POST submissions regardless of whether email is requested. The audit result page is still served; the rate-limit error message is user-friendly.
- **Web: `test_email.py` -- 24 unit tests for `email.py`.** Covers `email_configured()`, `_findings_to_csv_bytes()` (BOM, header, truncation, column values), `_send()` (all Postmark response codes, timeout, network errors), `send_audit_report_email()` (unconfigured guard, payload structure, attachment format), and `send_batch_audit_report_email()` (unconfigured guard, merged CSV file column, failed-result exclusion).
- **Docs: `about.html` -- Postmark listed in open-source dependencies table.** Postmark row added alongside WeasyPrint with version, license (MIT client library), and privacy note.
- **Docs: `user-guide.md` -- Email delivery section added to "How to Audit a Document".** Documents the optional email field, what is sent (scorecard + CSV), and the privacy policy (address never stored).

### Fixed

- Fixed the macOS DMG packaging step in `.github/workflows/build.yml` by switching directory copy commands to recursive copy (`cp -R`), resolving the GitHub Actions failure in "Create DMG (macOS)" for onedir PyInstaller outputs.
- Fixed workflow tip banner icons rendering as literal text (`&#9758;`) in all web form pages (`audit_form.html`, `fix_form.html`, `convert_form.html`, `export_form.html`, `template_form.html`) and the `_workflow_tip.html` partial. Jinja2 auto-escaping was converting `&` to `&amp;` when HTML entity strings were stored in `{% set %}` variables and rendered via `{{ }}`. Replaced entity strings (`"&#9758;"`, `"&#9432;"`) with literal Unicode characters (`"☞"`, `"ℹ"`) which pass through auto-escaping unchanged. The `aria-hidden="true"` on the icon span remains correct and is why screen readers were not affected.

### Changed

- Removed remaining stale APH "not yet complete" language from web guide and guidelines templates, aligning all live-facing APH copy with Release 1.2.0 finalized submission wording.
- Added an embedded **APH execution workflow** section to the web User Guide (`web/src/acb_large_print_web/templates/guide.html`) including an "instructor in your pocket" checklist and week-based deliverables.
- Added an **APH Submission Profile** section to the Guidelines reference page (`web/src/acb_large_print_web/templates/guidelines.html`) with profile model notes and Week 1-4 release gates.
- Added a markdown execution playbook at `docs/aph-release-1.2.0-execution.md` documenting weekly tasks, outputs, and embedded-documentation coverage.
- Expanded `docs/user-guide.md` with a dedicated Release 1.2.0 APH section and synchronized heading structure so the APH process is embedded directly in project documentation.
- Added APH official source links (`https://www.aph.org/resources/large-print-guidelines/`) to web and markdown documentation surfaces, with status notes aligned to the Release 1.2.0 APH submission workflow.
- Added clear Standards Profile guidance across product surfaces (README, PRD, user guide, web guide, audit/fix UI, and announcements), explicitly documenting that **ACB 2025 Baseline** is backward-compatible with no behavior change, **APH Submission** supports Release 1.2.0 APH submission evidence workflows, and **Combined Strict** provides all implemented checks in one strict reporting view.
- Reworked `docs/announcement-web-app.md` to deeply integrate the April 14 launch narrative (problem framing, three-step workflow, heading-detection explanation, community feedback call, distribution-status note), and regenerated `docs/announcement-web-app.html` from markdown to keep web-facing announcement assets synchronized.
- Synchronized `docs/announcement.md` to the same integrated April 14 launch narrative used by the web announcement so profile messaging and release language are consistent across announcement artifacts.
- Expanded web Settings integration so saved defaults now cover standards profiles (Audit/Fix/Template), quick-rule suppressions, advanced fix options (list levels, paragraph indents, heading controls), template defaults, export mode, and convert defaults via `web/src/acb_large_print_web/static/preferences.js` and `web/src/acb_large_print_web/templates/settings.html`.
- Added homepage operation tiles for **Guidelines** and **Settings** plus a "What Each Tab Does" section in `web/src/acb_large_print_web/templates/index.html` to make tab purpose discoverable for first-time users.
- Expanded APH messaging in `docs/announcement-web-app.md` and `docs/announcement.md` with explicit "why now" rationale, real-world operator stories, and multi-standard workflow guidance (ACB continuity, APH evidence mode, Combined Strict final QA, plus Settings persistence).
- Further enriched APH launch messaging in announcement sources with story-first day-in-the-life scenarios, explicit bridge-positioning (ACB stability plus APH expansion), and stronger user-option framing for cross-standard documentation workflows.

- Added AFB scoping guidance to persistent product docs: Guidelines page now clarifies ACB/APH production usage and that AFB JVIB style is manuscript-oriented (not a fix/audit profile), and FAQ now includes AFB scope, large print vs large-print spelling, em-dash, and running-number conventions.

### Changed

- Standardized web page title bars to the format `Page Name | GLOW (Guided Layout & Output Workflow)` across the shared base template and tab-navigation title fallback (`web/src/acb_large_print_web/templates/base.html`, `web/src/acb_large_print_web/static/tabs.js`), and simplified page title blocks in feedback/home templates to page-name values only.
- Removed the embedded week-phased Release 1.2.0 APH execution section from the web landing page (`web/src/acb_large_print_web/templates/index.html`) now that this workflow is already integrated into the guide and guidelines documentation surfaces.
- Added an explicit APH guidelines subheading to the homepage guidelines section (`web/src/acb_large_print_web/templates/index.html`) directly after the ACB heading area to improve standards discoverability.
- Updated APH status and profile language across README, site templates, and documentation to reflect that APH submission alignment is fully integrated in Release 1.2.0; replaced "APH Submission (Current Coverage)" wording with "APH Submission" for consistency.

### Removed

- Removed `docs/prd-flask-web-app.md` from the repository; `docs/prd.md` remains the canonical PRD source.
- Removed `docs/ollama-heading-detection-findings.md` after confirming it was unreferenced and no longer required for current release documentation.
- Removed `docs/aph-release-1.2.0-execution.md` after consolidating the APH execution workflow into embedded documentation surfaces (web guide, markdown user guide, and site content) so teams no longer depend on a standalone execution playbook.
- Removed `BITS-FEEDBACK-PLAN.md` after integrating retained AFB scoping and terminology actions into `README.md`, `web/src/acb_large_print_web/templates/guidelines.html`, and `web/src/acb_large_print_web/templates/faq.html`.

## [1.1.0] -- 2026-04-15

### Fixed

- Fix results no longer penalize users for faux-heading findings when heading detection is explicitly disabled in the Fix form; `ACB-FAUX-HEADING` is suppressed from post-fix scoring and the results page now lists suppressed rules.
- Legacy Word VML shapes now treat explicit `alt=""` as decorative content, preventing false `ACB-MISSING-ALT-TEXT` findings when decorative intent is correctly marked.
- Fix form list indentation controls are now always visible for discoverability and are disabled/enabled in place based on the "Flush all lists" checkbox instead of being hidden.
- Fix workflow now adds a page-growth warning when pre-fix body text appears below the 18pt ACB minimum, helping explain expected pagination increases after remediation.
- User guide FAQ expanded with operational guidance for heading-rule suppression behavior, page-count growth, list indentation controls, and decorative-image handling.

- Feedback submission returned a 500 "Something Went Wrong" error in production because Flask's default `instance_path` resolved to a site-packages subdirectory (not writable by the container's non-root user) instead of the `/app/instance` Docker volume. Fixed by passing an explicit `instance_path` to the `Flask()` constructor — defaults to CWD-relative `instance/` (resolves to `/app/instance` in Docker) and is overridable via `FLASK_INSTANCE_PATH`. Also broadened exception handling in `feedback.py` to catch `OSError` in addition to `sqlite3.Error` so any future path/permission failures are logged rather than surfaced as 500 errors.
- Web changelog page now builds its version list dynamically from `CHANGELOG.md` headings, so release `1.0.0` and future releases appear automatically without hardcoded template updates.
- Front page standards text now consistently references WCAG 2.2 AA (removed mixed WCAG 2.1 wording).
- Word fix workflow now preserves user-confirmed heading conversions through the heading review step even when form round-trip text normalization alters whitespace or punctuation.
- Added regression test coverage for confirmed heading application by paragraph index after review.
- Added community-driven project and feedback messaging to the web announcement content, including explicit note that extensive testing is producing strong results.
- Fix Results page now shows explicit score delta and weighted remaining-penalty breakdown (Critical/High/Medium/Low counts) to explain low grades when unresolved high-severity findings remain.
- Added heading-review telemetry logging in the fix confirm workflow to report confirmed heading selections received vs heading fixes applied.
- Fix Results page now displays heading review counts directly in the UI (`selected` vs `applied`) when interactive heading confirmation is used.
- Updated documentation links from `lp.csedesigns.com` to `glow.bits-acb.org` across announcement, deployment, and user guide content.
- Updated `web/Caddyfile.example` to support both `lp.csedesigns.com` and `glow.bits-acb.org`; operational scripts keep `lp.csedesigns.com` as the canonical default domain.
- Added a tracked `web/Caddyfile` with dual-domain app host support (`lp.csedesigns.com`, `glow.bits-acb.org`) for direct production deployment with Docker Compose.
- Deployment scripts now support optional alias-domain verification via `APP_ALIAS_DOMAIN` while keeping `APP_DOMAIN` defaulted to `lp.csedesigns.com`.

### Added

- Added a **Product Requirements Document** page at `/prd/` in the web app, rendering `docs/prd.md` as accessible HTML with a table of contents (mirrors changelog rendering pattern); linked in the web app footer navigation.
- Added a **Documentation and References** section to the web app About page (`/about/`) linking to the PRD, Changelog, User Guide, and FAQ.
- Added a `docs/prd.md` product requirements document (renamed and consolidated from `docs/prd-flask-web-app.md`) covering architecture, user stories, feature decisions, and implementation status.
- Added a **Help menu** to the desktop GUI (`WizardFrame`) with four items: User Guide, Changelog, Product Requirements Document, and About; each documentation item renders the corresponding markdown file to a temporary ACB-compliant HTML page (Arial 18pt, 1.5 line-height) and opens it in the default browser.

- Added a Playwright E2E regression harness under `web/e2e/` covering home, audit, fix, export, convert, template, and key static pages.
- Added upload-aware E2E tests using `E2E_UPLOAD_DOCX` (default `d:/code/test.docx`) for document workflow regression coverage.
- Added issue report generation (`web/e2e/scripts/generate-issue-report.mjs`) to summarize failed Playwright tests into `e2e/artifacts/ISSUES.md` alongside HTML/JSON/JUnit artifacts.
- Added Node test runner scaffolding in `web/package.json` and artifact ignores in `web/.gitignore` for repeatable local and CI-friendly regression execution.
- Updated `docs/deployment.md` with dual-domain deployment instructions (`APP_DOMAIN` + `APP_ALIAS_DOMAIN`, no-redirect scenario) and post-deploy Playwright regression commands/artifact paths.
- **Quick Rule Exceptions** section added to Fix and Audit forms with per-operation toggles to suppress `ACB-LINK-TEXT`, `ACB-MISSING-ALT-TEXT`, and `ACB-FAUX-HEADING` findings without changing default settings; improves workflow friction for documents with known acceptable exceptions.
- **Preserve centered headings** option added to Fix form to skip alignment override for heading paragraphs, preserving intentional heading center-alignment for design-driven documents.
- **Per-level list indentation** support added to Fix form, auditor, and fixer to apply level-specific indent targets (Level 1, 2, 3) instead of uniform indents; auditor recognizes paragraph list styles and applies per-level expectations; fixer applies corresponding per-level target indents.
- **Dedicated FAQ page** added at web app `/faq/` with answers to quick exception usage, heading preservation intent, per-level list indentation configuration, and known limitations; linked in main navigation footer.

---

## [1.0.0] -- 2026-04-14

### Core Platform

- Established the 1.0 release baseline across desktop and web toolchains, with synchronized rule metadata and cross-format audit/fix workflows.
- Introduced structured fix tracking with category-level reporting to make remediation output actionable for reviewers and administrators.
- Expanded supported workflows across Word, Excel, PowerPoint, Markdown, PDF, and ePub in a single toolkit.

### Product Identity and Guided Experience

- Rebranded the platform to **GLOW Accessibility Toolkit** (Guided Layout & Output Workflow) across web UI, desktop messaging, help content, and release surfaces.
- Added a clearer product identity with guided, user-friendly "magical" language while preserving standards-first behavior and compliance rigor.
- Kept release versioning at **1.0.0** while modernizing product naming and onboarding copy.

### Heading Intelligence and Structural Repair

- Added end-to-end faux heading detection and conversion in Word documents using heuristic scoring, optional AI refinement via Ollama, and interactive confirmation flows in the web UI.
- Added `ACB-FAUX-HEADING` and heading normalization behavior to improve semantic structure and post-fix heading hierarchy quality.
- Enabled heading detection by default in the web Fix workflow and clarified guidance for pasted and unstructured Word documents.

### ACB Layout Enforcement and Formatting Controls

- Added configurable list and paragraph indentation enforcement with flush-left defaults aligned to ACB large print policy.
- Added corresponding CLI, desktop GUI, and web controls so teams can apply strict defaults while still supporting policy-based overrides.
- Expanded automatic handling of emphasis, alignment, line spacing, page setup, language, and document-title repair.

### Conversion and Publishing

- Expanded conversion support to include Word, EPUB 3, and PDF outputs via Pandoc and WeasyPrint, in addition to existing text/HTML and DAISY pipeline flows.
- Added print-optimized ACB CSS generation for PDF workflows and improved conversion guidance in web UI and docs.

### Web Experience and Transparency

- Added full fix-details reporting in the web Fix results page with grouped remediation records.
- Clarified remaining-issues messaging to distinguish truly manual items from configurable optional behaviors.
- Added release version visibility in the global footer and About page so deployed environments clearly expose current release state.
- Enhanced health endpoint reporting to include web, pipeline, and ollama service status in one response.

### Documentation and Testing Program

- Added large synthetic stress corpus coverage for heading detection and repair validation, with scenario-family transparency documented in user-facing pages.
- Expanded guide/about/help surfaces to explain rule behavior, conversion pathways, and remediation workflows.
- Consolidated project docs and release-facing references to better support operations, onboarding, and compliance reporting.

### Security

- Added `pip-audit` to deployment requirements for continuous Python dependency vulnerability scanning. Integrated into release and deployment workflows to detect known CVEs in transitive dependencies.
- Resolved CVE-2026-40192 (pillow) and CVE-2026-40260 (pypdf) by upgrading to fixed versions: pillow >=12.2.0, pypdf >=6.10.0. All dependencies now pass pip-audit security checks.
- Fixed session timeout handling in web app: increased default session timeout to 4 hours for long document processing workflows, added automatic garbage collection of stale upload directories (24hr TTL by default), and improved error messages when sessions expire. Configurable via SESSION_TIMEOUT_MINUTES and UPLOAD_MAX_AGE_HOURS environment variables.

### Removed

- Removed in-progress noise and interim bugfix tracking from the 1.0 release narrative in favor of feature-grouped release notes.


---

## [0.3.0] -- 2026-04-12

### ePub Accessibility Auditing

- Added `epub_auditor.py` with 15 EPUB Accessibility 1.1 rules:
  - **EPUB-TITLE** -- ePub must have a title in OPF metadata
  - **EPUB-LANGUAGE** -- ePub must declare a language
  - **EPUB-NAV-DOCUMENT** -- ePub must include a navigation document (nav or NCX)
  - **EPUB-HEADING-HIERARCHY** -- heading levels must not skip
  - **EPUB-MISSING-ALT-TEXT** -- images must have alt text
  - **EPUB-TABLE-HEADERS** -- tables must use th elements
  - **EPUB-ACCESSIBILITY-METADATA** -- ePub should include schema.org metadata
  - **EPUB-LINK-TEXT** -- links must have descriptive text
  - **EPUB-ACCESSIBILITY-HAZARD** -- ePub should declare hazard metadata
  - **EPUB-ACCESS-MODE-SUFFICIENT** -- ePub should declare sufficient access modes
  - **EPUB-PAGE-LIST** -- ePub should include a page list for navigation
  - **EPUB-PAGE-SOURCE** -- ePub with page list should declare a page source
  - **EPUB-MATHML-ALT** -- MathML elements should have alt text or annotation
  - **ACE-EPUB-CHECK** -- DAISY Ace ePub-level check results
  - **ACE-AXE-CHECK** -- DAISY Ace axe-core HTML check results

### DAISY Ace Integration

- Added `ace_runner.py` integrating the DAISY Ace EPUB accessibility checker
- Ace provides 100+ axe-core rules applied to EPUB content documents
- Results mapped to ACE-EPUB-CHECK and ACE-AXE-CHECK rule IDs
- Graceful degradation when Ace is not installed (skips Ace checks)
- Vendored DAISY Ace source in `vendor/daisy-ace/` for offline builds and auditing

### W3C Accessibility Metadata Display

- Added `epub_meta_display.py` implementing the [W3C Accessibility Metadata Display Guide 2.0](https://w3c.github.io/publ-a11y/a11y-meta-display-guide/2.0/draft/techniques/epub-metadata/)
- Extracts and renders human-readable accessibility statements from EPUB metadata
- Sections: Access, Sufficient Access Modes, Features, Hazards, Conformance, Summary
- Vendored DAISY a11y-meta-viewer reference implementation in `vendor/daisy-a11y-meta-viewer/`
- Audit report renders metadata sections with details/summary accordions

### Online Help System

- Added `/guide` route with 14-section user guide:
  - Quick-start walkthrough (audit, fix, re-audit in 3 steps)
  - Per-feature step-by-step instructions (audit, fix, template, export, convert)
  - Understanding results (severity levels, scores, grades)
  - Common issues and how to fix them
  - Tips by document format
  - Recommended workflows
  - DAISY accessibility tools overview
  - Keyboard and screen reader tips
  - Frequently asked questions
  - Getting help
- Added contextual help on every form via `<details>` accordions and `aria-describedby`
- Added `_help_links.html` partial for per-rule Learn More links (ACB, WebAIM, WCAG Understanding, Microsoft, DAISY)
- Added `_help_rules.html` partial for severity-grouped rule checkboxes with attached help links
- Added `_workflow_tip.html` partial for contextual next-step banners between pages
- `rules.py` maps every rule ID to curated help URLs plus auto-generated WCAG Understanding doc links
- `help_urls_map` injected globally via Flask context processor

### Directory Restructure

- Renamed `word-addon/` to `desktop/` (Python desktop app and CLI)
- Renamed `word-addin/` to `office-addin/` (Office.js Word add-in)
- Updated all cross-references: CI workflow, Dockerfile, `.dockerignore`, deploy scripts, README, `copilot-instructions.md`

### Upload Limit

- Raised `MAX_CONTENT_LENGTH` from 100 MB to 500 MB
- Updated all form templates, user guide, FAQ, README, deployment docs, and error messages

### Docker

- Dockerfile now installs Node.js and DAISY Ace globally (`npm install -g @daisy/ace`)
- Added `pymupdf>=1.24.0` to web requirements

### Tests

- Added desktop tests: `epub_auditor`, `epub_meta_display`, `ace_runner`, integration
- 74 web tests passing

---

## [0.2.3] -- 2026-04-12

### UI and Accessibility Polish

- Fixed guidelines Expand/Collapse All button not working (inline `onclick` blocked by CSP; moved to external `guidelines.js`)
- Added `script-src 'self'` to Caddyfile CSP; added one-time `update-csp.sh` migration script
- Fixed 11 UI and accessibility issues across web templates:
  - Fixed openpyxl link pointing to Mammoth URL on About page (copy-paste error)
  - Added back-to-top links to all 7 About page sections
  - Version numbers now pulled from package metadata instead of hardcoded
  - Added `.card-convert` accent border (purple) and format pill styles for MD, PDF
  - Guidelines JS: sync Expand/Collapse button text on manual details toggle; force-open all `<details>` on `beforeprint`, restore on `afterprint`
  - Feedback form: added `aria-describedby` linking help text to textarea; added `required` on rating and task radio groups; added "Error:" prefix to error box
  - Audit report: added "What's Next?" guidance for Markdown and PDF formats
  - Context processor injects `web_version` and `desktop_version` into all templates

### Convert Page Rewrite

- Replaced jargon (MarkItDown, Pandoc, RST, ODT) with plain-language descriptions
- Added "Which option should I choose?" expandable guide with use cases
- Step 1/Step 2 fieldset labels to guide users through the form
- Explained difference between Export and Convert pages
- Added privacy note (file deleted immediately after conversion)

---

## [0.2.2] -- 2026-04-12

### Pandoc HTML Conversion

- Added `pandoc_converter.py` for Markdown, reStructuredText, OpenDocument, RTF, and Word to ACB-compliant HTML conversion via Pandoc
- Added CLI `convert-html` subcommand with `--title`, `--css`, `--lang` options
- Added GUI checkbox for Pandoc HTML export in save step
- Web convert route: two-way conversion (to-Markdown or to-ACB-HTML)
- Convert form: radio group for direction, updated help text

### Docker Build Optimization

- Dockerfile now installs Pandoc for server-side HTML conversion
- Root `.dockerignore` massively reduces build context (excludes CLI, GUI, build files, installer, TypeScript add-in, docs, scripts)
- Upload validation: added `CONVERT_EXTENSIONS` superset with optional `allowed_extensions` parameter

### Form Improvements

- Audit and fix forms: wrapped custom rules in `<details>` (collapsed by default) to reduce form length
- 69 total tests passing (4 new Pandoc conversion tests)

---

## [0.2.1] -- 2026-04-12

### Markdown and PDF Auditing

- Added `md_auditor.py` with Markdown-specific rules: heading hierarchy, emphasis violations (italic, bold-as-emphasis), link text, alt text, emoji, em-dashes, tables
- Added `pdf_auditor.py` with PDF rules: metadata (title, language), tagged structure, font sizes, font families, scanned page detection, bookmarks (via PyMuPDF)
- Added `converter.py` wrapping Microsoft MarkItDown for document-to-Markdown conversion
- Web audit and fix routes dispatch to format-specific auditors for `.md` and `.pdf`

### Help URL Data Layer

- Added `rules.py` with per-rule help URLs: curated links to ACB spec, WebAIM, Microsoft Office docs, WCAG Understanding docs
- Auto-generates WCAG Understanding doc URLs from `acb_reference` strings
- Added `_help_links.html` partial for rendering help links in findings tables
- All audit and fix reports now show clickable "Learn More" per finding

### About Page

- New `/about` route with mission, organizations, standards, dependency attributions (core libraries, optional, infrastructure), and project info
- Base template navigation updated with About and Convert links

### Convert Route

- New `/convert` route with file download
- CLI `convert` subcommand and GUI Convert tab added

### Dependencies

- Added `markitdown[pdf,docx,xlsx,pptx]>=0.1.5` and `pymupdf>=1.25` to desktop
- Added `markitdown` and `pymupdf` to web requirements

### Tests

- 65 tests passing (28 new): about page, convert route, MD/PDF audit, help URLs, upload validation

---

## [0.2.0] -- 2026-04-12

### Multi-Format Support (Excel and PowerPoint)

- Added `xlsx_auditor.py` with 6 MSAC rules for Excel workbooks: sheet names, table headers, merged cells, alt text, color-only data, hyperlink text
- Added `pptx_auditor.py` with 6 MSAC rules for PowerPoint presentations: slide titles, reading order, alt text, font sizes, speaker notes, chart descriptions
- Added `DocFormat` enum to `constants.py` with `formats` field on every `AuditRule`
- Added 12 new MSAC rule IDs across both formats
- Web upload validation accepts `.docx`, `.xlsx`, `.pptx` with magic-byte checks
- Audit route dispatches to format-specific auditors
- Fix route returns audit guidance for Excel/PowerPoint (no auto-fix yet)
- Landing page shows format pills and per-format capability badges
- Format tags in rule lists indicate which formats each rule applies to
- CLI audit, fix, and batch commands accept all three Office formats
- GUI file picker includes all three formats; wizard skips HTML export for non-Word
- TypeScript `constants.ts` synced with new `DocFormat` enum and MSAC rule definitions

### Accessibility Improvements

- Flash messages use text prefixes (Error/Success/Warning/Note) not color alone
- All severity badges, format pills, and tags have visible text labels
- Nav link focus indicators (3px solid outline) on all interactive elements
- Contrast meets AA thresholds for all new UI elements

### Documentation

- PRD updated to v2.0 with multi-format status and implementation notes
- Deployment guide expanded to comprehensive production reference
- All READMEs updated for multi-format support

### Tests

- 40 tests passing (12 new multi-format tests)

---

## [0.1.5] -- 2026-04-11

### Production Deployment Infrastructure

- Added `docker-compose.prod.yml` with Caddy reverse proxy for auto-HTTPS
- Added `Caddyfile.example` configuring `csedesigns.com` (static) and `lp.csedesigns.com` (Flask proxy)
- Made wxPython optional via `[gui]` extra in pyproject.toml so Docker builds succeed without GTK/X11
- Added deployment shell scripts: `bootstrap-server.sh`, `deploy-app.sh`, `backup-feedback.sh`, `restore-feedback.sh`, `post-deploy-check.sh`
- Fixed: include `templates/` and `static/` in web package data
- Fixed: silence Gunicorn home directory and Flask-Limiter storage warnings
- Fixed: create writable `.gunicorn` directory for control socket

### Security Hardening

- Warn when `SECRET_KEY` is not set (random key won't survive restarts)
- Replaced deprecated `FLASK_ENV` with `FLASK_DEBUG` in docker-compose
- Added `Cache-Control: no-store` to feedback review endpoint
- Replaced `innerHTML` with DOM API in `taskpane.ts` (XSS prevention)
- Resolved 3 Dependabot vulnerabilities in word-addin:
  - Upgraded copy-webpack-plugin to ^14 (fixes serialize-javascript RCE + DoS)
  - Added npm overrides for `serialize-javascript >=7.0.5` and `tmp >=0.2.4`
  - GHSA-5c6j-r48x-rmvq (high), GHSA-qj8w-gfj5-8c6v (high), GHSA-52f5-9888-hmc6 (low)

---

## [0.1.4] -- 2026-04-11

### Server Documentation

- Added Phase 6: SSL/TLS configuration (verification, custom certs, troubleshooting, staging)
- Added Phase 8: SFTP file access (commands, GUI clients, chroot option)
- Added Phase 1 hardening: fail2ban for SSH brute-force protection, swap file for OOM prevention
- Added Docker json-file log rotation (10 MB x 3 files) to `docker-compose.yml`
- Added Caddy Content-Security-Policy and HSTS headers to all Caddyfile examples
- Added automated daily backup script with 30-day retention
- Added Docker image pinning guidance for reproducible builds
- Added `.prettierignore` to protect Jinja2 templates from formatter damage
- Fixed Caddyfile `reverse_proxy` references (`app` to `web`)
- Removed deploy-word-addin GitHub Actions workflow (replaced by Flask web app)

---

## [0.1.3] -- 2026-04-11

### Flask Web Application

- New `web/` directory with Flask 3.x web application
- Routes: `/` (landing), `/audit`, `/fix`, `/template`, `/export`, `/guidelines`, `/feedback`
- CSRF protection via Flask-WTF on all forms
- Rate limiting via Flask-Limiter (10/minute on upload endpoints)
- SQLite feedback storage with WAL mode and password-protected review
- Docker + Gunicorn deployment with non-root `app` user and `/health` endpoint
- Full WCAG 2.2 AA compliance: skip link, landmarks, `aria-current`, focus styles
- Path traversal protection on fix download (`secure_filename` + resolve check)
- Feedback input validation (rating allowlist, 5000-character message limit)
- Inline styles moved to CSS classes

### Word Add-in (Office.js)

- New `word-addin/` directory with Office.js TypeScript port
- Audit, fix, and template functionality as a Word ribbon integration
- `constants.ts` mirroring Python `constants.py` for cross-implementation sync
- `auditor.ts`, `fixer.ts`, `template.ts` implementing core logic
- Webpack build, manifest files for sideloading

### Documentation

- Added Flask web app PRD (`docs/prd-flask-web-app.md`)
- Added comprehensive deployment guide (`docs/deployment.md`)
- Updated `copilot-instructions.md` with cross-implementation sync table
- Created `web/README.md` with architecture and quick start
- 28 tests passing

---

## [0.1.2] -- 2026-04-09

### CLI Improvements

- Bumped version to 0.1.2 (was stuck at 0.1.0 across v0.1.0 and v0.1.1 tags)
- Added `--dry-run/-n` to fix command (shows what would change without modifying)
- Added `--dry-run/-n` to batch fix (shows per-file fixable vs manual counts)
- Added batch progress output: "Processing 1/5: file.docx"
- Added `completions` subcommand (bash, zsh, fish, powershell)
- Respect `NO_COLOR` environment variable ([no-color.org](https://no-color.org))
- Added `exitCode` field to JSON audit report output
- Added `--recursive/-r` to batch for subdirectory scanning
- Batch accepts directories as file arguments
- Sort batch files for deterministic output
- Wired `--quiet/-q` to suppress info messages (`logging.WARNING`)
- Wired `--verbose/-v` for debug output (`logging.DEBUG`)
- Fixed version: 1.0.0 to 0.1.0 to match pre-release tags

### CLI Short Flags

- Global: `-V` (version), `-q` (quiet), `-v` (verbose)
- audit: `-f` (format), `-o` (output)
- fix: `-o` (output), `-b` (bound)
- template: `-b` (bound), `-n` (no-sample), `-t` (title), `-i` (install)
- batch: `-f` (format), `-d` (output-dir), `-b` (bound)
- export: `-o` (output), `-c` (cms), `-t` (title)
- Documented exit codes: 0=success, 1=error, 2=non-compliant

---

## [0.1.1] -- 2026-04-09

### Build System

- Switched PyInstaller from `--onefile` to `--onedir` to eliminate `[PYI-32340:WARNING]` temp directory cleanup noise on Windows
- Build now produces `.zip` archives for portable distribution
- Inno Setup installer updated: GUI to `{app}`, CLI to `{app}\cli`
- CLI PATH registration points to `{app}\cli` for command-line use
- Fixed absolute imports in entry points for PyInstaller compatibility
- Removed `--clean` flag so second PyInstaller build does not delete first

### Packaging

- Separate CLI and GUI executables:
  - CLI: `acb-large-print-cli-{os}-{arch}` (console, no wxPython dependency)
  - GUI: `acb-large-print-{os}-{arch}` (windowed, includes wxPython)
- macOS builds packaged into `.dmg` disk image
- CI simplified to 2-platform matrix: Windows x64 + macOS ARM64

---

## [0.1.0] -- 2026-04-09

### Initial Release

The first public release of the GLOW Accessibility Toolkit.

#### VS Code Agent Toolkit

- Large Print Formatter agent with 9 operating modes:
  - **Audit** -- check open HTML/CSS file against ACB Large Print rules
  - **Generate** -- create new ACB-compliant HTML from scratch
  - **Convert** -- transform existing HTML to ACB compliance
  - **Template** -- generate Word document templates with ACB styles
  - **CSS Embed** -- inject ACB CSS into existing HTML documents
  - **Word Setup** -- generate PowerShell COM script to configure Word styles
  - **Markdown Audit** -- check Markdown files for ACB emphasis, heading, and list issues
  - **Markdown Fix** -- auto-fix Markdown files for ACB compliance
  - **Markdown-to-HTML** -- convert Markdown to ACB-compliant HTML with document shell and CSS
- Markdown Accessibility assistant agent (WCAG audit orchestrator)
- Markdown Scanner, Markdown Fixer, and Markdown CSV Reporter sub-agents
- Slash commands: `/acb-audit`, `/acb-convert`, `/acb-md-audit`, `/acb-md-convert`, `/acb-word-setup`
- Auto-attach instructions for HTML/CSS editing
- Pattern library, severity scoring, emoji maps, and fix templates

#### Reference Files

- `acb-large-print.css` -- drop-in CSS stylesheet (rem-based, WCAG 2.2 AA, `@media print` overrides for ACB 1.15 line-height)
- `acb-large-print-boilerplate.html` -- semantic HTML skeleton with headings, lists, TOC leader dots, table, figure with caption, and endnotes

#### Desktop Tool (Python)

- CLI with subcommands: `audit`, `fix`, `template`, `export`, `batch`
- GUI: accessible 7-step wxPython wizard
- Word document auditor enforcing ACB Large Print Guidelines:
  - Font family (Arial), body size (18pt), heading sizes (22pt/20pt)
  - No italic, bold restricted to headings, underline emphasis
  - Flush left alignment, line spacing, margins, widow/orphan control
  - No hyphenation, page numbers, heading hierarchy
  - Document title, document language (WCAG 2.4.2, 3.1.1)
  - Alt text, table headers, hyperlink text (Microsoft Accessibility Checker rules)
- Word document fixer: auto-corrects fonts, sizes, spacing, alignment, emphasis
- Word template builder: generates `.dotx` with all ACB styles pre-configured
- HTML exporter via Mammoth: standalone pages and CMS-embeddable fragments
- Cross-platform PyInstaller builds (Windows x64, macOS ARM64)
- Inno Setup installer for Windows distribution

#### CI/CD

- GitHub Actions workflow for automated builds on push/tag/PR
- Artifact upload for all platform executables
- Release automation on version tags

#### Documentation

- Comprehensive toolkit documentation (`docs/acb-large-print-toolkit.md`)
- Project announcement (`docs/announcement.md`)
- ACB Large Print Guidelines source document (`docs/`)
