# GLOW Accessibility Tracking

Last updated: May 13, 2026

This file tracks current accessibility and crawl findings for the GLOW web app. It is intended to stay practical: confirmed user-facing issues first, manual-review items second, and explicitly excluded routes last.

## Current Position

You are right on track: a raw Flask route list is not the right accessibility scope by itself. It includes health checks, downloads, admin-only routes, dynamic token routes, and feature-gated AI pages that may not be visible or enabled in production.

The correct scan scope is:

- User-visible navigation and footer links rendered with the current feature flags and provider configuration.
- Same-origin HTML pages discovered from those visible links.
- Source-derived route checks only as a completeness backstop, with feature-gated, dynamic, download, and internal routes classified separately.

## Latest Evidence

Sources used:

- urlCheck same-origin crawl of `https://glow.bits-acb.org` with the GLOW automation consent header.
- urlCheck source-derived route probe built from the Flask route map.
- Direct HTTP checks for feature-gated routes.
- Current local feature flags in `instance/feature_flags.json`.

Current feature-gate interpretation:

- `GLOW_ENABLE_AI_WHISPERER` is `false`; BITS Whisperer should not appear in public navigation and `/whisperer/` should not be treated as a public crawl gap while disabled.
- `GLOW_ENABLE_AI_CHAT` is `false`; Document Chat should not appear in public navigation and `/chat/` should not be treated as a public crawl gap while disabled.
- `GLOW_ENABLE_AI_ALT_TEXT` is `true` locally, but the route is also provider-gated by `ai_alt_text_enabled()`. It should be scanned only when it appears in rendered navigation or when production provider configuration enables it.
- `/health` is an orchestration endpoint, not a user-facing HTML page. Do not count it as an accessibility page failure.

## Confirmed Issues To Address

Current source status: all known deterministic axe findings from the latest completed crawl have source fixes. Production still needs a post-deploy re-scan before this can be called verified in the live environment. Local crawl testing was stopped because it was hanging in this environment; use production or a deployed staging target for the next count.

### 1. Production still showed heading-order issues on `/audit/` and `/template/`

Status: Fixed in source, needs production verification after deploy.

Evidence from latest production crawl:

| URL | Rule | Impact | Nodes |
| --- | --- | --- | --- |
| `https://glow.bits-acb.org/audit/` | `heading-order` | moderate | 1 |
| `https://glow.bits-acb.org/template/` | `heading-order` | moderate | 1 |

Notes:

- These were already fixed in GLOW commits `e3900c2` on `main` and `656d435` on `feature/7.0.0` by promoting top-level in-content headings to `h2`.
- Re-scan production after deployment before reopening code work.

### 2. Production crawl found old public `.md` links returning 404

Status: Fixed in source, needs production verification after deploy.

Evidence from production crawl before/around deployment:

- `https://glow.bits-acb.org/README.md`
- `https://glow.bits-acb.org/guide/deployment.md`
- `https://glow.bits-acb.org/web/README.md`
- `https://glow.bits-acb.org/guide/prd.md`
- `https://glow.bits-acb.org/prd/deployment.md`

Notes:

- Public docs should link to HTML routes, not raw Markdown files.
- GLOW now has a public `/deployment/` page.
- The source and generated partials were fixed in commits `e3900c2` and `656d435`.
- Direct check later returned `200` for `/deployment/`.

### 3. Feature-gated routes must not leak into public navigation when disabled

Status: Watch item.

Routes observed as `404` in direct/source-derived checks:

- `/chat/`
- `/whisperer/`
- `/alt-text/`

Current interpretation:

- `/chat/` and `/whisperer/` are not current public gaps because their feature gates are disabled and they were not discovered in the visible homepage crawl.
- `/alt-text/` needs conditional review: scan it only when production renders the Alt-Text Helper link or provider configuration enables `ai_alt_text_enabled()`.

Action:

- Build future scan seed lists from rendered navigation/footer links, not just Flask routes.
- Keep source-route probes, but classify feature-gated routes as disabled/internal unless visible in rendered HTML.

## Manual Review Items

The latest homepage crawl reported no additional confirmed axe violations beyond the heading-order findings above. It did report incomplete/manual-review checks. The Rules Reference duplicate-ID items have now been fixed in source, and the Quick Start upload panel now uses solid high-contrast backgrounds so axe can calculate text contrast reliably.

| Rule | Count | Notes |
| --- | ---: | --- |
| `color-contrast` | 17 | Fixed in source for known gradient-backed Quick Start text; needs re-scan after deploy to confirm zero incomplete results. |
| `duplicate-id-aria` | 1 | Fixed in source by removing the stale duplicate `filter-type` control from Rules Reference. |
| `form-field-multiple-labels` | 1 | Fixed in source by removing the stale duplicate `filter-type` control from Rules Reference. |

Last completed pre-deploy crawl evidence after the first fixes showed `0` confirmed axe violations, `0` crawl 404s after the Markdown link cleanup, and remaining color-contrast incomplete checks only. A final local count was intentionally not used because local crawling was stopped.

Action:

- Re-run the crawl after deployment and move any remaining items back to confirmed issues only if they reproduce against the updated source.
- Use a production or deployed staging target for the next count, not the local Flask development server.

## Routes Excluded From Normal Page Accessibility Crawl

These routes may exist in Flask but should not be counted as public page gaps without additional context:

- Health/status machine endpoints: `/health`.
- Download/export endpoints: `/anthem/download`, `/magic/pronunciation/export.csv`, `/braille/download`, dynamic `/convert/download/...`, dynamic `/audit/share/.../csv`, and similar file-producing routes.
- Dynamic token/job routes that require prior workflow state: `/audit/share/<share_token>`, `/convert/preview/<token>/<filename>`, `/site-audit/jobs/<job_id>`, `/whisperer/retrieve/<token>`, and related routes.
- Disabled feature-gated AI routes: `/chat/`, `/whisperer/`, and any provider-gated AI route that is not rendered in visible navigation.
- Admin-only pages beyond the public sign-in or request-access flows.

## urlCheck Status

urlCheck fork: `accesswatch/urlCheck`.

Relevant pushed commits:

- `7af9396` - Adds crawl automation support, generic custom headers, HTTP error capture, non-HTML crawl skipping, and upstream contribution notes.
- `adb4c2d` - Forces modern Edge `--headless=new` when invisible mode is active.

Useful behavior now available:

- `--crawl` recursively discovers same-origin HTML pages until `--crawl-limit`.
- `--crawl` defaults to invisible/headless browsing unless `--authenticate` is set.
- `--header "Name: Value"` sends reusable custom headers.
- `--header-env Name=ENV_VAR` sends environment-backed custom headers for secret values.
- `--glow-consent-token` remains as a GLOW convenience, but the generic header options are the upstream-friendly path for Jamal.
- HTTP errors such as `404` are reported explicitly under failed scans.

## Next Scan Plan

1. Deploy the latest GLOW commits.
2. Generate a scan seed from rendered production navigation and footer links.
3. Add source-derived public routes only when they are enabled and user-visible.
4. Exclude health, download, dynamic, disabled, and admin-only routes from the normal page accessibility score.
5. Re-run urlCheck crawl and update this file with confirmed violations, 404s, and manual-review items.