This repository contains the ACB Large Print Toolkit -- a VS Code agent toolkit for formatting documents to comply with the American Council of the Blind Large Print Guidelines (revised May 6, 2025), supplemented with WCAG 2.2 AA digital accessibility rules.

## Repository layout

- `.github/agents/large-print-formatter.agent.md` -- Main agent (9 operating modes for audit, generate, convert, template, CSS embed, Word setup, Markdown audit, Markdown fix, Markdown-to-HTML)
- `.github/agents/markdown-a11y-assistant.agent.md` -- Bundled WCAG markdown audit orchestrator (from accessibility agents ecosystem)
- `.github/agents/markdown-scanner.agent.md` -- Internal: single-file accessibility scanner
- `.github/agents/markdown-fixer.agent.md` -- Internal: auto-fix applicator
- `.github/agents/markdown-csv-reporter.agent.md` -- Internal: CSV finding export
- `.github/prompts/` -- Slash command prompt files (.prompt.md) for /acb-audit, /acb-convert, /acb-md-audit, /acb-md-convert, /acb-word-setup
- `.github/instructions/` -- Auto-attach instruction files (activates on html/css editing)
- `.github/skills/markdown-accessibility/` -- Pattern library, severity scoring, emoji maps, fix templates
- `styles/` -- Reference CSS stylesheet (acb-large-print.css)
- `templates/` -- HTML boilerplate skeleton (acb-large-print-boilerplate.html)
- `docs/` -- Detailed toolkit documentation and history
- `samples/` -- Example source Markdown and converted HTML files
- `reference/` -- Source ACB specification document (.docx)

## Key conventions

- All CSS uses rem units (never px for text) to support browser zoom and reflow
- Digital content uses WCAG 2.2 AA line-height (1.5) which overrides ACB print spec (1.15); print media query reverts to 1.15
- Emphasis is underline only -- no italic anywhere, no bold for body emphasis
- In Markdown, `<u>text</u>` inline HTML is the underline convention (styled in CSS to look distinct from hyperlinks)
- The agent uses `vscode_askQuestions` for interactive decisions (CSS delivery, print intent, conflict resolution)
- When markdownlint and Pandoc are available, the agent uses them automatically for higher-quality Markdown processing
- Reference CSS: `styles/acb-large-print.css` (workspace) or `{{VSCODE_USER_PROMPTS_FOLDER}}/acb-large-print.css` (User-level)
- Reference HTML: `templates/acb-large-print-boilerplate.html` (workspace) or `{{VSCODE_USER_PROMPTS_FOLDER}}/acb-large-print-boilerplate.html` (User-level)

## Agent relationships

- `large-print-formatter` is the primary agent. It handles ACB-specific rules across HTML, CSS, Markdown, and Word
- `markdown-a11y-assistant` is a complementary agent for general WCAG markdown auditing (9 domains: links, alt text, headings, tables, emoji, Mermaid/ASCII diagrams, em-dashes, anchors, plain language)
- The large-print-formatter has handoff links to markdown-a11y-assistant for combined ACB + WCAG workflows
- `markdown-scanner`, `markdown-fixer`, and `markdown-csv-reporter` are internal sub-agents invoked by markdown-a11y-assistant -- not user-facing

## ACB rules (quick reference)

- Font: Arial only, 18pt body, 22pt headings, 20pt subheadings
- Alignment: flush left, ragged right (never justified)
- Emphasis: underline only (no bold for emphasis, no italic ever)
- Headings: proper hierarchy, no ALL CAPS, no skipped levels
- Lists: large solid bullets, no extra spacing between items
- Links: descriptive text (no bare URLs, no "click here")
- Spacing: 1 blank line between paragraphs, no blank lines between list items
- Digital supplement: WCAG 2.2 AA contrast (4.5:1), 400% zoom reflow, 1.5x line-height
