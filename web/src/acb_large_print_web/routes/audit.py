"""Audit route -- upload a .docx and view a compliance report."""

from flask import Blueprint, render_template, request

from acb_large_print.auditor import audit_document

from ..rules import filter_findings, get_all_rule_ids, get_rule_ids_by_severity
from ..upload import UploadError, cleanup_token, validate_upload

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/", methods=["GET"])
def audit_form():
    return render_template("audit_form.html")


@audit_bp.route("/", methods=["POST"])
def audit_submit():
    token = None
    try:
        token, saved_path = validate_upload(request.files.get("document"))

        mode = request.form.get("mode", "full")

        result = audit_document(saved_path)

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

        result.findings = filter_findings(result.findings, selected)

        return render_template(
            "audit_report.html",
            result=result,
            mode_label=mode_label,
        )
    except UploadError as e:
        return render_template("audit_form.html", error=str(e)), 400
    except Exception:
        return render_template(
            "audit_form.html",
            error="An error occurred while processing the document. "
            "Please ensure it is a valid .docx file and try again.",
        ), 500
    finally:
        if token:
            cleanup_token(token)
