---
name: ACB Audit
description: "Quick ACB Large Print compliance check on the current file. Works on HTML, CSS, and Word-related files."
mode: agent
agent: large-print-formatter
tools: [read, edit, search]
---

Run an ACB Large Print Guidelines audit on the currently open file.

1. Detect the file type (HTML, CSS, Word XML, or other)
2. Apply the full ACB Large Print Specification checklist
3. For HTML/CSS files, also check the HTML / Digital Content Supplementary Rules (WCAG 2.2 AA)
4. Report results as a structured checklist: PASS / FAIL per rule, with current vs. required values for each failure
5. End with a compliance score and a prioritized list of fixes (highest-impact first)

If no file is open, ask the user to open or specify a file.
