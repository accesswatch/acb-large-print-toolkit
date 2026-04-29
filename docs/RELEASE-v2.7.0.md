# v2.7.0 Release Summary: May 2026

## Overview

GLOW Accessibility Toolkit v2.7.0 is a UX-focused release that tightens the audit-fix-re-audit loop, consolidates Export into Convert, and adds several quality-of-life improvements including shareable report links, a Quick Wins filter, dark mode, and HTML preview for converted documents.

Core highlights:

- **Streamlined Audit → Fix → Re-Audit flow** -- upload once, cycle through all three steps without re-uploading
- **Export merged into Convert** -- the dedicated Export tab is gone; CMS Fragment is now a first-class direction in Convert
- **Shareable audit report URLs** -- send a read-only compliance report link to a colleague with one click
- **Quick Wins filter** -- one-click filter on the audit report shows only auto-fixable findings
- **Dark mode toggle (Light, Dark, or Auto)** -- footer dropdown and Settings panel option, persisted in `localStorage`, no flash on reload, ACB-compliant dark palette with WCAG 2.2 AA contrast
- **HTML preview on Convert** -- inline iframe preview of converted HTML output before download
- **Compliance grade on Fix result** -- before/after grade letters displayed in the score comparison boxes

---

## What Changed in v2.7.0

### 1. Streamlined Audit → Fix → Re-Audit (no re-upload)

The central UX improvement in this release: users no longer need to re-upload a document to move between audit, fix, and re-audit steps.

**New routes:**
- `GET /fix/from-audit/<token>` -- renders the Fix form with the audit session file pre-loaded
- `POST /fix/from-audit/<token>` -- runs the fix on the existing file; full heading-review path supported
- `POST /audit/from-fix` -- re-audits the fixed file from the fix session; full report with share link

**Template changes:**
- Audit report "Fix This Document" and "Fix These Auto-Fixable Issues" buttons now use the token-based route when a session is active
- Fix result "Re-Audit Now" replaced with "Re-Audit Fixed Document" -- a `<form>` POST that sends the existing session token rather than a plain navigation link
- Fix form shows a pre-filled notice ("Ready to fix: filename.docx -- no need to re-upload") when accessed via the from-audit route
- Session expired redirect returns to the fix form with an informational notice instead of a raw error

**Session lifecycle:**
- Document sessions remain active for up to one hour from upload
- The full Audit → Fix → Re-Audit cycle requires only one upload
- The `fix_from_audit_submit` route reuses the same heading-review confirm flow (`/fix/confirm`) as direct Fix uploads

### 2. Export folded into Convert

The standalone Export tab has been removed from the navigation.

- `/export` permanently redirects (301) to `/convert`
- CMS Fragment is now a dedicated direction in Convert, producing an identical `-cms.html` output
- Standalone HTML output is available via Convert > Accessible web page (HTML)
- `GLOW_ENABLE_EXPORT_HTML` now gates the CMS Fragment direction in Convert; the behavior is identical to before -- disabling it hides CMS Fragment without affecting other Convert directions
- Quick Start "CMS Fragment" action routes directly to Convert

### 3. Shareable audit report URLs

Every audit generates a UUID-keyed share link containing only the rendered HTML report.

- Share link is displayed in the Share section of every audit report
- Cached HTML is stored server-side for 1 hour and then permanently deleted
- The original document is never accessible via the share link
- Anyone with the link can view the report; no login required
- Shareable links work for all document formats (docx, xlsx, pptx, md, pdf, epub)
- Re-audit (from-fix) results also generate a share link

### 4. Quick Wins filter on audit report

A bar above the findings table shows how many of the reported findings are auto-fixable.

- "Show Quick Wins Only" button toggles the table between all findings and auto-fixable findings only
- "Fix These Auto-Fixable Issues" button links to Fix, using the session token when available (no re-upload)
- Button state is announced via `aria-pressed` for screen reader users
- Displayed only for Word documents with at least one fixable finding

### 5. Compliance grade on Fix result

The "After" score box on the Fix result page now shows a grade letter (A–F) alongside the numeric score.

- Color-coded by grade (A = green, B = blue-green, C = amber, D = orange, F = red)
- Matches the grade display already on the audit report
- Before/after comparison shows both grade letters and numeric scores side by side

### 6. Dark mode (user-selectable)

Light, Dark, or Auto modes selectable from the footer dropdown on every page and from the Settings page. Preference persists in `localStorage` per-browser and applies before first paint via an inline boot script in `<head>`, so there is no flash of wrong theme.

- All foreground/background contrast ratios meet WCAG 2.2 AA in dark mode
- All ACB-specific colors (severity badges, score grades, callout boxes) have dark-mode variants
- CSS keys off `html[data-theme="dark"]` so explicit user choice always wins over `prefers-color-scheme`
- Auto mode reacts live to OS theme changes via `matchMedia` listener
- Print media query continues to use light-mode ACB colors regardless of theme

### 7. HTML preview on Convert result

An inline iframe preview of converted HTML output is shown on the Convert result page when the output is an HTML file.

- Preview collapses by default on smaller viewports to avoid layout shift
- Can be toggled open/closed with a single button
- Uses `sandbox` attribute to prevent any script execution in the preview
- Preview updates immediately without reload

### 8. CMS Fragment clipboard copy

The Convert result page shows a "Copy to Clipboard" button for CMS Fragment output.

- One-click copy of the full HTML snippet
- Toast notification ("Copied to clipboard") confirms success, announced via ARIA live region
- Falls back gracefully when the Clipboard API is not available

### 9. Toast notification system

New `toast.js` module provides lightweight screen-reader-announced status toasts.

- Used for clipboard copy confirmation and other async UI feedback
- Announcements use `aria-live="polite"` so screen readers read them without interrupting the current focus
- Auto-dismisses after 3 seconds; keyboard-dismissible via Escape

### 10. Drag-and-drop upload

All upload forms now support drag-and-drop in addition to the file input.

- Keyboard accessible: the drop zone is also a focusable button that opens the file picker
- Visual drop zone with clear hover/focus state
- Accepted file types enforced on drop (same as the `accept` attribute on the file input)

---

## Privacy Policy Update

The Data Storage and Retention Policy has been updated to accurately reflect the audit session retention model introduced by the streamlined flow.

**Key changes:**
- Audit workflow description updated: files are retained briefly (up to 1 hour) to enable the Fix shortcut and Chat follow-on actions
- New paragraph describes shareable report links: cached HTML only, 1-hour expiry, original document never accessible
- "No permanent storage" section updated to clarify that the report cache holds only rendered HTML
- New analytics disclosure clarifies that operational metrics include aggregate visitor sessions and per-tool usage counters (with last-used timestamps), stored in local SQLite (`instance/visitor_counter.db`, `instance/tool_usage.db`) and excluding document content
- Last updated date changed to April 29, 2026

---

## Migration Notes

### `GLOW_ENABLE_EXPORT_HTML`

No action required. This flag now gates CMS Fragment in Convert rather than a separate Export route. Existing deployments with the flag disabled will continue to see CMS Fragment hidden; deployments with it enabled will see no change in behavior.

### Bookmarks and links to `/export`

All `/export` traffic is permanently redirected (301) to `/convert`. No action required for users.

---

## Files Changed

### Routes
- `web/src/acb_large_print_web/routes/fix.py` -- new `fix_from_audit_form` (GET) and `fix_from_audit_submit` (POST) routes; `_find_fixable_file` helper
- `web/src/acb_large_print_web/routes/audit.py` -- new `audit_from_fix` (POST) route; `werkzeug.utils.secure_filename` import added
- `web/src/acb_large_print_web/routes/convert.py` -- CMS Fragment direction, HTML preview, clipboard copy support
- `web/src/acb_large_print_web/routes/export.py` -- 301 redirect to Convert

### Templates
- `web/src/acb_large_print_web/templates/fix_form.html` -- prefill notice, conditional form action, session-expired notice
- `web/src/acb_large_print_web/templates/audit_report.html` -- Fix buttons use token-based route when session active; Quick Wins bar
- `web/src/acb_large_print_web/templates/fix_result.html` -- Re-Audit is now a POST form; grade on After box
- `web/src/acb_large_print_web/templates/privacy.html` -- updated audit workflow and share token wording

### Styles and Scripts
- `web/src/acb_large_print_web/static/css/style.css` -- dark mode, grade color tokens, convert result preview
- `web/src/acb_large_print_web/static/js/toast.js` -- new toast module
- `web/src/acb_large_print_web/static/js/upload.js` -- drag-and-drop zone

### Supporting modules
- `web/src/acb_large_print_web/report_cache.py` -- new; UUID-keyed HTML report cache with 1-hour TTL

### Documentation
- `CHANGELOG.md` -- v2.7.0 entry
- `docs/user-guide.md` -- streamlined flow, Quick Wins, shareable links, CMS Fragment redirect, Workflow H
- `docs/prd.md` -- v2.7.0 addendum table
- `docs/feature-flags.md` -- updated `GLOW_ENABLE_EXPORT_HTML` description
- `docs/RELEASE-v2.7.0.md` -- this file
- `docs/announcement-v2.7.0.md` / `.html` -- public release announcement

---

## Additional v2.7.0 Improvements

### 11. Streamlined Convert → Audit handoff

Convert results for HTML, Word, and EPUB output now offer "Audit This Document" as a one-click action that re-runs the audit on the converted file without re-uploading.

- New route: `POST /audit/from-convert`
- Resolves the converted file from the existing Convert session token using `secure_filename` with a path-traversal check
- Runs the standard audit pipeline and renders the full report (with share link)
- Gracefully falls back to the upload form when the session has expired

### 12. PDF and CSV downloads on the audit report

The "Share this report" section now offers two new download buttons alongside the share URL.

- **Download PDF** -- `GET /audit/share/<token>/pdf` renders the cached HTML to PDF via WeasyPrint, caches the result for the session lifetime, and serves `application/pdf`. When WeasyPrint is not installed the route returns 503 and the button is hidden.
- **Download CSV** -- `GET /audit/share/<token>/csv` returns the findings as a UTF-8 BOM CSV with a header preamble (filename, format, score, grade, profile, mode) followed by the standard column row. Encoded so Excel opens it cleanly.
- New module `csv_export.py` extracted from the email path; new helpers `report_cache.save_pdf()` / `load_pdf()` / `save_findings_data()` / `load_findings_data()`

### 13. Re-audit before/after diff banner

When an audit is re-run from a Fix session, the report shows a diff banner above the score:

- Score delta (e.g. "+12 points") and grade change
- Counts of fixed, persistent, and newly-introduced findings
- Lists the rule IDs that were resolved since the previous audit
- Implemented via a new `_compute_audit_diff()` helper in `routes/audit.py`; the fix result form propagates `prev_score` and a comma-joined list of rule IDs

### 14. Inline rule explanations

Each rule ID in the findings table is now wrapped in a `<details>` disclosure that shows the canonical description, ACB reference, and "Why this matters" rationale pulled from `rule_reference_metadata.py`.

- Keyboard-operable (Space/Enter to toggle)
- Opens in place without triggering layout shift
- Auto-fixable rules show an "Auto-fixable" badge inside the disclosure
- Hidden when printed

### 15. Roadmap page

Added `GET /roadmap` and `templates/roadmap.html`, linked from the footer alongside Privacy and Changelog. The page lists shipped highlights, in-progress work, and longer-term ideas.

### 16. Home page Settings link polish

On the main page Settings card, the "Personalization" chip is now a direct link to the Settings page (matching the card heading behavior), so users can open personalization defaults from either click target.

### 16. Global keyboard focus indicators and reduced motion

- `static/forms.css` now ships a global `:focus-visible` ring (3px solid `--color-primary` with 2px offset) that applies to all focusable elements; mouse clicks no longer leave a focus ring on buttons (`:focus:not(:focus-visible) { outline: none }`)
- All custom animations (toast slide-in, dropzone hover, consent modal fade) check `@media (prefers-reduced-motion: reduce)` and disable transitions when the user has requested reduced motion
- Consent modal body now scrolls (`max-height: 60vh`) so Decline/Accept stay visible on small viewports; modal traps focus while open and restores it to the trigger when closed

### 17. Test coverage

A new `web/tests/test_v270_new_routes.py` module adds 22 unit tests covering:

- `report_cache.save_findings_data()` / `load_findings_data()` / `save_pdf()` / `load_pdf()` -- roundtrip, bad token, missing share dir, TTL expiry
- `csv_export.findings_to_csv_bytes()` -- BOM, preamble, columns, empty list, filename safety
- `GET /audit/share/<token>/csv` -- cached path, 404 on unknown token, 404 on malformed token
- `GET /audit/share/<token>/pdf` -- cached path, 404 on unknown token, 503 when WeasyPrint missing
- `POST /audit/from-convert` -- expired and missing token error paths
- A CSS guard that fails if any shipped stylesheet introduces an `outline: none / 0 / transparent` rule outside the allowed `:focus:not(:focus-visible)` recipe, protecting the new global focus ring from future regressions

Full web suite: 266 passed, 20 skipped.

### 18. Visitor counter and tool usage analytics

**Visitor counter (footer badge):**

A new `visitor_counter.py` module tracks unique browser sessions using a single-row SQLite counter (`instance/visitor_counter.db`, WAL mode). The current count is displayed in the footer of every page as "Visitors: 1,234". One increment fires per session; static assets and `/health` are excluded.

**Tool usage analytics:**

A new `tool_usage.py` module records per-tool use counts in `instance/tool_usage.db`. Each of the six public tool endpoints (Audit, Fix, Convert, Template Builder, BITS Whisperer, Document Chat) increments its counter at the start of every successful submission. Increments are failure-safe (silently swallowed on DB error).

**Admin analytics dashboard (`/admin/analytics`):**

A new admin-only page shows total visitors, total tool uses, and a table of per-tool counts with share percentages and last-used timestamps. Linked from the Admin Queue dashboard.

**About page: Usage Statistics section:**

The public About page (`/about/`) now includes a "Usage Statistics" section showing visitor count, total tool uses, and a per-tool count table (zero-count tools are hidden until first use).

**New files:**
- `web/src/acb_large_print_web/visitor_counter.py`
- `web/src/acb_large_print_web/tool_usage.py`
- `web/src/acb_large_print_web/templates/admin_analytics.html`

**Changed files:**
- `web/src/acb_large_print_web/app.py` -- before_request hook + context processor injection
- `web/src/acb_large_print_web/templates/base.html` -- visitor count in footer
- `web/src/acb_large_print_web/templates/about.html` -- Usage Statistics section
- `web/src/acb_large_print_web/templates/admin_queue.html` -- link to analytics
- `web/src/acb_large_print_web/routes/about.py` -- passes tool_usage, total_uses, visitor_count to template
- `web/src/acb_large_print_web/routes/admin.py` -- new /admin/analytics route
- `web/src/acb_large_print_web/routes/audit.py`, `fix.py`, `convert.py`, `template.py`, `whisperer.py`, `chat.py` -- tool usage instrumentation
