"""Fix route -- upload a document and download a remediated copy."""

from pathlib import Path

from flask import Blueprint, render_template, request, send_file
from werkzeug.utils import secure_filename

from ..rules import (
    filter_findings,
    get_all_rule_ids,
    get_rule_ids_by_category,
    get_rule_ids_by_format,
    get_rule_ids_by_severity,
)
from ..upload import (
    UploadError,
    cleanup_token,
    get_temp_dir,
    validate_upload,
)

fix_bp = Blueprint("fix", __name__)


def _fix_by_extension(saved_path: Path, output_path: Path, *, bound: bool = False):
    """Dispatch to the correct fixer based on file extension.

    Returns (output_path, total_fixes, post_audit, warnings).
    """
    ext = saved_path.suffix.lower()
    if ext == ".xlsx":
        from acb_large_print.xlsx_auditor import audit_workbook
        post_audit = audit_workbook(saved_path)
        return saved_path, 0, post_audit, [
            "Excel workbooks cannot be auto-fixed yet. "
            "Review the audit findings and fix them manually in Excel."
        ]
    elif ext == ".pptx":
        from acb_large_print.pptx_auditor import audit_presentation
        post_audit = audit_presentation(saved_path)
        return saved_path, 0, post_audit, [
            "PowerPoint presentations cannot be auto-fixed yet. "
            "Review the audit findings and fix them manually in PowerPoint."
        ]
    elif ext == ".md":
        from acb_large_print.md_auditor import audit_markdown
        post_audit = audit_markdown(saved_path)
        return saved_path, 0, post_audit, [
            "Markdown auto-fix is coming soon. "
            "Review the audit findings and fix them in your text editor."
        ]
    elif ext == ".pdf":
        from acb_large_print.pdf_auditor import audit_pdf
        post_audit = audit_pdf(saved_path)
        return saved_path, 0, post_audit, [
            "PDF files cannot be auto-fixed. "
            "Use Adobe Acrobat Pro or re-export from the source application."
        ]
    elif ext == ".epub":
        from acb_large_print.epub_auditor import audit_epub
        post_audit = audit_epub(saved_path)
        return saved_path, 0, post_audit, [
            "ePub files cannot be auto-fixed yet. "
            "Review the audit findings and fix them in your ePub editor."
        ]
    else:
        from acb_large_print.fixer import fix_document
        return fix_document(saved_path, output_path, bound=bound)


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
    return saved_path.suffix.lower().lstrip(".")


@fix_bp.route("/", methods=["GET"])
def fix_form():
    return render_template("fix_form.html")


@fix_bp.route("/", methods=["POST"])
def fix_submit():
    token = None
    try:
        token, saved_path = validate_upload(request.files.get("document"))

        bound = request.form.get("bound") == "on"
        mode = request.form.get("mode", "full")
        doc_format = _format_from_path(saved_path)

        # Run pre-fix audit for before score
        pre_audit = _audit_by_extension(saved_path)

        # Fix the document (Word only for now; xlsx/pptx return audit-only)
        ext = saved_path.suffix.lower()
        output_name = saved_path.stem + "-fixed" + ext
        output_path = saved_path.parent / output_name
        _, total_fixes, post_audit, warnings = _fix_by_extension(
            saved_path, output_path, bound=bound
        )

        # Filter post-fix findings for display based on mode
        categories = request.form.getlist("category")
        if not categories:
            categories = ["acb", "msac"]
        category_rule_ids = get_rule_ids_by_category(*categories)
        format_rule_ids = get_rule_ids_by_format(doc_format)

        if mode == "essentials":
            selected = get_rule_ids_by_severity("Critical", "High")
            mode_label = "Essentials Fix -- Critical and High focus"
        elif mode == "custom":
            selected = set(request.form.getlist("rule"))
            if not selected:
                selected = get_all_rule_ids()
            mode_label = f"Custom Fix -- {len(selected)} rules selected"
        else:
            selected = get_all_rule_ids()
            mode_label = "Full Fix -- all rules"

        selected = selected & category_rule_ids & format_rule_ids
        post_findings = filter_findings(post_audit.findings, selected)

        return render_template(
            "fix_result.html",
            pre_score=pre_audit.score,
            pre_grade=pre_audit.grade,
            post_score=post_audit.score,
            post_grade=post_audit.grade,
            total_fixes=total_fixes,
            remaining=len(post_audit.findings),
            post_findings=post_findings,
            warnings=warnings,
            mode_label=mode_label,
            download_name=output_name,
            token=token,
        )
    except UploadError as e:
        if token:
            cleanup_token(token)
        return render_template("fix_form.html", error=str(e)), 400
    except Exception:
        if token:
            cleanup_token(token)
        return render_template(
            "fix_form.html",
            error="An error occurred while fixing the document. "
            "Please ensure it is a valid Office file and try again.",
        ), 500
    # Note: do NOT clean up here -- the temp dir must survive for the download


@fix_bp.route("/download", methods=["POST"])
def fix_download():
    """Serve the fixed file and clean up."""
    token = request.form.get("token", "")
    raw_name = request.form.get("download_name", "fixed.docx")
    download_name = secure_filename(raw_name) or "fixed.docx"

    temp_dir = get_temp_dir(token)
    if temp_dir is None:
        return render_template(
            "error.html",
            title="Download Failed",
            message="The fixed file is no longer available. Please run the fix again.",
        ), 404

    file_path = temp_dir / download_name
    # Ensure resolved path stays inside the temp directory (prevent traversal)
    try:
        file_path.resolve().relative_to(temp_dir.resolve())
    except ValueError:
        cleanup_token(token)
        return render_template(
            "error.html",
            title="Download Failed",
            message="Invalid file name.",
        ), 400

    if not file_path.exists():
        cleanup_token(token)
        return render_template(
            "error.html",
            title="Download Failed",
            message="The fixed file is no longer available. Please run the fix again.",
        ), 404

    response = send_file(
        str(file_path),
        as_attachment=True,
        download_name=download_name,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    @response.call_on_close
    def _cleanup():
        cleanup_token(token)

    return response
