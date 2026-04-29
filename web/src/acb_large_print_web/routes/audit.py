"""Audit route -- upload a document and view a compliance report."""

from collections import Counter
from pathlib import Path
import uuid

from flask import Blueprint, Response, abort, render_template, request, url_for
from werkzeug.utils import secure_filename as _sf

import re

from ..email import send_audit_report_email, send_batch_audit_report_email
from ..app import limiter
from ..rules import (
    build_rule_policy,
    filter_findings,
    get_all_rule_ids,
    get_profile_label,
    get_rule_ids_by_category,
    get_rule_ids_by_severity,
    get_rule_ids_by_format,
    get_rule_ids_by_profile,
    get_rules_by_format,
)
from ..upload import UploadError, cleanup_token, validate_upload
from ..customization_warning import detect_audit_customizations, generate_customization_warning

audit_bp = Blueprint("audit", __name__)

# Rule IDs that the fixer can auto-remediate (all document formats combined).
# Used by the audit report Quick Wins filter.
FIXABLE_RULE_IDS: frozenset[str] = frozenset({
    "ACB-FONT-FAMILY",
    "ACB-FONT-SIZE-BODY",
    "ACB-FONT-SIZE-H1",
    "ACB-FONT-SIZE-H2",
    "ACB-MARGINS",
    "ACB-LINE-SPACING",
    "ACB-ALIGNMENT",
    "ACB-LIST-INDENT",
    "ACB-PARA-INDENT",
    "ACB-FIRST-LINE-INDENT",
    "ACB-NO-ITALIC",
    "ACB-BOLD-BODY",
    "ACB-ALL-CAPS",
    "ACB-NO-ALLCAPS",
    "ACB-HYPHENATION",
    "ACB-PAGE-NUMBERS",
    "ACB-DOC-TITLE",
    "ACB-DOC-LANG",
    "ACB-FAUX-HEADING",
    "ACB-HEADING-HIERARCHY",
})

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
        rules_by_format=get_rules_by_format(),
    )


@audit_bp.route("/from-fix", methods=["POST"])
def audit_from_fix():
    """Re-audit a fixed document without re-uploading (uses existing session token)."""
    from ..upload import get_temp_dir, ALLOWED_EXTENSIONS
    from ..email import email_configured as _ec

    token = request.form.get("token", "").strip()
    download_name = request.form.get("download_name", "").strip()

    temp_dir = get_temp_dir(token)
    if temp_dir is None:
        return (
            render_template(
                "audit_form.html",
                error="Your session has expired. Please upload the fixed document to audit it.",
                ace_installed=_is_ace_installed(),
                email_configured=_ec(),
                rules_by_format=get_rules_by_format(),
            ),
            400,
        )

    # Resolve the fixed file -- prefer the named download, then any -fixed file, then any allowed file
    saved_path = None
    if download_name:
        candidate = temp_dir / _sf(download_name)
        try:
            candidate.resolve().relative_to(temp_dir.resolve())
            if candidate.exists() and candidate.suffix.lower() in ALLOWED_EXTENSIONS:
                saved_path = candidate
        except ValueError:
            pass
    if saved_path is None:
        for f in sorted(temp_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS and f.stem.endswith("-fixed"):
                saved_path = f
                break
    if saved_path is None:
        for f in sorted(temp_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
                saved_path = f
                break

    if saved_path is None:
        return (
            render_template(
                "audit_form.html",
                error="Fixed document not found. Session may have expired. Please upload again.",
                ace_installed=_is_ace_installed(),
                email_configured=_ec(),
                rules_by_format=get_rules_by_format(),
            ),
            400,
        )

    try:
        standards_profile = request.form.get("standards_profile", "acb_2025")
        profile_label = get_profile_label(standards_profile)
        doc_format = _format_from_path(saved_path)
        policy = build_rule_policy(request.form)
        mode_label = policy.mode_label
        suppressed_rules = sorted(policy.suppressed)

        result = _audit_by_extension(saved_path)
        result.findings = policy.filter_findings(result.findings, doc_format)

        chat_token = token  # keep token alive for further downstream use

        share_token = str(uuid.uuid4())
        try:
            share_url = url_for("audit.shared_report", share_token=share_token, _external=True)
        except Exception:
            share_url = None
            share_token = None

        html = render_template(
            "audit_report.html",
            result=result,
            mode_label=mode_label,
            profile_label=profile_label,
            doc_format=doc_format,
            ace_installed=_is_ace_installed(),
            suppressed_rules=suppressed_rules,
            email_status=None,
            ai_used=False,
            customization_warning="",
            chat_token=chat_token,
            fixable_rule_ids=FIXABLE_RULE_IDS,
            share_token=share_token,
            share_url=share_url,
        )

        if share_token:
            try:
                from ..report_cache import save_report
                save_report(share_token, html)
            except Exception:
                pass

        return html

    except Exception:
        return (
            render_template(
                "audit_form.html",
                error="An error occurred during re-audit. Please try again.",
                ace_installed=_is_ace_installed(),
                email_configured=_ec(),
                rules_by_format=get_rules_by_format(),
            ),
            500,
        )


@audit_bp.route("/share/<share_token>", methods=["GET"])
def shared_report(share_token: str):
    """Serve a cached, shareable audit report by token (valid for 1 hour)."""
    from ..report_cache import load_report
    html = load_report(share_token)
    if not html:
        abort(404)
    return Response(html, mimetype="text/html")


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

        policy = build_rule_policy(request.form)
        mode_label = policy.mode_label
        suppressed_rules = sorted(policy.suppressed)

        result = _audit_by_extension(saved_path)
        result.findings = policy.filter_findings(result.findings, doc_format)

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

        # Detect and warn about customizations from ACB defaults
        has_customizations, customization_reasons = detect_audit_customizations(request.form)
        customization_warning = ""
        if has_customizations:
            customization_warning = generate_customization_warning(customization_reasons)

        # Preserve the uploaded file for a potential Chat pivot.
        # Nulling token prevents the finally block from deleting it;
        # the temp dir is reclaimed by OS TTL or the next audit/chat cleanup.
        chat_token = token
        token = None

        # Generate share token before rendering so it can be embedded in the HTML.
        share_token = str(uuid.uuid4())
        try:
            share_url = url_for(
                "audit.shared_report", share_token=share_token, _external=True
            )
        except Exception:
            share_url = None
            share_token = None

        html = render_template(
            "audit_report.html",
            result=result,
            mode_label=mode_label,
            profile_label=profile_label,
            doc_format=doc_format,
            ace_installed=_is_ace_installed(),
            suppressed_rules=suppressed_rules,
            email_status=email_status,
            ai_used=False,
            customization_warning=customization_warning,
            chat_token=chat_token,
            fixable_rule_ids=FIXABLE_RULE_IDS,
            share_token=share_token,
            share_url=share_url,
        )

        # Cache the rendered report for the shareable URL (best-effort).
        if share_token:
            try:
                from ..report_cache import save_report
                save_report(share_token, html)
            except Exception:
                pass

        return html
    except UploadError as e:
        from ..email import email_configured as _ec
        return (
            render_template(
                "audit_form.html",
                error=str(e),
                ace_installed=_is_ace_installed(),
                email_configured=_ec(),
                rules_by_format=get_rules_by_format(),
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
                rules_by_format=get_rules_by_format(),
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

    policy = build_rule_policy(request.form)
    mode_label = policy.mode_label
    suppressed_rules = sorted(policy.suppressed)

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
                rules_by_format=get_rules_by_format(),
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
            result.findings = policy.filter_findings(result.findings, doc_format)
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

    # Detect and warn about customizations from ACB defaults
    has_customizations, customization_reasons = detect_audit_customizations(request.form)
    customization_warning = ""
    if has_customizations:
        customization_warning = generate_customization_warning(customization_reasons)

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
        customization_warning=customization_warning,
    )
