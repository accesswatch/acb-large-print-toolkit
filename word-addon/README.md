# ACB Large Print Tool

A cross-platform desktop application that audits, remediates, and exports Microsoft Word documents to comply with the American Council of the Blind (ACB) Large Print Guidelines, supplemented with WCAG 2.2 AA digital accessibility rules.

## Features

- Audit .docx files against 30+ ACB Large Print rules
- Auto-fix compliance issues (fonts, spacing, emphasis, headings, margins)
- Generate ACB-compliant Word templates (.dotx) with pre-configured styles
- Export to accessible HTML (standalone or CMS-ready fragments)
- Accessible GUI wizard (screen reader compatible, keyboard navigable)
- Full CLI for scripting and batch processing
- Cross-platform: Windows, macOS, and Linux (x64 and ARM64)

## Installation

### Pre-built executables

Download the latest release for your platform from the
[Releases page](https://github.com/your-org/acb-large-print/releases):

| Platform | Filename | Notes |
|---|---|---|
| Windows | `acb-large-print-win-x64.exe` | x64 binary, also runs on ARM64 via emulation |
| macOS | `acb-large-print-macos-arm64` | Apple Silicon (M1/M2/M3/M4) |

On macOS and Linux, make the file executable after downloading:

```bash
chmod +x acb-large-print-*
```

### Install from source

```bash
cd word-addon
pip install -e .

# or with dev dependencies
pip install -e ".[dev]"
```

Requires Python 3.10 or later.

### Dependencies

| Package | Version | Purpose |
|---|---|---|
| python-docx | 1.1.0+ | Read and write .docx files |
| mammoth | 1.8.0+ | Convert .docx to clean HTML |
| wxPython | 4.2.0+ | Accessible cross-platform GUI |

## Usage

### GUI mode (default)

Double-click the executable or run without arguments:

```bash
acb-large-print
```

The 7-step wizard walks through:

1. Open a .docx file
2. Initial audit (view compliance report in your browser)
3. Choose output options (standalone HTML, CMS fragment)
4. Auto-remediate all fixable issues
5. Verify the fixed document (view report showing improvements)
6. Save the fixed .docx and optional HTML exports
7. Summary of everything accomplished

### CLI mode

#### Audit a document

```bash
acb-large-print audit report.docx
acb-large-print audit report.docx --format json
acb-large-print audit report.docx -o audit-report.txt
```

#### Fix a document

```bash
acb-large-print fix report.docx
acb-large-print fix report.docx -o report-fixed.docx
acb-large-print fix report.docx --bound   # add binding margin
```

#### Create a template

```bash
acb-large-print template
acb-large-print template ACB-Template.dotx --bound --title "Meeting Agenda"
acb-large-print template --install   # also copy to Word's Templates folder
```

#### Export to HTML

```bash
# Standalone HTML + CSS file
acb-large-print export report.docx

# CMS fragment (embedded CSS, paste into WordPress/Drupal)
acb-large-print export report.docx --cms

# Custom title and output path
acb-large-print export report.docx -o output.html --title "Board Meeting Agenda"
```

#### Batch processing

```bash
acb-large-print batch audit *.docx
acb-large-print batch fix *.docx --output-dir fixed/
```

## Architecture

```
word-addon/
  src/acb_large_print/
    __init__.py          Version and metadata
    __main__.py          Entry point (CLI dispatch or GUI launch)
    constants.py         ACB rule definitions and thresholds
    auditor.py           Document scanner -- checks 30+ rules, returns AuditResult
    fixer.py             Auto-remediation engine -- applies fixes to python-docx Document
    reporter.py          Report generators (text, JSON, HTML)
    exporter.py          DOCX-to-HTML export (mammoth + ACB post-processing)
    template.py          Word template (.dotx) generator with ACB styles
    cli.py               argparse CLI with audit/fix/template/export/batch/gui commands
    gui.py               wxPython 7-step wizard (accessible, screen reader compatible)
  build.py               Cross-platform PyInstaller build script
  pyproject.toml         Project metadata and dependencies
  requirements.txt       Pip requirements (core dependencies)
  installer/
    acb-large-print.iss  Inno Setup installer script (Windows)
  LICENSE.txt            MIT License
```

### Module details

**auditor.py** scans a .docx file and returns an `AuditResult` containing:

- `passed` (bool): whether the document meets all rules
- `findings` (list): each finding has a rule ID, severity, description, location, and suggested fix
- `score` (int): compliance score (0--100)
- `grade` (str): letter grade A--F

**fixer.py** takes an `AuditResult` and the source document, then applies fixes:

- Font family (set to Arial)
- Font sizes (18pt body, 22pt headings, 20pt subheadings)
- Line spacing and paragraph spacing
- Remove italic and bold-as-emphasis
- Heading hierarchy corrections
- Margin and page layout adjustments
- Binding margin (optional)

**exporter.py** converts .docx to HTML via mammoth with ACB-specific style mapping:

- `export_standalone_html()`: full HTML document + external CSS file
- `export_cms_fragment()`: body-only HTML with embedded `<style>` block, scoped under `.acb-lp` class for safe CMS pasting
- Post-processes mammoth output: strips inline styles, cleans empty paragraphs, adds table `scope` attributes

**reporter.py** generates reports in three formats:

- `generate_text_report()`: plain text with ASCII severity indicators
- `generate_json_report()`: machine-readable JSON
- `generate_html_report()`: accessible HTML with severity badges, summary grid, and findings table

**gui.py** provides a wxPython wizard with full accessibility:

- All controls have labels or `SetName()` for screen readers
- Alt-key accelerators (Alt+B Back, Alt+N Next, Alt+C Cancel)
- Read-only text areas for report display
- HTML reports open in the default browser
- Standard file dialogs for all file operations
- Status bar announces the current step

## Building executables

### Local build (current platform)

```bash
cd word-addon
pip install pyinstaller>=6.0
python build.py
```

This produces a single-file executable in `dist/`:

- Windows: `acb-large-print-win-x64.exe` (or `win-arm64`)
- macOS: `acb-large-print-macos-arm64` (or `macos-x64`)
- Linux: `acb-large-print-linux-x64` (or `linux-arm64`)

### Cross-platform builds via GitHub Actions

Push a version tag to trigger automated builds on all 6 platforms:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This runs the workflow at `.github/workflows/build.yml` which:

1. Builds on 2 runners simultaneously (Windows x64, macOS ARM64)
2. Uploads each executable as a GitHub Actions artifact
3. Creates a combined download with both binaries
4. Creates a GitHub Release with executables attached (tag pushes only)

You can also trigger the workflow manually from the Actions tab and optionally upload to a release.

### Build matrix

| Runner | OS | Arch | Executable output |
|---|---|---|---|
| `windows-latest` | Windows | x64 | `acb-large-print-win-x64.exe` |
| `macos-latest` | macOS | ARM64 | `acb-large-print-macos-arm64` |

### Windows installer (optional)

For Windows distribution with Start menu shortcuts and Word template installation, build the Inno Setup installer:

1. Build the executable: `python build.py`
2. Open `installer/acb-large-print.iss` in Inno Setup
3. Compile -- produces `dist/installer/ACB-Large-Print-Setup-1.0.0.exe`

The installer is fully accessible: standard Windows controls, descriptive labels, per-user install (no admin rights needed).

### Platform notes

- **macOS**: The executable may need to be allowed in System Settings, Privacy and Security after first download (Apple Gatekeeper).
- **PyInstaller cannot cross-compile**: Each platform must be built natively. The GitHub Actions workflow handles this automatically.

## ACB Large Print rules (summary)

- Font: Arial only, 18pt body, 22pt headings, 20pt subheadings
- Alignment: flush left, ragged right (never justified)
- Emphasis: underline only (no bold for emphasis, no italic ever)
- Headings: proper hierarchy, no ALL CAPS, no skipped levels
- Lists: large solid bullets, no extra spacing between items
- Links: descriptive text (no bare URLs, no "click here")
- Spacing: 1 blank line between paragraphs, no blank lines between list items
- Digital supplement: WCAG 2.2 AA contrast (4.5:1), 400% zoom reflow, 1.5x line-height

Full specification: `reference/ACB Large Print Guidelines, revised 5-6-25.docx`

## HTML export details

### Standalone mode

Produces two files:

- `document.html` -- complete HTML5 document with `<link>` to CSS
- `acb-large-print.css` -- external stylesheet with all ACB + WCAG rules, including `@media print` overrides

### CMS fragment mode

Produces one file:

- `document-cms.html` -- body-only HTML with embedded `<style>` block
- All CSS selectors scoped under `.acb-lp` class to prevent CMS theme conflicts
- Content wrapped in `<div class="acb-lp">...</div>`
- No `<!DOCTYPE>`, `<html>`, `<head>`, or `<body>` tags -- the CMS provides these

### mammoth style mapping

The exporter maps Word styles to semantic HTML:

| Word Style | HTML Output |
|---|---|
| Heading 1 | `<h1>` |
| Heading 2 | `<h2>` |
| Heading 3--6 | `<h3>` through `<h6>` |
| Bold | `<strong>` (structural only, not emphasis) |
| Italic | Stripped (ACB prohibits italic) |
| Underline | `<u class="acb-emphasis">` |
| Hyperlinks | `<a href="...">` with descriptive text preserved |

Post-processing removes inline styles, cleans empty paragraphs, and adds `scope` attributes to table headers.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License. See [LICENSE.txt](LICENSE.txt).

Copyright 2026 BITS (Blind Information Technology Specialists).
