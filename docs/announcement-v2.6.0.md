# GLOW 2.6.0: Expanded Rule Coverage, Smarter Findings, and Community-Driven Accessibility Progress

**FOR IMMEDIATE RELEASE -- April 28, 2026**

GLOW (Guided Layout and Output Workflow) Accessibility Toolkit 2.6.0 is now available.

This release delivers broad accessibility rule expansion across PowerPoint, Markdown, and Excel, plus a practical new Excel remediation helper inspired by community tooling.

## The headline: stronger accessibility signal quality where teams spend time every day

GLOW 2.6.0 strengthens day-to-day outcomes by catching more real-world accessibility issues in presentation decks, documentation pipelines, and spreadsheets.

This is a practical release focused on finding what matters, reducing ambiguous findings, and improving remediation guidance.

## Acknowledgment and inspiration

GLOW 2.6.0 is substantially informed by the accessibility tooling work of Jamal Mazrui.

Two projects were especially influential:

- extCheck: https://github.com/jamalmazrui/extCheck
- xlHeaders: https://github.com/jamalmazrui/xlHeaders

We are grateful for the open-source leadership and practical implementation examples these tools provide to the accessibility community.

## What is new in 2.6.0

### 1. New PowerPoint timing and animation checks

GLOW now detects several high-value timing and motion risks in PPTX files:

- Fast auto-advance
- Repeating animations
- Rapid auto-triggered animation sequences
- Fast slide transitions

For users, this means stronger detection of motion and timing patterns that can harm readability and comfort.

### 2. Major Markdown accessibility quality expansion

GLOW 2.6.0 adds a substantial set of Markdown checks, including:

- Alt text quality checks (filename alt, redundant prefixes, too-short alt text)
- YAML front matter validation -- not just presence, but field depth:
  - Missing front matter block entirely
  - Unclosed front matter fence (no closing `---`)
  - Missing `title:` field (WCAG 2.4.2)
  - Missing `lang:` or `language:` field (WCAG 3.1.1)
- Heading quality and structure checks
- Code block language and formatting checks
- Raw HTML moving-content and table checks
- Table consistency checks (blank headers, column count mismatches)
- Fake list-pattern and ALL CAPS checks

For users, this means cleaner documentation audits with more actionable guidance and better semantic quality outcomes. All 25 Markdown rules include help links in the web UI.

### 3. New Excel checks for layout and naming quality

Two new XLSX checks target common spreadsheet accessibility friction:

- Detection of excessive blank-row spacing patterns
- Detection of default table names that should be descriptive

For users, this means clearer navigation quality and better context for assistive technology.

### 4. New xlHeaders-style Excel fixer utility

A new desktop helper creates named ranges in an xlHeaders-style convention to improve row and column header context in Excel navigation.

For users, this means a practical path from findings to stronger screen-reader behavior in spreadsheets.

### 5. Office add-in rule metadata alignment

Rule metadata updates were synced in the Office add-in constants registry to improve consistency with the desktop Python core.

### 6. New Rules Reference page

A new **Rules Reference** page is available in the GLOW web app at `/rules/`. It lists every audit rule across all document formats with severity, WCAG criterion mapping, fix guidance, and help links.

From the Rules Reference page you can filter by format, severity, or rule category, then save a custom rule set directly to Settings for use in Audit or Fix Custom mode. This replaces the previous workflow of selecting rules one-by-one on the Audit or Fix form.

## Notable changes in behavior

**Rules Reference page:** custom rule sets are now saved from the Rules Reference page and loaded into Audit or Fix Custom mode. See the new `/rules/` page in the web app.

**Settings persistence:** settings are now saved in browser local storage instead of preference cookies. Existing saved preferences carry forward automatically. No action required for most users; clearing browser site data will reset settings to defaults.

**Excel table-name findings** now use a dedicated rule ID (`XLSX-DEFAULT-TABLE-NAME`), improving report clarity and remediation targeting.

## Availability

GLOW 2.6.0 is available now.

- Changelog: CHANGELOG.md
- Release summary: docs/RELEASE-v2.6.0.md
- User guide: docs/user-guide.md

## About GLOW

GLOW helps teams audit, remediate, convert, and publish accessible documents aligned with ACB guidelines, WCAG 2.2 AA, and Microsoft Accessibility Checker expectations.
