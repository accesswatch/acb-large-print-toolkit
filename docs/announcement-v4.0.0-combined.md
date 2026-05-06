# GLOW 4.0.0: Calm, Confident Accessibility at Scale

**FOR IMMEDIATE RELEASE - May 4, 2026**

## Thank You First

GLOW exists because the blind and low-vision community keeps asking practical, specific, high-impact questions.

Questions like:

- Can this workflow be safer?
- Can this conversion be more reliable?
- Can the documentation match what is actually live today?

GLOW 4.0.0 is our answer to those questions.

## Executive Summary

GLOW (Guided Layout and Output Workflow) Accessibility Toolkit 4.0.0 is now available.

This is a trust-and-fidelity release. It does not chase novelty for novelty's sake. It strengthens the core production loop so teams can deliver accessible documents with more confidence and less uncertainty.

In one sentence:

**GLOW 4.0.0 hardens conversion behavior, secures re-audit transitions, and synchronizes public release documentation into one consistent 4.0.0 story.**

## What Is New in 4.0.0

### 1. Re-audit from Fix Results is now explicit and CSRF-protected

The "Re-Audit Fixed Document" action now submits through a POST form with CSRF protection and complete workflow context.

Why this matters:

- safer server handling for stateful re-audit actions
- preserved context for standards profile and prior finding comparisons
- clearer operational behavior for auditors and administrators

### 2. OpenDocument conversion path is more resilient

GLOW now supports a broader OpenDocument conversion path safely:

- `.fodt` can be handled directly as a native Pandoc input
- `.ods`, `.fods`, `.odp`, and `.fodp` can be pre-converted with LibreOffice before entering the existing MarkItDown plus Pandoc pipeline

Why this matters:

- fewer conversion dead ends in mixed-source environments
- better compatibility for teams receiving files from heterogeneous authoring tools

### 3. Better table preservation when converting PDFs

For PDFs with embedded table structures, downstream conversions now preserve table intent more reliably in outputs such as Word, HTML, and EPUB.

Why this matters:

- less structural loss during conversion
- cleaner outputs for follow-on review, publication, and accessibility remediation

### 4. Public release documentation has been synchronized

We aligned public and canonical release surfaces to 4.0.0 so release communication is no longer fragmented across older version pointers.

Updated resources include:

- `CHANGELOG.md`
- `docs/RELEASE-v4.0.0.md`
- `docs/announcement.md`
- `docs/announcement-web-app.md`
- `docs/announcement-web-app.html`
- `docs/prd.md`
- `docs/user-guide.md`

### 5. Site Audit web scanner for page-level accessibility checks

GLOW web now includes a dedicated Site Audit workflow at `/site-audit` for
website scanning and evidence export.

What it does:

- accepts URL lists and sitemap input
- supports optional in-site crawling with configurable page limits
- reports scanned, failed, and skipped totals per run
- produces downloadable artifacts: summary JSON, findings CSV, session log, and full ZIP bundle

Why this matters:

- extends GLOW from document remediation into practical website QA
- gives teams reproducible scan outputs for handoff and remediation tracking

## What Stays Strong from 3.1.0

GLOW 4.0.0 keeps the full strength of 3.1.0:

- Braille Studio and Speech Studio
- Status page and accessibility regression gates
- roadmap-core feature pack under explicit feature flags
- single-upload workflow across Audit, Fix, Re-Audit, Convert, and Speech handoffs

This release protects that foundation while reducing day-to-day workflow risk.

## Who This Release Is For

GLOW 4.0.0 is especially important for:

- teams processing mixed legacy and modern document formats
- administrators who need predictable operational behavior
- organizations that need release artifacts to be audit-ready and consistent

## Availability

GLOW 4.0.0 release artifacts:

- Release notes: `docs/RELEASE-v4.0.0.md`
- Full changelog: `CHANGELOG.md`
- PRD status and release context: `docs/prd.md`
- User workflow guidance: `docs/user-guide.md`

Repository release tag:

**https://github.com/accesswatch/acb-large-print-toolkit/releases/tag/v4.0.0**

## Closing

Accessibility work is long-horizon work.

Some releases introduce new tools. Some releases make the existing tools easier to trust when the stakes are high.

GLOW 4.0.0 is the second kind.

It is designed to help teams move faster by worrying less - because the workflow is safer, conversion behavior is stronger, and the documentation finally tells one clean story.
