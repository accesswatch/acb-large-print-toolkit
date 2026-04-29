# v2.6.0 Release Summary: April 28, 2026

## Overview

GLOW Accessibility Toolkit v2.6.0 expands document accessibility coverage in practical, user-visible ways across Word-adjacent workflows, PowerPoint timing/motion safety checks, Markdown quality auditing, and Excel structure support.

This release is strongly influenced by the open-source accessibility work of Jamal Mazrui. In particular, extCheck and xlHeaders helped identify high-value rule gaps and inspired both new checks and remediation behavior in this release.

Core highlights:

- New PowerPoint timing and animation checks for motion and reading-time safety
- Substantial Markdown accessibility quality rule expansion
- New Excel blank-row and default-table-name checks
- New xlHeaders-style Excel named-range fixer utility
- Rule metadata sync updates in the Office add-in constants registry

---

## Attribution and Community Impact

GLOW v2.6.0 includes explicit attribution to Jamal Mazrui and references to:

- extCheck: https://github.com/jamalmazrui/extCheck
- xlHeaders: https://github.com/jamalmazrui/xlHeaders

This attribution appears in release documentation and the web About page to credit the source inspiration and make that lineage transparent for users.

---

## What Changed in v2.6.0

### 1. PowerPoint timing and motion checks

Added four new PPTX rules and supporting auditor logic:

- PPTX-FAST-AUTO-ADVANCE
- PPTX-REPEATING-ANIMATION
- PPTX-RAPID-AUTO-ANIMATION
- PPTX-FAST-TRANSITION

User impact:

- Better detection of auto-advance slides that move too quickly
- Better detection of looped/repeating motion that may be disorienting
- Better reporting on rapid auto-triggered animation clusters
- Better coverage of transition speed concerns for vestibular accessibility

### 2. Markdown accessibility quality expansion

Added a broad set of Markdown-focused checks, including:

- Alt text quality checks (filename alt, redundant prefixes, too-short alt)
- YAML front matter validation (presence, closed fence, required fields):
  - `MD-NO-YAML-FRONT-MATTER` -- no front matter block at all
  - `MD-YAML-UNCLOSED-FENCE` -- opening `---` with no closing `---` fence
  - `MD-YAML-MISSING-TITLE` -- front matter lacks a `title:` field (WCAG 2.4.2)
  - `MD-YAML-MISSING-LANG` -- front matter lacks a `lang:` or `language:` field (WCAG 3.1.1)
- Heading quality checks (empty headings, excessively long headings, trailing punctuation)
- Code block checks (missing language and indented code block guidance)
- Raw HTML checks (table semantics and moving-content tags)
- Table consistency checks (blank headers and column mismatches)
- Fake list-pattern checks and ALL CAPS body-text checks

All 25 Markdown rules are registered in `constants.py`, `office-addin/src/constants.ts`, and `web/src/acb_large_print_web/rules.py` (help links added for every new rule in the web UI).

User impact:

- More actionable findings for documentation teams
- YAML front matter fields are now verified, not just present
- Better signal quality for both semantics and readability
- Better consistency with WCAG and ACB style expectations in Markdown-heavy workflows

### 3. Excel layout and naming checks

Added two new XLSX checks:

- XLSX-BLANK-ROWS-LAYOUT
- XLSX-DEFAULT-TABLE-NAME

User impact:

- Better detection of visual-spacing patterns that harm navigation
- Better labeling guidance for assistive-technology context

### 4. New Excel named-range fixer (xlHeaders-inspired)

Added desktop/src/acb_large_print/xlsx_fixer.py with add_excel_header_named_ranges() to generate xlHeaders-style defined names:

- ColumnTitleNN
- RowTitleNN
- Title01

User impact:

- Better screen reader context for row and column movement in Excel
- Practical bridge from audit findings to machine-applied remediation

### 5. Office add-in constants sync

Updated office-addin/src/constants.ts to keep rule registry alignment with new 2.6.0 rules and format metadata updates.

User impact:

- Better consistency between Python core and Office add-in rule metadata
- Fewer cross-surface mismatches when interpreting rule IDs and severities

### 6. New Rules Reference page

Added a new `/rules/` route and `rules_ref.html` template backed by `rule_reference_metadata.py`. The page lists every audit rule across all document formats with severity level, WCAG criterion mapping, auto-fix flag, and a help link.

Users can filter the reference by format, severity, or rule category. Saving a filtered set writes it to Settings as the Audit or Fix custom rule list, replacing the previous per-run selection workflow.

User impact:

- Easier discovery of what rules exist and what they check
- One-click path from rule research to saved custom audit or fix profile
- Better onboarding for new users unfamiliar with rule IDs

---

## Notable Behavior Changes

- Default Excel table-name findings now use XLSX-DEFAULT-TABLE-NAME instead of reusing XLSX-TABLE-HEADERS, improving reporting clarity and remediation targeting.- Settings are now saved in browser local storage instead of preference cookies. The Settings form no longer shows a cookie opt-in toggle. Existing users will need to re-save preferences on first visit after upgrade; the form pre-populates GLOW defaults automatically.

---

## Upgrade and Verification Checklist

1. Verify desktop constants include all new 2.6.0 rule IDs.
2. Run desktop tests and confirm expected Ollama live-test behavior in your environment.
3. Verify about-page attribution text renders correctly.
4. Confirm Office add-in rule metadata compiles and maps expected IDs.
5. Validate Markdown, PPTX, and XLSX sample audits include the new rule families.
6. Verify Rules Reference page loads at `/rules/` and displays rules for all document formats.
7. Verify Settings page saves and restores preferences via local storage (no cookie opt-in toggle present).

---

## Version Info

| Component | Version | Released |
|---|---|---|
| GLOW Toolkit | 2.6.0 | 2026-04-28 |
| Flask Web App | 2.6.0 | 2026-04-28 |
| Desktop CLI/GUI | 2.6.0 | 2026-04-28 |
| Office Add-in | 2.6.0 | 2026-04-28 |
