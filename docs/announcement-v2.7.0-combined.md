# GLOW Is Glowing: Everything We've Built, and What It Means for Accessible Documents Everywhere

**FOR IMMEDIATE RELEASE — April 29, 2026**

---

> *"What we are doing with GLOW isn't just building a tool. We are building infrastructure for dignity. Every inaccessible document is a door slammed in someone's face. GLOW is about kicking those doors open — permanently, systematically, and freely. What this team has built in the last two months is nothing short of extraordinary."*
>
> **— President, Blind Information Technology Solutions (BITS), American Council of the Blind**

---

The GLOW (Guided Layout & Output Workflow) Accessibility Toolkit has shipped three major releases in rapid succession — versions 2.5, 2.6, and 2.7 — and the cumulative result is a transformation of what it means to audit and remediate documents for accessibility. This is the announcement that puts all of it together.

What started as a capable but fragmented workflow has become something genuinely compelling: a unified, end-to-end accessibility pipeline that catches problems in Word, PowerPoint, Excel, Markdown, PDF, and EPUB documents — and then helps you fix them, verify them, convert them, share the proof, and do it again without ever uploading a file twice.

Let us show you what we built.

---

## THE HEADLINE FEATURES — THE ONES THAT CHANGE EVERYTHING

---

### 1. Upload Once. Audit. Fix. Re-Audit. Done.

> *"I want you to picture the old world for a moment. You audit a document, download the report, upload the same file again to fix it, download the fixed version, upload it a third time to confirm it worked. Three uploads. Three waiting screens. Three moments where someone gives up and sends the inaccessible version anyway. That stops today."*
>
> **— BITS President**

GLOW 2.7.0 introduces a fully streamlined Audit → Fix → Re-Audit loop. Upload your document once. Click **Fix This Document** on the audit report — your file is already there, no re-upload. Fix it. Click **Re-Audit Fixed Document** — still no re-upload. Get the new report instantly, with a before-and-after comparison showing exactly how much improved.

Your document session stays active for up to one hour. The entire compliance cycle — upload, audit, fix, confirm — requires exactly one upload.

This is the single most impactful workflow change in GLOW's history.

**New in 2.7.0:**
- `GET /fix/from-audit/<token>` — Fix form pre-loaded with your document
- `POST /audit/from-fix` — Re-audit the fixed file inline
- `POST /audit/from-convert` — Audit a freshly converted document with one action
- Before/after **diff banner** on every re-audit: score delta, grade change, which rule IDs were fixed, and any newly-introduced issues

---

### 2. Shareable Proof. PDF Downloads. CSV Exports.

> *"Accessibility is not just about the document. It's about accountability. When you can send a compliance report to a board member, a funder, or a regulator — with a single link, or a PDF they can file — that changes the conversation. GLOW now gives you that. The report, the evidence, the paper trail. All of it."*
>
> **— BITS President**

Every audit report in GLOW 2.7.0 generates a shareable link containing only the rendered HTML report — never the original document. Anyone with the link can view the report. No login required. It expires after one hour.

But we didn't stop at a link.

The **Download PDF** button renders a print-styled PDF of the full report, ready to attach to a board packet, compliance submission, or archival file. The **Download CSV** button exports every finding — severity, rule ID, message, location, ACB reference, auto-fix flag, help links — as a UTF-8 BOM CSV that opens cleanly in Excel and drops directly into your tracking spreadsheet or project management system.

Three formats. One click each. No copying, no screenshots, no reformatting.

---

### 3. The Rules Reference: Every Rule Explained, In Place

> *"The worst moment in an accessibility audit is when a report tells you something is wrong and you don't know why it matters. GLOW used to do that. It doesn't anymore. We now tell you what the rule is, why it matters for people with disabilities, what the ACB standard requires, and — when the tool can fix it — we tell you that too. Right there, inline, without leaving the page."*
>
> **— BITS President**

GLOW shipped a dedicated **Rules Reference page** (`/rules/`) — a searchable, filterable browser for every audit rule across Word, PowerPoint, Excel, Markdown, PDF, and EPUB. Every rule has a severity badge, profile membership, help links, extended rationale, suppression guidance, and a deep-linkable anchor.

GLOW 2.7.0 goes further: every rule ID in the findings table is now a **click-to-expand disclosure**. Open it to see the canonical description, ACB reference, and plain-language "Why this matters" rationale — without leaving the page or losing your place in a long findings list. Auto-fixable rules show an "Auto-fixable" badge inside the disclosure.

---

### 4. PowerPoint, Excel, Markdown, PDF, EPUB — All Covered, All Deeper

> *"When I say GLOW audits your documents, I mean all your documents. Not just Word files. The board deck you send to members. The spreadsheet with the program data. The Markdown content going into your website. The PDF from the printer. We have been systematically closing every gap, and this represent the most comprehensive expansion of coverage this toolkit has ever shipped."*
>
> **— BITS President**

**PowerPoint:**
- Fast auto-advance detection (slides changing before users can read them)
- Repeating animations that trigger without user control
- Rapid-fire animation sequences that overwhelm processing
- Fast slide transitions
- Missing slide titles, missing alt text on images, contrast issues
- Reading-order problems that scramble screen-reader output

**Excel:**
- Blank header cells in data tables
- Merged cells that break screen reader navigation
- All-uppercase header text
- Missing sheet descriptions
- Frozen panes at inaccessible scroll positions
- New `xlheaders` table-header remediation helper, inspired directly by Jamal Mazrui's open-source xlHeaders tool

**Markdown:**
16 new checks including:
- Alt text quality (filename alt, redundant prefixes, too-short)
- YAML front matter validation (missing block, unclosed fence, missing `title:`, missing `lang:`)
- Heading quality checks (empty headings, headings too long, punctuation-ended headings)
- Code block language identifiers
- Full help-link coverage for every rule in the web app

**PDF:**
- Smarter image-based PDF detection using coverage area (avoids false positives from decorative images)
- Resolution check: flags scanned pages below 150 DPI with OCR remediation guidance
- Classifies documents as entirely scanned, majority-scanned, or partially scanned

**EPUB:**
- EPUBCheck integration for authoritative package validation
- Findings mapped to `EPUBCHECK-ERROR` and `EPUBCHECK-WARNING` rules
- Controlled via `GLOW_ENABLE_EPUBCHECK` feature flag

---

### 5. Convert Anything. Preview It. Audit It. One Flow.

> *"People send us PowerPoints, spreadsheets, PDFs, CSV files, and ask 'can GLOW help with this?' The answer used to be 'sort of.' Now the answer is yes. Convert it to accessible HTML or Word or EPUB — with full ACB Large Print formatting applied automatically — then audit it, preview it, and download it. All in one place."*
>
> **— BITS President**

GLOW 2.7.0 expanded the Convert page to accept `.pptx`, `.xlsx`, `.xls`, `.pdf`, `.csv`, `.html`, `.htm`, `.json`, and `.xml` files as input for all Pandoc output directions. Files are automatically two-stage converted: MarkItDown extracts content to Markdown, then Pandoc applies full ACB Large Print formatting. Transparent to the user.

The Convert result page now shows:
- An **inline iframe preview** of converted HTML before download
- A **Copy to Clipboard** button for CMS Fragment output (ready to paste into WordPress or Drupal)
- An **Audit This Document** card for HTML, Word, and EPUB outputs — one click to verify the converted file's compliance

The file input also now filters available output options in real time based on what you upload, with a live-region hint announcing available formats and when two-stage chaining applies.

---

### 6. The Audit Report Is Now a Dashboard

> *"We wanted every person who opens an audit report to know in three seconds: is this document accessible or not? How bad is it? What do I do first? And then — when they run the fix — we wanted them to see the improvement immediately, unmistakably, with the score and the grade and the proof. That is what we built."*
>
> **— BITS President**

The audit report has been transformed:

- **Compliance grade letter** (A–F) displayed prominently at the top alongside the score
- **Quick Wins filter** — one click shows only auto-fixable findings; another takes you straight to Fix
- **After-action next-step cards** — "Fix This Document" and "Re-Audit Now" as prominent call-to-action cards, not buried links
- **Diff banner** on re-audit — score delta, grade change, fixed/persistent/new finding counts, resolved rule IDs
- **Inline rule disclosures** — every finding explains itself
- **Dark mode toggle** — choose Light, Dark, or Auto (follow system) from the footer or Settings page; preference persists across visits and applies before first paint with no flash. CSS keys off `html[data-theme="dark"]` so explicit user choice always wins over the OS setting. Full ACB-compliant dark palette with WCAG 2.2 AA contrast throughout.
- **Print CSS** — hides interactive elements, adds page-break rules for the findings table
- **Responsive layout** — fully usable on phones and tablets

---

### 7. Visual Polish: A UI That Feels Like It Was Built For Real Use

> *"You can ship every feature in the world, but if the page looks like it was assembled in 1998 and tabbing into a checkbox is a guessing game, your users will not stay. We sweated the visual layer in 2.7.0 — centered layout on wide screens, reading-width prose on narrow ones, an unmissable focus ring on every control, a real dark-mode toggle, and a navigation that finally puts document tools front-and-center."*
>
> **— BITS President**

GLOW 2.7.0 ships a focused round of visual and UX improvements across every page:

- **Centered, responsive page layout** — On wide and full-screen viewports GLOW no longer pins itself to the left half of the screen. The body is horizontally centered with a wider max-width (`min(82rem, 100%)`) and responsive horizontal padding (`clamp(1rem, 3vw, 2.5rem)`). Long-prose paragraphs and lists inside `<main>` are still constrained to a 70-character reading measure, while cards, tables, and form layouts use the full width. The result feels balanced on a 4K monitor and still respects the ACB reading-line guidance for body copy.
- **Reliable focus indicators on every control** — All interactive elements (links, buttons, inputs, selects, textareas, checkboxes, radios, `<summary>`, `[tabindex]`) now render a 3px solid blue outline plus a layered white-and-blue halo on `:focus-visible`. Native checkboxes and radios — which previously dropped their outline entirely on some browsers and OS themes (the consent checkbox was a known offender) — get an explicit ring with offset and a dashed outline on the wrapping `<label>` via `:has()`, so the control text is also visually located. A `forced-colors` block defers to the system `Highlight` color for Windows High Contrast users, and the dark-mode rules swap the white halo for a dark halo so the indicator stays visible against dark backgrounds. A CSS guard test fails the build if a future change reintroduces an `outline: none` rule outside the allowed `:focus:not(:focus-visible)` recipe.
- **Dark mode is now an explicit user choice** — A footer dropdown on every page and a new "Appearance" section at the top of the Settings page let users pick **Light**, **Dark**, or **Auto** (follow system, the default). The choice is stored in this browser's `localStorage` under `glow_theme` and is applied by an inline boot script in `<head>` before the stylesheet paints, so reloading never flashes the wrong theme. The CSS rewriting was a real change: every dark-mode rule now keys off `html[data-theme="dark"]` instead of `@media (prefers-color-scheme: dark)`, which means an explicit user choice always wins over the OS preference. Auto mode reacts live when you toggle dark mode in your operating system, via a `matchMedia` listener. A `<meta name="color-scheme" content="light dark">` tag tells the browser to render native widgets (scrollbars, native form controls) in the matching scheme. All ACB severity badges, score-grade colors, callout boxes, dropzones, share sections, and code blocks have hand-tuned dark variants. Print output continues to use the light ACB palette regardless of theme.
- **Navigation focused on document tools** — The main top ribbon now contains only the document tools you actually launch from it: **Quick Start, Template, Audit, Fix, Convert, Whisperer**. The previous Guidelines and Settings tabs have been moved into the footer "Additional links" navigation alongside User Guide, FAQ, About, PRD, Changelog, Feedback, Privacy, and Terms. They are also called out as cards on the Quick Start page so new users can find them on day one. The result is a top bar that reads as a workflow, not a kitchen-sink menu.
- **Quick Start "More resources" card** — A new card at the bottom of Quick Start surfaces Guidelines and Settings as plain-language suggestions, with one-line descriptions of what each page is for, so the navigation move never leaves anyone hunting.
- **Settings: Appearance fieldset** — The new Display options live at the top of `/settings/` as a standard fieldset with three radios (Auto / Light / Dark) wired to the same `data-theme-control` attribute the footer uses, so the two controls stay in sync automatically.
- **A11y status announcement** — Theme changes are announced through an `aria-live="polite"` region (`#theme-status`), so screen reader users get confirmation when they switch.
- **Color-scheme native rendering** — `<meta name="color-scheme" content="light dark">` makes browser-rendered scrollbars, native checkboxes, date pickers, and form glyphs match the active theme on macOS, Windows, iOS, and Android.

---

## THE INFRASTRUCTURE THAT MAKES IT ALL POSSIBLE

---

### Deployment Reliability: Deploy With Confidence, Roll Back Without Fear

> *"One thing I am incredibly proud of is that we can deploy GLOW to production without fear. Maintenance mode goes up. Code ships. Tests pass. Maintenance mode comes down. If anything breaks, it rolls back automatically. Operators get a timestamped log of every step. This is how real software should work."*
>
> **— BITS President**

GLOW delivered a production-grade deployment system:

- Automatic rollback on Docker health failure
- Timestamped deploy logs with per-step container status
- Maintenance mode toggle as a zero-downtime mechanism
- WSL pre-production staging environment for testing before production push
- Whisper model warm-up before maintenance is lifted so first-user requests never stall
- `scripts/post-deploy-check.sh` validates health, readiness, and warm model state before declaring success

---

### Accessibility of GLOW Itself: We Eat Our Own Cooking

> *"An accessibility toolkit that is not itself accessible is a contradiction. We do not accept that. We ran axe-core scans against every key route, fixed 18 templates, corrected ARIA roles, improved keyboard navigation, added global focus indicators, and ship with a CI gate that fails the build if we regress. GLOW is WCAG 2.2 AA compliant. We checked."*
>
> **— BITS President**

GLOW delivered a comprehensive accessibility sweep:

- 18 templates corrected for WCAG 2.2 AA compliance
- Proper modal dialog with focus trap for the cloud AI consent gate
- `aria-live` regions for dynamic UI feedback (chat character count, Whisperer progress)
- Full accessibility regression testing: Playwright + axe-core + SARIF output

GLOW 2.7.0 adds:

- Global `:focus-visible` ring on all focusable elements (3px solid, 2px offset)
- `prefers-reduced-motion` support across all custom animations
- Consent modal scrollable body so Decline/Accept stay visible on small viewports
- CSS guard test that fails if any future change suppresses the focus ring

---

### Rules Reference and Changelog: Everything Documented, Always

GLOW added a dedicated **Rules Reference page** (`/rules/`) covering all audit rules across all formats — searchable, deep-linkable, with extended rationale for every finding.

GLOW's **Changelog** (`/changelog`) is deployed inside the Docker image and served live. Every feature, every fix, every rule change is documented.

GLOW 2.7.0 adds a **Roadmap** page — linked from the footer — so contributors and adopters always know where the project is heading.

---

## A NOTE ON COMMUNITY AND ATTRIBUTION

> *"Open source works because people share. Jamal Mazrui shared. His extCheck and xlHeaders tools directly shaped GLOW's Excel and extension-based accessibility checks. That is how this community is supposed to work — building on each other's shoulders, giving credit, and making the next tool better than the last. We are grateful."*
>
> **— BITS President**

GLOW acknowledges the foundational work of **Jamal Mazrui** and his projects [extCheck](https://github.com/jamalmazrui/extCheck) and [xlHeaders](https://github.com/jamalmazrui/xlHeaders). GLOW's Excel header remediation helper and extension-type checking patterns draw direct inspiration from this work.

---

## THE NUMBERS

| | v2.5.0 | v2.6.0 | v2.7.0 |
|---|---|---|---|
| New audit rules | ~30 | ~40 | — |
| New web routes | 8 | 5 | 8 |
| New test cases | 40+ | 30+ | 22 |
| Templates updated | 18+ | 8 | 6 |
| Document formats covered | 6 | 6 | 6 |
| Test suite (web) | passing | passing | **266 passed, 20 skipped** |

---

## GET GLOW

GLOW is **free and open source**, available now at:

** [https://glow.bits-acb.org](https://glow.bits-acb.org)**

Source code, desktop tool, CLI, and VS Code agent toolkit:

**📦 [https://github.com/accesswatch/acb-large-print-toolkit/releases/tag/v2.7.0](https://github.com/accesswatch/acb-large-print-toolkit/releases/tag/v2.7.0)**

---

> *"To every person who has ever struggled to read a PDF that was never designed for them, an agenda formatted in 10pt Times New Roman, a spreadsheet that a screen reader couldn't parse — this work is for you. GLOW exists because you deserve better. And we are just getting started."*
>
> **— President, Blind Information Technology Solutions (BITS), American Council of the Blind**

---

*GLOW is a project of Blind Information Technology Solutions (BITS) of the American Council of the Blind. Questions, feedback, and contributions are welcome through the [Feedback](https://glow.bits-acb.org/feedback) page.*
