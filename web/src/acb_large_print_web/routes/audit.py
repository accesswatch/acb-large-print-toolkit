"""Audit route -- upload a document and view a compliance report."""

from collections import Counter
from pathlib import Path

from flask import Blueprint, render_template, request

import re

from ..email import send_audit_report_email, send_batch_audit_report_email
from ..app import limiter
from ..rules import (
    filter_findings,
    get_all_rule_ids,
    get_profile_label,
    get_rule_ids_by_category,
    get_rule_ids_by_severity,
    get_rule_ids_by_format,
    get_rule_ids_by_profile,
)
from ..upload import UploadError, cleanup_token, validate_upload

audit_bp = Blueprint("audit", __name__)

_BATCH_LIMIT = 3
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _validate_email(addr: str) -> bool:
    """Basic server-side email format check. Rejects obviously invalid addresses."""
    return bool(addr) and bool(_EMAIL_RE.match(addr)) and len(addr) <= 254


def _is_ace_installed() -> bool:
    """Ace is a required dependency -- always True in the web app."""
    try:
        from acb_large_print.ace_runner import ace_available

        return ace_available()
    except ImportError:
        return False


def _audit_by_extension(saved_path: Path):
    """Dispatch to the correct auditor based on file extension."""
    ext = saved_path.suffix.lower()
    if ext == ".xlsx":
        from acb_large_print.xlsx_auditor import audit_workbook

        return audit_workbook(saved_path)
    elif ext == ".pptx":
        from acb_large_print.pptx_auditor import audit_presentation

        return audit_presentation(saved_path)
    elif ext == ".md":
        from acb_large_print.md_auditor import audit_markdown

        return audit_markdown(saved_path)
    elif ext == ".pdf":
        from acb_large_print.pdf_auditor import audit_pdf

        return audit_pdf(saved_path)
    elif ext == ".epub":
        from acb_large_print.epub_auditor import audit_epub

        return audit_epub(saved_path)
    else:
        from acb_large_print.auditor import audit_document

        return audit_document(saved_path)


def _format_from_path(saved_path: Path) -> str:
    """Return the format key for a file path."""
    return saved_path.suffix.lower().lstrip(".")


def _build_rule_filter(form) -> tuple[set, str, list[str]]:
    """Compute the intersected rule ID set and labels from form data.

    Returns (selected_rule_ids, mode_label, suppressed_rules).
    """
    mode = form.get("mode", "full")
    standards_profile = form.get("standards_profile", "acb_2025")

    suppress_rule_ids: set[str] = set()
    if form.get("suppress_link_text") == "on":
        suppress_rule_ids.add("ACB-LINK-TEXT")
    if form.get("suppress_missing_alt_text") == "on":
        suppress_rule_ids.add("ACB-MISSING-ALT-TEXT")
    if form.get("suppress_faux_heading") == "on":
        suppress_rule_ids.add("ACB-FAUX-HEADING")
    suppressed_rules = sorted(suppress_rule_ids)

    categories = form.getlist("category") or ["acb", "msac"]
    category_rule_ids = get_rule_ids_by_category(*categories)
    profile_rule_ids = get_rule_ids_by_profile(standards_profile)

    if mode == "quick":
        base = get_rule_ids_by_severity("Critical", "High")
        mode_label = "Quick Audit -- Critical and High only"
    elif mode == "custom":
        base = set(form.getlist("rule")) or get_all_rule_ids()
        mode_label = f"Custom Audit -- {len(base)} rules selected"
    else:
        base = get_all_rule_ids()
        mode_label = "Full Audit -- all rules"

    # format-specific intersection happens per file in batch; caller handles it
    selected = base & category_rule_ids & profile_rule_ids
    return selected, mode_label, suppressed_rules


def _apply_filters(result, selected: set, doc_format: str, suppress_rule_ids: set):
    """Filter findings by selected rules, format scope, and suppressed rules."""
    format_rule_ids = get_rule_ids_by_format(doc_format)
    effective = (selected & format_rule_ids) - suppress_rule_ids
    result.findings = filter_findings(result.findings, effective)
    return result


@audit_bp.route("/", methods=["POST"])
@limiter.limit(
    "6 per minute",
    error_message="Too many audit requests. Please wait a moment and try again.",
)
def audit_submit_rate_limited():
    """Rate-limited POST handler -- delegates to audit_submit."""
    return audit_submit()


@audit_bp.route("/", methods=["GET"])
def audit_form():
    from ..email import email_configured
    return render_template(
        "audit_form.html",
        ace_installed=_is_ace_installed(),
        email_configured=email_configured(),
    )


def audit_submit():
    upload_mode = request.form.get("upload_mode", "single")

    if upload_mode == "batch":
        return _audit_batch()
    return _audit_single()


def _audit_single():
    """Handle single-file audit -- original behaviour."""
    token = None
    try:
        token, saved_path = validate_upload(request.files.get("document"))

        standards_profile = request.form.get("standards_profile", "acb_2025")
        profile_label = get_profile_label(standards_profile)
        doc_format = _format_from_path(saved_path)

        selected, mode_label, suppressed_rules = _build_rule_filter(request.form)
        suppress_rule_ids = set(suppressed_rules)

        result = _audit_by_extension(saved_path)
        result = _apply_filters(result, selected, doc_format, suppress_rule_ids)

        # Optional email delivery
        email_status = None
        if request.form.get("email_report") == "on":
            to_email = request.form.get("report_email", "").strip()
            if not _validate_email(to_email):
                email_status = {"success": False, "message": "Report could not be sent: the email address provided is invalid."}
            elif to_email:
                severity_breakdown = Counter(
                    str(f.severity.value) if hasattr(f.severity, "value") else str(f.severity)
                    for f in result.findings
                )
                ok, msg = send_audit_report_email(
                    to_email=to_email,
                    filename=saved_path.name,
                    doc_format=doc_format,
                    score=result.score,
                    grade=result.grade,
                    findings_count=len(result.findings),
                    severity_breakdown=dict(severity_breakdown),
                    findings=result.findings,
                )
                email_status = {"success": ok, "message": msg}

        return render_template(
            "audit_report.html",
            result=result,
            mode_label=mode_label,
            profile_label=profile_label,
            doc_format=doc_format,
            ace_installed=_is_ace_installed(),
            suppressed_rules=suppressed_rules,
            email_status=email_status,
            ai_used=False,
        )
    except UploadError as e:
        from ..email import email_configured as _ec
        return (
            render_template(
                "audit_form.html",
                error=str(e),
                ace_installed=_is_ace_installed(),
                email_configured=_ec(),
            ),
            400,
        )
    except Exception:
        from ..email import email_configured as _ec
        return (
            render_template(
                "audit_form.html",
                error="An error occurred while processing the document. "
                "Please ensure it is a valid Office file and try again.",
                ace_installed=_is_ace_installed(),
                email_configured=_ec(),
            ),
            500,
        )
    finally:
        if token:
            cleanup_token(token)


def _audit_batch():
    """Handle multi-file audit (up to _BATCH_LIMIT files).

    Gracefully trims to the limit rather than returning an error.
    Files that fail validation are skipped with a warning note instead
    of aborting the whole run.
    """
    standards_profile = request.form.get("standards_profile", "acb_2025")
    profile_label = get_profile_label(standards_profile)
    report_style = request.form.get("report_style", "combined")

    selected, mode_label, suppressed_rules = _build_rule_filter(request.form)
    suppress_rule_ids = set(suppressed_rules)

    uploaded_files = request.files.getlist("document")

    # Graceful over-limit: silently trim, note it in the results
    trimmed = len(uploaded_files) > _BATCH_LIMIT
    files_to_process = uploaded_files[:_BATCH_LIMIT]
    skipped_count = len(uploaded_files) - _BATCH_LIMIT if trimmed else 0

    if not files_to_process:
        from ..email import email_configured as _ec
        return (
            render_template(
                "audit_form.html",
                error="No files were received. Please add at least one document.",
                ace_installed=_is_ace_installed(),
                email_configured=_ec(),
            ),
            400,
        )

    file_results = []  # list of dicts: filename, doc_format, result, error
    tokens_to_clean = []

    for file_storage in files_to_process:
        token = None
        try:
            token, saved_path = validate_upload(file_storage)
            tokens_to_clean.append(token)
            doc_format = _format_from_path(saved_path)
            result = _audit_by_extension(saved_path)
            result = _apply_filters(result, selected, doc_format, suppress_rule_ids)
            file_results.append(
                {
                    "filename": saved_path.name,
                    "doc_format": doc_format,
                    "result": result,
                    "error": None,
                }
            )
        except UploadError as e:
            if token:
                cleanup_token(token)
            file_results.append(
                {
                    "filename": getattr(file_storage, "filename", "unknown") or "unknown",
                    "doc_format": None,
                    "result": None,
                    "error": str(e),
                }
            )
        except Exception:
            if token:
                cleanup_token(token)
            fname = getattr(file_storage, "filename", "unknown") or "unknown"
            file_results.append(
                {
                    "filename": fname,
                    "doc_format": None,
                    "result": None,
                    "error": "An unexpected error occurred while processing this file.",
                }
            )

    # Clean up all temp dirs
    for t in tokens_to_clean:
        cleanup_token(t)

    # Build aggregate stats for combined report header
    successful = [r for r in file_results if r["result"] is not None]
    failed = [r for r in file_results if r["result"] is None]

    total_findings = sum(len(r["result"].findings) for r in successful)
    avg_score = (
        round(sum(r["result"].score for r in successful) / len(successful))
        if successful
        else None
    )

    severity_totals: Counter = Counter()
    for r in successful:
        for f in r["result"].findings:
            severity_totals[f.severity.value] += 1

    # Optional email delivery (single combined email for the whole batch)
    email_status = None
    if request.form.get("email_report") == "on":
        to_email = request.form.get("report_email", "").strip()
        if not _validate_email(to_email):
            email_status = {"success": False, "message": "Report could not be sent: the email address provided is invalid."}
        elif to_email and successful:
            ok, msg = send_batch_audit_report_email(
                to_email=to_email,
                file_results=file_results,
                avg_score=avg_score,
                total_findings=total_findings,
            )
            email_status = {"success": ok, "message": msg}

    return render_template(
        "audit_batch_report.html",
        file_results=file_results,
        successful=successful,
        failed=failed,
        report_style=report_style,
        mode_label=mode_label,
        profile_label=profile_label,
        suppressed_rules=suppressed_rules,
        total_findings=total_findings,
        avg_score=avg_score,
        severity_totals=severity_totals,
        trimmed=trimmed,
        skipped_count=skipped_count,
        batch_limit=_BATCH_LIMIT,
        ace_installed=_is_ace_installed(),
        email_status=email_status,
    )
