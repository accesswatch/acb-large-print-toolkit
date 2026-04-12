"""Audit route -- upload a document and view a compliance report."""

from pathlib import Path

from flask import Blueprint, render_template, request

from ..rules import (
    filter_findings,
    get_all_rule_ids,
    get_rule_ids_by_category,
    get_rule_ids_by_severity,
    get_rule_ids_by_format,
)
from ..upload import UploadError, cleanup_token, validate_upload

audit_bp = Blueprint("audit", __name__)


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
    return render_template("audit_form.html")


@audit_bp.route("/", methods=["POST"])
def audit_submit():
    token = None
    try:
        token, saved_path = validate_upload(request.files.get("document"))

        mode = request.form.get("mode", "full")
        doc_format = _format_from_path(saved_path)

        result = _audit_by_extension(saved_path)

        # Determine category scope
        categories = request.form.getlist("category")
        if not categories:
            categories = ["acb", "msac"]
        category_rule_ids = get_rule_ids_by_category(*categories)

        # Scope to rules applicable to this format
        format_rule_ids = get_rule_ids_by_format(doc_format)

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
        selected = selected & category_rule_ids & format_rule_ids

        result.findings = filter_findings(result.findings, selected)

        return render_template(
            "audit_report.html",
            result=result,
            mode_label=mode_label,
            doc_format=doc_format,
        )
    except UploadError as e:
        return render_template("audit_form.html", error=str(e)), 400
    except Exception:
        return render_template(
            "audit_form.html",
            error="An error occurred while processing the document. "
            "Please ensure it is a valid Office file and try again.",
        ), 500
    finally:
        if token:
            cleanup_token(token)
