---
name: ACB Markdown to HTML
description: "Convert a Markdown file to ACB Large Print compliant HTML with proper document shell and CSS."
mode: agent
agent: large-print-formatter
tools: [read, edit, search, execute, vscode_askQuestions]
---

Convert the currently open Markdown file to ACB Large Print compliant HTML.

1. Audit the Markdown source for ACB issues first
2. Ask the user via `vscode_askQuestions`:
   - CSS delivery: embedded `<style>`, external `.css` file, or both
   - Whether the output will be printed
   - Output file name (suggest same name with `.html` extension)
3. Convert Markdown to HTML with a complete document shell
4. Apply all ACB Large Print Guidelines and WCAG 2.2 AA supplementary rules
5. Fix content anti-patterns in the resulting HTML
6. Write the output file and report a conversion summary with compliance score

If no file is open, ask the user to open or specify a file.
