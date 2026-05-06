# v4.0.0 Release Notes - May 4, 2026

## Overview

GLOW Accessibility Toolkit v4.0.0 is a trust-and-fidelity release.

This version focuses on what operators and content teams need most after a major feature cycle:

- conversion behavior that is predictable on real-world files
- re-audit workflow integrity that is explicit and secure
- public documentation that matches the live product state

No new platform category is introduced in this release. Instead, v4.0.0 hardens the existing platform so teams can operate with more confidence.

## Highlights

### 1. Re-audit from Fix Results now uses an explicit POST flow

The "Re-Audit Fixed Document" action on Fix Results now submits through a CSRF-protected POST form to `/audit/from-fix`.

Why this matters:

- preserves workflow context cleanly (token, profile, prior findings)
- avoids implicit GET re-audit transitions for stateful operations
- aligns the user action with server-side form safety expectations

### 2. OpenDocument conversion path hardening

Conversion support now better handles OpenDocument variants:

- `.fodt` is accepted as native Pandoc input
- optional LibreOffice pre-conversion is used for `.ods/.fods/.odp/.fodp` before entering the existing MarkItDown plus Pandoc chain

Why this matters:

- broader coverage of source document variants used by partner organizations
- fewer dead-end conversion attempts in mixed-format environments

### 3. Better PDF table preservation for downstream exports

When PDFs contain embedded table structures, the conversion pipeline now preserves table intent more reliably in Pandoc-backed outputs (including Word, HTML, and EPUB).

Why this matters:

- reduces table flattening in converted outputs
- improves auditability and usability of converted structured content

### 4. Public release-documentation synchronization

v4.0.0 aligns public-facing release references and canonical docs so users and operators see one consistent release story.

Updated surfaces include:

- `CHANGELOG.md`
- release pointers in `docs/announcement*.md` and `docs/announcement-web-app.html`
- PRD release metadata in `docs/prd.md`
- user-guide release framing in `docs/user-guide.md`
- v4 combined announcement artifacts

## Compatibility and operations

- v4.0.0 is backward-compatible with existing 3.1.0 deployment workflows.
- Existing feature flags and standards profiles remain unchanged.
- No migration is required for normal operation.

## Primary artifacts

- `CHANGELOG.md`
- `docs/announcement-v4.0.0-combined.md`
- `docs/announcement-v4.0.0-combined.html`
- `docs/user-guide.md`

### 5. Site Audit web scanner for WCAG-focused page checks

GLOW web now includes a dedicated **Site Audit** workflow at `/site-audit`.

What it provides:

- URL-list and sitemap input modes
- Optional in-site crawling with page-limit controls
- Run-level summary with scanned/failed/skipped counts
- Downloadable artifacts: summary JSON, findings CSV, session log, and full ZIP bundle
- Feature-flag control via `GLOW_ENABLE_SITE_AUDIT`

Why this matters:

- extends GLOW beyond file-centric accessibility into website QA workflows
- creates reproducible evidence bundles for reviewer handoff and remediation tracking
- `docs/prd.md`
