"""Audit route -- upload a document and view a compliance report."""

from pathlib import Path

from flask import Blueprint, render_template, request

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


@audit_bp.route("/", methods=["GET"])
def audit_form():
    return render_template("audit_form.html", ace_installed=_is_ace_installed())


@audit_bp.route("/", methods=["POST"])
def audit_submit():
    token = None
    try:
        token, saved_path = validate_upload(request.files.get("document"))

        mode = request.form.get("mode", "full")
        standards_profile = request.form.get("standards_profile", "acb_2025")
        profile_label = get_profile_label(standards_profile)
        doc_format = _format_from_path(saved_path)

        result = _audit_by_extension(saved_path)

        suppress_link_text = request.form.get("suppress_link_text") == "on"
        suppress_missing_alt_text = (
            request.form.get("suppress_missing_alt_text") == "on"
        )
        suppress_faux_heading = request.form.get("suppress_faux_heading") == "on"
        suppressed_rules: list[str] = []

        suppress_rule_ids: set[str] = set()
        if suppress_link_text:
            suppress_rule_ids.add("ACB-LINK-TEXT")
        if suppress_missing_alt_text:
            suppress_rule_ids.add("ACB-MISSING-ALT-TEXT")
        if suppress_faux_heading:
            suppress_rule_ids.add("ACB-FAUX-HEADING")

        if suppress_rule_ids:
            suppressed_rules = sorted(suppress_rule_ids)
            result.findings = [
                f for f in result.findings if f.rule_id not in suppress_rule_ids
            ]

        # Determine category scope
        categories = request.form.getlist("category")
        if not categories:
            categories = ["acb", "msac"]
        category_rule_ids = get_rule_ids_by_category(*categories)

        # Scope to rules applicable to this format
        format_rule_ids = get_rule_ids_by_format(doc_format)
        profile_rule_ids = get_rule_ids_by_profile(standards_profile)

        # Determine which rules to show based on mode
        if mode == "quick":
            selected = get_rule_ids_by_severity("Critical", "High")
            mode_label = "Quick Audit -- Critical and High only"
        elif mode == "custom":
            selected = set(request.form.getlist("rule"))
            if not selected:
                selected = get_all_rule_ids()
            mode_label = f"Custom Audit -- {len(selected)} rules selected"
        else:
            selected = get_all_rule_ids()
            mode_label = "Full Audit -- all rules"

        # Intersect with category scope AND format scope
        selected = selected & category_rule_ids & format_rule_ids & profile_rule_ids

        result.findings = filter_findings(result.findings, selected)

        return render_template(
            "audit_report.html",
            result=result,
            mode_label=mode_label,
            profile_label=profile_label,
            doc_format=doc_format,
            ace_installed=_is_ace_installed(),
            suppressed_rules=suppressed_rules,
        )
    except UploadError as e:
        return (
            render_template(
                "audit_form.html", error=str(e), ace_installed=_is_ace_installed()
            ),
            400,
        )
    except Exception:
        return (
            render_template(
                "audit_form.html",
                error="An error occurred while processing the document. "
                "Please ensure it is a valid Office file and try again.",
                ace_installed=_is_ace_installed(),
            ),
            500,
        )
    finally:
        if token:
            cleanup_token(token)
