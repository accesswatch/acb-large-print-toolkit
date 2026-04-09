"""Generate human-readable, browser-friendly, and machine-parseable audit reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from . import __version__
from . import constants as C
from .auditor import AuditResult


def _severity_marker(sev: C.Severity) -> str:
    """Plain-text severity marker (no color dependency for accessibility)."""
    return {
        C.Severity.CRITICAL: "[CRITICAL]",
        C.Severity.HIGH: "[HIGH]    ",
        C.Severity.MEDIUM: "[MEDIUM]  ",
        C.Severity.LOW: "[LOW]     ",
    }.get(sev, "[UNKNOWN] ")


def generate_text_report(result: AuditResult) -> str:
    """Generate a plain-text audit report.

    Designed for screen reader consumption -- no color, no ASCII art,
    structured with clear headings and consistent formatting.
    """
    lines: list[str] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append("=" * 70)
    lines.append("ACB Large Print Compliance Report")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"File:       {result.file_path}")
    lines.append(f"Date:       {timestamp}")
    lines.append(f"Tool:       ACB Large Print Tool v{__version__}")
    lines.append(f"Score:      {result.score}/100 (Grade {result.grade})")
    lines.append(f"Status:     {'PASS' if result.passed else 'FAIL'}")
    lines.append(f"Paragraphs: {result.total_paragraphs}")
    lines.append(f"Text runs:  {result.total_runs}")
    lines.append("")

    # Summary counts
    lines.append("-" * 70)
    lines.append("Summary")
    lines.append("-" * 70)
    lines.append(f"Critical: {result.critical_count}")
    lines.append(f"High:     {result.high_count}")
    lines.append(f"Medium:   {result.medium_count}")
    lines.append(f"Low:      {result.low_count}")
    lines.append(f"Total:    {len(result.findings)}")
    lines.append("")

    if result.findings:
        lines.append("-" * 70)
        lines.append("Findings")
        lines.append("-" * 70)
        lines.append("")

        for i, finding in enumerate(result.findings, 1):
            lines.append(f"  {i}. {_severity_marker(finding.severity)} {finding.rule_id}")
            lines.append(f"     {finding.message}")
            if finding.location:
                lines.append(f"     Location: {finding.location}")
            lines.append(f"     Reference: {finding.rule.acb_reference}")
            lines.append(f"     Auto-fixable: {'Yes' if finding.auto_fixable else 'No'}")
            lines.append("")
    else:
        lines.append("No findings. Document is fully compliant.")
        lines.append("")

    lines.append("=" * 70)
    lines.append("End of report")
    lines.append("=" * 70)

    return "\n".join(lines)


def generate_json_report(result: AuditResult) -> str:
    """Generate a JSON audit report for machine consumption."""
    data = {
        "tool": f"ACB Large Print Tool v{__version__}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file": result.file_path,
        "score": result.score,
        "grade": result.grade,
        "passed": result.passed,
        "summary": {
            "total": len(result.findings),
            "critical": result.critical_count,
            "high": result.high_count,
            "medium": result.medium_count,
            "low": result.low_count,
        },
        "document_stats": {
            "paragraphs": result.total_paragraphs,
            "runs": result.total_runs,
        },
        "findings": [
            {
                "rule_id": f.rule_id,
                "severity": f.severity.value,
                "message": f.message,
                "location": f.location,
                "auto_fixable": f.auto_fixable,
                "reference": f.rule.acb_reference,
            }
            for f in result.findings
        ],
        "exitCode": 0 if result.passed else 2,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_fix_summary(
    file_path: str,
    total_fixes: int,
    post_audit: AuditResult,
) -> str:
    """Generate a plain-text fix summary report."""
    lines: list[str] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append("=" * 70)
    lines.append("ACB Large Print Fix Report")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"File:        {file_path}")
    lines.append(f"Date:        {timestamp}")
    lines.append(f"Fixes made:  {total_fixes}")
    lines.append(f"Post-fix score: {post_audit.score}/100 (Grade {post_audit.grade})")
    lines.append("")

    if post_audit.findings:
        lines.append("-" * 70)
        lines.append("Remaining issues (require manual review)")
        lines.append("-" * 70)
        lines.append("")
        for i, finding in enumerate(post_audit.findings, 1):
            lines.append(f"  {i}. {_severity_marker(finding.severity)} {finding.rule_id}")
            lines.append(f"     {finding.message}")
            if finding.location:
                lines.append(f"     Location: {finding.location}")
            lines.append("")
    else:
        lines.append("All issues resolved. Document is fully compliant.")
        lines.append("")

    lines.append("=" * 70)
    lines.append("End of report")
    lines.append("=" * 70)

    return "\n".join(lines)


# ------------------------------------------------------------------
# HTML report (opens in browser for easy review)
# ------------------------------------------------------------------

_SEV_COLORS = {
    C.Severity.CRITICAL: "#d32f2f",
    C.Severity.HIGH: "#e65100",
    C.Severity.MEDIUM: "#f9a825",
    C.Severity.LOW: "#2e7d32",
}


def generate_html_report(
    result: AuditResult,
    *,
    title: str = "ACB Large Print Compliance Report",
) -> str:
    """Generate an accessible HTML audit report for browser viewing.

    Designed for opening in the system default browser so the user
    can review, print, or share the results.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status = "PASS" if result.passed else "FAIL"

    # Severity badge helper
    def sev_badge(sev: C.Severity) -> str:
        colour = _SEV_COLORS.get(sev, "#666")
        label = sev.value.upper()
        return (
            f'<span style="display:inline-block;padding:2px 8px;'
            f"border-radius:3px;color:#fff;"
            f'background:{colour};font-size:0.85em">'
            f"{label}</span>"
        )

    findings_rows: list[str] = []
    for i, f in enumerate(result.findings, 1):
        loc = escape(f.location) if f.location else "\u2014"
        fix = "Yes" if f.auto_fixable else "No"
        findings_rows.append(
            f"<tr>"
            f"<td>{i}</td>"
            f"<td>{sev_badge(f.severity)}</td>"
            f"<td>{escape(f.rule_id)}</td>"
            f"<td>{escape(f.message)}</td>"
            f"<td>{loc}</td>"
            f"<td>{fix}</td>"
            f"</tr>"
        )

    findings_table = ""
    if findings_rows:
        findings_table = (
            "<h2>Findings</h2>\n"
            "<table>\n"
            "  <caption>All audit findings sorted by severity</caption>\n"
            "  <thead>\n"
            "    <tr>\n"
            '      <th scope="col">#</th>\n'
            '      <th scope="col">Severity</th>\n'
            '      <th scope="col">Rule</th>\n'
            '      <th scope="col">Issue</th>\n'
            '      <th scope="col">Location</th>\n'
            '      <th scope="col">Auto-fix</th>\n'
            "    </tr>\n"
            "  </thead>\n"
            "  <tbody>\n"
            f"    {''.join(findings_rows)}\n"
            "  </tbody>\n"
            "</table>"
        )
    else:
        findings_table = (
            '<p style="font-size:1.2em;font-weight:700;color:#2e7d32">'
            "No findings. Document is fully compliant.</p>"
        )

    esc_title = escape(title)
    esc_file = escape(result.file_path)

    html = (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"  <title>{esc_title}</title>\n"
        "  <style>\n"
        "    html { font-size: 100%; }\n"
        "    body {\n"
        "      font-family: Arial, sans-serif; font-size: 1rem;\n"
        "      color: #1a1a1a; background: #fff;\n"
        "      max-width: 60em; margin: 0 auto; padding: 1.5em;\n"
        "      line-height: 1.5;\n"
        "    }\n"
        "    h1 { font-size: 1.5rem; margin-top: 0; }\n"
        "    h2 { font-size: 1.25rem; margin-top: 1.5em; }\n"
        "    table { border-collapse: collapse; width: 100%; margin-top: 0.5em; }\n"
        "    th, td { text-align: left; padding: 0.4em 0.6em;\n"
        "      border: 1px solid #ccc; vertical-align: top; }\n"
        "    th { background: #f5f5f5; }\n"
        "    .summary { display: flex; gap: 1.5em; flex-wrap: wrap; }\n"
        "    .summary dt { font-weight: 700; }\n"
        "    .summary dd { margin: 0 0 0.5em 0; }\n"
        "    .grade { font-size: 2.5rem; font-weight: 700;\n"
        "      display: inline-block; padding: 0.1em 0.4em;\n"
        "      border: 3px solid currentColor; border-radius: 6px;\n"
        "      line-height: 1; }\n"
        "    @media print { body { max-width: none; padding: 0; }\n"
        "      .no-print { display: none; } }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{esc_title}</h1>\n"
        '  <div class="summary">\n'
        f"    <dl><dt>File</dt><dd>{esc_file}</dd>\n"
        f"    <dt>Date</dt><dd>{timestamp}</dd>\n"
        f"    <dt>Tool</dt><dd>ACB Large Print Tool v{__version__}</dd></dl>\n"
        f"    <dl><dt>Score</dt>"
        f'<dd><span class="grade">{result.score}</span> / 100</dd>\n'
        f'    <dt>Grade</dt><dd><span class="grade">{result.grade}</span></dd>\n'
        f"    <dt>Status</dt><dd>{status}</dd></dl>\n"
        f"    <dl><dt>Critical</dt><dd>{result.critical_count}</dd>\n"
        f"    <dt>High</dt><dd>{result.high_count}</dd>\n"
        f"    <dt>Medium</dt><dd>{result.medium_count}</dd>\n"
        f"    <dt>Low</dt><dd>{result.low_count}</dd>\n"
        f"    <dt>Total findings</dt><dd>{len(result.findings)}</dd></dl>\n"
        "  </div>\n\n"
        f"  {findings_table}\n\n"
        '  <p class="no-print" style="margin-top:2em;color:#666;font-size:0.85em">\n'
        f"    Generated by ACB Large Print Tool v{__version__} on {timestamp}\n"
        "  </p>\n"
        "</body>\n"
        "</html>\n"
    )
    return html
