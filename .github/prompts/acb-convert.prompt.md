---
name: ACB Convert
description: "Reformat the current file to ACB Large Print compliance. Fixes all violations automatically."
mode: agent
agent: large-print-formatter
tools: [read, edit, search, execute, vscode_askQuestions]
---

Convert the currently open file to full ACB Large Print Guidelines compliance.

1. Detect the file type (HTML, CSS, Word XML, or plain text)
2. For HTML files, use `vscode_askQuestions` to ask the user:
   - Whether CSS should be embedded as a `<style>` block or linked as an external file
   - Whether print-specific rules apply (will this be printed?)
3. Read the file and identify every deviation from the ACB Large Print Specification
4. For HTML/CSS files, also check the HTML / Digital Content Supplementary Rules (WCAG 2.2 AA)
5. Apply all fixes automatically
6. Report a summary of changes made, organized by category (typography, spacing, layout, lists, semantics)
7. If any ACB/WCAG conflicts were resolved, note which value was chosen and why

If no file is open, ask the user to open or specify a file.
