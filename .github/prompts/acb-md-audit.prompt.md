---
name: ACB Markdown Audit
description: "Audit a Markdown file for ACB Large Print compliance. Checks heading hierarchy, emphasis, images, lists, ALL CAPS, and content patterns."
mode: agent
agent: large-print-formatter
tools: [read, search]
---

Run an ACB Large Print Guidelines audit on the currently open Markdown file.

1. Detect that this is a Markdown file
2. Apply the full Markdown-Specific Rules checklist (emphasis, heading hierarchy, images, links, lists, ALL CAPS, notes placement)
3. Also check core ACB rules that apply at the content level
4. Report results as a structured checklist: PASS / FAIL per rule with line numbers, current text vs. required fix
5. End with a compliance score and a prioritized list of fixes (marking which are auto-fixable)

If no file is open, ask the user to open or specify a file.
