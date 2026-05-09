# GLOW Accessibility Platform Plan

## Purpose

This document is the definitive plan for the entire GLOW. It covers every current feature, every planned enhancement, and a comprehensive UX redesign strategy that addresses all capabilities together.

GLOW is a multi-surface accessibility toolkit that helps authors, designers, developers, and accessibility specialists create, validate, transform, and deliver accessible content across every stage of the content lifecycle. It enforces the American Council of the Blind Large Print Guidelines (revised May 6, 2025), Microsoft Accessibility Checker rules, and WCAG 2.2 AA standards.

This plan does not prescribe immediate code changes. It defines the next architecture, UX, and product phases for all GLOW features as a unified system.

---

## Strategic Goals

1. Reduce cognitive load across all features by aligning navigation with user intent rather than product internals.
2. Improve output confidence across every feature area so users act on results with fewer second guesses.
3. Support users at every skill level: first-time authors, practitioners, accessibility specialists, team leads, and enterprise administrators.
4. Create a stable foundation for AI-enhanced workflows that can be activated incrementally across all features, not just in one area.
5. Keep accessibility as the core mission and make GLOW itself a model of accessible design at every interaction point.

---

## Platform Feature Inventory

The following sections describe every GLOW feature: what it currently does, who it serves, what it takes as input, what it produces, the outcomes it enables, and what planned enhancements will strengthen it.

---

### 1. Document Audit

**What It Does**

Document Audit accepts uploaded documents in Word, Excel, PowerPoint, PDF, EPUB, and HTML formats and evaluates them against ACB Large Print Guidelines, Microsoft Accessibility Checker rules, and WCAG 2.2 AA. It returns a scored report with categorized findings, severity levels, WCAG criterion references, and remediation links. It supports batch uploads, webhook callbacks, CSV exports, email report delivery, rule profile selection, and per-rule overrides.

**Current State**

Fully operational. Supports single and batch uploads. Supports AI-powered alt-text suggestions for images. Supports custom rule profiles (by format, category, severity, or preset profile). Fires signed HMAC webhooks to developer-supplied callback URLs. Generates a scored overall compliance percentage.

**Inputs**

- One or more uploaded documents (Word, Excel, PowerPoint, PDF, EPUB, HTML, CSV, JSON, XML, ODT, RTF)
- Rule profile selection (ACB 2025, WCAG AA, Microsoft, custom)
- Rule include and exclude lists (optional)
- Severity threshold gate (optional)
- Webhook callback URL (optional)
- Email delivery address (optional)

**Outputs**

- Scored compliance report (HTML and JSON)
- Findings list with severity, WCAG criterion, remediation guidance, and help links
- CSV export of all findings
- Batch summary report (for multi-file uploads)
- AI-generated alt-text suggestions for images where applicable
- Customization warning when user-applied overrides significantly weaken a rule profile

**Expected Outcomes**

- Authors catch accessibility problems before publishing or distributing
- Practitioners reduce manual review time with pre-scored, criterion-mapped findings
- Accessibility specialists use rule profiles to match organizational standards
- Managers use batch reports to assess content quality across a document library

**User Benefits By Level**

- New users: straightforward upload with clear plain-language findings and ACB guidance links
- Practitioners: severity filtering and criterion rollups cut triage time
- Specialists: rule profiles and overrides allow standards alignment
- Managers: batch and email delivery support library-scale audits
- Enterprise owners: webhook integration feeds findings into existing ticketing pipelines

**Projected Wins**

- 30 to 45 percent reduction in accessibility defects reaching publication
- 25 percent faster finding-to-fix cycle with inline remediation links
- 20 percent less manual reviewer effort through scored pre-triage

**Planned Enhancements**

1. Structured finding export with stable finding IDs and SARIF-compatible format for CI integration.
2. Comparative audit mode: upload two versions of the same document and show delta findings with regression callouts.
3. Guided review mode: step-by-step walkthrough for each finding with visual location indicators.
4. Exception notes: per-finding annotations allowing specialists to mark accepted deviations with rationale and expiry.
5. Trend line per document or template family: show compliance trajectory across version history.

---

### 2. Document Fix

**What It Does**

Document Fix accepts an uploaded document and returns a remediated version with ACB and WCAG compliance issues automatically corrected where correction is safe and deterministic. It shows a before/after summary of applied fixes, a compliance score improvement estimate, and a CSV of remaining manual-review issues it could not auto-correct.

**Current State**

Fully operational. Applies ACB structural and formatting fixes, heading hierarchy corrections, emphasis normalization, and other deterministic repairs. Uses AI gating to protect against runaway AI resource usage. Reports a compliance score and tracks severity-weighted deductions.

**Inputs**

- Uploaded document (Word, Excel, PowerPoint, PDF, HTML, EPUB, and supported formats)
- Rule profile selection (same options as Audit)
- Fix mode: conservative (safe only) or aggressive (best-effort)

**Outputs**

- Remediated document download
- Fix summary with before/after counts by category
- Compliance score before and after
- CSV of residual manual-review findings
- Customization warning when overrides reduce fix scope

**Expected Outcomes**

- Authors receive a corrected document in one step instead of working through findings manually
- Practitioners use Fix as a first-pass clean-up before detailed manual review
- Specialists use conservative mode to correct clear failures while preserving original intent

**User Benefits By Level**

- New users: one-step upload and download with an improved document and clear remaining guidance
- Practitioners: drastic reduction in repetitive manual formatting corrections
- Specialists: residual findings report gives a targeted review list
- Managers: batch fix capability reduces time to compliance at library scale

**Projected Wins**

- 40 to 60 percent of deterministic formatting issues resolved without manual effort
- 25 percent faster compliance achievement when combined with Audit
- 20 percent fewer repeated findings across revised document iterations

**Planned Enhancements**

1. Annotated diff view: show exact changes made in an inline visual comparison before the user downloads.
2. Selective fix confirmation: allow users to approve or skip each proposed change before applying.
3. Batch Fix mode: upload a ZIP of documents and receive a ZIP of remediated versions with a summary matrix.
4. Fix history per document token: compare current vs. prior run to confirm regression-free re-uploads.
5. AI-assisted explanation: for each applied fix, show a one-sentence plain-language explanation of why the change was necessary.

---

### 3. Convert and Export

**What It Does**

Convert accepts documents in over 20 formats and converts them to Markdown, ACB-compliant HTML, Word DOCX, EPUB 3, PDF, or DAISY Pipeline output. Two-stage chaining transparently extends Pandoc's native reach: formats Pandoc cannot read natively (PowerPoint, Excel, PDF, CSV, JSON, XML) are first converted to Markdown via MarkItDown, then that Markdown is fed to Pandoc. This makes GLOW's output format coverage one of the broadest available without requiring users to know the underlying pipeline.

**Current State**

Fully operational. Supports six conversion directions. Two-stage chaining is automatic and transparent. WeasyPrint is used for PDF rendering. DAISY Pipeline conversion is available when installed. LibreOffice pre-conversion extends ODT and legacy formats.

**Inputs**

- Uploaded document in any supported source format
- Target output format selection
- Optional title override
- ACB styling flag (include or exclude ACB CSS and heading structure normalization)

**Outputs**

- Converted file as a download (Markdown, HTML, DOCX, EPUB 3, PDF, or DAISY/EPUB)
- Standalone HTML includes embedded ACB CSS for direct distribution
- CMS fragment export strips document chrome and outputs embeddable body content only

**Expected Outcomes**

- Authors move content between formats without manual reformatting or losing accessibility structure
- Practitioners produce ACB-compliant HTML or EPUB from existing Word documents in a single step
- Specialists generate multiple output formats from one source document to support different delivery channels

**User Benefits By Level**

- New users: drag and drop any document, pick a target, download the result
- Practitioners: chain output to Audit or Fix for immediate compliance check on the converted file
- Specialists: DAISY Pipeline output supports specialized assistive technology readers
- Managers: batch format conversion for distribution library normalization
- Enterprise owners: CMS fragment export supports headless CMS publishing workflows

**Projected Wins**

- 50 to 70 percent reduction in manual reformatting time for format migrations
- 30 percent fewer structural accessibility defects introduced during format transitions
- 20 percent faster publishing pipeline for ACB-compliant HTML and EPUB delivery

**Planned Enhancements**

1. Conversion quality report: after conversion, run a lightweight Audit pass and embed a finding count with a link to the full audit result.
2. Batch conversion: ZIP upload with a manifest for multi-file conversions with consistent output configuration.
3. Round-trip conversion verification: convert from source to target and back, then diff the two to flag structural loss.
4. CSS theming options: allow users to select from ACB standard, high contrast, and custom CSS bundles at conversion time.
5. DAISY Pipeline status indicator: surface pipeline availability and version prominently so users understand output options before uploading.

---

### 4. Template Builder

**What It Does**

Template Builder generates a Word .dotx template pre-configured to ACB Large Print Guidelines. Users choose heading levels to include, font size overrides, bound or unbound layout, whether to include a sample content page, and the standards profile (ACB 2025 or others). The result is a ready-to-use Word template that enforces accessible typography and structure from the first keystroke.

**Current State**

Fully operational. Supports per-heading-level font size overrides. Generates templates that include proper paragraph styles, heading hierarchy, and sample content when requested. Standards profile selection allows ACB 2025 and other organizational style targets.

**Inputs**

- Document title
- Heading levels to include (H1 through H6, multi-select)
- Per-level font size overrides (optional; defaults to ACB spec)
- Bound or unbound layout
- Include sample content page flag
- Standards profile selection

**Outputs**

- Word .dotx template file download
- Template is pre-styled with ACB-compliant paragraph styles, heading styles, and typography

**Expected Outcomes**

- Authors start new documents in a compliant state rather than retrofitting accessibility after the fact
- Organizations distribute the template as a corporate standard to ensure consistent accessible output
- Practitioners save time by starting from a verified baseline instead of checking from scratch

**User Benefits By Level**

- New users: immediately produce compliant documents without knowing ACB rules
- Practitioners: maintain a library of project-specific templates generated from a verified baseline
- Specialists: adjust per-heading font sizes and profiles to match custom organizational standards
- Managers: standardize a single template across a team or department
- Enterprise owners: embed the template into onboarding workflows and knowledge bases

**Projected Wins**

- 60 to 80 percent reduction in formatting-related findings on documents started from a GLOW template
- 30 percent faster authoring time for staff who previously had to manually configure Word styles
- 20 percent reduction in template-related audit findings at publication

**Planned Enhancements**

1. Template library: save named templates and share or download them as a collection.
2. Audit the template itself: run a quick compliance check on the generated template to confirm it meets the chosen profile before download.
3. PowerPoint template generation: produce a .potx slide template with ACB-compliant text sizes, high-contrast color schemes, and accessible placeholder layouts.
4. Excel template generation: produce a spreadsheet template with accessible header rows, label conventions, and accessible color choices.
5. Color scheme presets: add high-contrast, print-optimized, and screen-reader-optimized color themes.

---

### 5. Speech Studio

**What It Does**

Speech Studio synthesizes text or uploaded documents into audio using Kokoro TTS and Piper TTS voice engines. It supports text preview (short input, instant WAV), document synthesis (full extracted text rendered to MP3 or WAV), voice selection, speed and pitch controls, and pronunciation dictionary integration from Magic Lab. It also includes document text extraction and rendering estimates before full synthesis.

**Current State**

Fully operational. Supports Kokoro and Piper voices. Text preview renders instantly. Document upload triggers text extraction via MarkItDown and synthesis pipeline. Pronunciation dictionary from Magic Lab is applied at synthesis time when enabled. WAV and MP3 output with configurable format preference. Feature-flag governed for full site administrator control.

**Inputs**

- Direct text input (up to 500 characters for preview) or document upload
- Voice selection (Kokoro or Piper voices)
- Speed multiplier
- Pitch multiplier
- Output format preference (WAV or MP3)
- Pronunciation dictionary (managed via Magic Lab, applied automatically)

**Outputs**

- WAV or MP3 audio file download
- Audio duration and processing time estimates before full synthesis
- First-sentence preview audio before full document synthesis
- Pronunciation-corrected audio when dictionary entries apply

**Expected Outcomes**

- Authors produce narration for accessible documents, training materials, and meeting announcements without external tooling
- Practitioners generate prototype narration for screen-reader testing and review
- Low-vision and reading-impaired users receive content in audio format when the document cannot be consumed visually

**User Benefits By Level**

- New users: choose a voice, paste text or upload a file, download audio in seconds
- Practitioners: use document synthesis to validate that complex documents read naturally when synthesized
- Specialists: tune pronunciation dictionary to correct domain-specific terminology for high-quality narration
- Managers: produce meeting agendas, board materials, and announcements in audio format without dedicated studio equipment
- Enterprise owners: integrate the feature flag to enable or disable synthesis for specific deployment contexts

**Projected Wins**

- 40 to 60 percent reduction in time to produce compliant audio-format content
- 20 percent improvement in narration accuracy through pronunciation dictionary tuning
- New content access channel for 10 to 15 percent of users who rely on audio delivery

**Planned Enhancements**

1. Batch document synthesis: submit a queue of documents and receive an audio archive.
2. SSML preview and editing: expose Speech Synthesis Markup Language controls for advanced users who want fine-grained narration control.
3. Voice preview gallery: play a 10-second sample from each available voice before committing to synthesis.
4. Chapter-level synthesis: for long documents, synthesize by heading section and produce a chapter-indexed audio package.
5. Accessibility-aware synthesis warnings: flag documents containing tables, code blocks, or figures that synthesize poorly and suggest reformatting.

---

### 6. BITS Whisperer

**What It Does**

BITS Whisperer transcribes uploaded audio files to text using the OpenRouter Whisper audio transcription endpoint, then delivers the result as a Markdown file or a Word DOCX. The transcript is produced locally, never stored beyond the session temp directory, and cleaned within one hour. The route is hidden entirely when no OpenRouter API key is configured.

**Current State**

Fully operational. Supports MP3, MP4, M4A, WAV, FLAC, OGG, OPUS, and WEBM audio files. Outputs plain Markdown transcript or Word document via Pandoc. Includes a protected retrieve flow for sharing transcripts securely. Uses the same operator API key as all other AI features.

**Inputs**

- Uploaded audio file (MP3, MP4, M4A, WAV, FLAC, OGG, OPUS, WEBM)
- Output format selection (Markdown or Word DOCX)
- Optional password for protected transcript retrieval

**Outputs**

- Markdown transcript file download or Word DOCX download
- Protected share link for transcript retrieval (when password is set)
- Audio duration estimate before processing

**Expected Outcomes**

- Meeting recordings, interviews, and narrated presentations are converted to editable Markdown or Word documents ready for accessibility processing
- Transcripts can be immediately fed into Audit or Fix for compliance checking
- Authors capture spoken content and deliver it as text-accessible documents without separate transcription services

**User Benefits By Level**

- New users: upload audio, select format, receive a document in seconds
- Practitioners: chain transcription output directly to Audit or Convert for multi-format delivery
- Specialists: produce signed transcripts of accessibility consultations or review sessions
- Managers: convert recorded board meetings and stakeholder sessions into accessible written records
- Enterprise owners: keep all transcription processing on-server with no data leaving except to the configured API endpoint

**Projected Wins**

- 50 to 70 percent reduction in time to produce written records from audio sources
- New accessibility pathway for 100 percent of recorded content that currently has no text equivalent
- 30 percent reduction in administrative cost for meeting documentation workflows

**Planned Enhancements**

1. Speaker diarization: identify and label distinct speakers in the transcript when the underlying model supports it.
2. Auto-chain to Audit: offer a one-click option to immediately audit the produced transcript document after transcription.
3. Vocabulary hints: supply a domain glossary at upload time to improve transcription accuracy for specialized terminology.
4. Timestamped transcript: include time markers for each paragraph to support video captioning workflows.
5. Caption export: convert timestamped transcripts to SRT or WebVTT captioning files for video accessibility compliance.

---

### 7. Braille Studio

**What It Does**

Braille Studio translates text to Braille and Braille to text using liblouis. It supports UEB Grade 1 and Grade 2 (current BANA literary standard), BANA Computer Braille Code (8-dot), and legacy EBAE Grade 1 and Grade 2. BRF output is wrapped at the BANA-standard 40 cells per line. Users can input text directly or upload a text or BRF file and receive the translated result as a download.

**Current State**

Fully operational when liblouis is available. Shows graceful degradation with an unavailability reason when liblouis is not installed. Displays a visual diff when translating Braille back to text so users can verify rendering accuracy.

**Inputs**

- Direct text input (up to 50,000 characters) or file upload (TXT, BRF, BRL, MD)
- Translation direction (text to Braille or Braille to text)
- Grade selection (UEB Grade 1, UEB Grade 2, Computer Braille, EBAE Grade 1, EBAE Grade 2)
- Output format (BRF or Unicode Braille)

**Outputs**

- Translated result in the target representation
- BRF file download with BANA-standard line wrapping
- Visual diff when reverse-translating Braille to text

**Expected Outcomes**

- Publishers and organizations serving blind readers produce correctly graded BRF files from existing text content
- Braille specialists validate translation accuracy before embossing
- Educators convert teaching materials to the appropriate Braille grade for their students

**User Benefits By Level**

- New users: paste text, select grade, download BRF in two steps
- Practitioners: upload large text files and receive production-ready BRF files without external embossing software
- Specialists: verify round-trip accuracy with the visual diff tool
- Managers: batch-produce Braille versions of meeting materials and organizational documents
- Enterprise owners: integrate via existing document workflows; the route is feature-flag controlled

**Projected Wins**

- 40 to 60 percent reduction in time to produce a BRF file compared to manual Braille transcription
- Elimination of grade selection errors for organizations standardizing on UEB Grade 2
- Braille access for content that currently has no tactile format equivalent

**Planned Enhancements**

1. Batch text-to-Braille: upload a ZIP of text files and receive a ZIP of BRF files with a translation report.
2. Grade recommendation: analyze input text and suggest the most appropriate Braille grade for the content type.
3. BRF preview: render a screen-side visual simulation of the embossed output so sighted reviewers can evaluate layout.
4. EBAE deprecation flag: warn when EBAE is selected and note that UEB is the current BANA standard.
5. Embosser profile integration: allow selection of common embosser page sizes (11x11, 11x17) so line wrapping matches the target device.

---

### 8. Document Chat

**What It Does**

Document Chat provides an AI-powered conversational interface for asking questions about an uploaded document. It supports tool calling for structured extraction, image description for uploaded image files, and context-aware responses using the full document content. It allows users to interrogate a document without reading it linearly.

**Current State**

Fully operational when AI features are enabled. Supports document upload and session-scoped conversation. Supports image files for visual description questions. Uses an AI gateway with quota management and session hashing. Rate-limited and gating-protected for resource fairness.

**Inputs**

- Uploaded document (wide format support) or image file
- Conversational question (up to 2,000 characters per message)
- Session context from prior turns in the conversation

**Outputs**

- Conversational response grounded in the uploaded document
- Structured extracted data (when tool calls are invoked)
- Image descriptions for visual content

**Expected Outcomes**

- Authors interrogate complex documents for accessibility issues, unclear headings, or missing alt-text descriptions without reading end-to-end
- Practitioners quickly locate relevant sections, check for specific rule violations, or extract structured summaries
- New users ask plain-language questions and receive guidance without knowing rule IDs or WCAG criteria

**User Benefits By Level**

- New users: ask "does this document have a logical heading structure?" and receive a plain-language answer
- Practitioners: extract accessibility-specific summaries ("list every image and describe whether it has alt text") for fast pre-audit triage
- Specialists: query for specific WCAG criterion compliance or ask for remediation guidance grounded in the document content
- Managers: produce plain-language summaries of document quality for leadership communication
- Enterprise owners: use session quotas and gating to manage AI resource consumption at scale

**Projected Wins**

- 30 to 50 percent faster pre-audit triage for practitioners using conversational extraction
- 40 percent reduction in time for managers to produce plain-language accessibility summaries
- New access pathway for users who struggle with tabular finding reports

**Planned Enhancements**

1. Audit assistant mode: pre-populate chat with a structured question sequence that walks through every ACB rule category.
2. Multi-document comparison chat: upload two versions and ask comparative questions.
3. Actionable output from chat: convert a chat-identified issue into a formal Audit finding that can be exported to CSV or filed as a ticket.
4. Memory across turns: retain document context across a longer session without requiring re-upload.
5. Citation anchoring: link each chat response to the specific page, section, or heading in the source document.

---

### 9. Magic Lab

**What It Does**

Magic Lab is GLOW's advanced features area. It hosts capabilities that are powerful but require more context or configuration than the primary tools. Current capabilities include: pronunciation dictionary management (for Speech Studio), document comparison (diff two documents by content), table structure analysis, PDF reading order detection, PDF OCR, and a community rule contribution system.

**Current State**

Fully operational for all enabled features. Each sub-feature is individually governed by a feature flag. Pronunciation dictionary entries can be added, edited, imported from CSV, and exported. Document comparison supports all major formats and returns a structured diff. Table advisor analyzes HTML and Markdown table structures. Reading order detection identifies visual ordering problems in PDFs. OCR extracts text from scanned PDF pages. Rule proposals are collected and displayed for administrator review.

**Inputs**

- Pronunciation dictionary: word, phonetic replacement, language scope
- Document compare: two uploaded documents in any supported format
- Table advisor: HTML or Markdown table text (pasted directly)
- Reading order: uploaded PDF
- OCR: uploaded PDF (scanned pages)
- Rule proposal: rule description, rationale, and example submission

**Outputs**

- Pronunciation dictionary (managed list, CSV export/import)
- Document comparison result (structured diff with change categories)
- Table structure analysis (caption presence, header scope, relationship issues)
- Reading order report (detected visual ordering anomalies)
- OCR text extraction result
- Rule proposal queue for administrator review

**Expected Outcomes**

- Speech Studio narration quality improves as domain-specific pronunciation corrections accumulate
- Practitioners catch structural regressions between document versions before publishing
- Table authors identify accessibility failures in complex table markup before conversion
- PDF specialists detect and report reading order problems that screen readers would encounter

**User Benefits By Level**

- New users: pronunciation dictionary improves their synthesized audio quality without technical knowledge
- Practitioners: document comparison replaces manual file diffing for accessibility regression checks
- Specialists: table advisor and reading order tools expose structural issues that standard audit rules may not catch
- Managers: community rule proposals allow teams to extend GLOW's rule library from field experience
- Enterprise owners: feature flags allow Magic Lab to be scoped to specialist users only

**Projected Wins**

- 20 to 35 percent improvement in pronunciation accuracy for domain-specific narration
- 30 percent faster regression detection between document versions
- 25 percent reduction in table accessibility defects in published content that uses the table advisor

**Planned Enhancements**

1. Document compare: add accessibility-specific change highlighting (heading structure changes, alt-text changes, reading-order changes).
2. Table auto-fixer: from table advisor output, generate a corrected version with proper headers, captions, and scope attributes.
3. Pronunciation dictionary sharing: export a dictionary and import it into another GLOW instance for organizational consistency.
4. Reading order visualization: render a numbered overlay on the PDF page thumbnail showing the detected reading sequence.
5. OCR post-processing: run a lightweight Audit pass on extracted OCR text to identify accessibility issues in the extracted content.

---

### 10. Site Audit

**What It Does**

Site Audit crawls a website or list of URLs and evaluates each page for WCAG 2.2 and ACB accessibility issues using a combination of HTTP-fetch heuristics and axe-cli analysis. It supports crawl depth control, domain restriction, URL exclusion patterns, strict open-source mode, background job execution, protected result access with password, and per-finding WCAG learning resources.

**Current State**

Fully operational with background jobs, token-protected access, crawl configuration, strict mode, and learning resources. Results are downloadable as JSON and CSV. Background jobs can be cancelled and polled. Protected results require a share token and optional password.

**Inputs**

- Starting URL or comma-separated URL list
- Crawl depth limit
- Domain stay-on-site restriction
- URL exclusion patterns
- Strict mode flag (disables heuristics; axe-only findings)
- Run in background flag
- Protect with token flag and optional password
- Scan timeout per page

**Outputs**

- Per-page findings with severity, WCAG criterion, element selector, and help text
- Site-level summary with total finding counts by severity
- WCAG learning resource links per finding
- JSON and CSV downloads
- Protected share link with optional password unlock
- Background job status and cancellation endpoint

**Expected Outcomes**

- Developers identify accessibility issues on published or staging websites without dedicated tooling
- QA teams run site-level scans as part of pre-release verification
- Accessibility managers produce site-wide compliance snapshots for governance reporting
- Background mode enables large site scans that would otherwise time out in a synchronous request

**User Benefits By Level**

- New users: paste a URL and receive a site-wide finding summary in minutes
- Practitioners: depth and exclusion controls let them scope scans precisely to changed areas
- Specialists: strict mode removes heuristic noise for high-confidence axe-only findings
- Managers: protected share links allow results to be delivered to stakeholders without exposing the full admin interface
- Enterprise owners: background jobs scale to large crawls without blocking server resources

**Projected Wins**

- 30 to 50 percent detection lift on JavaScript-heavy pages through planned Playwright integration
- 25 to 40 percent reduction in time from site finding to actionable ticket through planned GitHub issue sync
- 2x improvement in repeat scan adoption through scan profiles and scheduled monitoring

**Planned Enhancements**

These are inherited from the prior Site Audit phase plan and remain valid.

1. Scan profiles (Quick, Baseline, Strict, Forms, Visual, Enterprise).
2. Rendered browser engine using Playwright and axe for JavaScript-heavy pages.
3. Hybrid scan mode combining fast heuristic scan with selective deep rendering.
4. Authenticated crawl support for scanning protected pages.
5. URL classification report showing scanned, skipped, excluded, and duplicate pages with reason codes.
6. Evidence pack with HTML snapshots, full-page screenshots, and element screenshots per finding.
7. Finding clustering and deduplication with stable finding signatures.
8. Exception registry with expiry, owner, and rationale fields.
9. Trend analytics dashboard for historical run comparison.
10. GitHub issue sync for converting findings to accountable work items.
11. SARIF export for CI gate integration.
12. Guided manual verification workbench for criteria that automation cannot evaluate.

---

### 11. Guidelines and Rules Reference

**What It Does**

Guidelines renders the ACB Large Print Guidelines as a navigable, searchable web reference. Rules Reference renders the full GLOW rule catalog with rule IDs, categories, severities, WCAG criterion mappings, and remediation descriptions. Together they provide the authoritative standards documentation that all other GLOW features enforce.

**Current State**

Fully operational. Guidelines is a rendered HTML version of the ACB spec. Rules Reference is dynamically generated from the Python constants module and always reflects the current rule set.

**Planned Enhancements**

1. Filterable Rules Reference: add category, severity, format, and profile filters so specialists can browse rule subsets relevant to their work.
2. Deep-link anchors: every rule and guideline entry has a stable anchor URL for sharing in tickets, comments, and documentation.
3. Examples per rule: each rule entry shows a compliant example and a non-compliant example with visual contrast.
4. Changelog annotation: surface which rules were added, changed, or removed in each GLOW release to help practitioners stay current.
5. Export rules subset: allow users to export a filtered rule set to PDF or Markdown for offline reference or inclusion in organizational standards documents.

---

### 12. Settings and Preferences

**What It Does**

Settings allows users to configure persistent preferences that are applied across all GLOW features. Current preferences include theme, default rule profiles, output format preferences, and feature visibility options. Preferences are stored in browser local storage and applied on every session.

**Current State**

Operational. Preferences apply to the current browser and session. No server-side account storage exists in the base configuration.

**Planned Enhancements**

1. Preference export and import: serialize all preferences to a JSON file for backup or sharing across devices.
2. Named preference profiles: save multiple named configurations (for example, ACB Strict for document work, Quick Scan for site reviews) and switch between them with one click.
3. Tutorial mode toggle: allow first-time users to enable or disable guided tooltips and onboarding flows from Settings.
4. Keyboard shortcut reference: surface all available keyboard shortcuts for GLOW in a dedicated Settings panel.
5. Accessibility self-check: run a brief check of the user's current GLOW configuration and flag any settings that may reduce accessibility of the outputs they produce.

---

### 13. Admin and Governance

**What It Does**

The Admin area provides feature flag management, AI configuration, analytics, feedback review, and access queue management. Feature flags control which GLOW capabilities are available in a given deployment. Analytics surfaces usage patterns to inform capacity and feature planning. The access queue manages requests for elevated features.

**Current State**

Fully operational. Includes admin login, feature flag toggles with live effect, AI model and quota management, speech metrics, usage analytics, admin AI configuration, and feedback review.

**Planned Enhancements**

1. Audit log for feature flag changes: record when flags were toggled, by whom, and from what prior state.
2. Per-feature usage dashboards: show usage volume, error rates, and average processing times per feature for operational monitoring.
3. API key health indicators: surface the status of configured external API keys (OpenRouter, webhook endpoints) with last-success timestamps.
4. Role-based access tiers: add a reviewer tier with read access to analytics and feedback without full admin privileges.
5. Deployment health scorecard: a summary page showing all configured integrations, their status, and outstanding maintenance recommendations.

---

## Full Feature Matrix

The following table is the canonical cross-feature planning reference. It summarizes current state, primary planned enhancement, and projected win for every GLOW feature area.

| Feature Area | Current State | Primary Planned Enhancement | Projected Win |
| --- | --- | --- | --- |
| Document Audit | Production | Structured finding IDs and SARIF export | 30 percent faster CI integration |
| Document Fix | Production | Annotated diff view and selective fix confirmation | 40 percent reduction in user hesitation before applying fixes |
| Convert and Export | Production | Batch conversion with manifest and conversion quality report | 50 percent faster multi-format delivery |
| Template Builder | Production | Template library and PowerPoint and Excel template support | 60 to 80 percent fewer formatting findings on template-originated documents |
| Speech Studio | Production | Batch synthesis and SSML preview | 40 percent reduction in narration production time |
| BITS Whisperer | Production | Speaker diarization and caption export | New captioning workflow accessible in one step |
| Braille Studio | Production | Batch BRF production and embosser profile integration | 40 percent reduction in BRF production time |
| Document Chat | Production (AI-gated) | Audit assistant mode and actionable output | 30 to 50 percent faster pre-audit triage |
| Magic Lab | Production | Reading order visualization and table auto-fixer | 25 percent reduction in structural defects in published tables |
| Site Audit | Production | Playwright rendered engine and scan profiles | 30 to 50 percent detection lift on dynamic pages |
| Guidelines | Production | Deep-link anchors and per-rule examples | 20 percent reduction in rule interpretation errors |
| Rules Reference | Production | Filterable browsing and rules subset export | 30 percent faster profile customization |
| Settings | Production | Named preference profiles and preference export | 20 percent improvement in returning user setup time |
| Admin | Production | Audit log and per-feature dashboards | Operational visibility to support SLA management |

---

## UX Redesign: From Tab Sprawl to Mission-Oriented Navigation

### Problem

GLOW currently exposes its features as a horizontal tab bar. The current navigation includes: Audit, Fix, Convert, Template, Speech, Whisperer, Braille, Chat, Magic Lab, Site Audit, Guidelines, Rules, Settings, and admin links. This is thirteen or more tabs. On a standard desktop viewport this is visually dense. On a narrow laptop or tablet it wraps or overflows. On mobile it is unusable without a separate menu pattern.

Beyond width, the current IA organizes features by product name rather than user intent. A user who wants to make a Word document accessible for a low-vision reader must discover that the relevant features are Audit, Fix, Template, and Speech — none of those labels reveal that connection.

### Design Objective

Replace horizontal tab sprawl with a mission-oriented information architecture that:

1. Organizes navigation by what the user is trying to accomplish, not by feature name.
2. Scales vertically instead of horizontally so the design does not degrade as features grow.
3. Uses progressive disclosure to make defaults simple and advanced controls discoverable but not overwhelming.
4. Works on narrow viewports and mobile screens without separate breakpoint hacks.
5. Creates a clear place for AI features to appear contextually rather than as another top-level tab.

### Proposed Navigation Structure

#### Top-Level Navigation Groups

The navigation collapses thirteen tabs into five groups. Each group is a distinct user goal.

1. **Assess** — Is this content accessible?
   - Document Audit (single file or batch)
   - Site Audit (URL or crawl)

2. **Fix and Build** — Make content accessible.
   - Document Fix
   - Template Builder

3. **Transform** — Change the form of content.
   - Convert and Export (Markdown, HTML, DOCX, EPUB, PDF, DAISY)
   - Braille Studio (text to BRF and back)

4. **Listen and Speak** — Access and produce audio.
   - Speech Studio (text and document to audio)
   - BITS Whisperer (audio to text)

5. **Explore and Learn** — Reference, query, and configure.
   - Document Chat
   - Magic Lab
   - Guidelines
   - Rules Reference
   - Settings

This organization reduces navigation cognitive load from thirteen discrete labels to five goal-oriented groups. Each group is legible to a user who does not know the product before they arrive.

#### Mission Hub Home Page

The home page replaces the current generic landing with a mission hub. It shows five large action cards, one per navigation group, each with:

1. A one-sentence description of what the group accomplishes.
2. Two or three quick-launch entry points directly to the most common sub-feature.
3. A status indicator if any feature in the group is gated, restricted, or unavailable.

The home page is the primary orientation surface for new users and the fastest way for experienced users to jump to a feature without navigating a tab bar.

#### Left Sidebar Navigation (Replacing Horizontal Tabs)

The primary nav moves from a horizontal tab bar to a collapsible left sidebar. Behavior:

1. Sidebar is open by default on desktop viewport widths above 1024px.
2. Sidebar collapses to icons on viewports between 640px and 1024px.
3. Sidebar becomes a slide-over drawer on viewports below 640px, triggered by a hamburger button.
4. Each nav group is an expandable section; clicking the group label opens its sub-features inline.
5. The current route is highlighted within its group for clear location awareness.

This design scales to any number of future features without introducing visual congestion in the header.

#### Contextual Right Panel

When a user is working inside a tool (for example, reviewing Document Audit results), a contextual panel appears on the right or below the main content area. It contains:

1. What this feature does (one sentence, dismissible after first read).
2. Quick-action links relevant to the current result: export, share, open in Fix, open in Convert.
3. Related features: if reviewing an Audit result, the panel suggests Fix and Document Chat as next steps.
4. AI assist entry point (when enabled): a compact inline prompt entry for asking a question about the current result.

This eliminates the need for the user to navigate away to take the most logical next action.

#### Progressive Disclosure In Forms

Every feature form applies the same progressive disclosure pattern:

1. The primary input (upload or URL) is prominent and immediately usable with one action.
2. Basic options (profile or voice or grade selection) appear immediately below the primary input.
3. Advanced options (rule overrides, depth controls, synthesis fine-tuning, auth context) are collapsed behind an "Advanced" disclosure toggle.
4. A "What does this option do?" link appears next to every non-obvious control. It opens an inline help tooltip, not a new page.

This pattern applies to Document Audit, Document Fix, Convert, Template, Speech Studio, Whisperer, Braille Studio, and Site Audit.

#### AI Features as Contextual Modules

AI features do not get their own top-level tab. They appear as:

1. Inline assist panels within existing feature results (Audit results, Site Audit findings, Chat).
2. A "Draft fix suggestion" action on individual Audit findings (feature-flagged).
3. The Document Chat feature within the Explore and Learn group.
4. Magic Lab as the home for AI experiments and advanced AI tools.

This prevents AI-era features from creating a new round of tab sprawl as they mature.

### Why This Structure Wins Across All GLOW Features

1. **Document workflows**: Users who arrive to fix a Word document for a low-vision reader land on "Fix and Build" and find both Fix and Template. They do not need to know both feature names before they arrive.
2. **Site reviewers**: Users who want to check a website land on "Assess" and find Document Audit and Site Audit together, which correctly implies both are assessment tools.
3. **Audio workflows**: Users producing audio content land on "Listen and Speak" and find both synthesis (Speech Studio) and transcription (Whisperer) without needing to know the product names.
4. **Braille and specialist needs**: The Transform group correctly pairs format conversion with Braille translation, since both are about changing the form of content for a different channel.
5. **Discoverability**: Magic Lab and Document Chat are surfaced under "Explore and Learn" alongside Guidelines and Rules Reference, which correctly signals that they are for investigation and learning, not primary production workflows.
6. **Mobile and narrow screen usability**: The sidebar design works at every viewport. No feature is unreachable below a certain screen width.

### What Does Not Change

1. Feature URLs remain stable. Navigation is a shell change; no route moves.
2. All existing keyboard navigation patterns remain.
3. Feature flags continue to control individual feature availability.
4. The admin section retains its separate authentication boundary.

---

## AI Roadmap Across All Features

AI features in GLOW are activated by feature flags and available only when the operator configures an API key. The following describes how AI capabilities expand across every feature area when enabled.

### Document Audit

1. Alt-text suggestion: already live for image-bearing documents. Expand to suggest caption text, table summaries, and figure descriptions.
2. Plain-language finding explanation: replace technical rule messages with one-sentence plain-language explanations appropriate to user skill level.
3. Severity reasoning: explain why a specific finding was rated critical versus high, grounded in the document content.

### Document Fix

1. Draft fix confirmation: before applying a fix, show an AI-generated explanation of what will change and why.
2. Residual fix suggestions: for findings that cannot be auto-fixed, generate a specific, actionable suggestion that the user can apply manually.
3. Fix quality scoring: after applying fixes, generate a confidence score for each applied change and flag low-confidence changes for human review.

### Convert and Export

1. Conversion quality commentary: after conversion, generate a brief AI assessment of whether the converted output preserves the semantic accessibility structure of the source.
2. Missing metadata completion: suggest document title, language, and author metadata if any are absent from the source document.

### Template Builder

1. Template recommendation: based on the user's described document purpose, recommend a template configuration with pre-selected heading levels, sizes, and standards profile.
2. Template review: after generating a template, provide a one-paragraph review of how well it supports accessible authoring.

### Speech Studio

1. Synthesis pre-check: before synthesizing a long document, identify sections likely to render poorly (tables, code, special characters) and suggest simplifications.
2. Pronunciation review: after synthesis, flag words where the engine's rendering diverged significantly from expected pronunciation and suggest dictionary entries.

### BITS Whisperer

1. Transcript cleanup: post-process the raw transcription to normalize punctuation, remove filler words, and apply consistent capitalization for accessibility-ready text.
2. Accessibility check on transcript: run a lightweight finding pass on the transcript and summarize any accessibility concerns in the text before download.

### Braille Studio

1. Grade guidance: based on content analysis, recommend the most appropriate Braille grade for the target audience.
2. Round-trip accuracy explanation: when a reverse-translated result differs from the original, explain the linguistic reasons for the divergence.

### Document Chat

1. Structured audit extraction: add a predefined "Run Accessibility Audit Chat" mode that walks through every ACB rule category as a structured conversation.
2. Citation-grounded responses: every response cites the specific document section or paragraph it references.
3. Actionable output: a "Log this as a finding" button converts any chat-identified issue into a formal Audit finding for export.

### Magic Lab

1. Document compare: add an accessibility-specific diff mode that highlights heading structure changes, alt-text additions and removals, and reading-order anomalies.
2. Table advisor suggestions: move from analysis to direct correction suggestions, with a "Apply fix" action.
3. Rule proposal quality scoring: review submitted rule proposals and provide an AI-generated feasibility and quality assessment for the administrator.

### Site Audit

1. Finding summary per page: generate a one-paragraph plain-language summary of each scanned page's accessibility posture.
2. Remediation campaign draft: group findings by rule, generate a prioritized remediation queue, and draft GitHub issues for each group.
3. Trend anomaly detection: identify statistical outliers in trend data and surface them as alerts.

---

## Delivery Waves

This sequencing prioritizes UX foundation first, then feature deepening, then AI expansion. Each wave delivers standalone value.

### Wave 1: Navigation and Structure (Foundations)

Priority: Highest. This wave creates the new shell that every subsequent feature drops into.

1. Implement left sidebar navigation replacing horizontal tabs.
2. Build mission hub home page with five goal-oriented group cards.
3. Apply progressive disclosure pattern to all major feature forms.
4. Add contextual right panel with next-step suggestions to Audit and Site Audit result pages.
5. Implement mobile slide-over drawer for sub-640px viewports.

### Wave 2: Document Feature Depth

Priority: High. These enhancements increase output quality and user confidence across the most-used features.

1. Document Audit: structured finding IDs, SARIF export, comparative audit mode.
2. Document Fix: annotated diff view, selective fix confirmation.
3. Convert: batch conversion with manifest, conversion quality report.
4. Template: template library with save, name, and share.

### Wave 3: Media and Specialist Features

Priority: High for target audiences. Serves audio, Braille, and advanced specialist users.

1. Speech Studio: batch synthesis, SSML preview, chapter-level audio package.
2. BITS Whisperer: caption export (SRT and WebVTT), speaker diarization.
3. Braille Studio: batch BRF production, embosser profile selection.
4. Magic Lab: reading order visualization, table auto-fixer, document compare accessibility diff.

### Wave 4: Site Audit Quality and Scale

Priority: High for developer and QA audiences.

1. Scan profiles (Quick, Baseline, Strict, Forms, Visual, Enterprise).
2. Playwright rendered engine and hybrid mode.
3. Authenticated crawl support.
4. URL classification report.
5. Evidence pack.
6. Finding clustering and deduplication.

### Wave 5: Governance and Integration

Priority: Medium for enterprise and team audiences.

1. Exception registry with expiry across Document Audit and Site Audit.
2. GitHub issue sync for Site Audit findings.
3. SARIF export and CI gate for Site Audit.
4. Trend analytics dashboard.
5. Failure density metric.
6. Admin audit log and per-feature dashboards.

### Wave 6: AI Expansion

Priority: Medium, feature-flag gated throughout.

1. Expand alt-text suggestion to captions, table summaries, and figure descriptions in Document Audit.
2. Plain-language finding explanations across Document Audit and Site Audit.
3. Residual fix suggestions in Document Fix.
4. Transcript cleanup and accessibility check in BITS Whisperer.
5. Document Chat structured audit extraction mode.
6. Site Audit finding summary and remediation campaign draft.

### Wave 7: Deep AI and Personalization

Priority: Lower priority, long-term.

1. Audit assistant mode in Document Chat with citation anchoring.
2. Rule proposal quality scoring in Magic Lab.
3. Trend anomaly detection in Site Audit analytics.
4. Named preference profiles and accessibility self-check in Settings.
5. Per-feature usage dashboards in Admin.

---

## Risks and Mitigations

1. Risk: Navigation restructuring breaks user familiarity.
   - Mitigation: stable feature URLs, clear redirect notices for any changed paths, user testing before deployment.

2. Risk: Feature groupings do not match all user mental models.
   - Mitigation: run a card-sort exercise with a small sample of real users before finalizing group labels.

3. Risk: AI features increase complexity and user confusion about what is automated vs. manual.
   - Mitigation: every AI output carries a confidence label and a clear "human review required" indicator. No action is automatic without explicit user confirmation.

4. Risk: Feature flags create fragmented experiences across deployments.
   - Mitigation: the mission hub home page adapts to show only available features. Unavailable features display a clear unavailability message rather than a broken state.

5. Risk: Wave delivery sequence stretches too long before users see navigation improvement.
   - Mitigation: Wave 1 is scoped tightly to navigation shell only. It can ship without any feature changes and delivers immediate UX value independently.

---

## Measurement Framework

The following table maps product goals to measurable operational indicators across all features.

| Goal | Primary Metric | Supporting Metric | Success Threshold |
| --- | --- | --- | --- |
| Navigation usability | Feature-reach time (from home to first result) | Navigation error rate (wrong feature selected) | 30 percent reduction in reach time and 25 percent reduction in navigation errors |
| Document Audit quality | Confirmed issue yield per document upload | Escaped defect count in distributed documents | 30 percent yield lift and 20 percent escaped defect reduction |
| Document Fix adoption | Percentage of Audit sessions that proceed to Fix | Manual fix time after Fix is applied | 25 percent increase in Audit-to-Fix conversion rate |
| Convert completeness | Successful conversion rate across all format pairs | Post-conversion Audit finding count | 95 percent successful conversion rate and 20 percent fewer post-conversion findings |
| Speech quality | Pronunciation accuracy on domain vocabulary | User retry rate on synthesis | 20 percent improvement in pronunciation accuracy and 15 percent reduction in retries |
| Transcription utility | Caption export adoption rate | Transcript-to-Audit chaining rate | 20 percent of transcriptions proceed to caption export or Audit |
| Site Audit coverage | Confirmed finding yield on JS-heavy pages | Escaped defect count on scanned sites | 30 to 50 percent yield lift on dynamic pages |
| User onboarding | First-run task completion rate | Time to first meaningful result | 40 percent improvement in first-run completion and 30 percent reduction in time-to-result |
| AI feature trust | Accepted AI suggestion rate | Rollback rate on AI-applied changes | Accept rate above 70 percent and rollback rate below 10 percent |

---

## Implementation Readiness Checklist

1. Validate proposed navigation groups with a card-sort user test before building.
2. Define and freeze the five group labels and membership rules.
3. Define the contextual right panel content model for each feature result page.
4. Confirm stable feature URL contracts so navigation restructuring does not break existing links.
5. Define the normalized finding ID schema that spans Document Audit, Document Fix, and Site Audit.
6. Define the progressive disclosure pattern library (primary input zone, options zone, advanced drawer) as reusable template components.
7. Define the AI confidence label vocabulary and display standards before expanding AI features.
8. Confirm feature flag behavior for the mission hub home page (graceful degradation when features are unavailable).
9. Define the audit log schema for admin governance enhancements.
10. Validate that all planned Braille enhancements work within the liblouis availability constraints.

---

## Final Recommendations

Execute this plan in the wave order defined above, beginning with the navigation shell in Wave 1. That wave delivers the highest leverage per unit of effort: it improves every feature simultaneously without touching any feature's logic.

Document feature depth in Wave 2 and media features in Wave 3 address the most underserved current users: practitioners who need stronger evidence and specialists who need Braille, audio, and conversion quality improvements.

Site Audit quality improvements in Wave 4 raise GLOW's competitiveness as a web accessibility scanning tool. Governance in Wave 5 transforms it from a scan tool into an accountability platform.

AI expansion in Waves 6 and 7 builds on a stable, trusted foundation. Every AI feature ships behind a flag and with explicit human review requirements. Trust is built incrementally from the lowest-risk suggestions outward.

The result is a platform where every user, from a first-time author pasting text into Speech Studio to an enterprise platform owner monitoring site-wide accessibility trends, finds a clear path to their goal and receives results they can act on with confidence.
