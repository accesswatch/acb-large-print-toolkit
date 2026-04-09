---
name: ACB Word Setup
description: "Generate a PowerShell script to configure Microsoft Word styles for ACB Large Print compliance."
mode: agent
agent: large-print-formatter
tools: [read, edit, execute, vscode_askQuestions]
---

Generate a PowerShell COM automation script that configures a Microsoft Word document for ACB Large Print compliance.

1. Use `vscode_askQuestions` to ask:
   - Whether to create a new blank document or configure the currently open Word document
   - Whether the document will be bound (to set binding margins)
   - Whether to save the script as a .ps1 file in the workspace
2. Generate a PowerShell script that sets:
   - Normal style: Arial 18pt, no bold, 1.15 line spacing, flush left
   - Heading 1 style: Arial 22pt bold, flush left, space before 18pt, space after 12pt
   - Heading 2 style: Arial 20pt bold, flush left, space before 16pt, space after 10pt
   - List Bullet style: Arial 18pt, large bullet, hanging indent 0.5 inch, no extra line spacing between items
   - Page Setup: 1 inch margins (top, left, right, bottom), portrait orientation
   - If bound: add 0.5 inch extra to left margin for binding
   - Widow/orphan control: enabled
   - Hyphenation: disabled
   - Page numbers: Arial 18pt bold, lower right footer
3. Include comments in the script explaining each ACB rule being applied
4. Output the script for the user to review and run
