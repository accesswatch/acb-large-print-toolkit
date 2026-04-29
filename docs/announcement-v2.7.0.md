# GLOW 2.7.0: Upload Once, Audit Faster, Fix Smarter

**FOR IMMEDIATE RELEASE -- May 2026**

GLOW (Guided Layout and Output Workflow) Accessibility Toolkit 2.7.0 is now available.

This release is about reducing friction in the workflows that matter most: auditing a document, fixing what is broken, and confirming the fix worked. Starting today, the entire audit-fix-re-audit cycle requires uploading your document exactly once.

## The headline: one upload, three steps

Before this release, every step in a compliance workflow required re-uploading the same file. Audit it. Download the report. Upload it again to fix it. Download the fixed file. Upload it a third time to confirm the improvements.

GLOW 2.7.0 eliminates those extra uploads.

After your initial upload and audit:

1. Click **Fix This Document** -- GLOW opens the Fix page with your document already loaded.
2. Adjust options and click **Fix Document**.
3. Click **Re-Audit Fixed Document** -- GLOW runs the audit on the fixed file immediately.

Three actions. Zero re-uploads. Your document session stays active for up to one hour.

This is a meaningful change for organizations that process the same documents repeatedly: board meeting agendas, newsletter issues, and compliance submissions where the audit-fix-confirm loop happens on a deadline.

## What else is new in 2.7.0

### Shareable audit report links

Every audit report now includes a shareable link. Send your compliance report to a colleague, a board member, or an external reviewer without sharing the original document.

The link contains only the rendered HTML report -- never the document itself. It expires after one hour.

### Quick Wins filter

The audit report now includes a bar above the findings table showing how many issues are auto-fixable. One click filters to fixable issues only. Another click takes you straight to Fix with your document already loaded.

For organizations triaging a long list of findings, this filter surfaces the highest-return actions first.

### CMS Fragment is now in Convert

The dedicated Export tab has been retired. The CMS Fragment output -- a self-contained HTML snippet for pasting into WordPress, Drupal, or any CMS -- is now a direction in the Convert workflow, alongside Standalone HTML, Word, Markdown, and EPUB.

The `/export` URL now redirects automatically to Convert. No links need updating.

### Compliance grade on the Fix result

After running a fix, the result page shows before-and-after compliance scores with letter grades (A through F) so you can see at a glance whether the document reached an acceptable level or needs another pass.

### Dark mode toggle (Light, Dark, or Auto)

Choose your theme from the footer dropdown on every page, or from the new Appearance section on the Settings page. Pick **Light**, **Dark**, or **Auto** (follow your system). Your choice is stored in this browser only and applied before the page paints, so there is no flash on reload. Auto mode reacts live when you toggle dark mode in your operating system. The dark palette is ACB-compliant with WCAG 2.2 AA contrast throughout. Print output continues to use the light ACB palette.

### Centered layout on wide viewports

GLOW no longer pins itself to the left half of the screen on wide or full-screen monitors. The body is horizontally centered with a wider max-width and responsive horizontal padding. Long-prose paragraphs and lists inside `<main>` are still constrained to a 70-character reading measure, while cards, tables, and form layouts use the full width.

### Reliable focus indicators on every control

All interactive elements -- including native checkboxes and radios, which previously dropped their outline on some browsers and themes -- now show a 3px solid blue outline plus a layered halo on `:focus-visible`. Wrapping `<label>` elements get a dashed outline via `:has()` so the control text is visually located too. Windows High Contrast users get the system `Highlight` color, and dark mode swaps the white halo for a dark halo so the indicator stays visible.

### Navigation focused on document tools

The top ribbon now contains only the tools you launch from it: Quick Start, Template, Audit, Fix, Convert, Whisperer. Guidelines and Settings have moved into the footer "Additional links" navigation alongside User Guide, FAQ, About, PRD, Changelog, Feedback, Privacy, and Terms. Both are also called out as cards on the Quick Start page so new users always find them.

### HTML preview on Convert

When you convert a document to HTML, the result page shows a sandboxed inline preview before you download. Confirm what the output looks like without opening a separate file.

### Drag-and-drop upload

All upload forms now support drag-and-drop. The drop zone is keyboard accessible and falls back to the standard file picker on any device.

### Download your audit report as a PDF or CSV

The shareable report section now includes **Download PDF** and **Download CSV** buttons.

The PDF version of the report is generated server-side and styled for print, ready to attach to a board packet or compliance file. The CSV contains every finding (with severity, rule ID, message, location, ACB reference, and help links) ready to drop into Excel or a tracking spreadsheet.

### See exactly what changed when you re-audit

When you re-audit a document after fixing it, the report now shows a before-and-after diff banner: how many points the score improved, the new grade letter, and which specific rule IDs were fixed since the previous audit.

If a fix introduced a new issue, that is called out as well, so nothing slips through.

### Inline rule explanations on every finding

Every rule ID in the findings table is now a click-to-expand disclosure. Open it to see the rule description, ACB reference, and a plain-language "Why this matters" explanation -- without leaving the page or losing your place in a long findings list.

### Convert → Audit handoff

When you convert a document to HTML, Word, or EPUB, the result page now offers an "Audit This Document" button. One click runs the audit on the converted file -- no re-upload, no extra step.

### Roadmap page

The site footer now links to a Roadmap page that lists what shipped in this release, what is in flight, and what is being considered next. The roadmap is open for community feedback.

### Better keyboard focus and reduced motion support

GLOW now ships a clearer global keyboard focus indicator on every focusable element, and respects the `prefers-reduced-motion` setting -- toast slide-ins, dropzone hovers, and consent modal fades are disabled when reduced motion is requested. The cloud-AI consent dialog body now scrolls so the Decline/Accept buttons stay visible on small viewports.

## Privacy policy update

The Data Storage and Retention Policy has been updated to accurately reflect how audit session files are handled under the new streamlined flow.

Uploaded files are retained briefly (up to one hour from upload) to enable the Fix shortcut and Chat follow-on actions. Shareable report links contain only rendered HTML -- the original document is never stored in or accessible from the report cache.

## Get GLOW 2.7.0

GLOW is freely available at [https://glow.csedesigns.com](https://glow.csedesigns.com).

The source code is on GitHub. The Python desktop tool, CLI, and VS Code agent toolkit are updated in the same release.

Questions, feedback, and issue reports are welcome through the Feedback link on the site.

---

*GLOW is a community project of the Blindness and Information Technology Section (BITS) of the American Council of the Blind.*
