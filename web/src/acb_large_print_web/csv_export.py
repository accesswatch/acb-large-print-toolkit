"""CSV export helpers for audit findings.

Produces a flat CSV that compliance teams and ticket-tracking workflows
can ingest directly. The format is stable and documented so external
tooling can rely on the column order.

CSV columns (in order):
    severity, rule_id, message, location, acb_reference, auto_fixable,
    help_urls

The CSV is UTF-8 encoded with a BOM so it opens cleanly in Excel.
"""

from __future__ import annotations

import csv
import io
from typing import Iterable, Mapping


CSV_COLUMNS: tuple[str, ...] = (
    "severity",
    "rule_id",
    "message",
    "location",
    "acb_reference",
    "auto_fixable",
    "help_urls",
)


def _format_help_urls(urls: Iterable[Mapping[str, str]] | None) -> str:
    """Flatten a list of {label, url} dicts into a single ``"; "``-joined string."""
    if not urls:
        return ""
    parts: list[str] = []
    for entry in urls:
        label = (entry.get("label") or "").strip()
        url = (entry.get("url") or "").strip()
        if not url:
            continue
        parts.append(f"{label}: {url}" if label else url)
    return "; ".join(parts)


def findings_to_csv_bytes(
    findings: list[dict],
    *,
    filename: str = "",
    doc_format: str = "",
    score: int | None = None,
    grade: str = "",
    profile_label: str = "",
    mode_label: str = "",
) -> bytes:
    """Render a list of finding dicts to a UTF-8-with-BOM CSV byte string.

    A header block of comment lines (prefixed with ``#``) precedes the CSV
    header so that report context (filename, score, profile) travels with
    the export but is not parsed as data by spreadsheet tools.
    """
    buf = io.StringIO()
    # Context preamble (optional but useful for compliance reviewers).
    if filename:
        buf.write(f"# filename,{_csv_safe(filename)}\n")
    if doc_format:
        buf.write(f"# format,{_csv_safe(doc_format)}\n")
    if score is not None:
        buf.write(f"# score,{int(score)}\n")
    if grade:
        buf.write(f"# grade,{_csv_safe(grade)}\n")
    if profile_label:
        buf.write(f"# standards_profile,{_csv_safe(profile_label)}\n")
    if mode_label:
        buf.write(f"# mode,{_csv_safe(mode_label)}\n")
    buf.write(f"# total_findings,{len(findings)}\n")

    writer = csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(CSV_COLUMNS)
    for f in findings:
        writer.writerow([
            f.get("severity", ""),
            f.get("rule_id", ""),
            f.get("message", ""),
            f.get("location") or "",
            f.get("acb_reference", ""),
            "yes" if f.get("auto_fixable") else "no",
            _format_help_urls(f.get("help_urls")),
        ])
    # Excel-friendly UTF-8 BOM
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


def _csv_safe(text: str) -> str:
    """Strip newlines so a single value cannot break the comment header."""
    return str(text).replace("\r", " ").replace("\n", " ")


def safe_filename_stem(stem: str) -> str:
    """Sanitise a filename stem for use as a download filename."""
    keep = "".join(c if c.isalnum() or c in "-_." else "_" for c in (stem or ""))
    return keep.strip("._") or "audit-findings"
