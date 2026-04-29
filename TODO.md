# TODO — GLOW Accessibility Toolkit

This file is a human-readable summary of in-progress tasks tracked by the development agent.

## In Progress

- [x] Add unit tests for admin flags POST handler (cascade & audit)
- [x] Add assertions to admin auth tests for accessible inputs

## Pending (next actions)

_(none — all items completed)_

## v2.7.0 Release Roadmap

Status as of April 29, 2026 (branch `release/2.7.0`).

### Out of scope (locked)

- Batch / multi-file upload, queue, ZIP-of-many — defer to a future release
- Office Web Add-in (Word ribbon) feature work — not v2.7.0
- Desktop wxPython feature parity for new web flows — not v2.7.0

### Done in v2.7.0

- [x] `report_cache.py` extended: `save_findings_data` / `load_findings_data` / `save_pdf` / `load_pdf` (1 hour TTL, UUID-validated)
- [x] `csv_export.py` (new): `findings_to_csv_bytes` (UTF-8 BOM, comment preamble, `auto_fixable` yes/no, `help_urls` joined) and `safe_filename_stem`
- [x] Convert → Audit handoff (`audit.audit_from_convert` POST `/audit/from-convert`, button on convert result page)
- [x] PDF download of shared report (`audit.shared_report_pdf` GET `/audit/share/<share_token>/pdf`, WeasyPrint, lazy + cached, gated on `feature_weasyprint_enabled`)
- [x] CSV download of findings (`audit.shared_report_csv` GET `/audit/share/<share_token>/csv`)
- [x] Re-audit diff view (audit_report.html `<aside class="diff-callout">` with cleared / persistent / new counts and rule list; `prev_score` and `prev_rule_ids` carried via fix → audit form)
- [x] Inline rule explanations (`<details class="finding-explain">` per finding row; description, ACB reference, auto-fixable badge)
- [x] **Site-wide visible focus indicator** (3px high-contrast `:focus-visible` ring + box-shadow halo, applies globally; fixes Michael's "no visual indicator on Tab" report)
- [x] **Consent form scroll fix** (modal backdrop now `overflow-y: auto`, modal aligns to top, inner scroll region collapses on small viewports / heavy zoom; fixes Michael's "cannot reach Continue button" report)
- [x] `prefers-reduced-motion` global override in `forms.css`
- [x] Audit guardrail regressions fixed (landmark `<section>` → `<aside>`; convert tests updated to result-page contract)

### Remaining for v2.7.0 (in priority order)

#### 1. Tests for new routes (must precede commit)

- [ ] `audit_from_convert` happy path: token + auditable file → 200 with audit report
- [ ] `audit_from_convert` no-files-found: empty temp dir → 400 with `audit_form` error
- [ ] `audit_from_convert` expired token: missing temp dir → 400 with session-expired error
- [ ] `shared_report_csv`: known share token → `text/csv`, body starts with `# filename,`, columns match spec
- [ ] `shared_report_csv`: bad/expired token → 404
- [ ] `shared_report_pdf`: WeasyPrint flag off → 503
- [ ] `shared_report_pdf` with flag on → `application/pdf`; second request returns same bytes (cache hit)
- [ ] Re-audit diff: POST to `audit_from_fix` with `prev_score=80` and `prev_rule_ids` → response contains "Score improved", cleared/persistent/new wording
- [ ] `<details class="finding-explain">` block present in audit_report response
- [ ] CSS guard test: assert no new `outline: none` / `outline: 0` introduced in `static/*.css`

#### 2. Update docs

- [ ] `CHANGELOG.md` — `### Added` (Convert→Audit, PDF/CSV export, re-audit diff, inline rule explanations, global focus ring, reduced-motion); `### Fixed` (consent modal Continue button, missing focus indicator on Tab — credit Michael)
- [ ] `docs/user-guide.md` — new sections for "Audit your converted file", "Download findings as CSV", "Download report as PDF", "What changed since last audit"
- [ ] `docs/prd.md` — mark v2.7.0 features delivered; explicitly list batch + add-in as deferred
- [ ] `docs/RELEASE-v2.7.0.md` — release notes draft
- [ ] `docs/announcement-v2.7.0.{md,html}` — short user-facing post (BITS membership voice)
- [ ] Privacy / consent text — confirm `report.pdf` cache is covered by the existing 1 hour TTL statement (likely no change needed)

#### 3. Rebuild, verify, commit

- [ ] `python scripts/build-doc-pages.py`
- [ ] `cd web; $env:PYTHONPATH="src"; python -m pytest tests/ -q` (target ≥ 252 passed, 20 skipped)
- [ ] `python scripts/check-config-consistency.py`
- [ ] `python scripts/check-version-consistency.py`
- [ ] One feature commit + one docs commit on `release/2.7.0`

### Deferred (tracked in `/memories/repo/glow-followups.md`)

- [ ] `role="tablist"` cleanup on `base.html:21`
- [ ] TypeScript Office add-in cross-implementation sync (deferred with the add-in itself)
- [ ] Desktop CLI/GUI port of CSV export and re-audit diff (candidate for v2.8)

## Done

- [x] Kill all terminals and run WSL setup (user-run)
- [x] Provision WSL venv and install deps — created `~/glow-venv` (Python 3.13) in WSL Linux home; installed `web[dev]` and `desktop` as editable installs.
- [x] Run migration in WSL — verified `feature_flags` JSON backend (31 flags) loads cleanly; `migrate_json_to_sqlite()` ran without error. No SQLite migration needed (default backend is `json`).
- [x] Create WSL-side venv in WSL home — venv lives at `~/glow-venv` in the Linux home to avoid cross-OS symlink/executable errors.
- [x] Run web tests in WSL — 237 passed, 21 skipped after fixing 3 failures:
  - Fixed `from web.tests.helpers import ...` → `from tests.helpers import ...` in `test_admin_flags.py`
  - Fixed `assert_flag_rendered` helper to check `for="flag-{name}"` label association instead of auto-generated title-case label text that didn't match custom template labels
  - Fixed `test_admin_login_page_loads` to mock `email_configured` (email form only renders when SMTP is configured)
  - Fixed `admin_request_access` route + template to pass/use `form_disabled=True` so the email form is suppressed on 503 (no email config)

## Notes / Next Steps

- To run the new tests locally (Windows PowerShell) inside the project venv:

```powershell
& .\.venv\Scripts\Activate.ps1
python -m pytest -q web/tests/test_admin_flags.py::test_admin_ai_cascade_persists_and_audit
```

- For WSL runs, prefer the WSL instructions in `scripts/bootstrap-wsl.sh` and use the WSL dev compose if docker-based dev is desired.

If you'd like, I can also open a PR with these tests and the `TODO.md` update.
