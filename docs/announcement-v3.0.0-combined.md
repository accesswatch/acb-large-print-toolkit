# GLOW 3.0.0: Built by the Community, for the Community

**FOR IMMEDIATE RELEASE - April 30, 2026**


## THANK YOU. FIRST. BEFORE ANYTHING ELSE.

> "GLOW is not a product. It is a promise. A promise that the blind and low-vision community will have tools that actually work, tools that actually know what we need, tools that were built - not for us - but with us. Every feature in this platform exists because someone in this community was specific enough to say exactly what was wrong and brave enough to believe it could be fixed. We listened. We built. We are grateful from the bottom of our hearts."
>
> **- Jeff Bishop, President, Blind Information Technology Solutions (BITS), American Council of the Blind**

To every BITS member. Every AT user. Every board secretary who ever emailed us saying "the report has names in it, I cannot share that link with just anyone." Every chapter officer who said "my organization uses 20-point body text, not 18-point." Every accessibility coordinator who said "I love the cycle but I'm still uploading twice." Every blind professional who said "can GLOW just read the document to me?"

This release is yours. You asked for it. We built it. We mean that literally.


## EXECUTIVE SUMMARY

GLOW (Guided Layout & Output Workflow) Accessibility Toolkit 3.0.0 is now available.

This is the platform in its fullest form. A complete, self-hosted accessibility infrastructure for the blind and low-vision community - covering document auditing, auto-remediation, format conversion, and now narrated audio output. Built entirely on community feedback. Free to use. Open source. No cloud subscription. No API key required.

Here is what GLOW does today, in one breath:

**Upload a document once.** Audit it for accessibility compliance against ACB Large Print, WCAG 2.2 AA, and Microsoft Accessibility Checker standards. Auto-fix everything fixable without leaving the page. Re-audit the fixed version and see exactly what changed. Share the report - optionally password-protected - as a live link, a downloaded PDF, or a CSV. Convert it to a different format. Or convert it to speech and download narration audio in the voice of your choice.

That is the complete loop. One upload. Start to finish.

**Everything that follows is the full story.** The executive summary ends here. Keep reading to go deep.


## THE PROMISE: ONE UPLOAD, THE WHOLE CYCLE

Once upon a time, using GLOW meant uploading your document three times. Once to audit. Once to fix. Once more to check your work. That was friction that belonged to a different era.

GLOW's session model changed everything. You upload your document once. An encrypted session token carries it through every step for up to one hour. Every tool in the platform - Audit, Fix, Re-Audit, Convert, Convert-to-Speech - can read from that same session. The file picker disappears and is replaced with a quiet, reassuring message: "Ready. Your document is already here."

The journey looks like this now:

1. **Quick Start** - upload your file and let GLOW help you decide what to do with it
2. **Audit** - full compliance report, no second upload
3. **Fix** - auto-remediation applied in one click, no second upload
4. **Re-Audit** - instant re-check of the fixed document, no third upload
5. **Convert** - produce HTML, Word, EPUB, PDF, Markdown, or audio from the same session file

The diff banner at the top of every re-audit report tells the story of what changed: score delta, grade movement, which rules were resolved, and whether anything new appeared. Three seconds to understand the entire improvement.


## THE WORKFLOW ENHANCEMENTS: EIGHT FEATURES THAT SAVE TIME

In 3.0.0, every step of the accessibility cycle has been streamlined based on community feedback about where friction was highest.

### One-click re-audit after fixing
After you download your fixed document, the Fix result page shows a prominent "Re-Audit Fixed Document" button. Click it and you are in the audit report for the same file, no re-upload, profile preserved. This closes the gap that used to require tab-switching and file navigation.

### Direct convert-to-audit without re-uploading
Converted a Markdown file to HTML to test the output? The Convert result page now offers an "Audit This File" button that audits your newly converted document without asking you to upload again. The same file, same session, straight from Convert to Audit.

### Batch audit visibility and benefits
The Audit form highlights batch mode prominently with side-by-side callouts explaining when to use it: comparing format variants, testing before-and-after side by side, or bulk-checking a series of related documents. All three files are audited in one run and appear in a combined or per-file scorecard.

### Detailed before/after findings diffs
When you re-audit after fixing, you see not just score deltas but detailed sections showing: Which findings were newly detected (changes in your process or content), which are still present (focus here next), and which were resolved (your wins). This clarity keeps teams motivated and focused.

### Quick session restart with audit history
Your session remembers your last five audits with scores, filenames, and share links. Need to quickly re-audit a file you worked on yesterday? The history is right there. No rummaging through browser downloads. No forgetting names.

### Smart next-step guidance in Convert
After converting a document, Convert suggests contextually relevant next actions. Converting your newsletter to multiple formats to test? A card suggests auditing them all together in batch mode. This reduces the cognitive load of "what do I do now?"

### Reviewer feedback collection on shared reports
Shared audit reports now support optional passphrase protection (as before) and are built to support reviewer comments (foundation for future development). The infrastructure is in place for collaborative accessibility review workflows.

### Session restore after expiry
When your upload session expires, instead of a dead end, you see your audit history with one-click restore options. Continue from a previous audit or start fresh knowing your history is available if you need it.


## SPEECH STUDIO: WHEN DOCUMENTS LEARN TO SPEAK

> "We have been asked, more times than I can count, whether GLOW can produce audio versions of documents. Board minutes someone can listen to on their commute. A newsletter read aloud. A training handout in MP3 format. We heard you. Here it is."
>
> **- BITS President**

GLOW 3.0 introduces Speech Studio: a complete, self-hosted, CPU-only text-to-speech platform built into the GLOW web application.

No GPU required. No cloud API. No cost per request. No document leaves the server.

### What Speech Studio does

**Typed synthesis.** Type any text and hear it immediately. Adjust voice, speed, and pitch. Preview before you commit. Download as MP3 when you are satisfied.

**Uploaded document narration.** Upload a Word file, a PDF, a PowerPoint, a newsletter in Markdown - any format GLOW can read. Speech Studio extracts the readable content, shows you the first few sentences so you can preview the voice before waiting for the full job, and then generates complete narration audio for the entire document.

**The preview moment is important.** You hear the real voice on your real content before committing to a full generation. Not a generic demo clip. Your document, your words, in the voice you chose, within seconds. Then you decide whether to proceed.

**Voices.** GLOW ships with Kokoro ONNX voices - ten high-quality English voices, American and British accents, across a range of speaking styles. Piper TTS voices can be added by your administrator for additional variety.

**Adaptive timing estimates.** The first time you generate audio for a long document, GLOW estimates based on known baselines. Over time, as real conversions happen on your server, GLOW blends those measurements into its estimates. The more GLOW is used, the more accurate it becomes. Estimates are not guesses - they are calibrated to your infrastructure.

**Settings that remember you.** Voice, speed, pitch, and any text you typed are saved in your browser preferences when you have "Remember my settings" enabled. Return to Speech Studio the next day and your preferences are exactly where you left them.

**Seamless handoff from Convert.** Working in the Convert tab? Choose "Speech audio" as your output format and GLOW carries your session directly into Speech Studio - no second upload, no starting over. The same document you uploaded for conversion becomes your speech source with one click.

**Admin voice management.** Administrators can install or remove curated Piper voice packs directly from the admin dashboard. No terminal required. One click to add a new voice, one click to remove it, live status displayed instantly.

### The technical honesty

Speech Studio is CPU-only. A 300-word document generates narration in about 45-90 seconds on a typical server. A 3,000-word board report may take 5-8 minutes. Progress status updates keep you informed throughout. The system adapts its announcement cadence to the job size - no over-notification on short jobs, no silence on long ones.

This is not streaming, real-time cloud synthesis. It is deliberate, private, server-local narration for organizations that cannot and should not be sending document content to third-party APIs.


## THE AUDIT ENGINE: EVERY STANDARD, EVERY FORMAT

GLOW's accessibility audit engine covers six document formats with rules drawn from three standards bodies.

### Word documents

The Word audit is the deepest in the platform. Thirty-plus rules covering font family and size for body, headings, and lists; paragraph spacing and line height; emphasis (underline only - GLOW enforces the ACB prohibition on italic and catches bold-used-as-emphasis); alignment (left-justified only, never centered or justified); margins; heading hierarchy and numbering; alt text on images; table headers; document language; title; and link text.

When GLOW audits a Word document, the result is not a list of complaints. It is a prioritized, actionable map of the work required to make that document compliant - with every finding linked to the rule that fired, the reason it matters, and whether it can be auto-fixed.

### Excel workbooks

GLOW audits Excel for sheet names, table headers, merged cells, alt text on embedded images, color-only data encoding, hyperlink text quality, workbook title, and blank-row patterns that create layout-dependent navigation. The Excel fixer can add xlHeaders-style named ranges that dramatically improve screen reader header context.

### PowerPoint presentations

GLOW audits PowerPoint for slide titles, reading order, alt text on all visual elements, font sizes, speaker notes, chart descriptions, and - uniquely - timing and animation safety. Slides that auto-advance faster than a reader can process them, repeating animations, and rapid-fire transitions are flagged, because accessibility for motion-sensitive users is not optional.

### Markdown documents

GLOW's Markdown audit is the most thorough in any open-source accessibility tool. More than thirty rules covering YAML front matter (title, language, description, author, unclosed fences), heading hierarchy, heading quality (empty, too long, ending in punctuation, duplicate text), link text (ambiguous, URL-as-text, empty), alt text quality (too short, filename-as-alt, redundant prefix), code blocks, table consistency, fake lists, raw HTML, excessive blank lines, trailing spaces, ALL CAPS, em-dashes, and entire-line-bolded paragraphs.

YAML front matter is treated as an accessibility artifact, not just metadata. A document without a declared language is inaccessible to every screen reader that reads it. GLOW catches that.

### PDF documents

GLOW audits PDF for title, language, tag structure, font sizes, scanned page detection (with DPI quality checks - below 150 DPI draws a recommendation to re-scan at 300 DPI), bookmarks, and form fields. Scanned PDFs are classified as entirely scanned, majority-scanned, or partially scanned, with specific OCR remediation guidance for each case.

### EPUB publications

GLOW audits EPUB using two layers: a BITS-developed engine covering title, language, navigation documents, heading hierarchy, alt text, table headers, and W3C accessibility metadata; and DAISY Ace, which runs 100-plus axe-core accessibility rules against the rendered publication. EPUBCheck integration validates the package structure. When all three layers pass, you have independent confirmation of structural integrity, accessibility conformance, and specification compliance.


## THE RULES REFERENCE: KNOWLEDGE ON DEMAND

Every rule GLOW uses is documented at `/rules/` - a searchable, deep-linkable browser for the full rule catalog. Severity badges. Standards profile membership. Extended rationale. Suppression guidance. Help links to ACB, WCAG, WebAIM, and CommonMark specifications.

The Rules Reference is not just documentation. It is a working tool. You can build custom rule sets from it - check the rules you want, save to your browser, and your Audit and Fix sessions will use exactly those rules. For organizations with existing compliance processes, this means GLOW can fit your workflow rather than asking you to fit GLOW's.

Every rule ID in every audit report is a click-to-expand disclosure. The rationale, the standard reference, and the auto-fix badge are all there, inline, without navigating away from the report.


## THE FIXER: COMPLIANCE THAT APPLIES ITSELF

The best accessibility audit in the world does not help anyone if fixing the findings requires hours of manual edits in Word.

GLOW's auto-fixer applies every correctable finding in one operation. Font family, font size, paragraph spacing, line height, emphasis normalization, heading styles, list formatting, margin settings - all of it, applied consistently across the entire document.

The result appears instantly. A before-and-after score comparison shows the impact. The Re-Audit button is right there when you want it.

### Heading detection: turning visual structure into semantic structure

Many documents use bold large text to look like headings without using Word's actual Heading styles. A screen reader cannot navigate them. A compliance audit flags them. GLOW can fix them.

Heading detection uses a ten-signal heuristic that weighs font size, bold weight, capitalization pattern, preceding paragraph count, list proximity, and more. Each candidate is scored. The Heading Review page shows you every candidate with its score and proposed level. You confirm, adjust, or reject each one before anything is applied. Optional AI refinement is available for deployments where it is enabled.

### Font sizes that match your organization

The ACB defaults are 18pt body, 22pt Heading 1, and 20pt Heading 2 through 6. Those defaults are right for most organizations. But not all organizations. GLOW lets you override any size before running Fix, Audit, or Template generation. Your overrides are applied everywhere - in the auditor's expected-size comparisons, in the fixer's target sizes, in the template generator's pre-configured styles. List Bullet and List Number styles update automatically to match your body size.


## THE CONVERTER: ONE DOCUMENT, EVERY FORMAT

GLOW's Convert page accepts nearly any document format as input and produces any accessible format as output. Under the hood, it is a two-stage pipeline: MarkItDown extracts content to Markdown, then Pandoc applies full ACB Large Print formatting.

The formats that feed into the pipeline: Word, Markdown, PowerPoint, Excel, PDF, HTML, CSV, JSON, XML, EPUB, RTF, OpenDocument, and reStructuredText.

The formats it produces: accessible HTML, Word (.docx), EPUB 3, PDF, Markdown, CMS Fragment, and Speech audio.

### CMS Fragment

For organizations publishing to WordPress, Drupal, or any content management system: the CMS Fragment direction produces a scoped HTML snippet with embedded ACB-compliant CSS, wrapped in an `.acb-lp` container class. Paste it into your CMS editor. It will not conflict with your site theme.

### Two-stage conversion that just works

Upload a PowerPoint. Choose "Accessible web page." GLOW extracts the content through MarkItDown, applies ACB heading hierarchy and typographic formatting through Pandoc, and produces a compliant, fully styled HTML file. You do not see the intermediate step. You see the result.

The same pipeline works for Excel, PDF, HTML, CSV, JSON, and XML files as inputs.

### The result page

Convert results do not just download. They show. An inline preview of the converted HTML appears in the result page iframe. A Copy to Clipboard button captures the CMS Fragment. An "Audit This Document" card takes you to a compliance report on the converted output - no re-upload, same session.

### Intelligent input filtering

After you select a file, JavaScript reads the extension and enables only the output formats that support it. Unavailable options are disabled in place with a visual indicator. A live hint names the available formats and notes when two-stage chaining applies. No server round-trip. No surprises.


## THE TRUST LAYER: SCORES, GRADES, AND SHARING

### The grade that speaks first

Every audit report leads with a letter grade - A through F - displayed large at the top, before the score, before the findings table. Three seconds to understand whether a document is compliant. Color-coded. Unmistakable. The Fix result shows before-and-after grades side by side.

The grade is not decorative. It is computed from a weighted-penalty model that charges per rule at full severity, adds a capped surcharge for repeated occurrences, and stays stable through grouped-display rendering. When GLOW says B, it means B.

### Findings grouped by rule

Documents with systematic formatting problems used to produce audit reports with forty rows of "Arial not used" before the structural issues appeared. The findings table now groups all occurrences of the same rule into one row with a count badge and an expandable location list. Important issues are visible immediately. The table is as short as it can be while being as complete as it needs to be. CSV exports still emit one row per occurrence - nothing is lost in your spreadsheet.

### Quick Wins

When some of your findings are auto-fixable, the Quick Wins bar appears above the table. One click filters to only those findings. Another click takes you to Fix with your document already loaded. For teams working under deadline pressure, this is the fastest path to a meaningfully better score.

### Shareable reports

Every completed audit generates a shareable link to the rendered report. The link contains only the HTML report - never the original document. It expires in one hour.

From the share panel: **Download PDF** for board packets and compliance files. **Download CSV** for spreadsheets and project trackers.

And if your report contains member names, legal correspondence, or financial data: **set a passphrase**. Whoever follows your link sees a clean unlock form. Enter the correct passphrase and the full report opens. Enter it wrong and it stays locked. The passphrase is hashed with PBKDF2-SHA256 at 200,000 iterations and a unique salt the moment you set it. The cleartext is never stored anywhere. Send the passphrase through a separate channel from the link - that is the whole point.


## POWER USER AND INTEGRATOR FEATURES

For teams running GLOW on premise and building custom workflows around it, 3.0.0 includes fifteen new infrastructure capabilities.

### Standards profile propagation through workflows
Select your profile (ACB 2025, APH Submission, or Combined Strict) in Audit. Fix remembers it. Re-Audit uses it. Convert respects it. No profile confusion across tools.

### Webhook callbacks for custom integrations
Audit completion can trigger an HTTPS POST to a user-supplied webhook URL with HMAC-SHA256 signatures. The payload includes score, grade, findings count, and share link. Integrate GLOW into your incident tracking system, compliance dashboard, or analytics pipeline without polling.

### Configurable share link TTL
Set `SHARE_TTL_HOURS` in your environment. Shared reports remain available for 1 hour, 4 hours (default), 8 hours, or as long as you decide. Not everyone needs the same expiry window.

### Session-based auto-diff for testing workflows
The same session can audit your document twice. GLOW detects this and automatically shows before/after comparisons. Perfect for quality assurance testing - run Audit once, make a change, run Audit again, see exactly what changed.

### Large-file rate limiting
Files over 10 MB are subject to a separate, tighter rate limit (1 audit per minute vs. 6 audits per minute for smaller files). Prevents a single slow job from starving other users.

### Keyboard shortcuts for accessibility power users
Ctrl+U (Cmd+U on Mac) focuses the file picker from anywhere in GLOW. No need to find the button - just press your shortcut.

### Session keep-alive for long workflows
GLOW pings `/health` every 15 minutes when forms are active, keeping your session alive through longer workflow sessions.

### AI-powered alt-text suggestions API
`POST /audit/suggest-alt-text` with a session token and image index. Returns LLM-generated alt text suggestions for images in Word documents. Great for teams with large image-heavy documents.

### CSV export of remediation findings
`POST /fix/csv/<token>` downloads findings detected after fixing as a CSV. Build custom reports, track progress in your spreadsheet, integrate with your workflow.

### EPUB conformance level detection
When GLOW audits EPUB with Ace, it extracts the W3C conformance declaration (e.g., "EPUB Accessibility 1.0 - WCAG 2.0 AA") and displays it in reports. Know your publication's conformance level at a glance.

### Voice preview endpoint for Speech Studio
New `/speech/voice-preview` endpoint lets users click any voice button to hear a 3-5 second demo with the default test phrase. No waiting for synthesis. Just hear the voice and decide.

### Audit history in session storage
Sessions store up to 5 recent audits with scores, grades, filenames, and share tokens. Query the session history programmatically or use it for UI-driven restart workflows.

### Toast notification framework
All progress events and errors now communicate through accessible toast notifications. Keyboard navigable. Screen reader compatible. Emoji optional (no reliance on graphical icons).

### Template context injection
Templates always have `audit_history`, `share_ttl_hours`, and other runtime config available. No conditional logic needed in templates - the app context processor handles injection.

### Full backward compatibility
Every new feature is opt-in and non-breaking. Existing deployments continue to work. No migration required. Upgrade at your pace.


## THE HUMAN TOUCHES: DARK MODE

Choose Light, Dark, or Auto from the footer or Settings on any page. Your choice is stored in the browser and applied before first paint - no flash of the wrong theme. Full WCAG 2.2 AA contrast throughout all three modes. Print output always uses the light ACB palette regardless of screen setting.

### Focus indicators that never disappear

Every interactive element in GLOW has a 3-pixel solid outline with a layered halo on `:focus-visible`. Every one. Checkboxes that lost their outlines in certain browsers are fixed. Windows High Contrast is handled. Dark mode is handled. A CI test fails the build if a future code change suppresses the focus ring. The focus indicator is not an afterthought - it is protected by automated enforcement.

### Reduced motion

Every animation in GLOW - toast notifications, dropzone hover effects, consent modal fade - checks `prefers-reduced-motion` and disables transitions for users who have requested it.

### Drag and drop

Every file input in GLOW has a visual drag-and-drop zone. Drag a file onto it. The input updates, the hint text updates, and any dependent JavaScript fires correctly. The original keyboard-accessible file input remains fully functional and unchanged.

### The GLOW Anthem

"Let it GLOW" - a cinematic ballad embedded on the home page with an accessible audio player, integrated lyrics, and a download link. It is the sound of this community.

### Layout that works at any size

The page body is horizontally centered with responsive padding. Long-prose paragraphs use a 70-character reading measure. Cards, tables, and forms use the full available width. On narrow viewports, forms stack gracefully. On wide monitors, nothing stretches beyond readable.


## THE PLATFORM: OPERATIONS, ANALYTICS, AND DEPLOYMENT

### What is being used, and by whom

GLOW tracks aggregate usage in two SQLite stores - a visitor counter and a per-tool usage counter. No document content, no extracted text, no personal information. Just: how many sessions have visited, how many times was Audit used, when was Convert last invoked.

The About page surfaces these counts publicly. The Admin analytics dashboard breaks them down by tool with share percentages and last-used timestamps. Speech Studio adds voice/speed/pitch usage patterns and conversion timing telemetry. Anthem downloads are counted too.

Analytics exist for one reason: to understand what the community actually uses so GLOW can keep improving where it matters.

### Deployment you can trust

GLOW deploys via a single shell script with automatic rollback on Docker health failure. Maintenance mode toggles without a code deploy. A WSL pre-production staging path lets operators validate the full stack locally before touching production. Post-deploy checks confirm that security headers, health endpoints, and media content policy are correct before maintenance lifts. Timestamped deploy logs. Caddy proxy config validation from a disposable container before any live service is touched.

### Institutional branding

GLOW supports deployment-level branding profiles. The `bits` profile (default) carries full BITS and ACB identity. The `uarizona` profile switches to University of Arizona branding across navigation, footer, home page, and guidelines copy. One environment variable. One restart.

### Feature flags for every capability

Every major capability in GLOW is gated by a feature flag. Conversion directions. Export HTML. Heading detection. AI. Speech. Each flag can be set to false to hide the feature from navigation, forms, and result pages - consistently, completely, without workarounds. Deployments can enable only what they need.


## ATTRIBUTION AND COMMUNITY SHOULDERS

> "Open source works because people share. Jamal Mazrui shared. His extCheck and xlHeaders tools directly shaped GLOW's Excel and extension-based accessibility checks. That is how this community is supposed to work - building on each other's shoulders, giving credit, and making the next tool better than the last."
>
> **- BITS President**

GLOW acknowledges the foundational work of **Jamal Mazrui** and his projects [extCheck](https://github.com/jamalmazrui/extCheck) and [xlHeaders](https://github.com/jamalmazrui/xlHeaders). GLOW's Excel header remediation helper and extension-type checking patterns draw direct inspiration from this work.

GLOW also acknowledges the DAISY Consortium for the Ace accessibility checker and DAISY Pipeline, the Pandoc project for document conversion, the MarkItDown project for content extraction, the Kokoro and Piper projects for open-source speech synthesis, the CommonMark specification for Markdown, and the hundreds of individuals who have contributed accessibility standards work that makes GLOW possible to build at all.


## THE FULL PLATFORM, FEATURE BY FEATURE

For readers who want to drill all the way down:

| Capability | What it does |
|--|--|
| One-upload session model | Single upload persists across Audit, Fix, Re-Audit, Convert, and Speech |
| Quick Start | Upload once; choose Audit, Fix, Convert, or Speech; session carries forward |
| Word audit | 30+ rules: font, size, spacing, emphasis, alignment, headings, alt text, tables, properties |
| Excel audit | Sheet names, headers, merged cells, alt text, color-only data, hyperlinks, workbook title |
| PowerPoint audit | Slide titles, reading order, alt text, font sizes, notes, charts, timing, animation safety |
| Markdown audit | 30+ rules: YAML front matter, headings, links, alt text, code blocks, tables, lists, emphasis |
| PDF audit | Structure, language, scanned pages, DPI quality, bookmarks, form fields |
| EPUB audit | BITS engine + DAISY Ace (100+ axe-core rules) + EPUBCheck structure validation |
| Word auto-fix | Fonts, sizes, spacing, emphasis, headings, alignment, margins, styles |
| Heading detection | 10-signal heuristic; Heading Review confirmation; optional AI refinement |
| User-defined font sizes | Override any heading level and body size; propagates through fix, audit, and template |
| Convert: two-stage pipeline | MarkItDown → Pandoc for PowerPoint, Excel, PDF, HTML, CSV, JSON, XML inputs |
| Convert: output formats | Accessible HTML, Word, EPUB 3, PDF, Markdown, CMS Fragment, Speech audio |
| Convert result page | Inline HTML preview; clipboard copy for CMS Fragment; Audit This Document card |
| Speech Studio: typed synthesis | Type text; choose voice/speed/pitch; preview and download MP3 |
| Speech Studio: document narration | Upload document; preview first sentences; download full narration |
| Speech Studio: adaptive estimates | Timing estimates improve as real conversions happen on the same server |
| Speech Studio: settings persistence | Voice, speed, pitch, text saved in browser preferences |
| Convert-to-Speech handoff | "Speech audio" direction in Convert passes session to Speech Studio |
| Compliance grade | A-F letter grade, large at top of every audit report; before/after on fix result |
| Weighted score model | Stable, drift-resistant; grouped display does not affect computation |
| Findings grouped by rule | One row per rule, occurrence count badge, expandable location list |
| Quick Wins filter | Shows only auto-fixable findings; one click to Fix with file pre-loaded |
| Shareable report links | HTML-only link; never the document; expires in 1 hour |
| Passphrase protection | PBKDF2-SHA256 hash at 200,000 iterations; cleartext never stored |
| PDF download of report | Rendered to PDF via WeasyPrint; available on any share link |
| CSV download of findings | One row per finding; preamble header with score, grade, profile |
| Re-audit diff banner | Score delta, grade change, fixed/persistent/new rule counts |
| Inline rule explanations | Click to expand any rule ID: rationale, ACB reference, auto-fix badge |
| Rules Reference (/rules/) | Searchable, deep-linkable; full rule catalog; custom rule set builder |
| Drag-and-drop upload zones | Visual drop zone on every file input; keyboard input unchanged |
| Dark mode | Light/Dark/Auto; stored per browser; applied before first paint |
| Focus indicators | 3px outlined halo on all interactive elements; CI-enforced |
| Reduced motion support | All animations check `prefers-reduced-motion` |
| Centered wide-viewport layout | max-width `min(82rem, 100%)`; 70ch reading measure for prose |
| Tool usage analytics | Per-tool counts, last-used timestamps; About page + admin dashboard |
| Speech analytics | Voice/speed/pitch usage patterns; timing telemetry |
| Visitor counter | Unique browser session count; displayed in footer |
| Roadmap page (/roadmap/) | Shipped, in-progress, and planned work visible to community |
| Institutional branding | bits / uarizona profiles; one environment variable |
| Feature flags | Per-tool, per-direction, per-capability gating |
| Automated deployment | Docker health check + automatic rollback |
| WSL pre-production staging | Full stack validated locally before production deploy |
| Admin voice management | Install/remove Piper voice packs from admin dashboard |
| GLOW Anthem | "Let it GLOW" audio player, lyrics, and download on home page |
| BITS Whisperer | Audio transcription to Markdown/Word via server-side Whisper |
| Document Chat | Ask questions about your document in plain language |


## GET GLOW

GLOW is **free and open source**, available now at:

**[https://glow.bits-acb.org](https://glow.bits-acb.org)**

Source code, desktop tool, CLI, VS Code agent toolkit, and Office Add-in:

**[https://github.com/accesswatch/acb-large-print-toolkit/releases/tag/v3.0.0](https://github.com/accesswatch/acb-large-print-toolkit/releases/tag/v3.0.0)**

Release notes: `docs/RELEASE-v3.0.0.md`

Full changelog: `CHANGELOG.md`


## ONE LAST THING

Every inaccessible document is a door slammed in someone's face.

GLOW is about opening those doors - permanently, systematically, and freely.

Thank you for building it with us.

**- BITS**


