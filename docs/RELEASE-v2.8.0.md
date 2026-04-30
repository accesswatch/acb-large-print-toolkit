# v2.8.0 Release Summary: April 30, 2026

## Overview

GLOW Accessibility Toolkit v2.8.0 is a community-driven release. Every feature in this release was sourced directly from requests made by members of the BITS community and the broader blind and low-vision community who rely on GLOW to make documents readable. Thank you to everyone who filed suggestions, participated in testing, and shared real-world feedback across the 2.7.0 and earlier releases. This release is yours.

Core highlights:

- **Scoring and grade integrity refinements** -- fixes grade/score drift edge-cases, aligns score math with weighted-penalty model, and clarifies grouped-findings are presentation-only
- **Quick Start full handoff** -- upload once in Quick Start, go directly to Audit, Fix, or Convert with your file already loaded; no second upload at any step
- **Passphrase-protected shared audit reports** -- optionally lock a share link so only people who know the passphrase can open the report or download the CSV/PDF copy
- **User-defined font sizes** -- override the ACB default sizes (18pt body, 22pt H1, 20pt H2-H6) per-session for Fix, Audit, and Template, with full pipeline propagation
- **Findings grouped by rule** -- audit reports consolidate all occurrences of the same rule into one row with an occurrence count badge and expandable location list; the findings table is dramatically shorter and easier to act on

---

## What Changed in v2.8.0

### 1. Scoring and grade integrity refinements

**Background:** A major pain point raised by users was trust in score/grade outputs when many repeated findings were present, especially after grouped-table rendering shipped.

**What changed:**

- Score computation and grade display were aligned to the same weighted-penalty model end-to-end.
- Repeated findings are now consistently charged as: base severity deduction per rule, plus a capped per-extra-occurrence surcharge.
- Grouped findings remain a reporting UX feature only; grouping does not alter score math.
- Fix result messaging now explicitly clarifies that filtered display mode (for readability) is separate from full post-fix scoring.

**Outcome:** Users now get stable score/grade behavior that matches the documented model and avoids perceived inflation when repeated findings are grouped in the table.

---

### 2. Quick Start full handoff -- audit, fix, and convert without re-uploading

The most frequently cited friction point after 2.7.0's single-upload cycle (Audit → Fix → Re-Audit) was the Quick Start landing page itself: it still required a second upload when routing to Audit or Convert. That gap is closed in 2.8.0.

**How it works:**

`GET /audit/?token=<upload_token>` and `GET /convert/?token=<upload_token>` now resolve the token to the existing upload session and render the respective form with a "Ready to audit: filename.docx -- no need to re-upload" notice in place of the file picker. A hidden `token` field and `prefill=1` flag are injected into the form. The POST handlers check for `prefill=1` and reuse the cached session file rather than calling `validate_upload`.

Fix already used the `fix.fix_from_audit_form` route from 2.7.0; the Quick Start dispatcher in `routes/process.py` now sends `fix` actions through the same route so all three tools share the single-upload model.

**Routes and files changed:**
- `routes/audit.py` -- `audit_form` (GET) and `_audit_single` (POST path) handle `?token=` and `prefill=1`
- `routes/convert.py` -- `convert_form` (GET) and `convert_submit` (POST) handle `?token=` and `prefill=1`
- `routes/process.py` -- `process_go` routes `fix` actions to `fix.fix_from_audit_form`
- `templates/audit_form.html` -- prefill notice and hidden `token`/`prefill` fields
- `templates/convert_form.html` -- prefill notice and hidden `token`/`prefill` fields

**Tests:** `tests/test_v270_new_routes.py::TestQuickStartHandoff` (3 new tests)

---

### 3. Passphrase-protected shared audit reports

**Background:** Several BITS member organizations need to share compliance reports with external reviewers (auditors, board liaisons, funders) without making those reports publicly readable by anyone who guesses or intercepts the URL. The link-only share model from 2.7.0 was not sufficient for these workflows.

**How it works:**

The Audit form now includes a **Share Link Protection (Optional)** fieldset. If the user enters a passphrase (4-200 characters), it is hashed immediately on the server using PBKDF2-SHA256 with 200,000 iterations and a 16-byte random salt generated per share. The hash is written to `passphrase.txt` in the share cache directory alongside the HTML report. The cleartext passphrase is never stored, never logged, and never returned to the browser.

**Share endpoint behavior:**
- `GET /audit/share/<token>` -- if a passphrase is set, serves the new `share_unlock.html` template instead of the report (status 200)
- `POST /audit/share/<token>` -- verifies the submitted passphrase via `verify_share_passphrase()`; on match, serves the report (200); on mismatch, re-renders the unlock form with an "Incorrect passphrase" error (401)
- `GET /audit/share/<token>/csv` -- if passphrase set and no `?p=` query param or wrong value, returns the unlock form as 401; with correct `?p=`, serves the CSV
- `GET /audit/share/<token>/pdf` -- same gate as CSV

The `?p=` query parameter path on CSV and PDF is designed for the unlock form's "Download now" deep links -- a single form submission can redirect to the download in one step.

The audit report's "Share or download this report" panel shows a notice when passphrase protection is enabled, reminding the reporter to send the passphrase through a separate channel (not in the same message as the link).

**New helpers in `report_cache.py`:**
- `set_share_passphrase(token, passphrase)` -- hashes and stores; returns `False` if share dir does not exist or passphrase is empty
- `share_requires_passphrase(token)` -- returns `True` if `passphrase.txt` exists in the share dir
- `verify_share_passphrase(token, candidate)` -- returns `True` if no passphrase is set (open share) or if PBKDF2 comparison succeeds

**New template:** `templates/share_unlock.html` -- accessible unlock form with `<input type="password">`, `autocomplete="new-password"`, `aria-invalid` on error, 4-200 char range attributes, and a return-to-home link.

**Tests:** `tests/test_v270_new_routes.py::TestSharePassphrase` (7 new tests covering set/verify, unprotected shares, wrong passphrase rejection, CSV query-param unlock)

---

### 4. User-defined font sizes

**Background:** Multiple BITS member organizations produce documents in formats that differ from the ACB Large Print defaults -- high-contrast handouts at 20pt body, large-format posters at 24pt+ headings, organization-specific style guides with alternative heading hierarchies. Previously GLOW always applied 18/22/20pt regardless of what the user needed.

**How it works:**

The Fix and Template forms now include a **Font Sizes (Optional)** fieldset with inputs for body (Normal), Heading 1, Heading 2, Heading 3, Heading 4, Heading 5, and Heading 6. Empty fields keep the ACB defaults. Submitted values are clamped to the range 8pt-96pt server-side.

A `style_size_overrides` keyword argument threads the overrides through the full pipeline:
- `auditor.audit_document()` uses `effective_min_body_pt()` to set the minimum expected body size and `effective_styles()` for per-style expected sizes
- `fixer.fix_document()` applies `effective_styles()` so the fixer raises text to the user-specified target
- `template.create_template()` uses `effective_styles()` so the generated `.dotx` uses the user-specified sizes

When a custom body size is set, `List Bullet` and `List Number` styles are updated to match it so list text stays in sync with body text.

**New helpers in `desktop/src/acb_large_print/constants.py`:**
- `effective_styles(overrides)` -- returns a copy of `ACB_STYLES` with user overrides applied
- `effective_min_body_pt(overrides)` -- returns the effective body size minimum

**TypeScript mirror in `office-addin/src/constants.ts`:**
- `effectiveStyles(overrides: StyleSizeOverrides)` and `effectiveMinBodyPt(overrides)` with `StyleSizeOverrides` type

**Web routes:**
- `routes/fix.py` -- parses `body_size_pt`, `h1_size_pt` ... `h6_size_pt` form fields
- `routes/template.py` -- same parsing

**CSS:** New `.font-size-grid` rule in `static/forms.css` lays out the seven size inputs in a responsive grid.

---

### 5. Findings grouped by rule

**Background:** Documents with systematic formatting problems (wrong font applied to every paragraph, no alt text on every image) generated audit reports with dozens or hundreds of near-identical rows. Users had to scroll past 40 "Arial not used" rows to find structural issues. Reviewers receiving shared reports frequently asked for a summary view.

**How it works:**

A new `_findings_table.html` Jinja2 partial replaces the inline findings table in `audit_report.html`, `audit_batch_report.html`, and `audit_batch_individual_report.html`. The partial receives the raw findings list and groups occurrences by `rule_id` before rendering. Each rule gets one row. For rules with a single occurrence, the location text is shown inline. For rules with multiple occurrences, a `<details>` / `<summary>` disclosure shows "Show all N occurrences" and expands to a list of locations.

**New CSS in `static/forms.css`:**
- `.occurrence-count` -- base badge style
- `.occurrence-count--single` -- muted single-occurrence variant
- `.occurrence-count--multi` -- highlighted multi-occurrence variant (distinct color)
- `.occurrence-list` and `.occurrence-list__item` -- location list in the disclosure

**CSV export is unchanged** -- `csv_export.py` still emits one row per occurrence so spreadsheet analysis is unaffected.

---



## Files Changed

### Routes
- `web/src/acb_large_print_web/routes/audit.py` -- `audit_form` prefill handling; `_audit_single` `prefill=1` support; `share_passphrase_set` flag passed to template; `shared_report` now handles GET (unlock form) and POST (passphrase verify); `shared_report_csv` and `shared_report_pdf` gated by `_share_unlock_required`
- `web/src/acb_large_print_web/routes/convert.py` -- `convert_form` and `convert_submit` prefill handling
- `web/src/acb_large_print_web/routes/process.py` -- `fix` action routed to `fix.fix_from_audit_form`
- `web/src/acb_large_print_web/routes/fix.py` -- `style_size_overrides` wired to `fix_document()`
- `web/src/acb_large_print_web/routes/template.py` -- `style_size_overrides` wired to `create_template()`

### Templates
- `web/src/acb_large_print_web/templates/audit_form.html` -- "Share Link Protection" fieldset; "Font Sizes" fieldset
- `web/src/acb_large_print_web/templates/convert_form.html` -- prefill notice and hidden fields
- `web/src/acb_large_print_web/templates/audit_report.html` -- `share_passphrase_set` notice in share panel
- `web/src/acb_large_print_web/templates/fix_form.html` -- "Font Sizes" fieldset
- `web/src/acb_large_print_web/templates/template_form.html` -- "Font Sizes" fieldset
- `web/src/acb_large_print_web/templates/fix_result.html` -- Re-Audit form now accepts optional `share_passphrase` to protect shares generated from the Fix → Re-Audit flow
- `web/src/acb_large_print_web/templates/share_unlock.html` -- new; passphrase unlock form
- `web/src/acb_large_print_web/templates/_findings_table.html` -- new; grouped findings partial
- `web/src/acb_large_print_web/templates/audit_batch_report.html` -- uses `_findings_table.html` partial

### Styles
- `web/src/acb_large_print_web/static/forms.css` -- `.font-size-grid`, occurrence-count badge classes, occurrence-list styles

### Supporting modules
- `web/src/acb_large_print_web/report_cache.py` -- `set_share_passphrase()`, `share_requires_passphrase()`, `verify_share_passphrase()`
- `desktop/src/acb_large_print/constants.py` -- `effective_styles()`, `effective_min_body_pt()`
- `office-addin/src/constants.ts` -- `effectiveStyles()`, `effectiveMinBodyPt()`, `StyleSizeOverrides` type
- `office-addin/src/auditor.ts`, `fixer.ts`, `template.ts` -- `style_size_overrides` threading

### Tests
- `web/tests/test_v270_new_routes.py` -- 10 new tests: `TestSharePassphrase` (7) and `TestQuickStartHandoff` (3)

### Documentation
- `CHANGELOG.md` -- v2.8.0 entry; `[Unreleased]` section reset
- `docs/user-guide.md` -- "What's New in 2.8.0" section; passphrase subsection; font size overrides subsection
- `docs/prd.md` -- v2.8.0 addendum table; GLOW 3.0.0 Speech Platform section
- `docs/RELEASE-v2.8.0.md` -- this file
- `docs/announcement-v2.8.0-combined.md` -- public release announcement

---

## Upgrade Notes

### No breaking changes

All existing audit, fix, convert, and share URLs continue to work without modification. The passphrase feature is opt-in -- shares without a passphrase behave identically to 2.7.0.

### Font size defaults are unchanged

The ACB defaults (18pt body, 22pt H1, 20pt H2-H6) are unchanged. The new font size fields are optional; leaving them blank produces identical output to 2.7.0.

### Report cache is backward-compatible

Existing share tokens generated by 2.7.0 deployments will not have a `passphrase.txt` file and will behave as open (no passphrase required) shares. No migration needed.

---

## Test Suite

**276 passed, 20 skipped** (10 new tests added in this release; 266 from prior baseline)
