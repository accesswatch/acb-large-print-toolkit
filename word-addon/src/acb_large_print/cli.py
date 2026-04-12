"""Command-line interface for ACB Large Print Tool."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from . import __app_name__, __version__

log = logging.getLogger("acb_large_print")

# Respect NO_COLOR convention (https://no-color.org)
NO_COLOR = bool(os.environ.get("NO_COLOR"))


def _configure_logging(args: argparse.Namespace) -> None:
    """Set up logging based on --quiet / --verbose flags."""
    if getattr(args, "quiet", False):
        level = logging.WARNING
    elif getattr(args, "verbose", False):
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stderr,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="acb-large-print",
        description=(
            "ACB Document Accessibility Tool -- audit, fix, and create "
            "Office document templates that comply with the American "
            "Council of the Blind Large Print Guidelines."
        ),
        epilog=(
            "Examples:\n"
            "  acb-large-print audit report.docx\n"
            "  acb-large-print audit budget.xlsx\n"
            "  acb-large-print audit slides.pptx\n"
            "  acb-large-print audit report.docx -f json -o report.json\n"
            "  acb-large-print fix  report.docx -o report-fixed.docx\n"
            "  acb-large-print fix  report.docx -o fixed.docx -b\n"
            "  acb-large-print fix  report.docx --dry-run\n"
            "  acb-large-print template -t 'Meeting Minutes'\n"
            "  acb-large-print batch audit docs/ -r -f json\n"
            "  acb-large-print batch fix docs/ -r -d fixed/\n"
            "  acb-large-print export report.docx --cms\n"
            "\n"
            "Exit codes:\n"
            "  0  Success\n"
            "  1  Error (file not found, invalid arguments)\n"
            "  2  Audit completed with findings (document is non-compliant)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", "-V", action="version",
        version=f"{__app_name__} {__version__}",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress informational messages; only output results",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed processing information",
    )

    sub = parser.add_subparsers(dest="command", required=False)

    # ---- audit ----
    audit_p = sub.add_parser(
        "audit",
        help="Audit a document for ACB compliance",
        description="Scan a .docx, .xlsx, or .pptx file and report all ACB guideline violations.",
    )
    audit_p.add_argument("file", type=Path, help="Path to .docx, .xlsx, or .pptx file to audit")
    audit_p.add_argument(
        "--format", "-f", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )
    audit_p.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Save report to file instead of printing to console",
    )

    # ---- fix ----
    fix_p = sub.add_parser(
        "fix",
        help="Fix a document for ACB compliance",
        description="Automatically fix ACB compliance issues in a .docx file. Excel and PowerPoint files are audited with manual fix guidance.",
    )
    fix_p.add_argument("file", type=Path, help="Path to .docx, .xlsx, or .pptx file to fix")
    fix_p.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Output file path (default: overwrites input)",
    )
    fix_p.add_argument(
        "--bound", "-b", action="store_true",
        help="Add binding margin (0.5 inch extra on left)",
    )
    fix_p.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Show what would change without modifying any files",
    )

    # ---- template ----
    tmpl_p = sub.add_parser(
        "template",
        help="Create an ACB-compliant Word template",
        description="Create a .dotx template with all ACB styles pre-configured.",
    )
    tmpl_p.add_argument(
        "output", type=Path, nargs="?",
        default=Path("ACB-Large-Print.dotx"),
        help="Output template path (default: ACB-Large-Print.dotx)",
    )
    tmpl_p.add_argument(
        "--bound", "-b", action="store_true",
        help="Configure binding margins",
    )
    tmpl_p.add_argument(
        "--no-sample", "-n", action="store_true",
        help="Create empty template without sample content",
    )
    tmpl_p.add_argument(
        "--title", "-t", type=str, default="",
        help="Set the document title property",
    )
    tmpl_p.add_argument(
        "--install", "-i", action="store_true",
        help="Also install the template to Word's Templates folder",
    )

    # ---- batch ----
    batch_p = sub.add_parser(
        "batch",
        help="Process multiple documents at once",
        description="Run audit or fix on multiple .docx, .xlsx, or .pptx files.",
    )
    batch_p.add_argument(
        "action", choices=["audit", "fix"],
        help="Action to perform on each file",
    )
    batch_p.add_argument(
        "files", type=Path, nargs="+",
        help="Paths to .docx/.xlsx/.pptx files or directories (supports glob patterns)",
    )
    batch_p.add_argument(
        "--format", "-f", choices=["text", "json"], default="text",
        help="Output format for audit reports",
    )
    batch_p.add_argument(
        "--output-dir", "-d", type=Path, default=None,
        help="Directory for fixed files (batch fix)",
    )
    batch_p.add_argument(
        "--bound", "-b", action="store_true",
        help="Add binding margin (batch fix)",
    )
    batch_p.add_argument(
        "--recursive", "-r", action="store_true",
        help="Search subdirectories for .docx files",
    )
    batch_p.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Show what would change without modifying any files (batch fix)",
    )

    # ---- export ----
    export_p = sub.add_parser(
        "export",
        help="Export a Word document to ACB-compliant HTML",
        description=(
            "Convert a .docx file to ACB Large Print HTML. "
            "Two modes: standalone (full HTML + CSS file) or "
            "CMS fragment (embedded CSS, paste into WordPress/Drupal)."
        ),
    )
    export_p.add_argument("file", type=Path, help="Path to .docx file")
    export_p.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Output HTML file path (default: same name, .html extension)",
    )
    export_p.add_argument(
        "--cms", "-c", action="store_true",
        help="Generate a CMS fragment with embedded CSS instead of standalone",
    )
    export_p.add_argument(
        "--title", "-t", type=str, default="",
        help="Document title for the HTML output",
    )
    export_p.add_argument(
        "--css", type=Path, default=None,
        help="Custom CSS file path (standalone mode only)",
    )

    # ---- gui ----
    sub.add_parser(
        "gui",
        help="Launch the graphical interface",
        description="Open the ACB Large Print Tool in GUI mode.",
    )

    # ---- completions ----
    comp_p = sub.add_parser(
        "completions",
        help="Generate shell completion scripts",
        description="Print a completion script for your shell.",
    )
    comp_p.add_argument(
        "shell", choices=["bash", "zsh", "powershell", "fish"],
        help="Target shell",
    )

    return parser


# ── Supported file extensions ─────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".docx", ".xlsx", ".pptx"}


def _audit_by_extension(file_path: Path):
    """Dispatch to the correct auditor based on file extension."""
    ext = file_path.suffix.lower()
    if ext == ".xlsx":
        from .xlsx_auditor import audit_workbook
        return audit_workbook(file_path)
    elif ext == ".pptx":
        from .pptx_auditor import audit_presentation
        return audit_presentation(file_path)
    else:
        from .auditor import audit_document
        return audit_document(file_path)


def _fix_by_extension(file_path: Path, output_path: Path | None = None, *, bound: bool = False):
    """Dispatch to the correct fixer based on file extension.

    Returns (output_path, total_fixes, post_audit, warnings).
    """
    ext = file_path.suffix.lower()
    if ext == ".xlsx":
        from .xlsx_auditor import audit_workbook
        post_audit = audit_workbook(file_path)
        return file_path, 0, post_audit, [
            "Excel workbooks cannot be auto-fixed yet. "
            "Review the audit findings and fix them manually in Excel."
        ]
    elif ext == ".pptx":
        from .pptx_auditor import audit_presentation
        post_audit = audit_presentation(file_path)
        return file_path, 0, post_audit, [
            "PowerPoint presentations cannot be auto-fixed yet. "
            "Review the audit findings and fix them manually in PowerPoint."
        ]
    else:
        from .fixer import fix_document
        return fix_document(file_path, output_path=output_path, bound=bound)


def _cmd_audit(args: argparse.Namespace) -> int:
    """Execute the audit command."""
    from .reporter import generate_json_report, generate_text_report

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    ext = args.file.suffix.lower()
    if ext not in (".docx", ".xlsx", ".pptx"):
        print(f"Error: Unsupported file type '{ext}'. Use .docx, .xlsx, or .pptx.", file=sys.stderr)
        return 1

    log.debug("Auditing: %s", args.file)
    result = _audit_by_extension(args.file)
    log.debug("Score: %d/100 (%s), %d findings", result.score, result.grade, len(result.findings))

    if args.format == "json":
        report = generate_json_report(result)
    else:
        report = generate_text_report(result)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        log.info("Report saved to: %s", args.output)
    else:
        print(report)

    return 0 if result.passed else 2


def _cmd_fix(args: argparse.Namespace) -> int:
    """Execute the fix command."""
    from .reporter import generate_fix_summary

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    ext = args.file.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"Error: Unsupported file type '{ext}'. Use .docx, .xlsx, or .pptx.", file=sys.stderr)
        return 1

    if args.dry_run:
        # Dry-run: audit only, report what would be fixed
        log.info("Dry run -- no files will be modified")
        result = _audit_by_extension(args.file)
        fixable = [f for f in result.findings if f.auto_fixable]
        manual = [f for f in result.findings if not f.auto_fixable]
        print(f"File: {args.file}")
        print(f"Score: {result.score}/100 (Grade {result.grade})")
        print(f"Auto-fixable issues: {len(fixable)}")
        print(f"Manual-review issues: {len(manual)}")
        if fixable:
            print("\nWould fix:")
            for i, f in enumerate(fixable, 1):
                print(f"  {i}. [{f.severity.value}] {f.rule_id}: {f.message}")
        if manual:
            print("\nRequires manual review:")
            for i, f in enumerate(manual, 1):
                print(f"  {i}. [{f.severity.value}] {f.rule_id}: {f.message}")
        return 0 if result.passed else 2

    output_path, total_fixes, post_audit, warnings = _fix_by_extension(
        args.file,
        output_path=args.output,
        bound=getattr(args, "bound", False),
    )

    report = generate_fix_summary(str(output_path), total_fixes, post_audit)
    print(report)
    for w in warnings:
        print(f"  WARNING: {w}")

    return 0 if post_audit.passed else 2


def _cmd_template(args: argparse.Namespace) -> int:
    """Execute the template command."""
    from .template import create_template, install_template

    output = create_template(
        args.output,
        bound=args.bound,
        include_sample=not args.no_sample,
        title=args.title,
    )
    log.info("Template created: %s", output)

    if args.install:
        dest = install_template(output)
        log.info("Template installed to: %s", dest)
        log.info("It will appear in Word under File, New, Personal templates.")

    return 0


def _cmd_batch(args: argparse.Namespace) -> int:
    """Execute the batch command."""
    from .reporter import generate_fix_summary, generate_json_report, generate_text_report

    # Expand glob patterns and optional recursive search
    files: list[Path] = []
    for pattern in args.files:
        p = Path(str(pattern))
        if p.is_dir():
            # Directory given: find supported files
            glob_method = p.rglob if args.recursive else p.glob
            for ext in SUPPORTED_EXTENSIONS:
                files.extend(glob_method(f"*{ext}"))
        elif "*" in str(pattern) or "?" in str(pattern):
            if args.recursive:
                files.extend(pattern.parent.rglob(pattern.name))
            else:
                files.extend(pattern.parent.glob(pattern.name))
        else:
            files.append(pattern)

    if not files:
        print("Error: No matching document files found.", file=sys.stderr)
        return 1

    total_files = len(files)
    exit_code = 0
    total_processed = 0
    total_issues = 0

    for idx, file_path in enumerate(sorted(files), 1):
        if not file_path.exists():
            log.warning("Skipping (not found): %s", file_path)
            continue
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            log.warning("Skipping (unsupported format): %s", file_path)
            continue

        total_processed += 1
        log.info("Processing %d/%d: %s", idx, total_files, file_path.name)

        if args.action == "audit":
            result = _audit_by_extension(file_path)
            total_issues += len(result.findings)

            if args.format == "json":
                report = generate_json_report(result)
            else:
                report = generate_text_report(result)
            print(report)
            print()

            if not result.passed:
                exit_code = 2

        elif args.action == "fix":
            if args.dry_run:
                result = _audit_by_extension(file_path)
                fixable = [f for f in result.findings if f.auto_fixable]
                manual = [f for f in result.findings if not f.auto_fixable]
                print(f"File: {file_path}")
                print(f"  Auto-fixable: {len(fixable)}, Manual: {len(manual)}")
                total_issues += len(result.findings)
                if not result.passed:
                    exit_code = 2
                continue

            out = None
            if args.output_dir:
                args.output_dir.mkdir(parents=True, exist_ok=True)
                out = args.output_dir / file_path.name

            output_path, total_fixes, post_audit, warnings = _fix_by_extension(
                file_path, output_path=out, bound=getattr(args, "bound", False),
            )
            report = generate_fix_summary(str(output_path), total_fixes, post_audit)
            print(report)
            for w in warnings:
                print(f"  WARNING: {w}")
            print()

            if not post_audit.passed:
                exit_code = 2

    # Batch summary
    log.info("Batch complete: %d files processed%s",
             total_processed,
             f", {total_issues} total findings" if args.action == "audit" else "")

    return exit_code


def _cmd_export(args: argparse.Namespace) -> int:
    """Execute the export command."""
    from .exporter import export_cms_fragment, export_standalone_html

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    # Default output path
    if args.output:
        out = args.output
    elif args.cms:
        out = args.file.with_suffix(".html").with_stem(args.file.stem + "-cms")
    else:
        out = args.file.with_suffix(".html")

    title = args.title or args.file.stem.replace("-", " ").replace("_", " ")

    if args.cms:
        path, warnings = export_cms_fragment(args.file, out, title=title)
        log.info("CMS fragment saved: %s", path)
    else:
        html_path, css_path, warnings = export_standalone_html(
            args.file, out, title=title, css_path=args.css,
        )
        log.info("HTML saved: %s", html_path)
        log.info("CSS saved:  %s", css_path)

    if warnings:
        log.warning("Conversion warnings (%d):", len(warnings))
        for w in warnings:
            log.warning("  - %s", w)

    return 0


def _cmd_gui(_args: argparse.Namespace) -> int:
    """Launch the graphical interface."""
    try:
        from .gui import launch_gui
    except ImportError:
        print(
            "Error: wxPython is not installed. The GUI requires wxPython.\n"
            "Install it with: pip install wxPython>=4.2.0\n"
            "Use CLI commands instead: acb-large-print --help",
            file=sys.stderr,
        )
        return 1
    launch_gui()
    return 0


def _cmd_completions(args: argparse.Namespace) -> int:
    """Generate shell completion script."""
    prog = "acb-large-print"
    commands = "audit fix template batch export gui completions"
    prog_under = prog.replace("-", "_")

    if args.shell == "bash":
        script = (
            f"# bash completion for {prog}\n"
            f"_{prog_under}_completions() {{\n"
            '    local cur="${COMP_WORDS[COMP_CWORD]}"\n'
            '    local prev="${COMP_WORDS[COMP_CWORD-1]}"\n'
            '    case "$prev" in\n'
            f'        {prog}) COMPREPLY=($(compgen -W "{commands} --help --version --quiet --verbose" -- "$cur")) ;;\n'
            '        audit)  COMPREPLY=($(compgen -W "--format --output --help" -- "$cur") $(compgen -f -X \'!*.docx\' -- "$cur")) ;;\n'
            '        fix)    COMPREPLY=($(compgen -W "--output --bound --dry-run --help" -- "$cur") $(compgen -f -X \'!*.docx\' -- "$cur")) ;;\n'
            '        batch)  COMPREPLY=($(compgen -W "audit fix" -- "$cur")) ;;\n'
            '        export) COMPREPLY=($(compgen -W "--output --cms --title --css --help" -- "$cur") $(compgen -f -X \'!*.docx\' -- "$cur")) ;;\n'
            '        --format|-f) COMPREPLY=($(compgen -W "text json" -- "$cur")) ;;\n'
            '        *) COMPREPLY=($(compgen -f -- "$cur")) ;;\n'
            "    esac\n"
            "}}\n"
            f"complete -o default -F _{prog_under}_completions {prog}"
        )
        print(script)

    elif args.shell == "zsh":
        script = (
            f"#compdef {prog}\n"
            "_arguments \\\n"
            f"    '1:command:({commands})' \\\n"
            "    '--help[Show help]' \\\n"
            "    '--version[Show version]' \\\n"
            "    '--quiet[Suppress info messages]' \\\n"
            "    '--verbose[Show debug output]' \\\n"
            '    \'*:file:_files -g "*.docx"\''
        )
        print(script)

    elif args.shell == "fish":
        lines = []
        for cmd in commands.split():
            lines.append(f"complete -c {prog} -n '__fish_use_subcommand' -a {cmd}")
        lines.append(f"complete -c {prog} -s h -l help -d 'Show help'")
        lines.append(f"complete -c {prog} -s V -l version -d 'Show version'")
        lines.append(f"complete -c {prog} -s q -l quiet -d 'Suppress info'")
        lines.append(f"complete -c {prog} -s v -l verbose -d 'Debug output'")
        print("\n".join(lines))

    elif args.shell == "powershell":
        cmds_quoted = ", ".join(f"'{c}'" for c in commands.split())
        script = (
            f"Register-ArgumentCompleter -CommandName {prog} -ScriptBlock {{\n"
            "    param($wordToComplete, $commandAst, $cursorPosition)\n"
            f"    $commands = @({cmds_quoted})\n"
            "    $flags = @('--help', '--version', '--quiet', '--verbose')\n"
            '    ($commands + $flags) | Where-Object { $_ -like "$wordToComplete*" } |\n'
            "        ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }\n"
            "}"
        )
        print(script)

    return 0


def main(argv: list[str] | None = None, *, force_cli: bool = False) -> int:
    """CLI entry point. Returns exit code.

    Args:
        argv: Command line arguments (None = sys.argv).
        force_cli: If True, never launch the GUI (print help instead).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args)

    if args.command is None:
        if force_cli:
            parser.print_help()
            return 0
        # No command given -- launch GUI by default if wxPython available
        try:
            from .gui import launch_gui
        except ImportError:
            parser.print_help()
            print(
                "\nNote: GUI unavailable (wxPython not installed). "
                "Use a subcommand above.",
                file=sys.stderr,
            )
            return 1
        launch_gui()
        return 0

    dispatch = {
        "audit": _cmd_audit,
        "fix": _cmd_fix,
        "template": _cmd_template,
        "batch": _cmd_batch,
        "export": _cmd_export,
        "gui": _cmd_gui,
        "completions": _cmd_completions,
    }

    handler = dispatch.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1
