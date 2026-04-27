Feature Flags
=============

Purpose
-------
Server-side feature flags allow operators to enable/disable functionality at runtime without redeploying or changing environment variables. They are useful for:

- Gradual rollouts
- Emergency disable of features (e.g., AI chat) when upstream providers fail
- A/B experiments (future)

Implementation
--------------
- Flags are persisted in JSON at `instance/feature_flags.json`.
- The admin UI (Admin → Feature flags) exposes a simple UI to toggle flags.
- The `acb_large_print_web.feature_flags` module provides `get_flag`, `set_flag`, `get_all_flags`, and `reset_defaults`.
- `acb_large_print_web.ai_features` prefers persisted flags and falls back to environment variables.

Operational notes
-----------------
- Flag changes apply immediately across worker processes that share the instance volume. For multi-worker deployments, ensure the `instance/` path is a shared volume.
- Defaults are designed to preserve existing behavior (all AI features enabled unless OpenRouter key is missing).

Seeding and persistence
-----------------------
- On first app startup (when `instance/feature_flags.json` does not exist) the application now writes a seeded file with canonical defaults. This ensures there is always a persisted source-of-truth for flags and avoids ambiguity between environment-only flags and persisted flags.
- The seeded defaults are defined in `web/src/acb_large_print_web/feature_flags.py` under `_DEFAULTS`.
- The `instance/feature_flags.json` file must be persisted across restarts and mounted into containers for consistent behavior between worker processes.

Testing
-------
- `web/tests/conftest.py` provides `feature_flags_fixture` to mutate flags for a test and restore them after.

Impact of disabling AI flags
----------------------------
- Disabling `GLOW_ENABLE_AI` or feature-specific flags such as `GLOW_ENABLE_AI_CHAT` and `GLOW_ENABLE_AI_WHISPERER` immediately hides AI UI elements in templates (Jinja guards read persisted flags) and causes AI-dependent routes to return 404 or tests to skip based on the guard logic.
- Health and readiness endpoints will reflect flag state: AI readiness will be `not-ready` if flags are disabled even if credentials are present.
- Disabling flags is a fast operator kill-switch that does not require redeploy — however changes are persisted in `instance/feature_flags.json` and thus survive restarts.

CI / Testing guidance
---------------------
- Most live AI tests are already guarded with `pytest.mark.ai_live` or conditional skips that check `ai_chat_enabled()` / `ai_whisperer_enabled()`. The repository includes `web/tools/sweep_ai_tests.py` to heuristically scan tests for unguarded AI references; run it after modifying tests.
- Recommended practice for new AI-dependent tests:
	- Mark integration tests that make live OpenRouter calls with `@pytest.mark.ai_live` and rely on `web/tests/conftest.py` to skip when AI is disabled.
	- For Whisperer/audio tests, use `@pytest.mark.ai_whisper`.
	- Use `feature_flags_fixture.set('GLOW_ENABLE_AI_CHAT', False)` within unit tests that need to assert UI behavior when AI is off.

Runbook: disabling AI in production
----------------------------------
1. Navigate to Admin → Feature flags and toggle the appropriate `GLOW_ENABLE_*` flag(s).
2. Confirm the `instance/feature_flags.json` was updated (path: `<app instance>/feature_flags.json`).
3. Check `/health` to verify AI readiness shows `not-ready` and that web UI no longer exposes AI actions.
4. If disabling due to upstream outage, optionally alert the team and note the timestamp in the incident log (consider adding telemetry/audit in a future change).

Examples
--------
- Check current flags programmatically (Python REPL inside app context):

```python
from acb_large_print_web import feature_flags
with app.app_context():
		print(feature_flags.get_all_flags())
```

- Toggle a flag from admin UI — the JSON file will be updated under `instance/feature_flags.json`.

Next steps
----------
- Add RBAC for who can change flags (currently admin users only).
- Consider a migration to a server-side DB (SQLite or Postgres) for audit trails and multi-node consistency.
- Add telemetry for flag changes for audit and rollback analysis.
