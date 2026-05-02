# v3.1.0 Release Notes — May 1, 2026

## Overview

GLOW Accessibility Toolkit v3.1.0 ships 11 new features and hardening improvements on top of the v3.0.0 community release. The headline additions are Braille Studio (BANA-compliant text-to-braille and braille-to-text translation), a significantly improved Speech Studio document narration pipeline, a new Server Status diagnostic page, and a comprehensive WCAG 2.2 AA self-audit of GLOW's interface running on every CI build.

All features are enabled by default and fully backward-compatible. No database migrations or configuration changes are required to upgrade from v3.0.0.

## Roadmap.md Additions Implemented in v3.1.0

The following roadmap items were explicitly implemented in this release and are
feature-gated for controlled rollout.

| Roadmap Item | Implementation | Feature Flag |
|-------------|----------------|--------------|
| 1.5 Back-translation quality scoring | Braille result quality card with fidelity metrics/advisories | `GLOW_ENABLE_BRAILLE_BACK_TRANSLATION_SCORE` |
| 2.5 Pronunciation dictionary management | Dictionary CRUD + CSV import/export + speech pre-processing | `GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY` |
| 2.6 Real-time streaming audio preview | `POST /speech/stream` chunked WAV response | `GLOW_ENABLE_SPEECH_STREAM` |
| 3.3 Table accessibility advisor | `POST /magic/table-advisor` analysis API + form | `GLOW_ENABLE_TABLE_ADVISOR` |
| 3.4 Reading order detection and correction | `POST /magic/reading-order` (PyMuPDF block-order heuristic findings) | `GLOW_ENABLE_READING_ORDER_DETECTION` |
| 3.5 OCR for scanned PDFs | `POST /magic/ocr` best-effort extraction (`pytesseract`/Pillow runtime-gated) | `GLOW_ENABLE_PDF_OCR` |
| 3.6 Document comparison and change tracking | `POST /magic/compare` similarity + unified diff preview | `GLOW_ENABLE_DOCUMENT_COMPARE` |
| 4.3 OpenDocument Text (ODT) export | Convert direction `to-odt` via Pandoc | `GLOW_ENABLE_CONVERT_TO_ODT` |
| 7.3 Cognitive accessibility profile | Settings toggle + simplified UI mode + auto-expanded help sections | `GLOW_ENABLE_COGNITIVE_PROFILE` |
| 7.4 High-contrast / forced-colors mode | Forced-colors CSS support with system color tokens | `GLOW_ENABLE_FORCED_COLORS_MODE` |
| 9.1 Public rule contribution portal | `/magic` rule proposal forms + JSON proposal endpoints + Rules Reference link | `GLOW_ENABLE_RULE_CONTRIBUTIONS` |

### Magic Lab endpoint summary

The roadmap 2.x/3.x/9.x advanced features are surfaced in a new Magic Lab route:

- `GET /magic/`
- `POST /magic/table-advisor`
- `POST /magic/reading-order`
- `POST /magic/ocr`
- `POST /magic/compare`
- `POST /magic/pronunciation`
- `POST /magic/pronunciation/delete`
- `POST /magic/pronunciation/import`
- `GET /magic/pronunciation/export.csv`
- `POST /magic/pronunciation/preview`
- `POST /magic/rules/propose`
- `GET /magic/rules/proposals`

---

## New Features

### 1. Braille Studio

A new dedicated tool at `/braille/` translates English text to braille and braille back to English using the liblouis translation library — the same engine used by JAWS, NVDA, and BrailleNote.

**Supported translation tables:**

| Table | Description |
|-------|-------------|
| UEB Grade 1 | Unified English Braille, uncontracted — current BANA literary standard (adopted 2016) |
| UEB Grade 2 | Unified English Braille, contracted — current BANA literary standard |
| EBAE Grade 1 | English Braille American Edition, uncontracted — pre-2016 legacy interop |
| EBAE Grade 2 | English Braille American Edition, contracted — pre-2016 legacy interop |
| Computer Braille | BANA Computer Braille Code, 8-dot — for code, terminal output, and technical content |

**Output formats:**

- **Unicode Braille** (U+2800--U+28FF): paste into documents, emails, or web pages
- **BRF (Braille Ready Format)**: ASCII-encoded braille wrapped at the BANA-standard 40 cells per line, with optional embosser pagination (form feeds every 25 lines); downloadable as `.brf`

**Back-translation:** Paste or upload a `.brl` or `.brf` file and receive the English source text. Useful for proofreading contracted G2 output and verifying embosser-ready files.

**Input:** Direct text paste or file upload (`.txt`, `.md`, `.brl`, `.brf`). Downloaded results available as `.brl`, `.brf`, or `.txt`.

**Operational notes:**

- Feature-gated via `GLOW_ENABLE_BRAILLE` (default: enabled)
- `GLOW_ENABLE_CONVERT_TO_BRAILLE` and `GLOW_ENABLE_EXPORT_BRAILLE` control translation and download sub-endpoints independently
- 30 requests/minute rate limit on form and download endpoints
- Graceful degradation: when liblouis is not installed, the page renders a clear message describing the dependency rather than showing errors
- Braille tab visible in main navigation when the flag is enabled

---

### 2. Speech Studio: Pandoc document preparation pipeline

Uploaded documents are now converted to normalized plain text via Pandoc before synthesis. This ensures consistent, clean narration regardless of source format.

**Supported input formats for narration:** `.md`, `.rst`, `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.epub`, `.odt`, `.rtf`, and all other formats Pandoc accepts. Plain `.txt` files bypass Pandoc and work on servers where Pandoc is not installed.

**What changes from v3.0.0:** When Pandoc is absent and a non-text file is uploaded, GLOW returns a clear error message naming the missing dependency. Previously the behavior was undefined for several input types.

**Diagnostic artifacts:** Two intermediate files are persisted in the session temp directory for operator diagnostics:
- `speech_rendered.txt` — the Pandoc plain-text output
- `speech_source.txt` — the normalized source text after GLOW pre-processing

---

### 3. Speech Studio: staged workflow UI

The document narration flow is redesigned as an explicit two-stage process to eliminate confusion about when preview and download are available.

**Before (v3.0.0):** Preview and download buttons were visible on page load regardless of preparation state.

**After (v3.1.0):**

1. Upload your document or type your text.
2. Click **Next: Prepare text and estimate** — extraction, word count, and timing estimate run.
3. **Preview first sentences** and **Download full document audio** appear only after preparation succeeds.

Controls are hidden via both semantic `hidden`/`aria-hidden` attributes and JavaScript state, so they cannot appear on first load even if CSS state is inconsistent. Preparation errors auto-scroll into view so a failed prepare step is immediately visible without the user scrolling manually.

---

### 4. Server Status page (`/status`)

A new human-readable diagnostics page gives operators a clear view of server state without needing to parse raw JSON.

**Content rendered at `/status`:**

- Service probes: speech engine reachability, braille library import
- Readiness summary: speech and braille ready/not-ready with explanations
- Feature flag summary (enabled count, disabled count)
- Full feature flag table with current values
- Raw JSON output (the same payload as `/health`) for copy-paste into monitoring tools

**Consent:** `/status` is exempt from the consent gate, so it is reachable by uptime monitors, load balancer health probes, and Docker orchestration without a browser session.

---

### 5. axe-core/Playwright WCAG 2.2 AA self-audit in CI

Every CI build now audits GLOW's own interface at WCAG 2.2 AA using `@axe-core/playwright`.

**Routes audited (17 total):**

| Group | Routes |
|-------|--------|
| Core tools | Home, Audit, Fix, Convert, Template |
| New in 3.0/3.1 | Speech Studio, Braille Studio |
| Reference and info | Settings, Guidelines, User Guide, About, Changelog, FAQ, Rules Reference |
| Utility | Feedback, Privacy Policy, Status |

**Interactive states tested:**

| State | Description |
|-------|-------------|
| Help accordions open | All `<details>` elements expanded |
| Service unavailable | Speech/braille unavailable banners rendered |
| Dark mode | `prefers-color-scheme: dark` emulated |
| Mobile viewport | 375 x 812 px (iPhone SE equivalent) |

**CI behavior:**

- Critical and serious violations: fail the build immediately with selector-level diagnostic output
- Moderate and minor violations: advisory warnings, do not block the build
- Results written to `artifacts/axe-results.json` and uploaded to GitHub Code Scanning as SARIF (unchanged from prior release)

Added `@axe-core/playwright ^4.11.2` to `web/package.json`. New `test:axe` npm script runs only the axe spec separately from the functional regression suite.

---

### 6. New feature flags for speech and braille export/conversion

Four granular feature flags provide per-endpoint control over speech and braille capabilities:

| Flag | Controls | Default |
|------|---------|---------|
| `GLOW_ENABLE_CONVERT_TO_SPEECH` | Text extraction and narration preparation endpoints | `true` |
| `GLOW_ENABLE_EXPORT_SPEECH` | Audio file download endpoints | `true` |
| `GLOW_ENABLE_CONVERT_TO_BRAILLE` | Braille translation endpoint | `true` |
| `GLOW_ENABLE_EXPORT_BRAILLE` | Braille result download endpoints | `true` |

All four flags appear in the Admin feature flags panel under the **Exports** and **Convert** subfeature groups. Toggle in `instance/feature_flags.json` or via the Admin UI.

---

### 7. Speech and Braille readiness in `/health`

The `/health` endpoint now includes explicit service readiness fields for speech and braille:

```json
{
  "services": {
    "speech": { "status": "ok", "engine": "piper" },
    "braille": { "status": "ok", "version": "3.24.0" }
  },
  "readiness": {
    "speech": true,
    "braille": true
  }
}
```

This means monitoring dashboards and the `/status` page can surface speech or braille service degradation without requiring a test synthesis or translation request.

---

## Infrastructure and Quality

### 8. liblouis Docker deployment hardening

The production Docker image now ships working liblouis Python bindings with a build-time verification gate.

**What changed in `web/Dockerfile`:**

- Installs `liblouis-bin`, `liblouis-dev`, `liblouis-data`, and `python3-louis` via apt
- Copies the `louis` module into the pip Python 3.13 site-packages so `import louis` resolves at runtime
- Runs `python3 -c "import louis"` as a smoke test during the Docker build — the build fails immediately if the binding is absent, catching deployment failures before the image is pushed

The `pylouis` stub package (which installed no importable code) has been removed from `web/pyproject.toml` and `web/requirements.txt`.

---

### 9. CI Pandoc integration

Three CI workflows now install Pandoc explicitly before running the web test suite:

- `deploy.yml`
- `feature-flags-ci.yml`
- `accessibility-regression.yml`

This ensures the full Speech Studio document-prepare path is exercised in CI, not just the `.txt` bypass path.

---

### 10. Speech route regression test suite

`web/tests/test_speech_routes.py` is a new test module covering:

- Staged prepare action rendering (prepare button visible, download/preview hidden before prepare)
- Pandoc-required behavior (missing Pandoc returns correct error)
- Text extraction paths for each supported input type
- Persistence of `speech_rendered.txt` and `speech_source.txt` artifacts after a successful prepare

---

### 11. `/status` consent exemption and braille nav regression test

- `/status` is now listed in the consent-gate exemption list alongside `/health`, so it is reachable without a browser consent session.
- `test_main_nav_shows_braille_tab_when_enabled` added to `web/tests/test_braille.py` to guard against regressions where the Braille tab disappears from navigation when `GLOW_ENABLE_BRAILLE` is set to `true`.

---

## Fixes in v3.1.0

| Fix | Description |
|-----|-------------|
| Speech staged actions hidden on load | The post-prepare action group (`Preview first sentences`, `Download full document audio`) now uses both semantic `hidden`/`aria-hidden` and JS state toggling so controls do not appear before preparation completes. |
| `/status` JSON serialization with mocked values | Health payload construction now coerces non-string `louis_version` values to text before JSON serialization, preventing failures when test mocks return non-JSON-native types. |
| `/changelog/` Jinja TemplateSyntaxError | `scripts/build-doc-pages.py` wraps auto-generated partials in `{% raw %}...{% endraw %}` so changelog entries that document Jinja syntax are treated as plain text. |
| `post_findings.json` in project root | Post-fix findings are now always written inside the session temp directory (`get_temp_dir(token)`) instead of resolving to the working directory on some hosts. |
| `POST /audit/` returning 405 | The `@audit_bp.route('/', methods=['POST'])` decorator was accidentally dropped from `audit_submit_rate_limited`. Restored. |
| Desktop mammoth/markitdown conflict | `desktop/pyproject.toml` and `desktop/requirements.txt` pinned to `mammoth>=1.11.0,<1.12.0` for compatibility with `markitdown[docx,pdf,pptx,xlsx]>=0.1.5`. |
| Braille tab local flag defaults | Added `GLOW_ENABLE_BRAILLE: true` to `instance/feature_flags.json` and `web/instance/feature_flags.json` so local runs do not rely on implicit default resolution. |
| Convert page speech copy | The Convert page speech direction now explicitly states that Speech Studio renders the document to plain text first before showing estimate and download controls. |

---

## Upgrade Notes

**From v3.0.0:** No migration required. All new flags default to `true` (enabled). Deploy the new Docker image and restart.

**Pandoc:** Required for Speech Studio document upload narration (non-`.txt` formats). Install on your server with `apt-get install pandoc`. Already installed in the Docker image as of v3.0.0. CI workflows now also install it explicitly.

**liblouis:** Required for Braille Studio. Installed automatically in the Docker image as of v3.1.0 (`python3-louis` via apt). For bare-metal installs, run `apt-get install liblouis-bin liblouis-dev liblouis-data python3-louis`.

**axe-core/Playwright CI:** If you run the GLOW test suite locally, run `npm install` in `web/` to pull in the new `@axe-core/playwright` package.

---

## What's Next (Roadmap Preview)

The following items from the product roadmap are the leading candidates for v3.2.0:

- **Nemeth Code braille** (STEM math via liblouis nemeth tables + LaTeX/MathML pre-processing)
- **BRF embosser formatting** (title page, running headers, pagination per BANA Formats Guidelines)
- **SSML authoring interface** (pause markers, emphasis controls for Speech Studio power users)
- **Chapter-split document synthesis** (one MP3 per heading chapter, ZIP download)
- **Plain Language rewriting** (AI-powered Flesch-Kincaid simplification pass, human review before apply)

See `roadmap.md` in the repository root for the full prioritized roadmap with server requirement notes for each item.
