# v2.5.0 Release Summary: April 28, 2026

## Overview

GLOW Accessibility Toolkit v2.5.0 is focused on user-facing quality in audit/fix outcomes, report-to-action workflow clarity, deployment-safe branding, and feature-gated consistency. This release builds directly on the v2.0.0 foundation and removes several day-to-day friction points that affected real workflows.

Important release posture: AI features are currently disabled by default in production and staging. This does not reduce core capability in any way for primary workflows.

Operational model: v2.5.0 ships as one unified release. Feature flags control what is visible and actionable at runtime, so teams can safely pare down or phase in capabilities without forking release content.

Core workflows fully available in 2.5.0:

- Audit
- Fix
- Export to HTML
- Convert between formats
- Template generation
- Standards guidance and reporting
- Branding profile support

---

## What Changed Since v2.0.0

### 1. Audit and fix quality improvements for Word workflows

v2.5.0 includes targeted remediation improvements for real-world Word content:

- Deeper heading normalization now covers Heading 4 through Heading 6 so built-in Word heading levels beyond Heading 3 are normalized consistently.
- Paragraph spacing normalization is now applied directly to paragraph content in addition to style-level normalization.
- Repeated non-Arial findings in audit output are capped and summarized instead of flooding the report.

User impact:

- Cleaner, more actionable audit reports
- More predictable fix output for mixed-format legacy documents
- Less time spent triaging duplicate findings

### 2. Report and action-flow usability improvements

v2.5.0 improves post-audit and post-fix user guidance:

- "What's Next" and related cross-links now better align with enabled features.
- Batch and single-report guidance now better supports format-specific follow-up actions.
- Web accessibility improvements across forms and reporting pages reduce friction for keyboard and assistive technology users.

User impact:

- Better continuity from finding -> decision -> remediation
- Fewer dead-end actions
- More accessible, lower-friction completion path

### 3. Feature-gated navigation and cross-links are now consistent

In v2.0.0, most entry points were available but some cross-page links could still appear for disabled features. In v2.5.0, result pages and "What's Next" actions now respect the same feature flags as top-level navigation.

User impact:

- Fewer dead-end links
- Fewer confusing "why is this hidden here but visible there?" moments
- Clearer next actions after Audit, Fix, and Convert

### 4. Branding profiles are now deployment-aware and complete

GLOW now supports profile-based branding through `GLOW_BRAND_PROFILE` with two values:

- `bits` (default)
- `uarizona`

The profile drives:

- Navigation logo and alt text
- Theme class and visual palette
- Favicon
- Shared wording across key templates

This means one deployment variable controls the full identity surface cleanly and consistently.

### 5. Dedicated HTML export and granular convert-direction controls

v2.5.0 adds:

- `GLOW_ENABLE_EXPORT_HTML` as a first-class flag
- Per-direction convert flags:
  - `GLOW_ENABLE_CONVERT_TO_MARKDOWN`
  - `GLOW_ENABLE_CONVERT_TO_HTML`
  - `GLOW_ENABLE_CONVERT_TO_DOCX`
  - `GLOW_ENABLE_CONVERT_TO_EPUB`
  - `GLOW_ENABLE_CONVERT_TO_PDF`
  - `GLOW_ENABLE_CONVERT_TO_PIPELINE`

User impact:

- Operators can phase output formats safely
- UI only shows available targets
- Direct requests to disabled targets are blocked server-side

### 6. Real-world branding polish for institutional deployments

v2.5.0 includes production logo assets, profile-aware alt text, profile-aware favicons, and UA-themed color tokens for the University of Arizona profile.

User impact:

- Trustworthy first impression for institutional users
- Better recognition and consistency in branded environments
- Improved non-visual clarity through accurate logo alt text

### 7. Admin visibility for active branding profile

Admin Feature Flags (Advanced tab) now shows the active branding profile as read-only deployment metadata and explains exactly how to switch it.

User impact:

- Less operator confusion
- Faster diagnosis when a deployment appears "wrong brand"
- Clear boundary between runtime flags and deploy-time profile settings

---

## High-Profile User-Impact Fixes Resolved in v2.5.0

- Fixed mismatched cross-links on result pages when features are disabled.
- Fixed Convert page guidance links so they only appear when corresponding features are enabled.
- Fixed branding consistency by making logo, theme, and favicon profile-driven from one source.
- Fixed docs/operator ambiguity by documenting profile selection and where it is configured.
- Fixed noisy Word audit output by summarizing repeated non-Arial findings.
- Fixed inconsistent paragraph spacing remediation in mixed-format Word documents.

---

## Comparison Snapshot: v2.0.0 -> v2.5.0

| Area | v2.0.0 | v2.5.0 |
|---|---|---|
| Branding | Mostly BITS-centric text and visuals | Full profile-aware branding (`bits` or `uarizona`) |
| Feature gating | Strong at top-level routes | End-to-end (nav + forms + result cross-links) |
| Export controls | General converter controls | Dedicated HTML export flag + per-direction convert flags |
| Operator clarity | Profile setting implicit | Profile visible in Admin with deployment guidance |
| AI posture | Introduced cloud pathways | AI defaults remain off; core workflows unaffected |

---

## How Profile Detection Works

GLOW reads `GLOW_BRAND_PROFILE` from environment at app runtime. The branding context is injected globally and used by templates to render profile-specific assets and language.

Implementation points:

- `web/src/acb_large_print_web/branding.py`
- `web/src/acb_large_print_web/app.py`

Operational rule:

- Profile changes require restart/redeploy.
- Profile is intentionally not a runtime toggle in Admin.

---

## Upgrade and Verification Checklist

1. Set versioned artifacts to 2.5.0.
2. Ensure `GLOW_BRAND_PROFILE` is set as desired in deployment environment.
3. Verify feature flags in Admin -> Feature flags.
4. Run focused regression tests:
   - `tests/test_app.py`
   - `tests/test_admin_flags.py`
5. Validate visual branding for target profile.

---

## Version Info

| Component | Version | Released |
|---|---|---|
| GLOW Toolkit | 2.5.0 | 2026-04-28 |
| Flask Web App | 2.5.0 | 2026-04-28 |
| Desktop CLI/GUI | 2.5.0 | 2026-04-28 |
| Office Add-in | 2.5.0 | 2026-04-28 |
