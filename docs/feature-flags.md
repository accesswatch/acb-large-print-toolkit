Feature Flags
=============

Purpose
-------
Server-side feature flags allow operators to enable or disable functionality at runtime without redeploying. They are useful for:

- Gradual rollouts
- Emergency disable of features (e.g., AI chat) when upstream providers fail
- Scoped enablement of subfeatures for experiments or restricted deployments

Implementation
--------------
- Flags are persisted in `instance/feature_flags.json` by default (or in `instance/feature_flags.db` when `sqlite` backend is configured).
- The admin UI (Admin → Feature flags) exposes a grouped UI (AI / Core / Advanced) with tabs and accordions, a master AI switch, per-flag metadata, and a migration helper.
- The `acb_large_print_web.feature_flags` module provides `get_flag`, `set_flag`, `get_all_flags`, and `reset_defaults`.
- `acb_large_print_web.ai_features` resolves flags in this order: explicit environment variable → persisted server-side flag → module defaults. Environment variables override persisted flags for immediate operator control.

Operational notes
-----------------
- Flag changes apply immediately across worker processes that share the instance volume. For multi-worker deployments, ensure the `instance/` path is a shared volume or use a centralized backend.
-- Defaults are intentionally conservative for AI features: AI flags default to `false`. Non-AI GLOW flags default to `true` so core workflows are available by default.

Seeding and persistence
-----------------------
- On first app startup (when `instance/feature_flags.json` does not exist) the application writes a seeded file with canonical defaults. This ensures there is always a persisted source-of-truth for flags and avoids ambiguity between environment-only flags and persisted flags.
- The seeded defaults are defined in `web/src/acb_large_print_web/feature_flags.py` under `_DEFAULTS`.
- The `instance/feature_flags.json` file must be persisted across restarts and mounted into containers for consistent behavior between worker processes.

Testing
-------
- `web/tests/conftest.py` provides `feature_flags_fixture` to mutate flags for a test and restore them after.

Impact of disabling AI flags
----------------------------
- Disabling `GLOW_ENABLE_AI` or feature-specific flags such as `GLOW_ENABLE_AI_CHAT` and `GLOW_ENABLE_AI_WHISPERER` immediately hides AI UI elements in templates (Jinja guards consult the resolved flag values) and causes AI-dependent routes to raise `AIFeatureDisabled` or return 404/503 behavior depending on gating.
- The admin UI enforces cascade behavior: turning off the master `GLOW_ENABLE_AI` will force AI subfeatures off server-side; the UI also disables child checkboxes client-side for clarity.
- Health and readiness endpoints will reflect flag state: AI readiness will be `not-ready` if flags are disabled even if credentials are present.

CI / Testing guidance
---------------------
- Most live AI tests are guarded with `pytest.mark.ai_live` or conditional skips that check `ai_chat_enabled()` / `ai_whisperer_enabled()`.
- Use `web/tools/sweep_ai_tests.py` to heuristically scan tests and templates for unguarded AI references; consider adding it to CI lint steps.
- Recommended practice for new AI-dependent tests:
	- Mark integration tests that make live OpenRouter calls with `@pytest.mark.ai_live` and rely on `web/tests/conftest.py` to skip when AI is disabled.
	- For Whisperer/audio tests, use `@pytest.mark.ai_whisper`.
	- Use `feature_flags_fixture.set('GLOW_ENABLE_AI_CHAT', False)` within unit tests that need to assert UI behavior when AI is off.

Runbook: disabling AI in production
----------------------------------
1. Navigate to Admin → Feature flags and toggle the appropriate `GLOW_ENABLE_*` flag(s).
2. Confirm the `instance/feature_flags.json` (or sqlite backend) was updated.
3. Check `/health` to verify AI readiness shows `not-ready` and that web UI no longer exposes AI actions.
4. Communicate the change to on-call and update incident notes. For emergencies you may temporarily set an env var to override persisted flags for immediate behavior (env overrides are not persisted).

Examples
--------
- Check current flags programmatically (Python REPL inside app context):

```python
from acb_large_print_web import feature_flags
with app.app_context():
		print(feature_flags.get_all_flags())
```

- Toggle a flag from admin UI — the JSON file will be updated under `instance/feature_flags.json` (or the sqlite backend will be written to).

Next steps
----------
- Add RBAC for who can change flags (currently admin users only).
- Consider a centralized backend (Postgres/Redis) or a tiny API-backed feature flag service for multi-node deployments and audit trails.
- Add telemetry/webhook integration to record flag changes for incident response.

Flags reference
---------------
This section documents every `GLOW_ENABLE_*` feature flag the application currently supports. Each entry lists the flag name, default value (as shipped), effect, and operational notes.

- **`GLOW_ENABLE_AI`** (default: `false`)
	- Purpose: Master AI enable switch. When `false`, all user-facing AI features are hidden and AI-dependent routes raise `AIFeatureDisabled` or return gated responses.
	- Notes: Toggling this flag in the admin UI cascades and forces all AI subfeatures off. Environment variable `GLOW_ENABLE_AI` overrides persisted settings for immediate effect.

- **`GLOW_ENABLE_AI_CHAT`** (default: `false`)
	- Purpose: Enables the Document Chat UI and associated chat routes.
	- Notes: When `false`, chat UI elements are hidden. Tests marked with `@pytest.mark.ai_live` should be skipped when chat is off.

- **`GLOW_ENABLE_AI_WHISPERER`** (default: `false`)
	- Purpose: Enables the BITS Whisperer (audio transcription) UI and routes.
	- Notes: When `false`, Whisperer entry points are removed and audio POST handlers reject requests as unsupported.

- **`GLOW_ENABLE_AI_HEADING_FIX`** (default: `false`)
	- Purpose: Enables AI-powered heading detection/refinement used in the Fix workflow.
	- Notes: When `false`, heading-detection form options that request AI are ignored and AI-based heuristics are disabled.

- **`GLOW_ENABLE_AI_ALT_TEXT`** (default: `false`)
	- Purpose: Enables AI-assisted alt-text suggestions UI and helpers.
	- Notes: When `false`, AI alt-text controls are hidden and automated suggestions are disabled.

- **`GLOW_ENABLE_AI_MARKITDOWN_LLM`** (default: `false`)
	- Purpose: Enables MarkItDown LLM enhancements and integration points.
	- Notes: When `false`, any experimental LLM-driven MarkItDown features are turned off.

Additional non-AI GLOW flags (defaults: `true`)

-- **`GLOW_ENABLE_AUDIT`** (default: `true`)
	- Purpose: Enable audit workflows and UI. When `false` certain audit entry points are hidden.

-- **`GLOW_ENABLE_CHECKER`** (default: `true`)
	- Purpose: Enable the accessibility checker UI and automations.

-- **`GLOW_ENABLE_CONVERTER`** (default: `true`)
	- Purpose: Enable document conversion pathways (MarkItDown, Pandoc hooks).

-- **`GLOW_ENABLE_TEMPLATE_BUILDER`** (default: `true`)
	- Purpose: Enable template builder UI features.

-- **`GLOW_ENABLE_WORD_SETUP`** (default: `true`)
	- Purpose: Enable Word setup helpers and instructions.

-- **`GLOW_ENABLE_MARKDOWN_AUDIT`** (default: `true`)
	- Purpose: Enable markdown-specific audit features and integrations.

Backend and metadata
--------------------
- The application supports two storage backends for persisted feature flags:
	- `json` (default) — flags are stored in `instance/feature_flags.json`.
	- `sqlite` — optional SQLite DB at `instance/feature_flags.db` providing `flags` table with `updated_at` metadata.
- Configure the backend via the environment variable `FEATURE_FLAGS_BACKEND=json|sqlite`.
- When using the `sqlite` backend, a `migrate_json_to_sqlite()` helper exists to copy existing JSON flags into the DB. The admin UI displays the active backend and per-flag `updated_at` timestamps and exposes an idempotent migration button.

Admin UI behavior
-----------------
- The admin Flags page (`Admin → Feature flags`) shows the active backend, grouped tabs (AI / Core / Advanced), each flag's current value, and a last-modified timestamp when available. The page includes a master AI switch that cascades to child AI flags client-side and server-side.
- Resetting defaults writes the recommended defaults into the chosen backend and is accessible from the admin UI.

API / Python helpers
--------------------
- `acb_large_print_web.feature_flags.get_flag(name, default=None)` — read boolean flag (falls back to module `_DEFAULTS` when not present; environment vars can override persisted values).
- `acb_large_print_web.feature_flags.set_flag(name, value)` — persist a flag value to the active backend.
- `acb_large_print_web.feature_flags.get_all_flags()` — returns a dict of all known flags and their boolean values.
- `acb_large_print_web.feature_flags.reset_defaults()` — reset persisted flags to the module defaults.
- `acb_large_print_web.feature_flags.get_flag_meta(name)` — returns `{updated_at, backend}` metadata for a flag when available.
- `acb_large_print_web.feature_flags.migrate_json_to_sqlite()` — convenience helper to migrate JSON store into SQLite (best-effort).

Operational recommendations
--------------------------
- For single-node or simple container deployments, `json` backend is sufficient and easy to mount.
- For multi-node deployments or when audit/history is required, use `sqlite` or a central DB and ensure the `instance/` path is shared or replaced by a centralized service.
- Consider adding an audit log or webhook when flags change so on-call and incident tooling can be notified automatically.

Maintenance and rollout
-----------------------
- When toggling flags in production, follow the Runbook above: toggle via admin UI, verify `/health`, and communicate to the team.
- If you plan to change the backend in a running deployment, run `migrate_json_to_sqlite()` (or use the admin migration button when implemented) and verify values match before switching.

Testing notes
-------------
- Unit and integration tests should use `feature_flags_fixture` (in `web/tests/conftest.py`) or call `set_flag()` inside the test's app context and restore afterwards.
- Use `web/tools/sweep_ai_tests.py` to detect unguarded AI references in tests and templates; run it as part of local pre-commit checks or CI lint steps.
