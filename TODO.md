# TODO — GLOW Accessibility Toolkit

This file is a human-readable summary of in-progress tasks tracked by the development agent.

## In Progress

- [x] Add unit tests for admin flags POST handler (cascade & audit)
- [x] Add assertions to admin auth tests for accessible inputs

## Pending (next actions)

_(none — all items completed)_

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
