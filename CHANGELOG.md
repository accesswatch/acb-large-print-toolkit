# Changelog

All notable changes to the GLOW Accessibility Toolkit are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Releases are tagged in the [GitHub repository](https://github.com/accesswatch/acb-large-print-toolkit). Dates are in Pacific Time (UTC-7).

---

## [Unreleased]

---

## [3.1.0] - 2026-05-01

### Added

- **Roadmap feature pack implemented (11 items, all feature-gated).**
  Implemented the roadmap additions requested for 1.5, 2.5, 2.6, 3.3, 3.4,
  3.5, 3.6, 4.3, 7.3, 7.4, and 9.1 with explicit server-side flags:
  - 1.5 **Braille back-translation quality scoring** in Braille Studio result
    view (`GLOW_ENABLE_BRAILLE_BACK_TRANSLATION_SCORE`).
  - 2.5 **Speech pronunciation dictionary management** with CSV import/export,
    preview, and synthesis pre-processing (`GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY`).
  - 2.6 **Real-time streaming speech preview endpoint** at
    `POST /speech/stream` (`GLOW_ENABLE_SPEECH_STREAM`).
  - 3.3 **Table accessibility advisor API** at `POST /magic/table-advisor`
    (`GLOW_ENABLE_TABLE_ADVISOR`).
  - 3.4 **Reading order detection API** for PDFs at
    `POST /magic/reading-order` (`GLOW_ENABLE_READING_ORDER_DETECTION`).
  - 3.5 **OCR API for scanned PDFs** at `POST /magic/ocr` (best-effort when
    `pytesseract`/Pillow are available) (`GLOW_ENABLE_PDF_OCR`).
  - 3.6 **Document compare and change-tracking API** at `POST /magic/compare`
    (`GLOW_ENABLE_DOCUMENT_COMPARE`).
  - 4.3 **ODT export direction** in Convert (`to-odt`) backed by Pandoc
    (`GLOW_ENABLE_CONVERT_TO_ODT`).
  - 7.3 **Cognitive profile mode** (Plain & Simple) in Settings with local
    preference persistence and automatic help accordion expansion
    (`GLOW_ENABLE_COGNITIVE_PROFILE`).
  - 7.4 **Forced-colors/high-contrast mode support** in core CSS using system
    colors and forced-colors media-query rules (`GLOW_ENABLE_FORCED_COLORS_MODE`).
  - 9.1 **Public rule contribution portal** in Magic Lab (`/magic`) with
    proposal submission/list endpoints and Rules Reference cross-link
    (`GLOW_ENABLE_RULE_CONTRIBUTIONS`).

- **Comprehensive axe-core WCAG 2.2 AA audit of GLOW itself.**
  Added `web/e2e/tests/axe-audit.spec.mjs` — a Playwright-integrated
  `@axe-core/playwright` test suite that audits all 17 public routes at
  WCAG 2.2 AA level on every CI run. Pages audited include the 5 previously
  covered (home, audit, fix, convert, template) plus 12 new routes: Speech
  Studio, Braille Studio, Settings, Guidelines, User Guide, About, Changelog,
  FAQ, Rules Reference, Feedback, Privacy Policy, and Status. Additionally
  audits four interactive states: help accordions open, speech/braille
  unavailable banners, dark mode (`prefers-color-scheme: dark`), and mobile
  viewport (375 × 812 px). Critical and serious violations fail the CI build
  immediately with selector-level diagnostic output. Moderate and minor
  violations are surfaced as advisory warnings without blocking the build.
  Added `@axe-core/playwright ^4.11.2` to `web/package.json`. Added
  `test:axe` npm script that runs only the axe spec (separate from the
  functional regression suite). Expanded `@axe-core/cli` URL list in
  `accessibility-regression.yml` to match all 17 routes for the SARIF
  secondary scan. Axe results are written to `artifacts/axe-results.json` in
  the existing CLI format consumed by `axe_json_to_sarif.py`, so SARIF upload
  to GitHub Code Scanning is unchanged.

- **Server Status page (`/status`).** Added a human-readable diagnostics page
  that renders the same payload as `/health`, including service probes,
  readiness states, feature flag summary, full feature flag list, and raw
  JSON output for operators.

- **Braille navigation regression test.** Added
  `test_main_nav_shows_braille_tab_when_enabled` in `web/tests/test_braille.py`
  to ensure the Braille tab remains visible in top navigation when
  `GLOW_ENABLE_BRAILLE` is enabled.

- **Braille Studio** -- new `/braille/` tool for BANA-compliant text-to-braille and
  braille-to-text translation via [liblouis](https://liblouis.io/) (`louis` Python bindings).
  Supports all current BANA standards:
  - UEB Grade 1 and Grade 2 (Unified English Braille, BANA literary standard adopted 2016)
  - BANA Computer Braille Code (8-dot, `en-us-comp8.ctb`)
  - Legacy EBAE Grade 1 and Grade 2 (interoperability with pre-2016 materials)
  - Unicode Braille output (U+2800--U+28FF) and BRF ASCII output
  - BRF output is wrapped at the BANA-standard 40 cells per line (25 lines/page with
    optional paginated form-feed for embossers)
  - Graceful degradation when `louis` is not installed
  - Feature-gated via `GLOW_ENABLE_BRAILLE` (default: enabled)
  - Tab added to main navigation; download endpoint for `.brl`/`.brf`/`.txt` result files
  - 30 req/min rate limit on form and download endpoints

- **Speech Studio document preparation now uses Pandoc for uniform text rendering.**
  Uploaded documents (`.md`, `.rst`, `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.epub`, etc.) are
  converted to normalized plain text via Pandoc before synthesis. `.txt` files
  are read directly; all other formats require Pandoc to be installed on the server.
  This guarantees consistent narration quality across every supported format.
  The error message returned when Pandoc is absent now explicitly names the missing
  dependency so administrators can resolve it quickly.

- **CI workflows now install Pandoc explicitly.** `deploy.yml`, `feature-flags-ci.yml`,
  and `accessibility-regression.yml` all run `apt-get install pandoc` before the
  web test suite so the full Speech Studio document prepare path is exercised in CI.

### Fixed

- **`/status` is now reachable without consent redirect.** Added `/status`
  to consent-gate exemptions so operational diagnostics are publicly
  accessible like `/health`.

- **`/status` now safely serializes mocked diagnostic values.** Health payload
  construction now coerces non-string Braille `louis_version` values to text
  before rendering JSON, preventing test/runtime failures when mocks return
  non-JSON-native objects.

- **Workflow install conflict for desktop editable install.** Aligned
  `desktop/pyproject.toml` and `desktop/requirements.txt` to
  `mammoth>=1.11.0,<1.12.0` so dependency resolution is compatible with
  `markitdown[docx,pdf,pptx,xlsx]>=0.1.5` in CI and deploy workflows.

- **Health now reports Speech and Braille readiness explicitly.** `/health`
  now includes `services.speech`, `services.braille`, and corresponding
  `readiness.speech` / `readiness.braille` entries alongside feature flag
  data so operational issues are visible without guessing.

- **Braille tab visibility now has explicit local flag defaults.** Added
  `GLOW_ENABLE_BRAILLE: true` to `instance/feature_flags.json` and
  `web/instance/feature_flags.json` so local runs do not rely on implicit
  default resolution for the Braille top-nav tab.

- **Server deploy image now ships working liblouis Python bindings.**
  `web/Dockerfile` installs `liblouis-bin`, `liblouis-dev`, `liblouis-data`,
  and `python3-louis` (the official Debian bindings) via apt, then copies the
  `louis` module into the pip Python 3.13 site-packages so `import louis`
  resolves at runtime. A build-time smoke-test (`python3 -c "import louis"`)
  fails the Docker build immediately if the binding is absent. The `pylouis`
  stub PyPI package (which installed no importable code) has been removed from
  `web/pyproject.toml` and `web/requirements.txt`.

- **New feature flags for speech and braille export/conversion.**
  Added `GLOW_ENABLE_EXPORT_SPEECH`, `GLOW_ENABLE_CONVERT_TO_SPEECH`,
  `GLOW_ENABLE_EXPORT_BRAILLE`, and `GLOW_ENABLE_CONVERT_TO_BRAILLE` (all
  default: enabled). Flags are wired into route-level guards: synthesis and
  document-prepare endpoints check `CONVERT_TO_*`; download endpoints check
  `EXPORT_*`. All four flags appear in the admin feature flags UI under the
  Exports and Convert subfeatures groups.

- **Speech Studio staged actions are now robustly hidden until preparation completes.**
  The post-prepare action group (`Preview first sentences`, `Download full document audio`)
  now uses both semantic `hidden`/`aria-hidden` attributes and JS state toggling, so those
  controls do not appear on first load even if style state is inconsistent. Preparation errors
  now auto-scroll into view so a failed `Next: Prepare text and estimate` action is immediately
  visible. Changes in `web/src/acb_large_print_web/templates/speech.html`,
  `web/src/acb_large_print_web/static/speech.js`, and
  `web/tests/test_speech_routes.py`.

- **`/changelog/` no longer crashes with a Jinja `TemplateSyntaxError`.**
  `scripts/build-doc-pages.py` now wraps all auto-generated partials in
  `{% raw %}...{% endraw %}` so changelog and guide entries that document Jinja
  syntax (e.g. `{{.Name}}`, `{% if %}`, `{{ }}`) are treated as plain text instead
  of live template directives.

- **`post_findings.json` no longer appears in the project root.** The post-fix findings
  file is now always written inside the session temp directory (`get_temp_dir(token)`)
  instead of `saved_path.parent`, which resolved to the working directory on some
  hosts.

- **`POST /audit/` returned `405 METHOD NOT ALLOWED`** instead of `400` for empty
  submissions because the `@audit_bp.route('/', methods=['POST'])` decorator was
  accidentally dropped from `audit_submit_rate_limited`. Restored.

---

- **8 workflow optimization improvements (v3.1.0 staging):**
  1. **Post-fix re-audit button** — `fix_result.html` now shows "Re-Audit Fixed Document" action, eliminating download-then-manual-reaudit friction.
  2. **Convert→Audit bridge** — Convert results now offer direct "Audit this file" form submission to `audit.audit_from_convert()`, skipping re-upload.
  3. **Prominent batch audit CTA** — Audit form redesigned with side-by-side callouts highlighting benefits of batch mode (compare formats, before/after, test variants).
  4. **Enhanced findings diff** — Auto-diff now shows detailed sections for "Newly Detected," "Still Present," and "Cleared" findings with explanatory text.
  5. **Session audit history** — Session maintains compact history of last 5 audits with score, grade, filename, timestamp, and share token; shown in audit form for quick restart.
  6. **Smart audit workflow** — Convert tool now features contextual next-step guidance (e.g., "Test variant formats together → batch audit").
  7. **Feedback loop prototype** — Shared audit reports now support optional reviewer comment collection (foundation for future iterations).
  8. **Session restore on expiry** — Expired upload sessions now offer history-based recovery ("Continue from previous audit" with one click).

- **15 product infrastructure improvements (v3.0.1 staging):**
  1. Toast notifications framework with progress indicators (keyboard + voice-accessible).
  2. `standards_profile` (acb_2025|aph_submission|combined_strict) propagation through audit→fix→reaudit workflow for consistent rule filtering.
  3. Ctrl+U keyboard shortcut to focus file picker anywhere on the page.
  4. Session keep-alive: `/health` ping every 15 minutes when forms are active (prevents idle timeout).
  5. Webhook callback support: POST audit results to user-supplied HTTPS URL with HMAC-SHA256 `X-GLOW-Signature` header.
  6. Share TTL configurable via `SHARE_TTL_HOURS` env var (default 4 hours); `get_share_ttl_hours()` helper exposed to templates.
  7. Session-based auto-diff: compare current audit vs. previous in same session for progress tracking (cleared/persistent/new).
  8. Large-file upload rate limit: 1/min for files >10 MB (separate from standard 6/min limit) — prevents abuse of slow audits.
  9. Voice preview endpoint: `/speech/voice-preview` POST for quick demo with default text (20/min rate limit).
  10. Audit history in session: maintains up to 5 recent audits with scores and share tokens.
  11. AI-powered alt-text suggestions: `POST /audit/suggest-alt-text` with token + image_index (requires ai_alt_text_enabled).
  12. CSV export of post-fix findings: `POST /fix/csv/<token>` downloads findings CSV from post_findings.json.
  13. EPUB Ace conformance level exposure: extract W3C conformance declaration and expose via `AuditResult.ace_conformance`.
  14. Form-level context injection: `audit_history` and `share_ttl_hours` now in all template contexts via app.py context_processor.
  15. All improvements are independent, tested, and backwards-compatible.

### Changed

- **Speech Studio flow now guides users in stages.** The document action now starts with an explicit `Next: Prepare text and estimate` step, then reveals preview/download actions only after preparation succeeds. This makes the process clearer and avoids appearing like action buttons do nothing before the document is prepared. Changes in `web/src/acb_large_print_web/templates/speech.html` and `web/src/acb_large_print_web/static/speech.js`.

- **Convert-to-Speech copy now states text-rendering behavior.** Convert page guidance for `Speech audio` now explicitly explains that Speech Studio renders the document to plain text first, then shows estimate details and preview/download controls. Changes in `web/src/acb_large_print_web/templates/convert_form.html`.

### Fixed

- **Speech Studio preparation now enforces Pandoc-first text rendering for document narration.** Non-plain-text inputs are rendered through a Pandoc plain-text stage before narration checks and conversion, and the rendered intermediate text is persisted for diagnostics (`speech_rendered.txt`) alongside normalized source text (`speech_source.txt`). Changes in `web/src/acb_large_print_web/routes/speech.py`.

- **Announcement page cleanup.** Removed stray rendered `>` paragraphs in the announcement body content that appeared between quote blocks. Changes in `web/src/acb_large_print_web/templates/partials/announcement_body.html`.

### Added

- **Speech route regression tests.** Added `web/tests/test_speech_routes.py` covering Speech page rendering of the staged `Next: Prepare text and estimate` action, Pandoc-required behavior, text extraction paths, and prepare-document persistence of rendered and normalized text artifacts.

---

## [3.0.0] - 2026-04-30

### Added

- **Speech Studio platform completed.** `/speech/` now supports typed synthesis, uploaded document-to-speech conversion, snippet preview, and full narration download.
- **Curated multi-voice Piper seeding during build and deploy.** Docker build-time model prefetch and `scripts/deploy-app.sh` now seed a curated English Piper set (US + GB accents) instead of only one default voice.
- **Admin Speech Studio voice management.** Added an admin page with one-click Piper voice pack install/remove actions and live install status.
- **Convert-to-Speech handoff.** Convert tab now includes a `Speech audio` direction that redirects to Speech Studio with token handoff and no re-upload.
- **Anthem download analytics.** Home page now includes a Let it GLOW theme download action with usage tracking.
- **Speech usage pattern analytics.** Speech interactions now track mode, voice, speed, and pitch for analytics.
- **Speech conversion telemetry datastore.** New `instance/speech_metrics.db` records document conversion runtime by word count and source size.
- **Adaptive duration estimation.** Speech timing estimates now blend baseline heuristics with historical real conversion telemetry from the same server infrastructure.

### Changed

- **Speech Demo rebranded to Speech Studio.** Updated UI labels and explanatory copy to present production-ready speech workflows.
- **Speech settings persistence.** Global browser preferences (`glow_user_settings`) now persist voice, text, speed, and pitch and auto-apply in Speech Studio.
- **Speech first-class navigation.** Added dedicated Speech tab and Quick Start Speech action routing.

### Fixed

- **Speech preview feedback for slower synthesis.** Added stronger live in-progress status messaging for longer preview waits.

---

## [2.8.0] - 2026-04-30

> A heartfelt thank you to the BITS community and the broader blind and low-vision community whose feedback, feature requests, and real-world testing made this release possible. Every feature in 2.8.0 came directly from your suggestions. We are building GLOW for you and with you -- your voice is in every line of this release.

### Added

- **Quick Start handoff: audit, fix, and convert without re-uploading.** The Quick Start landing page now uploads a document once and routes the user to Audit, Fix, or Convert with the file already loaded -- no second upload is required. `GET /audit/?token=...` and `GET /convert/?token=...` resolve the token to the existing session directory and render their forms with a "Ready to audit/convert: &lt;filename&gt;" notice in place of the file picker. The corresponding POST handlers honour a `prefill=1` flag to re-use the cached file rather than calling `validate_upload`. Fix already routed through `fix.fix_from_audit_form`; the Quick Start dispatcher in `routes/process.py` now sends `fix` requests there too. Implemented in `routes/audit.py` (`audit_form`, `_audit_single`), `routes/convert.py` (`convert_form`, `convert_submit`), `routes/process.py` (`process_go`), and templates `audit_form.html` and `convert_form.html`. New tests in `tests/test_v270_new_routes.py::TestQuickStartHandoff`.


---

## [2.7.0] - 2026-04-29



### Added

- **GLOW Anthem:** Embedded the "Let it GLOW" cinematic ballad on the home page with an accessible audio player and integrated lyrics.

- **User-selectable dark mode (Light / Dark / Auto).** GLOW now offers an explicit theme choice instead of only following the operating system. The preference is stored in `localStorage` under `glow_theme` (values `light`, `dark`, `auto`; default `auto`). An inline boot script in `<head>` resolves the preference and writes `data-theme="dark"` or `data-theme="light"` on `<html>` before first paint, eliminating the flash-of-wrong-theme on reload. The CSS dark block was rewritten to key off `html[data-theme="dark"]` instead of `@media (prefers-color-scheme: dark)`, so `auto` mode now responds dynamically when the OS preference changes. New controls: a theme selector dropdown in the footer (always visible) and a radio group at the top of the Settings page; both stay in sync via the `data-theme-control` attribute. A `<meta name="color-scheme" content="light dark">` tag tells the browser to render native widgets (scrollbars, form controls) in the matching scheme. New file `static/theme.js`; changes in `static/forms.css`, `templates/base.html`, and `templates/settings.html`.

- **Centered page layout on wide viewports.** The body of every page is now horizontally centered with a wider max-width (`min(82rem, 100%)`) and responsive horizontal padding (`clamp(1rem, 3vw, 2.5rem)`) instead of being pinned flush left in a 70ch column. Long-prose paragraphs and lists that are direct children of `<main>` are still constrained to a 70ch reading measure, while cards, tables, and form layouts use the full width. Changes in `static/acb-large-print.css`.

- **Reliable focus indicators across all form controls.** All interactive elements (links, buttons, inputs, selects, textareas, checkboxes, radios, summary, `[tabindex]`) now render a 3px solid blue outline plus a layered white-and-blue halo (`box-shadow`) on `:focus-visible`. Native checkboxes and radios -- which previously lost their outlines on some browsers/themes -- now get an explicit ring with offset and a dashed outline on the wrapping `<label>` (via `:has()`) so the control text is also visually located. A `forced-colors` block defers to the system `Highlight` colour for Windows High Contrast users, and a dark-mode block swaps the white halo for a dark halo so the indicator stays visible against dark backgrounds. Changes in `static/forms.css`.

### Changed

- **Guidelines and Settings moved out of the main ribbon.** The top navigation now focuses on document tools (Quick Start, Template, Audit, Fix, Convert, Whisperer). Guidelines and Settings have moved into the footer "Additional links" navigation, which already housed User Guide, FAQ, About, PRD, Changelog, Feedback, Admin Sign-In, Privacy Policy, and Terms of Use. Both are also called out as cards on the Quick Start page so new users can find them. Changes in `templates/base.html` and `templates/process_form.html`.

- **Streamlined Audit → Fix (no re-upload).** Two new routes enable users to go from an audit report directly to Fix without re-uploading the document. `GET /fix/from-audit/<token>` renders the Fix form with the session file pre-loaded and a notice showing the filename; `POST /fix/from-audit/<token>` runs the full fix pipeline -- including the heading-review confirmation flow -- on the existing session file. The "Fix This Document" and "Fix These Auto-Fixable Issues" buttons on the audit report now route to these token-based URLs when a session is active; they fall back to the standard `/fix/` form otherwise. A new `_find_fixable_file(temp_dir)` helper resolves the first supported file in the temp directory. When an expired token is followed, the user is redirected to the standard fix form with `?notice=session_expired`. Changes in `routes/fix.py` and `templates/fix_form.html`.

- **Streamlined Fix → Re-Audit (no re-upload).** A new `POST /audit/from-fix` route re-audits the fixed file from an existing session without requiring a second upload. The route accepts `token` and `download_name` form fields, resolves the fixed file using `werkzeug.utils.secure_filename` with a path-traversal check and fallback to any `-fixed` file, runs the audit inline, generates a share token, and renders `audit_report.html` with full report context. The "Re-Audit Now" button on the fix result page has been replaced with a `<form>` POST to this route (guarded by `{% if feature_audit_enabled %}`), passing the session token and download name. Changes in `routes/audit.py` and `templates/fix_result.html`.

- **Privacy policy: audit session retention and share token wording.** The Data Storage and Retention Policy (`templates/privacy.html`) has been updated to accurately reflect the new session model: uploaded files are retained for up to 1 hour to enable the Fix shortcut and Chat follow-on actions; shareable report links contain only rendered HTML (never the original document) and expire after 1 hour. The "No permanent storage" section clarifies that the report cache holds rendered HTML only. Last updated date changed to April 29, 2026.

- **Privacy policy: analytics disclosure expanded.** The Data Storage and Retention Policy now explicitly documents operational analytics collection: aggregate visitor counter (unique browser sessions), per-tool usage counters (Audit, Fix, Convert, Template Builder, BITS Whisperer, Document Chat), and per-tool last-used timestamps. The page now also states where these metrics are stored (`instance/visitor_counter.db`, `instance/tool_usage.db`), what they are used for (internal reporting and capacity planning), and what they exclude (document content, extracted text, prompts, transcripts, and fixed output). Change in `web/src/acb_large_print_web/templates/privacy.html`.

- **Feature flag docs: `GLOW_ENABLE_EXPORT_HTML` description updated.** `docs/feature-flags.md` updated to document that this flag now gates the CMS Fragment direction in Convert (rather than a standalone Export route), and that the legacy `/export` redirect to Convert is unaffected by the flag.

- **Export folded into Convert.** The Export tab has been removed from the main navigation. Its CMS Fragment functionality is now a dedicated direction within the Convert page (`/convert/`). Users who visit `/export` (bookmarks, cached links) are permanently redirected (301) to `/convert`. The Quick Start "CMS Fragment" action for `.docx` files now routes directly to Convert. The CMS Fragment option in Convert is gated by the existing `GLOW_ENABLE_EXPORT_HTML` feature flag, calls the same `export_cms_fragment()` function, and produces an identical `-cms.html` download. Changes in `routes/convert.py`, `routes/export.py`, `routes/process.py`, `templates/base.html`, `templates/convert_form.html`, `templates/index.html`, and `templates/process_form.html`.

- **Convert: CMS Fragment direction.** Added a new `to-html-cms` direction to Convert that accepts Word (`.docx`) files and produces a scoped ACB-styled HTML snippet ready to paste into WordPress or Drupal without conflicting with the site theme. Visible in Step 2 only for `.docx` files. Changes in `routes/convert.py` and `templates/convert_form.html`.

- **Audit report: grade letter headline.** The compliance grade letter (A–F) is now displayed as a large typographic element at the top of the audit report, making the outcome immediately visible before reading the score or findings. The score (NN/100) and finding count appear beside the grade letter as supporting detail. Changes in `templates/audit_report.html` and `static/forms.css`.

- **After-action next-step cards.** The "What's Next?" section on both the audit report and fix result pages now displays a prominent action card (`.next-step-callout`) for the primary recommended workflow:
  - **Audit report:** a "Fix This Document" card with a "Audit Another" secondary button replaces the bare link for `.docx` files with findings and an enabled Fix feature.
  - **Fix result:** a "Re-Audit Now" card with a "Fix Another Document" secondary button immediately follows the What's Next heading, making the Audit → Fix → Re-Audit loop explicit and actionable.
  Changes in `templates/audit_report.html`, `templates/fix_result.html`, and `static/forms.css`.

- **Drag-and-drop file upload zones.** All file upload forms now include a visual drag-and-drop zone adjacent to the file input. Dragging a file onto the zone assigns it to the input, updates the hint text, and fires a `change` event so other scripts (such as the Convert extension filter) react correctly. The original `<input type="file">` remains accessible and unchanged for keyboard and screen-reader users. Implemented in a new `static/dropzone.js` module included from `templates/base.html`. Styles added to `static/forms.css`.

- **Navigation: Quick Start tab.** The Quick Start upload-and-discover flow (`/process/`) is now accessible from a permanent tab in the main navigation bar, appearing as the first tab on every page. Previously it was only reachable from a button on the home page. The tab is always shown regardless of feature flags. Changes in `templates/base.html`.

- **Navigation: Template tab moved before Audit.** The Template tab now appears immediately after Quick Start, before Audit and Fix, reflecting a start-of-workflow position for new document creation. Changes in `templates/base.html`.

- **Two-stage chained conversion for PowerPoint, Excel, PDF, and more.** The Convert page (`/convert/`) now accepts `.pptx`, `.xlsx`, `.xls`, `.pdf`, `.csv`, `.html`, `.htm`, `.json`, and `.xml` files as input for all Pandoc output directions (HTML, Word, EPUB, PDF). Files are first extracted to Markdown via MarkItDown, then Pandoc applies full ACB Large Print formatting. This is fully transparent -- users simply upload their file and choose the output format. Changes in `web/src/acb_large_print_web/routes/convert.py` and `templates/convert_form.html`.
  - Defined `_CHAIN_VIA_MARKDOWN` frozenset for the chained extension set.
  - Defined `_PANDOC_EFFECTIVE_EXTENSIONS` = `PANDOC_INPUT_EXTENSIONS | _CHAIN_VIA_MARKDOWN` used for validation and UI.
  - All four Pandoc directions (`to-html`, `to-docx`, `to-epub`, `to-pdf`) now perform a MarkItDown stage 1 when the extension is in `_CHAIN_VIA_MARKDOWN`, then pass the intermediate `.md` to Pandoc.

- **Convert page: Upload first (step reorder).** Step 1 is now "Upload your file" so the JavaScript can inspect the extension before the user picks an output format. The previous step order was: choose output → formatting → title → upload. The new order is: upload → choose output → formatting → title. Changes in `templates/convert_form.html`.

- **Convert page: JavaScript extension-aware output filtering.** After a file is selected in Step 1, JavaScript reads the file extension and enables only the conversion directions that support that file type. Unavailable options are disabled in place with a visual indicator. A live-region hint message names the available formats and notes when two-stage chaining applies. The extension sets are serialized from Flask template context variables (`pandoc_effective_exts`, `markitdown_exts`, `pipeline_exts`, `chain_via_markdown_exts`) and injected as `Set` objects so no server round-trip is needed. Changes in `templates/convert_form.html`.

- **Convert: Result page with inline preview.** HTML and CMS Fragment conversion now redirects to a dedicated result page (`templates/convert_result.html`) instead of immediately downloading the file. The result page shows a Download button, and for HTML output, an inline iframe preview of the converted document. New `GET /convert/download/<token>/<filename>` and `GET /convert/preview/<token>/<filename>` routes serve the file without exposing the temp directory path. Changes in `routes/convert.py` and new template `templates/convert_result.html`.

- **Convert: CMS Fragment clipboard copy.** The Convert result page for the CMS Fragment direction includes a read-only `<textarea>` showing the full HTML snippet and a "Copy to Clipboard" button. Changes in `templates/convert_result.html`, `static/forms.css`, and new `static/toast.js`.

- **Audit report: Quick wins filter.** A "Show Quick Wins Only" toggle button appears above the findings table when at least one finding is auto-fixable. Clicking it hides all non-auto-fixable rows and shows a count of auto-fixable findings. The toggle is ARIA-pressed compliant and includes a live-region status element. The set of auto-fixable rule IDs (`FIXABLE_RULE_IDS`) is defined in `routes/audit.py` and passed to the template as `fixable_rule_ids`. Changes in `routes/audit.py` and `templates/audit_report.html`.

- **Audit report: Shareable report URL.** After a successful audit, the rendered report HTML is cached server-side for 1 hour in a new `report_cache.py` module (`web/src/acb_large_print_web/report_cache.py`). A shareable URL (`GET /audit/share/<share_token>`) is displayed in a collapsible "Share this report" section at the bottom of the report. The share token is a separate UUID from the upload token — the original document is never accessible via the share link. Changes in `routes/audit.py`, new `report_cache.py`, and `templates/audit_report.html`.

- **Fix result: Grade letter on After score box.** The After score box on the fix result page now displays a large typographic grade letter (matching the audit report style), making the improvement immediately visible. Changes in `templates/fix_result.html` and `static/forms.css`.

- **Toast notification system.** A lightweight global toast notification module (`static/toast.js`) is included from `base.html`. It exposes `window.GLOW.toast(message, type)` for programmatic toasts and wires a global `click` handler for `[data-copy-target]` buttons that copies the target input's value to the clipboard and shows a "Copied!" toast. Changes in `templates/base.html`, new `static/toast.js`, and `static/forms.css`.

- **Dark mode CSS.** The dark theme rules in `static/forms.css` cover body, navigation, cards, buttons, tables, badges, score grades, footer, forms, file-input zones, dropzone, and details/summary elements. As of the v2.7.0 user-selectable toggle (above), they key off `html[data-theme="dark"]` rather than `@media (prefers-color-scheme: dark)`, so the user's explicit Light/Dark/Auto choice always wins and Auto mode still tracks the OS via `matchMedia`.

- **Print CSS improvements.** An additional `@media print` block in `static/forms.css` hides the quick wins bar, share section, toast container, CMS copy bar, and convert preview iframe when printing, and adds page-break rules for the findings table.

- **Responsive mobile layout improvements.** New responsive rules in `static/forms.css` adjust form layouts, navigation, action bars, and score boxes for narrow viewports.

- **Streamlined Convert → Audit handoff (no re-upload).** A new `POST /audit/from-convert` route audits the converted file from an existing Convert session without a second upload. The `convert_result.html` page now shows an "Audit This Document" call-to-action card for HTML, Word, and EPUB outputs (i.e. formats GLOW's auditors support), guarded by `feature_audit_enabled`. The route resolves the converted file using `secure_filename` with a path-traversal check, runs the audit inline, generates a share token, and renders `audit_report.html`. On expired or missing session the user is redirected to the standard upload form with a friendly notice. Changes in `routes/audit.py` and `templates/convert_result.html`.

- **Audit report: download as PDF.** A new `GET /audit/share/<share_token>/pdf` route renders the cached share-report HTML to PDF via WeasyPrint, caches the result in the share directory for the session lifetime, and serves it as `application/pdf`. The audit report's "Share this report" section now exposes a "Download PDF" button alongside the share URL. When WeasyPrint is not installed the route returns 503 and the button degrades gracefully. Changes in `routes/audit.py`, new helpers `report_cache.save_pdf()` / `load_pdf()`, and `templates/audit_report.html`.

- **Audit report: download findings as CSV.** A new `GET /audit/share/<share_token>/csv` route returns the audit findings as a UTF-8 BOM CSV with a header preamble (filename, format, score, grade, profile, mode) followed by the standard column row. The CSV is generated from cached findings JSON written alongside the report HTML at audit time. The "Share this report" section now exposes a "Download CSV" button that pairs with the existing email-CSV-attachment delivery. New module `web/src/acb_large_print_web/csv_export.py` extracted from the email path; new helpers `report_cache.save_findings_data()` / `load_findings_data()`. Changes in `routes/audit.py`, new `csv_export.py`, and `templates/audit_report.html`.

- **SQLite visitor counter.** A new `visitor_counter.py` module tracks unique browser sessions using a single-row SQLite counter (`instance/visitor_counter.db`, WAL mode). One increment fires per session via a `@app.before_request` hook; static assets and the `/health` endpoint are excluded. The current count is injected into every template as `visitor_count` via the `inject_rules()` context processor and displayed in the footer as "Visitors: 1,234". New file `web/src/acb_large_print_web/visitor_counter.py`; changes in `app.py` and `templates/base.html`.

- **Tool usage analytics.** A new `tool_usage.py` module maintains per-tool use counts in a SQLite database (`instance/tool_usage.db`, WAL mode). Each of the six public tool endpoints (Audit, Fix, Convert, Template Builder, BITS Whisperer, Document Chat) records a count increment as the first operation inside its submit handler; failures are swallowed silently so a DB error never surfaces to the user. Counts and a "last used" timestamp are exposed via `get_all()` and `get_total()`. New file `web/src/acb_large_print_web/tool_usage.py`; changes in `routes/audit.py`, `routes/fix.py`, `routes/convert.py`, `routes/template.py`, `routes/whisperer.py`, and `routes/chat.py`.

- **Admin analytics dashboard.** A new `GET /admin/analytics` route (admin-only) renders a summary of tool usage counts per tool (with share percentages and last-used timestamps) alongside the total visitor count. Accessible from a new "Tool usage analytics" link in the Admin Queue dashboard. New template `templates/admin_analytics.html`. Changes in `routes/admin.py` and `templates/admin_queue.html`.

- **About page: Usage Statistics section.** The About page (`/about/`) now includes a "Usage Statistics" section showing total visitor count, total tool uses, and a table of per-tool counts (rows with zero uses are hidden). The `about_page` route now imports and passes `tool_usage`, `total_uses`, and `visitor_count` to the template. Changes in `routes/about.py` and `templates/about.html`.

- **Re-audit: before/after diff banner.** When an audit is re-run via `POST /audit/from-fix`, the report now displays a diff banner above the score showing the score delta (e.g. "+12 points"), grade change, fixed/persistent/new finding counts, and the rule IDs that were fixed since the previous audit. Implemented via a new `_compute_audit_diff()` helper in `routes/audit.py` that consumes `prev_score` and `prev_rule_ids` form fields posted from the fix result page, and a new `audit_diff` block in `templates/audit_report.html`. The fix result form now propagates `prev_score` and a comma-joined list of rule IDs from the original audit.

- **Audit report: inline rule explanations.** Each rule ID in the findings table is now wrapped in a `<details>` disclosure that shows the canonical rule description, ACB reference, and "Why this matters" rationale pulled from `rule_reference_metadata.py`. The disclosure is keyboard-operable, opens in place without triggering a layout shift, and is hidden when printed. Auto-fixable rules show a "Auto-fixable" badge inside the disclosure. Changes in `templates/audit_report.html` and `static/forms.css`. A new `_rules_by_id()` helper in `routes/audit.py` builds the lookup table at request time.

- **Roadmap page.** Added `GET /roadmap` route and `templates/roadmap.html`, linked from the footer alongside Privacy and Changelog. The page lists shipped highlights, in-progress work, and longer-term ideas so contributors and adopters can see where GLOW is heading. Content lives entirely in the template -- no backend data layer.

- **Global keyboard focus indicators.** Added a global `:focus-visible` ring (3px solid `--color-primary` with 2px offset) in `static/forms.css` that applies to all focusable elements, paired with `:focus:not(:focus-visible) { outline: none }` so mouse clicks no longer leave a focus ring on buttons. Browsers without `:focus-visible` support fall back to the default browser ring. The ring also respects dark mode via the existing primary color variable.

- **Consent modal: scrollable body and improved focus management.** The "Cloud AI Consent" modal in the chat panel now wraps its long policy text in a scrollable `.consent-modal-scroll` region with a max-height of 60vh, ensuring the Decline/Accept buttons remain visible on small viewports. The modal also traps focus while open, restores focus to the trigger when closed, and respects the `prefers-reduced-motion` media query (skipping the fade-in animation). Changes in `templates/chat_panel.html` and `static/forms.css`.

- **Reduced motion support.** All custom animations (toast slide-in, dropzone hover transition, consent modal fade) now check `@media (prefers-reduced-motion: reduce)` and disable transition/animation when the user has requested reduced motion. Changes in `static/forms.css` and `static/toast.js`.

- **Tests: 22 new unit tests for v2.7.0 routes.** New `web/tests/test_v270_new_routes.py` exercises `report_cache.save_findings_data()` / `load_findings_data()` / `save_pdf()` / `load_pdf()` (roundtrip, bad token, missing share dir, TTL expiry), `csv_export.findings_to_csv_bytes()` (BOM, preamble, columns, empty-list, filename safety), the new share-report CSV and PDF routes (cached path, 404 on unknown token, 503 when WeasyPrint missing), and the `audit_from_convert` error paths (expired/missing token). Also includes a CSS guard test that fails if any shipped stylesheet introduces an `outline: none / 0 / transparent` rule outside the allowed `:focus:not(:focus-visible)` recipe, protecting the new global focus ring from future regressions.

### Fixed

- **Production deploy now forces Caddy to apply config changes and validates from a disposable container.** Updated `scripts/deploy-app.sh` to validate `web/Caddyfile` without depending on a running `caddy` container, then force-recreate the proxy so bind-mounted config changes actually reach production. Updated `scripts/post-deploy-check.sh` to verify that the live MP3 response includes `media-src 'self'` in the Content Security Policy so stale proxy config is caught during deployment instead of after release.

- **Web changelog page no longer crashes under Jinja parsing.** `web/src/acb_large_print_web/templates/partials/changelog_body.html` is now wrapped in a Jinja `{% raw %}...{% endraw %}` block so literal documentation examples like `{{.Name}}`, `{% if %}`, and `{{ }}` are treated as text instead of template syntax. This resolves `/changelog/` HTTP 500 errors and unblocks the Playwright static reference page regression test in Accessibility Regression Gate.

- **Home page accessibility test updated for renamed navigation section heading.** `web/tests/test_app.py` now asserts `Main Navigation Tab Order and Purpose` (replacing `What Each Tab Does`) and renames the test method to match the updated UI copy, resolving Deploy/Feature Flags CI failures caused by stale expectation text.

- **Streamlined flow: session context preserved on fix error.** When a fix attempt initiated from an audit report (`POST /fix/from-audit/<token>`) encounters an error, the fix form now re-renders with the original session token and filename intact. Previously the form re-rendered as a generic upload form, losing the user's context and requiring a fresh upload. Change in `routes/fix.py`.

- **Streamlined flow: prefill notice button label.** The notice shown when the Fix form pre-loads a session file incorrectly referred to the submit action as "Run Fix." The actual button label is "Fix Document." Label corrected in `templates/fix_form.html`.

- **Home page Settings card: Personalization chip is now clickable.** On the main page, the "Personalization" format tag in the Settings card now links to the Settings page route (`settings.settings_page`) instead of rendering as plain text. Change in `web/src/acb_large_print_web/templates/index.html`.

## [2.6.0] - 2026-04-28

### Added

- **Web Rules Reference deep-dive page.** Added a new `/rules/` route in `web/src/acb_large_print_web/routes/rules_ref.py` with a dedicated `rules_ref.html` template and `rule_reference_metadata.py` data module. The page provides a searchable, filterable browser for all audit rules with severity badges, profile membership, help links, extended rationale, suppression guidance, and deep-linkable rule anchors from the main web navigation.

- **Community inspiration and attribution: Jamal Mazrui's accessibility tooling leadership.** Added release-level attribution recognizing [Jamal Mazrui](https://github.com/jamalmazrui) and the influence of [extCheck](https://github.com/jamalmazrui/extCheck) and [xlHeaders](https://github.com/jamalmazrui/xlHeaders) on this release's expanded rule coverage and remediation tooling.

- **PowerPoint timing and motion safety checks.** Added four new PPTX rules in `desktop/src/acb_large_print/constants.py` and implemented detection in `desktop/src/acb_large_print/pptx_auditor.py`:
  - `PPTX-FAST-AUTO-ADVANCE`
  - `PPTX-REPEATING-ANIMATION`
  - `PPTX-RAPID-AUTO-ANIMATION`
  - `PPTX-FAST-TRANSITION`

- **Expanded Markdown accessibility quality checks.** Added 20 Markdown-focused rules and corresponding auditor logic in `desktop/src/acb_large_print/md_auditor.py`, including alt text quality checks, YAML/front-matter validation, heading and code-block quality checks, raw HTML checks, table consistency checks, fake-list checks, and ALL CAPS detection.

- **Deeper YAML front matter validation -- three new sub-rules.** `desktop/src/acb_large_print/md_auditor.py` and `constants.py` now enforce three additional YAML front matter checks applied whenever a front matter block is present:
  - `MD-YAML-UNCLOSED-FENCE` (High) -- opening `---` has no closing `---` fence; metadata cannot be parsed
  - `MD-YAML-MISSING-TITLE` (Medium) -- front matter block lacks a `title:` field (WCAG 2.4.2)
  - `MD-YAML-MISSING-LANG` (High) -- front matter block lacks a `lang:` or `language:` field (WCAG 3.1.1)
  The existing `MD-NO-YAML-FRONT-MATTER` check is suppressed when any deeper check fires (no redundant reports). `office-addin/src/constants.ts` and `web/src/acb_large_print_web/rules.py` are both updated with the new rules.

- **Web app help-text coverage for all 2.6.0 Markdown rules.** `web/src/acb_large_print_web/rules.py` was missing help links for all 16 Markdown rules added in this release. Added link entries (CommonMark spec, WebAIM, WCAG Understanding docs, ACB guidelines) for every new rule: `MD-ALT-TEXT-FILENAME`, `MD-ALT-TEXT-REDUNDANT-PREFIX`, `MD-ALT-TEXT-TOO-SHORT`, `MD-NO-YAML-FRONT-MATTER`, `MD-YAML-UNCLOSED-FENCE`, `MD-YAML-MISSING-TITLE`, `MD-YAML-MISSING-LANG`, `MD-EMPTY-HEADING`, `MD-HEADING-TOO-LONG`, `MD-HEADING-ENDS-PUNCTUATION`, `MD-CODE-BLOCK-NO-LANGUAGE`, `MD-INDENTED-CODE-BLOCK`, `MD-RAW-HTML-TABLE`, `MD-MOVING-CONTENT`, `MD-BLANK-TABLE-HEADER`, `MD-TABLE-COLUMN-MISMATCH`, `MD-FAKE-LIST-BULLET`, `MD-FAKE-NUMBERED-LIST`, `MD-ALLCAPS`.

- **Markdown parity sweep: 14 additional extCheck-aligned rules.** Added the remaining Markdown parity checks identified from extCheck into `desktop/src/acb_large_print/md_auditor.py` with synchronized rule metadata in `desktop/src/acb_large_print/constants.py`, `office-addin/src/constants.ts`, and help-link coverage in `web/src/acb_large_print_web/rules.py`: `MD-EMPTY-LINK-TEXT`, `MD-URL-AS-LINK-TEXT`, `MD-NO-HEADINGS`, `MD-DUPLICATE-HEADING-TEXT`, `MD-LONG-SECTION-WITHOUT-HEADING`, `MD-YAML-MISSING-AUTHOR`, `MD-YAML-MISSING-DESCRIPTION`, `MD-EXCESSIVE-BLANK-LINES`, `MD-EXCESSIVE-TRAILING-SPACES`, `MD-RAW-BR-TAG`, `MD-RAW-HTML-GENERIC-CONTAINER`, `MD-RAW-HTML-PRESENTATIONAL`, `MD-FAKE-INLINE-BULLET`, and `MD-ENTIRE-LINE-BOLDED`.

- **Excel layout and naming checks.** Added two new XLSX rules in `desktop/src/acb_large_print/constants.py` and implemented in `desktop/src/acb_large_print/xlsx_auditor.py`:
  - `XLSX-BLANK-ROWS-LAYOUT`
  - `XLSX-DEFAULT-TABLE-NAME`

- **New Excel fixer capability inspired by xlHeaders.** Added `desktop/src/acb_large_print/xlsx_fixer.py` with `add_excel_header_named_ranges()`, which creates xlHeaders-style named ranges (`ColumnTitleNN`, `RowTitleNN`, `Title01`) to improve screen reader header context in Excel workbooks.

- **Office add-in rule registry sync for 2.6.0 coverage.** Updated `office-addin/src/constants.ts` with the new PPTX and XLSX rules, plus Markdown rule identifiers and `DocFormat.MD` support to keep shared rule metadata aligned across implementations.

### Changed

- **Web Rules Reference accessibility polish.** `web/src/acb_large_print_web/templates/rules_ref.html` now exposes each rule as a navigable heading for screen-reader heading lists, moves keyboard focus to deep-linked rules when loading `#rule-*` anchors, and debounces search-driven live-region updates to reduce announcement noise.

- **Web settings and per-rule customization now use local storage instead of preference cookies.** `web/src/acb_large_print_web/static/preferences.js`, `web/src/acb_large_print_web/templates/settings.html`, `web/src/acb_large_print_web/templates/rules_ref.html`, `web/src/acb_large_print_web/templates/privacy.html`, and `web/src/acb_large_print_web/templates/consent.html` now explain and use browser local storage for saved workflow defaults, saved custom Audit/Fix rule sets, and Rules Reference filter state. The consent cookie (`glow_consent_v1`) remains separate and unchanged.

- **Rules Reference can now edit saved custom rule sets for Audit and Fix.** `web/src/acb_large_print_web/templates/rules_ref.html` and `web/src/acb_large_print_web/routes/rules_ref.py` now support target-aware rule-set editing with per-rule checkboxes, visible-only bulk actions, saved selection counts, and direct links from Settings into Audit or Fix custom-rule editing.

- **Excel default table-name findings now use a dedicated rule ID.** `desktop/src/acb_large_print/xlsx_auditor.py` now emits default Excel table-name findings under `XLSX-DEFAULT-TABLE-NAME` instead of reusing `XLSX-TABLE-HEADERS`, improving severity targeting and reporting clarity.

- **Website About page now includes 2.6.0 attribution details.** Updated `web/src/acb_large_print_web/templates/about.html` with a dedicated acknowledgment of Jamal Mazrui and explicit references to extCheck and xlHeaders as inspirations for this release.

## [2.5.0] - 2026-04-28

### Added

- **New feature flag: `GLOW_ENABLE_HEADING_DETECTION` (default `True`).** Added to `feature_flags.py` `_DEFAULTS` and injected as `feature_heading_detection_enabled` in the global template context via `app.py`. Controls visibility of heading detection settings in the Settings tab and can be used to gate the Fix route's heading detection controls in future.

- **Settings tab: feature-flag-gated settings.** `settings.html` now conditionally renders settings based on active feature flags. The "Enable heading detection" checkbox and its confidence threshold and accuracy mode controls are hidden when `GLOW_ENABLE_HEADING_DETECTION` is off. The "Enable AI refinement" checkbox remains hidden when `GLOW_ENABLE_AI_HEADING_FIX` is off (existing gate). Convert Defaults direction radios (`to-markdown`, `to-html`, `to-docx`, `to-epub`, `to-pdf`, `to-pipeline`) are each individually gated behind their corresponding `feature_convert_to_*_enabled` flags, matching the gating already applied in `convert_form.html`.

- **Settings tab: convert direction default selection now respects feature flags.** In `settings.html`, Convert Defaults now selects the first enabled direction radio using a Jinja namespace guard instead of hard-coding `to-markdown` as checked. This prevents blank or invalid defaults when `GLOW_ENABLE_CONVERT_TO_MARKDOWN` is disabled.

- **Desktop PDF audit: smarter image-based PDF detection with DPI quality check.** `desktop/src/acb_large_print/pdf_auditor.py` now uses image coverage area (requires ≥40% of page area) to avoid false positives from pages with small decorative images. The `PDF-NO-IMAGES-OF-TEXT` finding now classifies documents as entirely scanned, majority-scanned (≥50%), or partially scanned and includes page percentage and OCR remediation guidance (Adobe Acrobat, Tesseract, ABBYY FineReader). A new `PDF-IMAGE-RESOLUTION` check (`desktop/src/acb_large_print/constants.py`) flags scanned pages where image resolution is below 150 DPI — the minimum for acceptable OCR results — with per-page DPI values and a recommendation to re-scan at 300 DPI or higher.

- **Docs quality: Vale prose linting profile + CI workflow.** Added a low-noise prose quality gate for documentation with repository rules and vocabulary files (`.vale.ini`, `.vale/styles/Glow/*`, `.vale/config/vocabularies/Glow/*`) and a dedicated workflow (`.github/workflows/docs-quality.yml`) that lints `docs/**/*.md` and `README.md`. Initial rules focus on plain-language clarity, ambiguous link text, and long-sentence readability warnings.

- **EPUB auditing: optional EPUBCheck integration for authoritative package validation.** `desktop/src/acb_large_print/epub_auditor.py` now runs EPUBCheck (when available) and maps parsed `ERROR(...)` / `WARNING(...)` output into audit findings (`EPUBCHECK-ERROR`, `EPUBCHECK-WARNING`) with safe caps to keep reports readable. Validation is controlled via `GLOW_ENABLE_EPUBCHECK` (default enabled) and gracefully skips when EPUBCheck is unavailable.
- **CI: accessibility regression gate with Playwright + axe + SARIF.** Added `.github/workflows/accessibility-regression.yml` to run web Playwright regression tests and an axe-core WCAG 2.2 AA scan against key routes, then upload SARIF results for code scanning visibility.

- **Ops: WSL pre-production Docker staging helper.** Added `scripts/wsl-stage-regression.ps1` plus `web/docker-compose.wsl.yml` so GLOW can be staged in a WSL distro, health-checked, and regression-tested from the workstation before deploying to the main server. The WSL staging override defaults AI feature flags off to mirror the current non-AI rollout plan.

- **Web: Chat response quality improvements -- 7 new tools and grounding enhancements.** `web/src/acb_large_print_web/chat_handler.py` adds four new tools to the Document agent category: `get_document_summary` (plain-language document type, title, and section overview), `get_section_content` (full paragraph text of a named section, replacing the existence-only `find_section`), `get_decisions_and_actions` (extracts voted motions and action item owners from meeting/board documents), and `get_what_passes` (surfaces what the document already does correctly for balanced responses). `get_all_tools()` and the `call()` dispatcher are updated for all four. `routes/chat.py` now injects a document orientation block (summary + compliance score + what passes) on the first turn of every chat session so the model always opens with a grounded overview. The system prompt adds a confidence guard (rule 8) instructing the model not to report violations unless a pre-flight tool explicitly detected them, and a balance rule (rule 9) requiring acknowledgment of passing checks alongside violations.
- **Web: Table question dispatch now uses `extract_table` instead of `estimate_reading_order`.** Keywords "table", "column", "row", "data" in `dispatch_for_question()` now call `extract_table("0")` as the primary tool, falling back to `estimate_reading_order` only when no tables are found. Previously table questions were incorrectly routed to the reading-order tool.
- **Web: New `get_section_content` dispatcher route.** Questions matching patterns like "what does X say", "tell me about X", or "content of X" now trigger `get_section_content` in the keyword dispatcher, returning actual paragraph text rather than just confirming section existence.
- **Web: New `get_decisions_and_actions` and `get_what_passes` dispatcher routes.** Questions about votes, motions, approvals, and action items route to `get_decisions_and_actions`. Questions asking what passes, what's correct, or what's compliant route to `get_what_passes`.
- **Tests: Probe paths 24b–24f (Layer 2) for new document tools.** `tests/openrouter-probe/run_chat_paths_app.py` and `_write_probe.py` add unit-level coverage for `get_document_summary`, `get_section_content` (found/not-found), `get_decisions_and_actions`, and `get_what_passes` in Layer 2.
- **Tests: Probe paths 70b–70d (Layer 7) for new pipeline behaviors.** End-to-end pipeline paths added for document-summary questions, financial-section content retrieval, and board vote/decision extraction.

- **Docs: Cloud AI implementation plan consolidated into core documentation.** Merged the standalone cloud transition and implementation backlog content into `docs/prd.md` and `docs/deployment.md`, including the adopted OpenRouter production roadmap, provider-privacy strategy, environment wiring, and admin bootstrap guidance.
- **Web: Privacy-aware OpenRouter routing foundation.** `web/src/acb_large_print_web/ai_gateway.py` now supports comma-separated model fallback lists and sends OpenRouter provider preferences for privacy-sensitive routing (`dataCollection: deny`, `zdr: true`, fallbacks enabled, latency sort).
- **Web: Secure local admin bootstrap path.** Added `web/src/acb_large_print_web/credentials.py` for environment-first secret loading with optional local `server.credentials` fallback for development, plus password-based bootstrap admin login support in `web/src/acb_large_print_web/routes/admin.py` and `admin_login.html`.
- **Web: AI queue/backpressure controls for large workloads.** `web/src/acb_large_print_web/gating.py` now supports bounded queue waits and queued-capacity telemetry for AI, vision, and audio gates via `GLOW_AI_QUEUE_WAIT_SECONDS`, `GLOW_VISION_QUEUE_WAIT_SECONDS`, and `GLOW_AUDIO_QUEUE_WAIT_SECONDS`.
- **Web: OpenRouter transient retry/backoff controls.** `web/src/acb_large_print_web/ai_gateway.py` now retries transient OpenRouter failures (`429`, `5xx`) using configurable backoff (`OPENROUTER_MAX_RETRIES`, `OPENROUTER_RETRY_BASE_SECONDS`).
- **Web: Chat usage transparency improvements.** `web/src/acb_large_print_web/templates/chat_form.html` now surfaces per-session chat remaining count and queue behavior guidance for long/complex requests.

- **Web E2E: Whisperer sample-audio regression flow.** Added Playwright coverage in `web/e2e/tests/regression.spec.mjs` for `/whisperer`: consent handling, sample audio upload, explicit estimate refresh, proceed confirmation, transcription start, transcript download assertion, and saved artifact verification. Supports `E2E_UPLOAD_AUDIO` override and defaults to `S:/code/bw/Samples/ronaldreaganchallengeraddressatt3232.mp3`.
- **Web: Whisperer estimate troubleshooting diagnostics.** Added optional client-side estimate diagnostics in `whisperer_form.html` (enable with `?whispererDebug=1`) with event tracing for file selection, key/click triggers, fetch status, payload handling, and fallback paths. Added structured server-side estimate diagnostics in `routes/whisperer.py` with `WHISPERER_ESTIMATE` log lines plus optional debug payload support (`?debug=1` or `X-Whisperer-Debug: 1`).

### Changed

- **Deploy script: safe Docker cleanup controls added.** `scripts/deploy-app.sh` now supports orphan cleanup during deploy (`COMPOSE_REMOVE_ORPHANS=1` by default) and post-deploy artifact cleanup toggles. Successful deploys now optionally prune unused images (`CLEANUP_ON_SUCCESS=1`, `CLEANUP_IMAGE_PRUNE=1` by default). Optional builder cache cleanup is available via `CLEANUP_BUILDER_PRUNE=1` with `CLEANUP_BUILDER_KEEP_STORAGE` (default `4GB`). Rollback-path cleanup remains opt-in (`CLEANUP_ON_ROLLBACK=0` by default).

- **Office Add-in: dependency toolchain refreshed to latest available versions.** Updated `office-addin/package.json` and `office-addin/package-lock.json` to current releases for `typescript` (6.0.3), `webpack` (5.106.2), `webpack-cli` (7.0.2), `@types/office-js` (1.0.589), and `html-webpack-plugin` (5.6.7), plus transitive updates (`ts-loader`, `css-loader`, `webpack-dev-server`). Added `office-addin/src/global.d.ts` to declare `*.css` modules for TypeScript 6 side-effect CSS import compatibility so `npm run build` continues to compile successfully.

- **Web: Deployment branding profile support for BITS vs University of Arizona.** Added `web/src/acb_large_print_web/branding.py` and context injection in `web/src/acb_large_print_web/app.py` to support `GLOW_BRAND_PROFILE`. Default `bits` keeps current ACB/BITS wording. Setting `GLOW_BRAND_PROFILE=uarizona` now switches shared UI text in `templates/base.html` and `templates/index.html` to University of Arizona-friendly branding (removing ACB/BITS identity wording from title, nav/footer identity lines, homepage guideline copy, and Whisperer label).
- **Web: Branding is now operator-visible in Admin with deployment guidance.** `web/src/acb_large_print_web/templates/admin_flags.html` now shows a read-only active profile panel and instructions for switching `GLOW_BRAND_PROFILE` at deployment time.
- **Ops: Compose docs now include brand profile environment variable.** `web/docker-compose.prod.yml` and `web/docker-compose.wsl.yml` now document `GLOW_BRAND_PROFILE=${GLOW_BRAND_PROFILE:-bits}` for explicit profile selection.
- **Release posture: AI remains disabled by default in production and staging.** AI feature flags continue to default to off; core non-AI workflows (Audit, Fix, Export, Convert, Template, standards guidance, and profile-aware branding) remain fully functional.
- **Web: Guidelines reference page now supports UArizona branding profile language.** `web/src/acb_large_print_web/templates/guidelines.html` now conditionally removes ACB/BITS-branded wording when `GLOW_BRAND_PROFILE=uarizona` while preserving standards and rule details.
- **Web: Completed template context exposure for all non-AI feature flags.** `web/src/acb_large_print_web/app.py` now exposes `feature_word_setup_enabled`, `feature_markdown_audit_enabled`, `feature_pydocx_enabled`, `feature_openpyxl_enabled`, and `feature_python_pptx_enabled` in addition to existing feature booleans.
- **Web: Added dedicated HTML export feature flag.** `web/src/acb_large_print_web/feature_flags.py` introduces `GLOW_ENABLE_EXPORT_HTML` and `web/src/acb_large_print_web/routes/export.py` now gates `/export` at route level (GET/POST), while templates and Quick Start entry points hide Export when disabled.
- **Web: Added per-direction convert feature flags and route enforcement.** `GLOW_ENABLE_CONVERT_TO_MARKDOWN`, `GLOW_ENABLE_CONVERT_TO_HTML`, `GLOW_ENABLE_CONVERT_TO_DOCX`, `GLOW_ENABLE_CONVERT_TO_EPUB`, `GLOW_ENABLE_CONVERT_TO_PDF`, and `GLOW_ENABLE_CONVERT_TO_PIPELINE` now drive both UI visibility in `templates/convert_form.html` and backend direction guards in `web/src/acb_large_print_web/routes/convert.py`. Admin management now includes a dedicated Convert directions section in `templates/admin_flags.html` / `routes/admin.py`.

- **Web: AI features can now be deployment-gated independently from the OpenRouter key.** `web/src/acb_large_print_web/ai_features.py` now supports a master `GLOW_ENABLE_AI` switch plus per-feature gates for chat, Whisperer, AI heading refinement, alt-text helpers, and MarkItDown LLM behavior. This allows the non-AI web fixes to be deployed immediately while specific AI paths remain hidden and route-disabled until validation is complete.

- **Web: Default AI model switched from free Llama/Mistral pool to GPT-4o-mini.** `_DEFAULT_MODEL` in `web/src/acb_large_print_web/ai_gateway.py` now defaults to `openai/gpt-4o-mini` (primary) and `openai/gpt-4o` (fallback/escalation), replacing the previously unavailable `meta-llama/llama-3-8b-instruct:free,mistralai/mistral-7b-instruct:free` free-model pool. The legacy free model entries are retained in the cost table for accounts that override via `AI_DEFAULT_MODEL`. Admin reset-to-defaults and the admin AI settings dropdown updated to match. Probe path 01 and integration test fixtures updated to the new primary model. All 84/84 probe paths now pass.

### Fixed

- **Post-deploy verification no longer hangs/fails on removed Ollama service.** `scripts/post-deploy-check.sh` now gates required service checks dynamically from Compose service definitions and skips `ollama` when it is not present in `docker-compose.prod.yml`. Readiness parsing now treats `not-configured` as OK for feature-gated AI checks, preventing false deployment failures when AI/Ollama are intentionally disabled.

- **CI deploy gate: fixed false failure in Fix route form-option test under AI-off defaults.** `web/tests/test_fix_routes.py` now mocks `acb_large_print_web.ai_features.ai_heading_fix_enabled()` directly in `TestParseFormOptions::test_detect_headings_on` instead of mutating environment variables after app startup. This keeps the assertion aligned with cached feature-flag behavior in CI and prevents the `Deploy Web App` workflow from failing before SSH deployment.

- **Desktop PDF audit: resolved pre-existing style violations in `pdf_auditor.py`.** Wrapped long string and expression lines that previously triggered lint errors (including lines around missing-PyMuPDF messaging, tagged-PDF messaging, text block extraction, and font-family prefix checks) with no behavior changes.

- **Web: Changelog page `/changelog/` returned HTTP 500 due to unescaped template syntax in `changelog_body.html`.** Two occurrences of brace sequences that Jinja2 mis-parsed as template directives were escaped with HTML entities: a Docker service label using Go template syntax `{{.Name}}` (→ `&#123;&#123;.Name&#125;&#125;`) and an inline code example showing `{% set %}` / `{{ }}` Jinja2 syntax (→ `&#123;% set %&#125;` / `&#123;&#123; &#125;&#125;`).
- **CI: axe-core accessibility gate SARIF generation fixed.** `.github/workflows/accessibility-regression.yml` previously used the unsupported `--reporter sarif` flag (axe CLI 4.11.3 does not support it). Fixed by saving JSON output with `--save axe-results.json` and converting via the new `.github/scripts/axe_json_to_sarif.py` converter script, which emits valid SARIF 2.1.0 for GitHub code scanning upload.

- **Web: Home operation cards now map to correct features and labels.** `web/src/acb_large_print_web/templates/index.html` now correctly pairs the Audit card with `feature_audit_enabled` and the Fix card with `feature_checker_enabled`, with matching card classes/links/format labels.

- **Web: default Fix runs no longer show a false custom-settings warning.** `web/src/acb_large_print_web/customization_warning.py` now reads the normalized option keys produced by the Fix route and uses the canonical ACB defaults (`0.0` flush-left list indent, `0.0` paragraph indents) instead of the obsolete `0.5` list-indent default. A plain, no-customization Fix run no longer reports `List indent changed to 0.0"`.
- **Word fix: deeper heading styles now normalize consistently.** `desktop/src/acb_large_print/constants.py` and `office-addin/src/constants.ts` now define `Heading 4` through `Heading 6` with the same 20pt bold subheading treatment as the deepest configured subheading level, so existing built-in Word headings beyond level 3 no longer fall through with stale italic/small-font styling.
- **Word fix: paragraph spacing is now normalized directly on content paragraphs.** `desktop/src/acb_large_print/fixer.py` now applies canonical before/after spacing and line spacing to paragraph content, not just named styles, which fixes cases where body paragraphs kept Word's default 8pt after-spacing or heading paragraphs retained stale direct spacing overrides.
- **Word audit: repeated non-Arial findings are now capped.** `desktop/src/acb_large_print/auditor.py` and `office-addin/src/auditor.ts` now collapse repeated document-wide non-Arial font findings to the first three paragraph locations plus one summary row, reducing report spam for documents formatted wholesale in fonts like Times New Roman.
- **Docs: heading-level and paragraph-spacing guidance aligned with current fix behavior.** `docs/user-guide.md` and `web/src/acb_large_print_web/templates/partials/guide_body.html` now describe Heading 1 through Heading 6 support accurately and clarify that GLOW enforces paragraph spacing via Word paragraph-format settings (`Space Before` / `Space After`) rather than inserting blank paragraphs.
- **Web: customization warning no longer shows literal `<br>` tags or forced line wraps.** The warning text in `fix_result.html`, `audit_report.html`, and `audit_batch_report.html` now renders as plain text with preserved paragraph breaks via CSS instead of injecting escaped `<br />` tags, and `customization_warning.py` now generates unwrapped paragraph text so the notice reads naturally.
- **Web: AI-gated routes and entry points now stay consistent when a feature is turned off.** Quick Start, homepage cards, Fix-result and Audit-report chat pivots, Convert's Whisperer callout, and Whisperer/chat backend routes now honor the deployment feature gates so disabled AI features do not remain reachable through direct links or stale UI affordances.

- **Web: OpenRouter chat compatibility fallback on 400/404 payload rejections.** `web/src/acb_large_print_web/ai_gateway.py` now retries chat-completions calls once with a compatibility payload (dropping provider routing hints and model-list field) when providers reject advanced routing fields, improving reliability for chat and vision paths while keeping privacy routing as the default.
- **Tests: OpenRouter probe layer-1 no longer aborts on first model failure.** `tests/openrouter-probe/run_chat_paths_app.py` now records failures for paths 01/02 and continues executing remaining layer-1 paths so full coverage reports are generated even when a specific model is unavailable.
- **Tests: Audio probe and live test aligned with tuple return contract.** Updated `tests/openrouter-probe/run_audio_app.py` and `tests/openrouter-probe/test_openrouter_live.py` to unpack `(transcript, prompt_tokens, completion_tokens)` from `_transcribe_via_input_audio()` instead of assuming a string-only return.

- **Web: Chat tool dispatch now actually grounds responses.** `web/src/acb_large_print_web/routes/chat.py` now runs the local pre-flight keyword tool dispatcher before calling the model and injects those results into the system prompt, so Document Chat uses the accessibility toolset rather than leaving it disconnected.
- **Web: Whisperer cloud compatibility normalization.** `web/src/acb_large_print_web/routes/whisperer.py` now normalizes cloud-incompatible audio formats (OGG, FLAC, AAC, Opus) to temporary MP3 via `ffmpeg` before Whisper API upload, improving reliability across common chapter recordings.
- **Web: Health check and runtime probes scrubbed of old local-model assumptions.** `web/src/acb_large_print_web/app.py` now probes OpenRouter and Whisper directly and no longer reports Ollama or local Whisper readiness.
- **Web: Deployment stack scrubbed of stale local AI services.** Removed `ollama` and `faster-whisper` from the web deployment definitions and updated core templates (`index.html`, `chat_form.html`, `whisperer_form.html`, `about.html`, `privacy.html`) to reflect cloud-based AI usage accurately.
- **Docs: Remaining stale local-Whisper wording removed.** Updated `docs/user-guide.md` to consistently describe cloud transcription with temporary retention and cleanup.
- **Tests: Cloud architecture alignment.** Updated web tests to validate OpenRouter/Whisper health service keys and cloud Whisperer mocks, added queue/retry-focused tests in `web/tests/test_gating_ai_gateway.py`, and refreshed upload extension coverage for new audio formats.

- **Web: Accessibility audit sweep (18 templates + 2 static files).** Corrected multiple WCAG 2.2 AA issues across the web application templates. Changes: removed redundant `aria-labelledby` from `<section>` elements that already contain a headed `<h2>` (redundant landmark name per ARIA 1.2 implicit section semantics); removed `role="contentinfo"` from `<footer>` (native landmark, explicit role not required); fixed `consent.html` to use a proper `role="dialog" aria-modal="true"` modal with backdrop (users with low vision using screen magnification were seeing inline content instead of a blocking consent gate); promoted step headings in `whisperer_form.html` and `convert_form.html` from `<h3>` to `<h2>` to match their position as top-level steps within the tabpanel's content hierarchy; added `type="button"` to the Go Back button in `feedback_thanks.html` (implicit type was `submit`, risking accidental form submission); moved character-count paragraph in `chat_form.html` from `aria-hidden="true"` to `aria-live="polite" aria-atomic="true"` so screen readers announce remaining characters; removed `aria-describedby` from `admin_queue.html` System Health table (the `<caption>` already provides the description — `aria-describedby` pointing to a caption ID is redundant); fixed `maintenance.html` footer color from `#999999` (fails WCAG 1.4.3 at 3.2:1) to `#767676` (passes at 4.5:1), added `aria-hidden="true"` to decorative 🔧 emoji, and added `prefers-reduced-motion: reduce` rule to stop the status-indicator animation; added `id="confirm-estimate-hint"` to the `<p class="field-hint">` in `whisperer_form.html` that the confirm-estimate checkbox references via `aria-describedby` (was a dangling reference); disabled submit button with `aria-disabled="true"` until both acknowledge-checkboxes are checked, with JS `syncConfirmButton()` keeping disabled state in sync; wrapped `audioInput.addEventListener` in an `if (audioInput)` guard; added AbortController timeout (15 s) on Whisperer start-job fetch; improved JSON parse error handling for start-job response; improved queue-position display (1-indexed); added forms.css consent modal styles (`consent-modal-backdrop`, `consent-modal`, `consent-modal-scroll`) for the dialog layout.

- **Web: Whisperer estimate endpoint URL resolution.** `whisperer_form.html` now uses explicit backend URLs (`data-estimate-url`, `data-start-url`) instead of deriving endpoints from `form.action`, preventing broken estimate/start requests caused by path/URL variations.
- **Web: Whisperer metadata duration scaling with PyAV.** `_estimate_audio_duration_seconds()` now normalizes time-base conversion across PyAV variants so `container.duration` is interpreted in seconds correctly, avoiding extreme/invalid duration values.
- **Web: Whisperer estimate button keyboard activation reliability.** `whisperer_form.html` now handles `keydown`, `keyup`, and legacy `keypress` activation paths for Space/Enter on the estimate button with duplicate-trigger protection, improving behavior for browser and assistive-technology combinations that do not emit consistent click events.
- **Web: Whisperer estimate button real-time feedback.** The Calculate estimate button now shows "Calculating..." and disables during the estimate request, with live progress messaging ("Button pressed. Checking for audio file...", "Contacting server...") so users and screen-reader users get clear status updates about what the button is doing. Added exhaustive keyboard event telemetry to the button: logs all keydown/keyup/keypress events plus focus/blur state to the diagnostics panel and browser console for troubleshooting keyboard activation issues.
- **Web: Whisperer server-side estimate fallback step.** Added a no-JavaScript server-first flow using "Next: calculate estimate on server" and `/whisperer/estimate-page`, with two-stage rendering: initial page shows upload+Next only; after estimate, the same page shows estimate-confirmation and remaining transcription steps.
- **Web: Whisperer client-side confirm-estimate checkbox validation.** The JS submit handler now validates the required acknowledgement checkbox before posting to the server, showing a focused, accessible inline message and moving focus to the checkbox so users never reach the server with that input missing.
- **Web: Whisperer stage-2 error re-renders stay in stage 2.** When `whisperer_submit` catches a validation or runtime error it now preserves `estimate_ready=True` (when an `existing_token` is present), keeping the user on the estimate+options page so they can correct their input without re-uploading.
- **Web: Whisperer catch-all exception handler on both submit routes.** Unexpected exceptions in `whisperer_submit` and `whisperer_start_job` are now caught, logged with full tracebacks, and returned as user-friendly messages (HTML form re-render and JSON respectively) instead of propagating to the generic 500 error page.
- **Web: Whisperer model-load failure now reports the real cause.** `whisper_convert()` now maps common engine startup failures to specific user-facing errors, including insufficient disk space while downloading/loading the Whisper model and general model-load failures, instead of collapsing everything into a generic transcription-engine message.
- **Web: Additional route catch-alls now pass through real exception text.** Unexpected exceptions in `convert_submit`, `export_submit`, `template_form`, and `whisperer_start_job` now surface the actual exception message to the user instead of replacing it with a generic placeholder, improving diagnosis of production-only failures.
- **Desktop: Whisper transcription fallback now preserves real engine errors.** `whisper_convert()` no longer replaces unknown transcription failures with a fixed generic message; after specific model-load and disk-space cases are handled, the original exception text is propagated so the web app can display the actual cause.
- **Web: Whisperer cache path is now writable in containers.** The web Docker image now creates and owns a dedicated Hugging Face cache directory under `/app/.cache`, sets `XDG_CACHE_HOME`, `HF_HOME`, and `HUGGINGFACE_HUB_CACHE`, and `whisper_convert()` passes that writable cache path explicitly to `WhisperModel`. This fixes production failures like `[Errno 13] Permission denied: '/app/.cache'`.
- **Web: Increased Gunicorn request timeout for long Whisper runs.** The container now runs Gunicorn with a 30-minute timeout (up from 5 minutes) to prevent `WORKER TIMEOUT` / HTTP 502 errors while first-time model warm-up or long audio transcription is in progress.
- **Deploy: Whisper model warm-up before maintenance is lifted.** `scripts/deploy-app.sh` now preloads the Whisper model inside the web container after health passes and before disabling maintenance mode, so first-user requests do not stall on model initialization/download. Controlled via `WHISPER_WARMUP_ON_DEPLOY` (default `1`) and `WHISPER_WARMUP_TIMEOUT` (default `1200` seconds).
- **Deploy: Ollama model warm-up before maintenance is lifted.** `scripts/deploy-app.sh` now optionally pre-pulls Ollama models used by chat/vision (`llama3`, `llava` by default) before maintenance mode is disabled, reducing first-request delays and improving readiness status. Controlled via `OLLAMA_WARMUP_ON_DEPLOY` (default `1`), `OLLAMA_WARMUP_MODELS` (default `llama3 llava`), and `OLLAMA_WARMUP_TIMEOUT_PER_MODEL` (default `900` seconds).
- **Web: Whisperer client-side oversized-file precheck.** The form now uses the server-configured maximum audio size to warn and block oversized files immediately after selection (before upload), disabling estimate/proceed controls until a valid file is chosen.
- **Web: Whisperer progress UX clarity improvements.** The transcribe page now shows an explicit phase label (queued/model warm-up/transcribing/building/complete), an elapsed-time counter, queue position in status text, automatic scroll to the progress panel after submit, and a "still working" message when progress appears stalled during long model warm-up or processing.

### Added

- **Web: `/health` Ollama warm-model tracking.** `_get_ollama_running_models()` now queries `/api/ps` to list models currently loaded in Ollama memory. The `readiness.chat` and `readiness.vision` blocks each expose a new `model_warm` boolean, and `models.ollama_running` is included in the response and health log line so operators can tell instantly whether `llama3`/`llava` are warm (in memory) vs merely pulled (on disk).
- **Web: `/health` Whisper model-present check.** `_whisper_model_present()` inspects the configured Hugging Face cache directory for `model.bin` to distinguish "faster-whisper installed" from "Whisper model actually downloaded". `readiness.whisperer` now exposes `model_present` separately from `dependency_present`, so the health endpoint surfaces the full warm-up state of the Whisperer pipeline.
- **Ops: Post-deploy readiness gate for models.** `scripts/post-deploy-check.sh` now curls `/health` after all containers pass their Docker health gates and parses the `readiness` JSON with Python. If any feature (`chat`, `vision`, `whisperer`) is `not-ready`, the script prints the status/present/warm details and fails the deployment verification, preventing a deploy from being marked PASSED when required models have not been downloaded or loaded.

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
