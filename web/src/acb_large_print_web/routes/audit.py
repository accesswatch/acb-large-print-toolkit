"""Audit route -- upload a document and view a compliance report."""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import uuid

from flask import Blueprint, Response, abort, render_template, request, url_for
from werkzeug.utils import secure_filename as _sf

import re

from ..email import send_audit_report_email, send_batch_audit_report_email
from ..app import limiter
from ..csv_export import findings_to_csv_bytes, safe_filename_stem
from ..rules import (
    build_rule_policy,
    filter_findings,
    get_all_rule_ids,
    get_help_urls,
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


def _rules_by_id() -> dict:
    """Lazy lookup of rule metadata keyed by rule_id for inline explanations."""
    from acb_large_print.constants import AUDIT_RULES

    out: dict[str, dict] = {}
    for rid, rule in AUDIT_RULES.items():
        out[rid] = {
            "rule_id": rid,
            "description": rule.description,
            "auto_fixable": rule.auto_fixable,
            "acb_reference": rule.acb_reference,
        }
    return out


def _findings_to_dicts(findings) -> list[dict]:
    """Convert Finding dataclass instances to JSON-serialisable dicts."""
    out: list[dict] = []
    for f in findings:
        sev = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
        out.append({
            "rule_id": f.rule_id,
            "severity": sev,
            "message": f.message,
            "location": getattr(f, "location", "") or "",
            "acb_reference": getattr(f, "acb_reference", "") or "",
            "auto_fixable": getattr(f, "auto_fixable", False),
            "help_urls": get_help_urls(f.rule_id, getattr(f, "acb_reference", "") or ""),
        })
    return out


def _save_share_artifacts(
    share_token: str | None,
    html: str,
    *,
    findings,
    filename: str,
    doc_format: str,
    score: int,
    grade: str,
    profile_label: str,
    mode_label: str,
    passphrase: str | None = None,
) -> None:
    """Persist HTML and findings JSON for the share token (best-effort).

    When ``passphrase`` is provided (truthy, non-empty after stripping) the
    share is also passphrase-protected via ``set_share_passphrase``.
    """
    if not share_token:
        return
    try:
        from ..report_cache import (
            save_findings_data,
            save_report,
            set_share_passphrase,
        )

        save_report(share_token, html)
        save_findings_data(share_token, {
            "filename": filename,
            "doc_format": doc_format,
            "score": int(score),
            "grade": grade,
            "profile_label": profile_label,
            "mode_label": mode_label,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "findings": _findings_to_dicts(findings),
        })
        cleaned = (passphrase or "").strip()
        if cleaned:
            set_share_passphrase(share_token, cleaned)
    except Exception:
        pass


def _share_passphrase_from_form() -> str | None:
    """Read and validate an optional share passphrase from the current request.

    Returns the cleaned passphrase, or None when none was supplied. A minimum
    length of 4 characters is enforced so accidental whitespace cannot lock a
    share. Maximum 200 characters to avoid pathological inputs.
    """
    raw = (request.form.get("share_passphrase") or "").strip()
    if not raw:
        return None
    if len(raw) < 4 or len(raw) > 200:
        return None
    return raw


def _compute_audit_diff(
    findings,
    *,
    prev_score: int | None,
    prev_rule_ids: list[str],
    current_score: int,
):
    """Return a diff summary dict comparing this audit to a previous one.

    ``prev_rule_ids`` may include duplicates (one entry per finding); both
    sides are reduced to multisets so we can compute "cleared" vs "remaining"
    counts, plus a set of newly-introduced rule IDs.
    Returns None when prev_score is missing.
    """
    if prev_score is None:
        return None
    current_ids = [f.rule_id for f in findings]
    cur_counter = Counter(current_ids)
    prev_counter = Counter(prev_rule_ids)
    cleared_total = sum((prev_counter - cur_counter).values())
    new_ids = sorted(set(cur_counter) - set(prev_counter))
    persistent_total = sum((cur_counter & prev_counter).values())
    new_total = sum(cur_counter[r] for r in new_ids)
    return {
        "prev_score": int(prev_score),
        "current_score": int(current_score),
        "delta": int(current_score) - int(prev_score),
        "prev_count": sum(prev_counter.values()),
        "current_count": sum(cur_counter.values()),
        "cleared_count": cleared_total,
        "persistent_count": persistent_total,
        "new_count": new_total,
        "new_rule_ids": new_ids,
    }


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
    from ..upload import get_temp_dir, ALLOWED_EXTENSIONS

    # Quick Start handoff: ?token=... pre-fills the form with the file
    # already uploaded via /process. The user does not need to upload again.
    prefill_token = (request.args.get("token") or "").strip()
    prefill_filename = None
    if prefill_token:
        temp_dir = get_temp_dir(prefill_token)
        if temp_dir is not None:
            for f in sorted(temp_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
                    prefill_filename = f.name
                    break
        if prefill_filename is None:
            prefill_token = None  # session expired or no file -- ignore

    return render_template(
        "audit_form.html",
        ace_installed=_is_ace_installed(),
        email_configured=email_configured(),
        rules_by_format=get_rules_by_format(),
        prefill_token=prefill_token or None,
        prefill_filename=prefill_filename,
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

        # Compute a diff vs the audit that ran before the fix, when present.
        prev_score_raw = request.form.get("prev_score", "").strip()
        try:
            prev_score_int: int | None = int(prev_score_raw) if prev_score_raw else None
        except ValueError:
            prev_score_int = None
        prev_rule_ids_raw = request.form.get("prev_rule_ids", "")
        prev_rule_ids = [r.strip() for r in prev_rule_ids_raw.split(",") if r.strip()]
        audit_diff = _compute_audit_diff(
            result.findings,
            prev_score=prev_score_int,
            prev_rule_ids=prev_rule_ids,
            current_score=result.score,
        )

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
            share_passphrase_set=bool(_share_passphrase_from_form()),
            rules_by_id=_rules_by_id(),
            audit_diff=audit_diff,
            audit_source="from-fix",
        )

        _save_share_artifacts(
            share_token,
            html,
            findings=result.findings,
            filename=saved_path.name,
            doc_format=doc_format,
            score=result.score,
            grade=result.grade,
            profile_label=profile_label,
            mode_label=mode_label,
            passphrase=_share_passphrase_from_form(),
        )

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


@audit_bp.route("/from-convert", methods=["POST"])
def audit_from_convert():
    """Audit a converted document without re-uploading (uses existing token).

    Mirrors :func:`audit_from_fix` but locates any auditable file in the
    session temp directory rather than expecting a ``-fixed`` suffix.
    """
    from ..upload import get_temp_dir, ALLOWED_EXTENSIONS
    from ..email import email_configured as _ec

    token = request.form.get("token", "").strip()
    download_name = request.form.get("download_name", "").strip()

    temp_dir = get_temp_dir(token)
    if temp_dir is None:
        return (
            render_template(
                "audit_form.html",
                error="Your session has expired. Please upload the converted document to audit it.",
                ace_installed=_is_ace_installed(),
                email_configured=_ec(),
                rules_by_format=get_rules_by_format(),
            ),
            400,
        )

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
        # Prefer the most recently modified auditable file in the temp dir.
        candidates = [
            f for f in temp_dir.iterdir()
            if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
        ]
        if candidates:
            saved_path = max(candidates, key=lambda p: p.stat().st_mtime)

    if saved_path is None:
        return (
            render_template(
                "audit_form.html",
                error="The converted file could not be audited (its format is not supported by the auditor).",
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

        chat_token = token

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
            share_passphrase_set=bool(_share_passphrase_from_form()),
            rules_by_id=_rules_by_id(),
            audit_diff=None,
            audit_source="from-convert",
        )

        _save_share_artifacts(
            share_token,
            html,
            findings=result.findings,
            filename=saved_path.name,
            doc_format=doc_format,
            score=result.score,
            grade=result.grade,
            profile_label=profile_label,
            mode_label=mode_label,
            passphrase=_share_passphrase_from_form(),
        )

        return html

    except Exception:
        return (
            render_template(
                "audit_form.html",
                error="An error occurred while auditing the converted document. Please try again.",
                ace_installed=_is_ace_installed(),
                email_configured=_ec(),
                rules_by_format=get_rules_by_format(),
            ),
            500,
        )


@audit_bp.route("/share/<share_token>/csv", methods=["GET"])
def shared_report_csv(share_token: str):
    """Download the cached audit findings as a UTF-8 CSV file."""
    from ..report_cache import load_findings_data

    gate = _share_unlock_required(share_token)
    if gate is not None:
        return gate

    data = load_findings_data(share_token)
    if not data:
        abort(404)

    csv_bytes = findings_to_csv_bytes(
        data.get("findings", []),
        filename=data.get("filename", ""),
        doc_format=data.get("doc_format", ""),
        score=data.get("score"),
        grade=data.get("grade", ""),
        profile_label=data.get("profile_label", ""),
        mode_label=data.get("mode_label", ""),
    )

    stem = safe_filename_stem(Path(data.get("filename", "audit") or "audit").stem)
    download_name = f"{stem}-findings.csv"
    return Response(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


@audit_bp.route("/share/<share_token>/pdf", methods=["GET"])
def shared_report_pdf(share_token: str):
    """Render the cached HTML report as a PDF (lazy, cached for repeat downloads)."""
    from ..report_cache import (
        load_findings_data,
        load_pdf,
        load_report,
        save_pdf,
    )

    gate = _share_unlock_required(share_token)
    if gate is not None:
        return gate

    pdf_bytes = load_pdf(share_token)
    if pdf_bytes is None:
        html = load_report(share_token)
        if not html:
            abort(404)
        try:
            from weasyprint import HTML  # type: ignore[import-not-found]
        except ImportError:
            abort(503)
        try:
            pdf_bytes = HTML(string=html, base_url=request.url_root).write_pdf()
        except Exception:
            abort(500)
        if pdf_bytes:
            save_pdf(share_token, pdf_bytes)

    data = load_findings_data(share_token) or {}
    stem_source = data.get("filename") or "audit"
    stem = safe_filename_stem(Path(stem_source).stem or "audit")
    download_name = f"{stem}-audit-report.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


@audit_bp.route("/share/<share_token>", methods=["GET", "POST"])
def shared_report(share_token: str):
    """Serve a cached, shareable audit report by token (valid for 1 hour).

    When the share is passphrase-protected, render a small unlock form on
    GET and validate the supplied passphrase on POST. The passphrase is also
    accepted via the ``?p=...`` query string for convenience (e.g. when the
    sharer pastes a combined link into chat) -- but the prompt is the
    canonical path.
    """
    from ..report_cache import (
        load_report,
        share_requires_passphrase,
        verify_share_passphrase,
    )

    html = load_report(share_token)
    if not html:
        abort(404)

    if share_requires_passphrase(share_token):
        candidate = (request.form.get("share_passphrase")
                     or request.args.get("p")
                     or "").strip()
        if not candidate or not verify_share_passphrase(share_token, candidate):
            return render_template(
                "share_unlock.html",
                share_token=share_token,
                error=bool(candidate),
                target="report",
            ), (401 if candidate else 200)

    return Response(html, mimetype="text/html")


def _share_unlock_required(share_token: str) -> Response | None:
    """Return an unlock-form Response when a passphrase is required and missing.

    Used by the CSV and PDF download endpoints, which accept the passphrase
    only via ``?p=...`` (no POST body) so a single click from the unlock form
    can deep-link to either download.
    """
    from ..report_cache import (
        share_requires_passphrase,
        verify_share_passphrase,
    )
    if not share_requires_passphrase(share_token):
        return None
    candidate = (request.args.get("p") or "").strip()
    if candidate and verify_share_passphrase(share_token, candidate):
        return None
    return render_template(
        "share_unlock.html",
        share_token=share_token,
        error=bool(candidate),
        target="download",
    ), 401  # type: ignore[return-value]


def audit_submit():
    upload_mode = request.form.get("upload_mode", "single")

    if upload_mode == "batch":
        return _audit_batch()
    return _audit_single()


def _audit_single():
    """Handle single-file audit -- original behaviour."""
    token = None
    try:
        from ..tool_usage import record as _record_usage
        from ..upload import get_temp_dir, ALLOWED_EXTENSIONS
        _record_usage("audit")

        # Quick Start handoff: when a session token is posted with prefill=1
        # we re-use the previously uploaded file rather than requiring a new
        # upload. validate_upload() is skipped entirely in that path.
        saved_path = None
        prefill_token = (request.form.get("token") or "").strip()
        if prefill_token and request.form.get("prefill") == "1":
            temp_dir = get_temp_dir(prefill_token)
            if temp_dir is not None:
                for f in sorted(temp_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
                        saved_path = f
                        break
            if saved_path is None:
                # Session expired or file missing -- fall through to normal upload
                prefill_token = ""
            else:
                token = prefill_token

        if saved_path is None:
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
            share_passphrase_set=bool(_share_passphrase_from_form()),
            rules_by_id=_rules_by_id(),
            audit_diff=None,
            audit_source="upload",
        )

        _save_share_artifacts(
            share_token,
            html,
            findings=result.findings,
            filename=saved_path.name,
            doc_format=doc_format,
            score=result.score,
            grade=result.grade,
            profile_label=profile_label,
            mode_label=mode_label,
            passphrase=_share_passphrase_from_form(),
        )

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
