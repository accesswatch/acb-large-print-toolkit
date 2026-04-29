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

### Dark mode

GLOW now respects the system `prefers-color-scheme: dark` setting with an ACB-compliant dark color scheme. All contrast ratios meet WCAG 2.2 AA in dark mode. Print output continues to use the light ACB palette.

### HTML preview on Convert

When you convert a document to HTML, the result page shows a sandboxed inline preview before you download. Confirm what the output looks like without opening a separate file.

### Drag-and-drop upload

All upload forms now support drag-and-drop. The drop zone is keyboard accessible and falls back to the standard file picker on any device.

## Privacy policy update

The Data Storage and Retention Policy has been updated to accurately reflect how audit session files are handled under the new streamlined flow.

Uploaded files are retained briefly (up to one hour from upload) to enable the Fix shortcut and Chat follow-on actions. Shareable report links contain only rendered HTML -- the original document is never stored in or accessible from the report cache.

## Get GLOW 2.7.0

GLOW is freely available at [https://glow.csedesigns.com](https://glow.csedesigns.com).

The source code is on GitHub. The Python desktop tool, CLI, and VS Code agent toolkit are updated in the same release.

Questions, feedback, and issue reports are welcome through the Feedback link on the site.

---

*GLOW is a community project of the Blindness and Information Technology Section (BITS) of the American Council of the Blind.*
