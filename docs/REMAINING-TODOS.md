# Remaining Work (short session-friendly order)

This file lists pending tasks and a suggested small-first ordering so you can resume later.

Priority: small/quick tasks first (can be done in 5-15 minutes), larger sweeps later.

## 1) Add new flags to Admin UI (small)
- File: `web/src/acb_large_print_web/routes/admin.py`
- Goal: Add all new `GLOW_ENABLE_*` keys to the `feature_keys` list so the admin UI can toggle them.
- Estimated: 5-10 minutes
- Status: (will be updated by the assistant)

## 2) Update admin cascade rules (small)
- File: `web/src/acb_large_print_web/routes/admin.py`
- Goal: Ensure `GLOW_ENABLE_AI` master flag cascades to AI subfeatures (already present), and consider cascading document-type toggles if desired.
- Estimated: 5-10 minutes
- Status: not started

## 3) Sweep templates to hide disabled text (medium)
- Files: `web/src/acb_large_print_web/templates/**`, `docs/user-guide.md` and rendered user-guide pages
- Goal: Remove/hide any About/User Guide sections, nav tabs, or UI text referencing features that are disabled by flags (e.g., AI chat, Whisperer, DAISY, PDF features).
- Estimated: 30-90 minutes (depends on template count)
- Status: not started

## 4) Add flags to injector and template helpers (done)
- File: `web/src/acb_large_print_web/app.py`
- Goal: Inject feature flags into templates (convenience booleans like `feature_pdf_enabled`)
- Status: completed

## 5) Admin docs for bootstrap and flag management (small)
- File: `docs/adminsetup.md` (created)
- Goal: Provide operator guidance for bootstrap, rotating secrets, and managing flags via UI or `instance/feature_flags.json`.
- Status: created

## 6) Update admin UI templates (`admin_flags.html`) (small)
- File: `web/src/acb_large_print_web/templates/admin_flags.html`
- Goal: Ensure the UI lists the new flags and works with metadata & audit rows.
- Estimated: 10-20 minutes
- Status: not started

## 7) Gate AI tests and CI (medium)
- Files: `tests/*`, CI workflow files
- Goal: Add pytest markers/fixtures to skip AI tests when AI is not enabled; update CI to run AI tests only when `GLOW_ENABLE_AI` is set.
- Estimated: 30-60 minutes
- Status: not started

## 8) Migrate persisted flags / audit verification (optional)
- Files: `instance/feature_flags.json` -> `instance/feature_flags.db` migration tests
- Goal: Verify migration helper and audit entries integrity. Optionally migrate live data.
- Estimated: 20-40 minutes
- Status: not started

---

Notes:
- If you have to leave, this file describes the immediate next steps and estimated durations.
- I will now perform step #1 (small) and update the status below when done.
