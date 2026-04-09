---
applyTo: "**/*.{html,css,htm}"
---

## ACB Large Print Reminders for Web Content

When editing HTML or CSS files that may be used for ACB Large Print compliance:

- **Font**: Arial only, minimum 18pt (1.5rem) for all text including captions and page numbers
- **Headings**: 22pt (1.833rem) bold; subheadings 20pt (1.667rem) bold; flush left
- **Line height**: 1.5 minimum for digital (WCAG 1.4.12); ACB print spec is 1.15
- **Spacing**: letter-spacing >= 0.12em, word-spacing >= 0.16em, paragraph spacing >= 2em
- **Alignment**: Flush left, ragged right -- never justify text
- **Layout**: Single column, max-width ~70ch, no multi-column layouts
- **Emphasis**: Underline must look distinct from hyperlinks (different thickness, color, or style)
- **Lists**: No blank lines between bullet items; use semantic `<ul>`/`<ol>`/`<li>`
- **Contrast**: 4.5:1 minimum (AA), 7:1 recommended (AAA); use measurable ratios
- **No ALL CAPS** for headings, labels, or body text
- **Reflow**: Content must work at 400% zoom without horizontal scrolling; use relative units
- **Semantic HTML**: proper `<h1>`-`<h6>`, `lang` attribute, `<th scope>`, meaningful `alt` text
- **Hyphenation**: Always off (`hyphens: none`)
- **Notes/citations**: Place at end of article, never inline
- **Starter CSS**: A drop-in ACB stylesheet is available at `styles/acb-large-print.css` (workspace) or `{{VSCODE_USER_PROMPTS_FOLDER}}/acb-large-print.css` (User-level)
