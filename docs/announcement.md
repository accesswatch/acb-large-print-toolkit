# GLOW 2.5.0: A Smoother, Safer Accessibility Workflow for Real Teams

**FOR IMMEDIATE RELEASE -- April 28, 2026**

GLOW (Guided Layout & Output Workflow) Accessibility Toolkit 2.5.0 is now available, delivering a major user-experience refinement release built on top of the 2.0.0 foundation.

Where 2.0.0 introduced broad platform capability, 2.5.0 focuses on what users feel every day: fewer dead ends, clearer next steps, stronger branding consistency, and safer rollout controls for operators.

## The headline: better outcomes in audit and fix, with cleaner guided workflows

GLOW 2.5.0 improves the path from upload to accessible output by delivering cleaner audit/fix results first, then tightening feature visibility and workflow consistency across the app.

Users now see only the actions that are enabled in their deployment, including on result pages and "What's Next" links. This release ships as one codebase with feature gating controlling visibility and access, so teams can safely enable capabilities on their own rollout timeline.

## What is new in 2.5.0

### 1. Better audit and fix outcomes for Word documents

This release includes practical quality improvements in the core document remediation path:

- Heading normalization now covers deeper built-in heading levels (Heading 4 through Heading 6) so older source documents do not keep stale heading formatting.
- Paragraph spacing normalization is applied directly to paragraph content, not only named styles, which improves consistency in real-world documents with mixed direct formatting.
- Repeated non-Arial findings in audit output are now capped and summarized, reducing report noise while keeping the most useful locations visible.

For users, this means cleaner reports and more predictable fixed documents, especially for legacy files with inconsistent Word formatting.

### 2. Accessibility and workflow polish across reports and next steps

Report and follow-up flows were refined so users can move from findings to action with less confusion:

- Result-page and batch-report calls-to-action now stay aligned with enabled features.
- More format-aware guidance appears in "What's Next" sections for common document types.
- Form and navigation accessibility improvements reduce friction for keyboard and screen-reader users.

### 3. End-to-end feature gating consistency

Feature flags now apply consistently across navigation, forms, and follow-up links in reports/results. If a feature is off, its links and prompts are hidden where users make decisions.

This gating model keeps the experience clean for teams that intentionally pare down available features, while still shipping a unified release.

### 4. Profile-aware branding for institutional deployments

GLOW now supports deployment-level branding profiles:

- `bits` (default)
- `uarizona`

This profile controls logo, alt text, theme styling, favicon, and profile-specific wording, so the entire UI stays coherent for each organization.

### 5. Granular conversion controls

Operators can now manage conversion options with precision:

- Dedicated `GLOW_ENABLE_EXPORT_HTML`
- Per-direction convert flags for Markdown, HTML, DOCX, EPUB, PDF, and Pipeline

This enables safe phased rollouts and cleaner user experience during transitions.

### 6. Better operator visibility

Admin now clearly shows the active branding profile and explains exactly how to change it at deployment time.

### 7. Stronger PDF and EPUB confidence with automated accessibility regression checks

This release also improves document-quality signal and release safety for non-AI workflows:

- PDF scanning detection is smarter and now distinguishes likely full-page scans from decorative-image pages.
- New low-resolution scan guidance flags scanned pages below 150 DPI and recommends 300 DPI or higher for reliable OCR outcomes.
- EPUB audits can optionally include EPUBCheck validation results as structured findings.
- Web accessibility regression checks now run as a repeatable Playwright + axe + SARIF pipeline.

For users and operators, this means clearer remediation guidance for scanned PDFs, stronger EPUB validation confidence, and more dependable accessibility quality gates before release.

## High-profile user-impact fixes in this release

- Resolved mismatched cross-links that could point users to disabled features.
- Resolved Convert guidance links so they only appear when relevant features are enabled.
- Resolved branding drift by centralizing logo/theme/favicon selection through one profile variable.
- Resolved profile-discovery confusion by documenting and surfacing profile status in Admin and deployment docs.
- Resolved noisy Word audit output by capping repeated font findings to concise, actionable summaries.
- Resolved inconsistent Word remediation in mixed-format documents by applying spacing normalization directly to content paragraphs.

## Looking back: 2.0.0 to 2.5.0

GLOW 2.0.0 delivered major platform capabilities and cloud-ready architecture.

GLOW 2.5.0 makes that platform easier and safer to operate in production:

- clearer UX at decision points
- cleaner deployment controls
- stronger institutional identity support
- better alignment between what is configured and what users actually see

## AI status update

At this time, AI features remain disabled by default in production and staging.

This does not limit functionality for core GLOW workflows. Audit, Fix, Export, Convert, Template, and standards-guidance workflows remain fully available and production-ready.

## Technology stewardship and mission impact

GLOW 2.5.0 also reflects a core operating principle: responsible stewardship of the technology we build so it can reach the widest possible audience.

As part of that commitment, BITS partnered with the University of Arizona to deliver a fully branded, non-AI-capable experience tailored for educational use while preserving the full strength of core accessibility workflows.

> "As President of BITS, I believe we are stewards of the technology we create. Our partnership with the University of Arizona reflects that responsibility by delivering a fully branded, non-AI-capable GLOW experience that still gives students, faculty, and staff powerful access to accessible documents. When accessibility is practical, reliable, and welcoming, it does more than improve compliance. It opens doors to participation, learning, and success." -- Jeff Bishop, President, BITS

## Availability

GLOW 2.5.0 is available now.

- Changelog: `CHANGELOG.md`
- Release summary: `docs/RELEASE-v2.5.0.md`
- User guide: `docs/user-guide.md`
- Feature flags and profile ops: `docs/feature-flags.md`

## About GLOW

GLOW (Guided Layout & Output Workflow) helps teams audit, remediate, convert, and publish accessible documents aligned to ACB, WCAG 2.2 AA, and Microsoft Accessibility Checker expectations.
