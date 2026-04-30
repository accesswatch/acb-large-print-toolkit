# GLOW 2.8.0: Built by the Community, for the Community

**FOR IMMEDIATE RELEASE — April 30, 2026**

---

> *"What we are doing with GLOW isn't just building a tool. We are building infrastructure for dignity. Every inaccessible document is a door slammed in someone's face. GLOW is about kicking those doors open — permanently, systematically, and freely. And GLOW 2.8.0 is the most direct expression of that mission yet — because every single feature in this release came from you."*
>
> **— President, Blind Information Technology Solutions (BITS), American Council of the Blind**

---

The GLOW (Guided Layout & Output Workflow) Accessibility Toolkit v2.8.0 is now available.

This release is different from every release before it. Not because of the volume of what shipped — though that volume is significant. It is different because every feature in 2.8.0 came directly from the blind and low-vision community. From BITS members. From board members who need to share compliance reports without accidentally publishing sensitive documents. From organizations with house styles that don't match the ACB default. From people who asked, week after week: "Can Quick Start just take me all the way?"

The answer is yes. And this is the release that says it.

---

## A THANK YOU THAT BELONGS AT THE TOP

> *"GLOW exists because of this community. Not despite it, not around it — because of it. The feedback you gave us shaped every line of code in this release. We heard you about the second upload. We heard you about sharing reports with external reviewers safely. We heard you about your organization's different font sizes. We heard you about the findings table being overwhelming. We fixed every single one of those things. Thank you. Genuinely."*
>
> **— President, Blind Information Technology Solutions (BITS), American Council of the Blind**

To every BITS member, every low-vision reader, every AT user, every accessibility coordinator, every board secretary who has ever filed a compliance report — this release is yours. You asked for it. We built it. We hope it makes your work a little easier, a little faster, and a little less frustrating.

---

## WHAT'S NEW IN 2.8.0

---

### 1. Score and Grade Trust: Restored and Hardened

> *"One of the most important pieces of feedback we got was not about buttons or workflow. It was about trust. People asked: 'Can I trust this score? Can I trust this grade?' We took that seriously. We did deep work on scoring consistency in 2.8.0 so the answer is yes."*
>
> **— BITS President**

This was a significant pain point for teams using GLOW reports as evidence in board packets, policy sign-off, and external compliance reviews.

2.8.0 includes in-depth scoring refinements:

- Corrected edge cases where grade presentation could appear out of sync with underlying score math.
- Clarified and stabilized weighted-penalty behavior for repeated findings.
- Ensured grouped findings (single-row display with occurrence counts) remain a **presentation-only** improvement and do not alter score computation.
- Tightened pre/post reporting language so filtered displays are clearly distinguished from full post-fix scoring.

The outcome is simple: when GLOW says a document is a B, you can trust that result.

---

### 2. Quick Start Finally Goes All The Way

> *"The most common piece of feedback we heard was this: 'I love that I don't have to re-upload to fix and re-audit. But I still have to upload twice when I start from Quick Start.' We heard that. It is fixed."*
>
> **— BITS President**

GLOW introduced the Audit → Fix → Re-Audit single-upload cycle for the main workflow. But Quick Start — the first page most new users land on — still required a second upload when it handed off to Audit or Convert. That was a gap. 2.8.0 closes it completely.

Starting today:

1. Go to **Quick Start**.
2. Upload your document once.
3. Choose **Audit**, **Fix**, or **Convert**.
4. Your file is already there. The form says "Ready to audit: your-document.docx — no need to re-upload." No file picker. No wait. Just the options you need.

The complete GLOW workflow — Quick Start, Audit, Fix, Re-Audit, Convert — now requires exactly one upload. Your session stays active for up to one hour.

---

### 3. Passphrase-Protected Shared Reports

> *"We had organizations telling us: 'We love the shareable link. But we can't use it. The report has member names. We can't send a URL that anyone with the link can open.' That is a completely valid concern and we had no good answer for it until now."*
>
> **— BITS President**

Shared audit reports can now be protected with a passphrase.

Set it in the new **Share Link Protection** section at the bottom of the Audit form before you run your audit. Four characters minimum, two hundred characters maximum. Then share the link.

The same protection is available when you are in the **Fix → Re-Audit** path: the Re-Audit form on the Fix result page now includes an optional share passphrase field so reports generated from fixed documents can be protected the same way.

When your colleague opens the link, they see a clean unlock form asking for the passphrase. Enter it correctly and the full report opens. Enter it wrong and it stays locked. Download buttons for CSV and PDF are locked the same way.

What happens on the server:

- Your passphrase is immediately hashed with PBKDF2-SHA256 using 200,000 iterations and a random salt unique to your share.
- The cleartext passphrase is never stored. It is never logged. GLOW cannot recover it.
- The hash lives in the share cache directory alongside the report HTML, and it expires with the report after one hour.

**One practical note:** send your passphrase through a separate channel from the link. A text message, a phone call, a separate email. The whole point is that the link alone should not be enough.

This feature was requested by organizations handling member health data, legal correspondence, and financial compliance documents. It is now shipping for everyone.

---

### 4. Your Font Sizes, Not Just Ours

> *"ACB says 18pt body, 22pt Heading 1, 20pt subheadings. Those are the right defaults and we defend them. But we kept hearing from organizations with 20pt body policies, from people producing large-format poster content, from teams with established style guides that predate GLOW. They needed GLOW to work with their sizes, not against them. Now it does."*
>
> **— BITS President**

The Fix and Template forms now include a **Font Sizes** section where you can override the body point size and any heading level from H1 through H6.

Leave all fields blank and GLOW behaves exactly as it always has. Fill in one or more and GLOW uses your sizes everywhere:

- The **auditor** evaluates your document against your specified sizes instead of the ACB defaults.
- The **fixer** raises text to your specified sizes when applying corrections.
- The **template generator** builds the `.dotx` with your specified sizes pre-configured.
- **List Bullet** and **List Number** styles update to match your body size automatically.

Values are clamped to 8pt-96pt. The ACB defaults remain unchanged for anyone who does not set overrides.

This feature was requested by organizations with specific house styles. It ships today.

---

### 5. Findings Grouped by Rule

> *"We got feedback that audit reports on systematically broken documents — wrong font on every paragraph, no alt text on every image — were exhausting to read. Forty rows of 'Arial not used.' You couldn't find the structural problems underneath. We fixed the table."*
>
> **— BITS President**

Audit reports now group all occurrences of the same finding under a single row.

If your document has 40 paragraphs in Times New Roman, you see one row: "ACB-FONT-FAMILY — 40 occurrences — Show all." Click to expand and see the exact location of each one. Or address the rule and move on.

Single-occurrence findings still display inline as before. Multi-occurrence findings show a count badge and a `Show all N occurrences` disclosure.

The findings table is dramatically shorter. Important structural issues are no longer buried under dozens of formatting rows. CSV exports are unchanged — they still emit one row per occurrence so nothing is lost in your spreadsheet analysis.

This was requested by teams who process long documents with systematic formatting problems. It is live now.

---



## EVERYTHING THAT CAME BEFORE — THE FULL STORY

These features were introduced in earlier 2.x releases and remain core to GLOW today. If you are new to GLOW or sharing this announcement with someone who is, this is the full picture.

---

### One Upload. The Whole Cycle.

Upload your document once. Audit it. Fix it without re-uploading. Re-audit the fixed file without re-uploading. The diff banner at the top of the re-audit tells you exactly what changed: score delta, grade change, which rules were resolved, and whether any new issues were introduced.

Your document session stays active for one hour. The complete compliance cycle — audit, fix, confirm — requires exactly one upload.

---

### Shareable Reports. PDF Downloads. CSV Exports.

Every audit generates a shareable link to the rendered HTML report. The link contains only the report — never the original document. It expires in one hour.

Alongside the link: **Download PDF** for board packets and compliance files. **Download CSV** for spreadsheets and project trackers. Three formats, one click each.

And now in 2.8.0: protect any of those with a passphrase if you need to.

---

### The Compliance Grade That Speaks First

Every audit report leads with a letter grade — A through F — displayed large at the top, before the score, before the table. Three seconds to know if a document is accessible or not. Color-coded. Unmistakable.

The Fix result shows before-and-after grades side by side. The re-audit diff shows the grade change alongside the score change.

---

### Quick Wins: The Fastest Path to a Better Score

The Quick Wins bar above the findings table shows how many of your findings can be auto-fixed. One click filters the table to those findings only. Another click takes you to Fix with your document already loaded.

For organizations triaging long findings lists under deadline pressure, this surfaces the highest-return actions first.

---

### Inline Rule Explanations

Every rule ID in the findings table is a click-to-expand disclosure. Open it to see the canonical rule description, the ACB guideline reference, and a plain-language "Why this matters" rationale. Auto-fixable rules show an "Auto-fixable" badge. No leaving the page. No searching the documentation separately.

---

### A Rules Reference for Every Rule

`/rules/` — a searchable, deep-linkable browser for every audit rule across Word, PowerPoint, Excel, Markdown, PDF, and EPUB. Severity badges, profile membership, help links, extended rationale, and suppression guidance for each one.

---

### Convert Anything. Preview It. Audit It.

The Convert page accepts PowerPoint, Excel, PDF, CSV, JSON, HTML, and XML as input alongside the standard Markdown and Word formats. GLOW automatically runs two-stage conversion: MarkItDown extracts content to Markdown, then Pandoc applies ACB Large Print formatting.

The Convert result shows an inline preview for HTML output. A Copy to Clipboard button for CMS Fragment output. And an "Audit This Document" card that takes you to a compliance report on the converted file with one click.

---

### Heading Detection: Real Headings From Faux Headings

Many documents use bold or large text to look like headings instead of Word's actual Heading styles. Screen readers cannot navigate them. GLOW can find and convert those visual headings into real semantic heading styles.

Ten-signal heuristic scoring plus optional AI refinement. The Heading Review page lets you confirm or adjust every candidate before fixes are applied. Accuracy modes from Conservative to Thorough. Available in the web app and desktop CLI.

---

### Dark Mode. Focused Layout. Reliable Focus Indicators.

**Dark mode** — choose Light, Dark, or Auto (follow system) from the footer or Settings. Stored per-browser. Applied before first paint with no flash. Full WCAG 2.2 AA contrast throughout. Print output always uses the light ACB palette.

**Centered layout on wide viewports** — the body is horizontally centered with a max-width of `min(82rem, 100%)`. Long-prose paragraphs use a 70-character reading measure. Cards, tables, and forms use the full width.

**Reliable focus indicators** — every interactive element has a 3px solid outline plus a layered white-and-blue halo on `:focus-visible`. Windows High Contrast and dark mode both handled. A CSS guard test fails the build if a future change suppresses the focus ring.

---

### Coverage Across Every Format

| Format | What GLOW checks |
|--------|----------------|
| Word (.docx) | Fonts, sizes, spacing, emphasis, alignment, margins, headings, alt text, table headers, document properties, language, link text |
| Excel (.xlsx) | Sheet names, table headers, merged cells, alt text, color-only data, hyperlink text, workbook title, blank-row patterns |
| PowerPoint (.pptx) | Slide titles, reading order, alt text, font sizes, notes, chart descriptions, timing and animation safety |
| Markdown (.md) | YAML front matter, heading hierarchy, emphasis violations, link text, alt text quality, emoji, em-dashes, tables, code blocks |
| PDF (.pdf) | Title, language, tagging, font sizes, scanned pages, bookmarks, form fields |
| ePub (.epub) | Title, language, navigation, headings, alt text, table headers, accessibility metadata, MathML — plus DAISY Ace (100+ axe-core rules) |

---

### BITS Whisperer: Audio to Accessible Document

Upload a meeting recording, a conference call, a voice memo. GLOW transcribes it to Markdown or Word using server-side Whisper integration, complete with cleanup and normalization. Choose background mode for long recordings; get an email when it is done.

---

### Document Chat: Ask Anything About Your Document

Upload a document and ask questions in plain language. GLOW's Document Chat answers in the context of your actual file — structure, compliance, content. Export the conversation to Markdown, Word, or PDF.

---

### Deployment You Can Trust

Automated deployment with automatic rollback on Docker health failure. Maintenance mode toggle for zero-downtime deploys. WSL pre-production staging. Timestamped deploy logs. `POST /health` validation before maintenance lifts. Whisper model pre-warmed before first users arrive.

---

## WHAT COMES NEXT: GLOW 3.0.0 AND THE SPEECH PLATFORM

> *"We have been asked, more times than I can count, whether GLOW can produce audio versions of documents. Board minutes someone can listen to on their commute. A newsletter read aloud. A training handout in MP3 format. We have heard you. We are building it."*
>
> **— BITS President**

GLOW 3.0.0 will introduce a self-hosted text-to-speech platform powered by Kokoro ONNX — a CPU-only TTS engine that produces high-quality MP3 audio from document content without requiring a GPU, without sending content to third-party cloud services, and without per-request API costs.

The speech platform will include:

- **Preview generation** — hear the first 8 seconds before committing to a full generation job
- **Async processing** — long documents queue in the background with position tracking and email notification
- **Customizable voice and speed** — pre-configured voice profiles, adjustable speaking rate
- **GLOW integration** — "Listen to this report" on audit results; "Download as audio" alongside HTML/Word/PDF on Convert results; a full BITS Whisperer → TTS round-trip pipeline (transcribe audio, edit, re-synthesize)
- **CPU-first architecture** — runs on the same server GLOW runs on today; no GPU required

The Kokoro engine runs at approximately 0.8-1.5x realtime on a modern CPU. A 2-minute audio clip from 300 words generates in under 3 minutes on a standard server. The full technical specification is in `docs/speech.md` and the `GLOW 3.0.0 Speech Platform` section of the PRD.

This is not a distant roadmap item. It is the next planned major release. We will share progress updates as development proceeds.

---

## A NOTE ON COMMUNITY, ATTRIBUTION, AND GRATITUDE

> *"Open source works because people share. Jamal Mazrui shared. His extCheck and xlHeaders tools directly shaped GLOW's Excel and extension-based accessibility checks. That is how this community is supposed to work — building on each other's shoulders, giving credit, and making the next tool better than the last. We are grateful."*
>
> **— BITS President**

GLOW acknowledges the foundational work of **Jamal Mazrui** and his projects [extCheck](https://github.com/jamalmazrui/extCheck) and [xlHeaders](https://github.com/jamalmazrui/xlHeaders). GLOW's Excel header remediation helper and extension-type checking patterns draw direct inspiration from this work.

And to the BITS community and the broader blind and low-vision community: every feature in GLOW 2.8.0 exists because you told us what you needed. You filed the issues. You sent the emails. You described your workflows. You explained why re-uploading three times was a barrier, why passphrase protection mattered to your organization, why your font sizes were different, why the findings table was overwhelming. We listened. We built. We are grateful.

GLOW is free. It is open source. It is built for you and with you. That does not change.

---

## THE NUMBERS

| | v2.5.0 | v2.6.0 | v2.7.0 | v2.8.0 |
|---|---|---|---|---|
| New audit rules | ~30 | ~40 | — | — |
| New web routes | 8 | 5 | 10 | 3 |
| New test cases | 40+ | 30+ | 22 | 10 |
| Templates updated | 18+ | 8 | 7 | 6 |
| Document formats covered | 6 | 6 | 6 | 6 |
| New security features | — | — | — | 1 (passphrase-protected shares) |
| Community-requested features | — | — | — | 4 of 4 |
| Test suite (web) | passing | passing | 266 passed, 20 skipped | **276 passed, 20 skipped** |

---

## GET GLOW

GLOW is **free and open source**, available now at:

**[https://glow.bits-acb.org](https://glow.bits-acb.org)**

Source code, desktop tool, CLI, and VS Code agent toolkit:

**[https://github.com/accesswatch/acb-large-print-toolkit/releases/tag/v2.8.0](https://github.com/accesswatch/acb-large-print-toolkit/releases/tag/v2.8.0)**

---

> *"To every person who has ever struggled to read a PDF that was never designed for them, an agenda formatted in 10pt Times New Roman, a spreadsheet that a screen reader couldn't parse — this work is for you. GLOW exists because you deserve better. Every feature in this release, every line of code, every test — all of it was built because you asked for it and because you deserve tools that actually work for you. We are just getting started."*
>
> **— President, Blind Information Technology Solutions (BITS), American Council of the Blind**

---

*GLOW is a project of Blind Information Technology Solutions (BITS) of the American Council of the Blind. Questions, feedback, and contributions are welcome through the [Feedback](https://glow.bits-acb.org/feedback) page.*
