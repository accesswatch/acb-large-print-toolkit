"""Command-line interface for ACB Large Print Tool."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __app_name__, __version__

log = logging.getLogger("acb_large_print")


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
            "ACB Large Print Tool -- audit, fix, and create Word document "
            "templates that comply with the American Council of the Blind "
            "Large Print Guidelines."
        ),
        epilog=(
            "Examples:\n"
            "  acb-large-print audit report.docx\n"
            "  acb-large-print audit report.docx -f json -o report.json\n"
            "  acb-large-print fix  report.docx -o report-fixed.docx\n"
            "  acb-large-print fix  report.docx -o fixed.docx -b\n"
            "  acb-large-print template -t 'Meeting Minutes'\n"
            "  acb-large-print batch audit *.docx -f json\n"
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
        help="Audit a Word document for ACB compliance",
        description="Scan a .docx file and report all ACB guideline violations.",
    )
    audit_p.add_argument("file", type=Path, help="Path to .docx file to audit")
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
        help="Fix a Word document for ACB compliance",
        description="Automatically fix ACB compliance issues in a .docx file.",
    )
    fix_p.add_argument("file", type=Path, help="Path to .docx file to fix")
    fix_p.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Output file path (default: overwrites input)",
    )
    fix_p.add_argument(
        "--bound", "-b", action="store_true",
        help="Add binding margin (0.5 inch extra on left)",
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
        description="Run audit or fix on multiple .docx files.",
    )
    batch_p.add_argument(
        "action", choices=["audit", "fix"],
        help="Action to perform on each file",
    )
    batch_p.add_argument(
        "files", type=Path, nargs="+",
        help="Paths to .docx files (supports glob patterns)",
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

    return parser


def _cmd_audit(args: argparse.Namespace) -> int:
    """Execute the audit command."""
    from .auditor import audit_document
    from .reporter import generate_json_report, generate_text_report

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    log.debug("Auditing: %s", args.file)
    result = audit_document(args.file)
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
    from .fixer import fix_document
    from .reporter import generate_fix_summary

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    output_path, total_fixes, post_audit = fix_document(
        args.file,
        output_path=args.output,
        bound=args.bound,
    )

    report = generate_fix_summary(str(output_path), total_fixes, post_audit)
    print(report)

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
    from .auditor import audit_document
    from .fixer import fix_document
    from .reporter import generate_fix_summary, generate_json_report, generate_text_report

    # Expand glob patterns and optional recursive search
    files: list[Path] = []
    for pattern in args.files:
        p = Path(str(pattern))
        if p.is_dir():
            # Directory given: find .docx files
            glob_method = p.rglob if args.recursive else p.glob
            files.extend(glob_method("*.docx"))
        elif "*" in str(pattern) or "?" in str(pattern):
            if args.recursive:
                files.extend(pattern.parent.rglob(pattern.name))
            else:
                files.extend(pattern.parent.glob(pattern.name))
        else:
            files.append(pattern)

    if not files:
        print("Error: No matching .docx files found.", file=sys.stderr)
        return 1

    exit_code = 0
    total_processed = 0
    total_issues = 0

    for file_path in sorted(files):
        if not file_path.exists():
            log.warning("Skipping (not found): %s", file_path)
            continue
        if file_path.suffix.lower() != ".docx":
            log.warning("Skipping (not .docx): %s", file_path)
            continue

        total_processed += 1

        if args.action == "audit":
            result = audit_document(file_path)
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
            out = None
            if args.output_dir:
                args.output_dir.mkdir(parents=True, exist_ok=True)
                out = args.output_dir / file_path.name

            output_path, total_fixes, post_audit = fix_document(
                file_path, output_path=out, bound=args.bound,
            )
            report = generate_fix_summary(str(output_path), total_fixes, post_audit)
            print(report)
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
    }

    handler = dispatch.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1
