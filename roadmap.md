# GLOW Accessibility Toolkit — Product Roadmap

**Last updated:** May 2026  
**Current version:** 3.0.0  
**Audience:** Developers, contributors, BITS leadership, partner organizations

This document is a living vision — not a commitment schedule. Items are grouped by theme and ordered within each theme by rough impact. Server requirements are called out explicitly for each significant feature so infrastructure decisions can be made in advance.

---

## Guiding Philosophy

GLOW exists to remove every barrier between a person with a document and a document that works for them. Blind and low-vision users, Deafblind readers, educators building large-print materials, and organizations complying with ADA Section 508 all need different things from the same source file. GLOW should be the single tool that serves all of them — online, offline, at the command line, inside Microsoft Office, and eventually embedded in their existing publishing workflow.

Dream large: a world where no one with low vision ever opens a Word document and reads 10-point Times New Roman again. Where a teacher clicks one button and gets an ACB-compliant large-print PDF, a BRF for the student's embosser, and an MP3 for the drive home. That is the target.

---

## Completed in v3.1.0 (Removed from Active Backlog)

The following roadmap entries are complete and shipped as core features in
v3.1.0. They have been removed from active theme backlogs below:

- 1.5 Back-translation quality scoring
- 2.5 Pronunciation dictionary management
- 2.6 Real-time streaming audio preview
- 3.3 Table accessibility advisor
- 3.4 Reading order detection and correction
- 3.5 Optical character recognition (OCR) for scanned PDFs
- 3.6 Document comparison and change tracking
- 4.3 OpenDocument Text (ODT) export
- 7.3 Cognitive accessibility profile
- 7.4 High-contrast and forced-colors mode
- 9.1 Public rule contribution portal

---

## Theme 1 — Braille Depth and Quality

### 1.1 Nemeth Code support
Mathematical braille (Nemeth Code and UEB Math) is entirely absent today. STEM accessibility is a critical gap. liblouis ships Nemeth tables (`nemeth.ctb`); the missing piece is a pre-processing stage that detects LaTeX/MathML/plain-text equations in the source and routes them through the Nemeth pipeline before merging back into the UEB output stream.

**Server requirements:** None beyond existing liblouis install. LaTeX detection can be done with a regex/heuristic pass in Python; MathML parsing needs `lxml`. No GPU, no significant RAM increase.

### 1.2 Tactile graphics pipeline
Braille documents frequently need tactile image descriptions. Today GLOW strips images; instead it should detect images in source documents, run an image-captioning model, and inject BRL descriptions at the insertion point. For SVG/diagrams, a separate path should use Inkscape's headless CLI to rasterize and then a captioning model to describe.

**Server requirements:** A captioning model endpoint (OpenRouter gpt-4o-mini vision is already wired in for alt-text; same endpoint works here). Inkscape headless (`apt install inkscape`). No GPU needed.

### 1.3 Embosser-ready BRF formatting
Current BRF output is BANA 40×25 but has no page-number support, running headers, or Title Page block. BANA Formats Guidelines mandate these for books and multi-section documents. Add a BRF formatting layer that injects title page, running headers (document title + page number), and pagination metadata.

**Server requirements:** None — pure Python formatting logic.

### 1.4 Interpoint layout preview
Interpoint braille (back-to-back pages) has different margin and page-length rules. Add an interpoint mode to the BRF formatter and a visual preview that shows dot patterns using CSS + Unicode Braille so sighted teachers can verify output without an embosser.

**Server requirements:** None — CSS rendering in the browser.

## Theme 2 — Speech Studio Expansion

### 2.1 SSML authoring interface
The current synthesis interface accepts plain text. Power users need control over pauses, emphasis, and pronunciation. Add an optional SSML authoring mode with a visual pause-marker toolbar so users can produce narrations with correct prosody without writing XML by hand.

**Server requirements:** None new — Kokoro and Piper both consume SSML via `piper` flags. Kokoro's ONNX route needs a text preprocessing wrapper.

### 2.2 Chapter-split document synthesis
Long documents currently produce one monolithic MP3. Add a chapter-detection pass (heading hierarchy) that splits the audio output into one file per chapter, named by heading text, packaged as a ZIP. This is transformative for textbooks and lengthy board minutes.

**Server requirements:** Additional ephemeral disk space (~100 MB per session for large docs). Existing ffmpeg already installed. Job queue (see Theme 5) becomes important here.

### 2.3 DAISY 3 talking book export
Combine the DAISY Pipeline 2 (already deployed as a sidecar) with Speech Studio synthesis to produce a full DAISY 3 talking book from any source document: structured XML + chapter-split MP3s, packaged as a `.daisy` ZIP. This is the gold standard for accessible audiobooks and is currently a manual multi-step process outside any tool.

**Server requirements:** DAISY Pipeline 2 already deployed. Additional disk: ~500 MB working space for a 100-page document. Processing time: 5–10 minutes for a long document → requires the async job queue (Theme 5). This is a flagship feature.

### 2.4 Voice cloning / custom voice upload (on-premise)
Organizations (school districts, state agencies) may want narration in a consistent, branded voice. Add support for uploading a custom ONNX voice model file to the speech-models volume. Admin UI for upload, test synthesis, and activation. Ship with a clear disclaimer about consent and ethics.

**Server requirements:** No additional compute — ONNX inference already runs on CPU. Admin UI file upload endpoint. Voice file validation (format check, size cap at 150 MB).

---

## Theme 3 — Document Intelligence and AI

### 3.1 Plain Language rewriting
Accessibility is not just formatting — it is comprehension. Add an AI-powered "Simplify Language" pass that rewrites dense legal, medical, or technical paragraphs to a target Flesch-Kincaid reading level chosen by the user. Preserve all factual content; flag rewrites for human review before applying.

**Server requirements:** OpenRouter API key (already wired). No additional server resources. Cost: ~$0.002/page at gpt-4o-mini prices.

### 3.2 Automatic image alt-text for all formats
The existing AI alt-text feature works for `.docx`. Extend it to:
- PDF image extraction (PyMuPDF already installed)
- PowerPoint embedded images (python-pptx already installed)
- EPUB images (already extracted by the EPUB auditor)

This completes the alt-text pipeline across every format GLOW handles.

**Server requirements:** No new dependencies. OpenRouter vision endpoint already wired.

---

## Theme 4 — Output Format Expansion

### 4.1 Large-print PDF with proper TOC and bookmarks
The current PDF export uses WeasyPrint which produces flat, linearized PDFs. Add a post-processing step using `pypdf` or `reportlab` to inject:
- Named bookmarks from heading hierarchy
- Document outline panel
- Tagged PDF structure (PDF/UA-1 compliance markers)

This is required for WCAG 2.1 Success Criterion 2.4.5 (Multiple Ways) in PDF form.

**Server requirements:** `pypdf>=4.0` (pure Python, no system deps). `reportlab` optional for full PDF/UA tagging.

### 4.2 PDF/UA-1 compliance export
PDF/UA-1 (ISO 14289-1) is the gold standard for accessible PDF. Full compliance requires Tagged PDF with correct artifact marking, proper reading order, role maps for custom tag types, and alt text on all figures. This is a significant project but would make GLOW the only open-source tool that can certify PDF/UA output from Word source documents.

**Server requirements:** `pdfua` or custom tag-injection layer on top of WeasyPrint output. No GPU or large-memory requirement, but build and test time is significant. This is a 2–3 sprint effort.

### 4.4 EPUB 3 with Media Overlays (read-along)
An EPUB 3 Media Overlay synchronizes text highlighting with audio narration. Combined with the Speech Studio chapter-split output (2.2) and DAISY Pipeline, GLOW could produce a read-along EPUB where each sentence highlights as it is spoken. This is transformative for students learning to read.

**Server requirements:** DAISY Pipeline 2 (already deployed). liblouis (already installed). The orchestration layer is the work — no new server software needed.

### 4.5 HTML5 accessible slide deck export (from PowerPoint)
Convert PPTX to a fully accessible, keyboard-navigable HTML5 presentation (using `reveal.js` or `impress.js`) with speaker notes, alt text, and proper heading structure. Screen reader users currently have no accessible way to present PowerPoint slides without the full Office suite.

**Server requirements:** `python-pptx` (already installed). `npm` (already installed for DAISY Ace). Bundle `reveal.js` into the Docker image (~3 MB).

### 4.6 Structured data export (JSON-LD, schema.org)
For organizations that ingest documents into content management systems, export document metadata (title, author, headings, accessible descriptions) as schema.org `Article` or `DigitalDocument` JSON-LD. This enables downstream search indexing and CMS ingestion without manual re-tagging.

**Server requirements:** None — pure Python serialization.

---

## Theme 5 — Infrastructure and Scale

### 5.1 Async job queue with progress streaming
Long-running jobs (DAISY talking book, OCR, batch audit of 50 files) cannot run synchronously. Add a Celery + Redis job queue. The browser polls a `/job/<id>/status` endpoint via SSE (Server-Sent Events) and displays a live progress bar. On completion, the result is stored in the session volume for download.

**Server requirements:** Redis (`docker run redis:7-alpine` — ~30 MB RAM at idle). Celery worker container (~150 MB RAM). This is a foundational infrastructure investment that unlocks many other features. Recommend adding to the `docker-compose.prod.yml` as two new services.

### 5.2 User accounts and document history
Currently all sessions are anonymous and ephemeral. Add an optional lightweight account system (email + password or SSO) that persists:
- Audit history across sessions
- Saved settings profiles
- Document library (last 10 uploads, 30-day retention)
- Shared reports associated with an account

**Server requirements:** PostgreSQL (upgrade from SQLite) or keep SQLite with WAL mode for single-server deployments. `Flask-Login` + `Flask-Mail` for account management. `bcrypt` for password hashing. Optional: OAuth2 via `authlib` for Google/Microsoft SSO.

### 5.3 Batch processing API (REST)
Organizations with document management systems need to automate GLOW. Add a REST API with API key authentication that accepts file uploads and returns JSON findings, download URLs, and job status. Rate-limited per API key. OpenAPI 3.1 spec auto-generated from route docstrings.

**Server requirements:** `flask-restx` or `flasgger` for spec generation. API key table in SQLite/Postgres. No additional compute.

### 5.4 Webhook delivery with retry
The webhook system (already implemented for audit) should be expanded to all major workflow events (fix complete, convert complete, speech download ready) and given a delivery retry queue with exponential backoff and a dead-letter log visible in the admin panel.

**Server requirements:** Requires the Celery queue (5.1) for reliable async retry. Without Celery, webhook delivery remains fire-and-forget.

### 5.5 Multi-tenant deployment mode
School districts, state libraries, and national organizations each want their own branded GLOW instance but don't want to run separate servers. Add a tenant model: each tenant gets a subdomain (`district.glow.example.org`), branded logo/colors, its own API key, its own feature flag set, and isolated document storage. Billing and usage rolled up per tenant.

**Server requirements:** Caddy `{subdomain}.{domain}` wildcard TLS (Caddy already supports this). Tenant config table in Postgres. Shared application container with tenant isolation enforced at the Flask request context level. This is a significant architectural investment — scope it as a separate branch/milestone.

### 5.6 CDN and edge caching for static assets
The current Caddy config serves all static assets from the container filesystem. For high-traffic deployments, add a CDN layer (Cloudflare or Fastly) in front of all `/static/` paths and configure proper `Cache-Control` headers with content-hash fingerprinting. Audit and fix result downloads should never be cached; static assets should be cached indefinitely.

**Server requirements:** Cloudflare free tier is sufficient. Asset fingerprinting requires a build step (`flask-assets` or a custom Webpack pass).

---

## Theme 6 — Integrations and Ecosystem

### 6.1 Microsoft Word add-in completion
The Office.js add-in (`office-addin/`) exists but is not feature-complete. Priority completions:
- Full audit with in-document annotation (comments on flagged paragraphs)
- One-click ACB formatting apply
- Braille preview pane (Unicode Braille, not BRF) for the current selection
- Export to Speech via the web app with single sign-on token handoff

**Server requirements:** None — runs client-side in the Word task pane and calls the web API.

### 6.2 Google Docs add-on
Millions of blind and low-vision users work in Google Docs. A Google Workspace Add-on using Apps Script can:
- Export the document to DOCX via the Drive API
- POST to the GLOW REST API (5.3) for audit/fix
- Download the fixed DOCX and re-import it as a new revision
- Surface findings as Google Docs comments

**Server requirements:** GLOW REST API (5.3) must be deployed. No additional server resources.

### 6.3 Canvas LMS integration
Canvas is the dominant LMS in K-12 and higher education. A Canvas LTI 1.3 tool that checks course materials for ACB compliance before they are published. Instructors get a compliance score in the Canvas UI and a link to GLOW to fix issues before students see the material.

**Server requirements:** LTI 1.3 authentication (`pylti1p3`). Webhook from Canvas to GLOW. No special compute.

### 6.4 Blackboard / Moodle plugins
Same concept as Canvas (6.3) but for Blackboard Ultra and Moodle. Lower priority due to smaller user base in the blind community, but important for international deployments.

**Server requirements:** Same as 6.3.

### 6.5 Email-to-GLOW gateway
An SMTP listener (or Postmark inbound hook, which is already configured) that accepts an email with a document attachment, runs the full audit+fix pipeline, and replies with the fixed document and a PDF accessibility report. No browser required. Transformative for users who are more comfortable with email than web applications.

**Server requirements:** Postmark inbound webhook endpoint (`/api/inbound-email`). Async job queue (5.1). Postmark server token already partially configured.

### 6.6 Zapier / Make.com / n8n connectors
Publish a Zapier integration that exposes GLOW audit, fix, and convert as Zap actions. This opens GLOW to tens of thousands of no-code automation users who can build document compliance workflows without writing a single line of code.

**Server requirements:** GLOW REST API (5.3) with OAuth2 app credentials for Zapier. Zapier developer account (free tier available).

---

## Theme 7 — Accessibility of GLOW Itself

### 7.1 Full keyboard-only workflow audit
Commission an independent keyboard-only audit of the entire application (every form, every modal, every dynamic widget) using only a keyboard, no mouse. Fix every gap. Publish the audit report publicly.

**Server requirements:** None — this is a QA effort.

### 7.2 Screen reader regression suite (NVDA + JAWS + VoiceOver)
Add automated axe-core checks to CI (partially done via Playwright). Expand to manual regression scripts for NVDA+Firefox, JAWS+Chrome, and VoiceOver+Safari covering the five most common workflows. Run before every release.

**Server requirements:** CI runner with Windows (for NVDA/JAWS tests). GitHub Actions Windows runners available at standard billing rates.

### 7.5 Internationalization (i18n) foundation
The UI is English-only. Add Flask-Babel scaffolding, extract all user-facing strings to `.po` message catalogs, and ship a Spanish translation as the first non-English locale. Spanish is the primary language of a large segment of the blind community served by BITS-affiliated organizations.

**Server requirements:** `Flask-Babel` + `pybabel`. Translation files shipped in the Docker image. No runtime cost.

---

## Theme 8 — Analytics and Reporting

### 8.1 Accessibility compliance trend dashboard
Show organizations how their document corpus is improving over time: average compliance score per week, most common rule violations, percentage of documents reaching grade A. Requires document history (Theme 5.2) but can be approximated with anonymous aggregate session data first.

**Server requirements:** Time-series SQLite tables. Chart rendering via Chart.js (already in the frontend) or server-side SVG. No additional server software.

### 8.2 Rule violation heatmap
Which ACB/WCAG rules are violated most across all documents processed by this GLOW instance? Show a heatmap (rule × week) that helps administrators understand where to focus training and templates. Publishable as an anonymized public report.

**Server requirements:** Aggregate counters in the existing `tool_usage.db` or a new `findings_stats.db`. No PII involved.

### 8.3 Automated compliance report for organizations
Generate a branded PDF compliance report (organization logo, date range, document count, pass/fail breakdown, top violations, recommendations) that can be submitted to procurement officers, auditors, or grant funders as evidence of accessibility program activity.

**Server requirements:** WeasyPrint (already installed). Report template in Jinja2/HTML. Optional: Postmark to email the report on a schedule.

### 8.4 Export audit findings to SARIF
Security tooling has standardized on SARIF (Static Analysis Results Interchange Format) for structured findings. Accessibility tooling should too. Add a `/audit/sarif/<token>` download endpoint that emits a SARIF 2.1.0 JSON file mapping each ACB finding to a SARIF `result` with URI, region, and rule metadata. This enables GitHub Advanced Security and Azure DevOps to display accessibility findings inline in pull request reviews.

**Server requirements:** None — pure JSON serialization. SARIF schema validation via `jsonschema` (already a transitive dep).

---

## Theme 9 — Community and Ecosystem Growth

### 9.2 Plugin architecture for custom rule sets
Organizations with requirements beyond ACB (APH, Benetech, state-specific mandates) should be able to ship a `.glow-rules` Python package that the runtime discovers and loads via entry points (`importlib.metadata`). Rules are first-class citizens: they appear in the UI, can be toggled, and are documented in the guidelines page.

**Server requirements:** None — Python entry point mechanism. Security consideration: only rules installed in the Docker image at build time are loaded; no runtime code upload.

### 9.3 Embeddable audit widget (JavaScript SDK)
A 10 KB JavaScript snippet that organizations can embed in their own document management portals. The widget shows a compliance badge for any document URL and links to GLOW for full remediation. Uses the REST API (5.3) behind the scenes.

**Server requirements:** REST API (5.3). CORS headers on the API endpoints. CDN hosting for the SDK script.

### 9.4 Annual ACB Accessibility State of the Union report
Each year, publish an anonymized aggregate report of accessibility trends across all documents processed by public GLOW instances. Which rules improved? Which got worse? What formats are most problematic? Partner with ACB to publish and publicize. This establishes GLOW as a data source of record for print accessibility.

**Server requirements:** Aggregate query across `findings_stats.db`. Annual job (cron). Output: Markdown → ACB-compliant HTML → PDF.

---

## Prioritized To-Do List

The items below are drawn from the themes above, sequenced by a combination of: **impact on blind/low-vision users** × **implementation effort** × **infrastructure readiness**. Items marked 🔥 are highest leverage — they unlock multiple downstream features.

### Tier 1 — Ship Next (High impact, low-to-medium effort, no new infra)

| # | Item | Theme | Effort |
|---|------|-------|--------|
| 1 | 🔥 Async job queue (Celery + Redis) | 5.1 | Medium — unlocks chapters 2.2, 2.3, 3.5 |
| 2 | 🔥 OCR for scanned PDFs (Tesseract) | 3.5 | Low-Medium — `apt install tesseract-ocr` + `pytesseract` |
| 3 | SSML authoring interface | 2.1 | Low — UI work, existing synth engines already support it |
| 4 | Chapter-split document synthesis (ZIP of MP3s) | 2.2 | Low — heading detection already exists |
| 5 | Plain Language rewriting (AI) | 3.1 | Low — OpenRouter already wired, UI + prompt engineering |
| 6 | Alt-text for PDF and PPTX images | 3.2 | Low — PyMuPDF + python-pptx + existing AI alt-text path |
| 7 | PDF bookmarks and TOC injection | 4.1 | Low — `pypdf` pure Python |
| 8 | ODT export via Pandoc | 4.3 | Very Low — one routing addition |
| 9 | Pronunciation dictionary (admin-managed) | 2.5 | Low — SQLite + TTS pre-processing pass |
| 10 | SARIF export endpoint | 8.4 | Low — pure JSON serialization |

### Tier 2 — Next Quarter (High impact, medium effort, some infra)

| # | Item | Theme | Effort |
|---|------|-------|--------|
| 11 | 🔥 DAISY 3 talking book export | 2.3 | Medium — Pipeline 2 already deployed, orchestration work |
| 12 | Nemeth Code braille (STEM) | 1.1 | Medium — liblouis tables exist, pre-processing needed |
| 13 | Table accessibility advisor | 3.3 | Medium — structural analysis + AI suggestions |
| 14 | 🔥 REST API with API key auth | 5.3 | Medium — foundational for Google Docs, Zapier, Canvas |
| 15 | BRF title page + running headers | 1.3 | Low — pure formatting logic |
| 16 | Reading order detection (PDF + DOCX) | 3.4 | Medium — PyMuPDF spatial analysis |
| 17 | Compliance trend dashboard | 8.1 | Medium — needs session history (5.2) or aggregate data |
| 18 | High-contrast / forced-colors CSS fix | 7.4 | Low — CSS only, high a11y value |
| 19 | Cognitive accessibility "Plain & Simple" mode | 7.3 | Low — CSS + template flag |
| 20 | Full keyboard-only workflow audit + fix | 7.1 | Medium — QA sprint, then fixes |

### Tier 3 — Next Two Quarters (High strategic value, larger effort or new infra)

| # | Item | Theme | Effort |
|---|------|-------|--------|
| 21 | 🔥 User accounts + document history | 5.2 | Large — auth, Postgres migration, UI |
| 22 | 🔥 Word add-in completion | 6.1 | Large — TypeScript, Office.js, in-document annotation |
| 23 | EPUB 3 Media Overlays (read-along) | 4.4 | Large — Speech + Pipeline + EPUB authoring |
| 24 | HTML5 accessible slide deck (from PPTX) | 4.5 | Medium — python-pptx + reveal.js |
| 25 | PDF/UA-1 compliance export | 4.2 | Large — full Tagged PDF pipeline |
| 26 | Tactile graphics pipeline | 1.2 | Medium — Inkscape + AI captioning |
| 27 | Screen reader regression suite | 7.2 | Large — Windows CI, manual scripts |
| 28 | Internationalization (Spanish) | 7.5 | Medium — Flask-Babel + translation effort |
| 29 | Compliance report PDF (org-branded) | 8.3 | Low — WeasyPrint template |
| 30 | Rule violation heatmap | 8.2 | Low — aggregate SQLite + Chart.js |

### Tier 4 — Visionary (Large effort, transformative impact, plan now)

| # | Item | Theme | Effort |
|---|------|-------|--------|
| 31 | 🔥 Google Docs add-on | 6.2 | Large — Apps Script + OAuth2 + REST API |
| 32 | Canvas LMS LTI 1.3 integration | 6.3 | Large — pylti1p3, LTI platform setup |
| 33 | Email-to-GLOW gateway | 6.5 | Medium — Postmark inbound + job queue |
| 34 | Multi-tenant deployment mode | 5.5 | Very Large — architectural investment |
| 35 | Public rule contribution portal | 9.1 | Medium — GitHub API + voting UI |
| 36 | Plugin architecture for custom rulesets | 9.2 | Large — entry points + security model |
| 37 | Real-time streaming audio preview | 2.6 | Medium — Gunicorn worker change + SSE |
| 38 | Voice cloning / custom voice upload | 2.4 | Medium — admin upload + ONNX validation |
| 39 | Zapier / Make / n8n connectors | 6.6 | Medium — REST API + OAuth2 app registration |
| 40 | Annual ACB State of the Union report | 9.4 | Medium — aggregate query + PDF export |

---

## Server Sizing Guide

| Deployment scale | Recommended spec | Notes |
|-----------------|-----------------|-------|
| Single org / team | 2 vCPU, 4 GB RAM, 40 GB SSD | Current production config. Adequate through Tier 1. |
| Multi-org / Tier 2–3 | 4 vCPU, 8 GB RAM, 80 GB SSD | Needed once Celery + Redis are added. |
| Tier 4 / multi-tenant | 8 vCPU, 16 GB RAM, 200 GB SSD + object storage (S3/R2) | Postgres, Redis cluster, CDN required. |
| OCR at scale | Add 2 Celery worker containers | Tesseract is CPU-bound; parallelism is horizontal, not vertical. |
| Speech at scale | Add 1–2 speech worker containers | Kokoro ONNX inference is single-threaded per request; scale horizontally. |
| Braille at scale | No separate workers needed | liblouis is sub-millisecond per page. |

---

## Immediate Next Steps (This Sprint)

1. **Upgrade the server** — 24 pending OS updates + restart required (noted during May 1 session)
2. **Verify Dockerfile liblouis smoke-test passes** in the current deploy run (watch `a43f53f` build logs)
3. **Spike the Celery + Redis queue** — add `redis:7-alpine` and a `celery-worker` service to `docker-compose.prod.yml` behind a feature flag
4. **Install Tesseract** in the Dockerfile and wire up `pytesseract` for scanned PDF detection → OCR
5. **Chapter-split synthesis** — extend Speech Studio with heading-based document segmentation and ZIP download
