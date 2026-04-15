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


def _fix_by_extension(
    saved_path: Path,
    output_path: Path,
    *,
    bound: bool = False,
    list_indent_in: float = 0.0,
    list_hanging_in: float = 0.0,
    para_indent_in: float = 0.0,
    first_line_indent_in: float = 0.0,
    detect_headings: bool = False,
    use_ai: bool = False,
    heading_threshold: int | None = None,
    confirmed_headings: list | None = None,
    heading_accuracy: str = "balanced",
):
    """Dispatch to the correct fixer based on file extension.

    Returns (output_path, total_fixes, fix_records, post_audit, warnings).
    """
    ext = saved_path.suffix.lower()
    if ext == ".xlsx":
        from acb_large_print.xlsx_auditor import audit_workbook

        post_audit = audit_workbook(saved_path)
        return (
            saved_path,
            0,
            [],
            post_audit,
            [
                "Excel workbooks cannot be auto-fixed yet. "
                "Review the audit findings and fix them manually in Excel."
            ],
        )
    elif ext == ".pptx":
        from acb_large_print.pptx_auditor import audit_presentation

        post_audit = audit_presentation(saved_path)
        return (
            saved_path,
            0,
            [],
            post_audit,
            [
                "PowerPoint presentations cannot be auto-fixed yet. "
                "Review the audit findings and fix them manually in PowerPoint."
            ],
        )
    elif ext == ".md":
        from acb_large_print.md_auditor import audit_markdown

        post_audit = audit_markdown(saved_path)
        return (
            saved_path,
            0,
            [],
            post_audit,
            [
                "Markdown auto-fix is coming soon. "
                "Review the audit findings and fix them in your text editor."
            ],
        )
    elif ext == ".pdf":
        from acb_large_print.pdf_auditor import audit_pdf

        post_audit = audit_pdf(saved_path)
        return (
            saved_path,
            0,
            [],
            post_audit,
            [
                "PDF files cannot be auto-fixed. "
                "Use Adobe Acrobat Pro or re-export from the source application."
            ],
        )
    elif ext == ".epub":
        from acb_large_print.epub_auditor import audit_epub

        post_audit = audit_epub(saved_path)
        return (
            saved_path,
            0,
            [],
            post_audit,
            [
                "ePub files cannot be auto-fixed yet. "
                "Review the audit findings and fix them in your ePub editor."
            ],
        )
    else:
        from acb_large_print.fixer import fix_document

        ai_provider = None
        if detect_headings and use_ai:
            try:
                from acb_large_print.ai_provider import get_provider

                ai_provider = get_provider()
            except Exception:
                pass  # Fall back to heuristic-only
        return fix_document(
            saved_path,
            output_path,
            bound=bound,
            list_indent_in=list_indent_in,
            list_hanging_in=list_hanging_in,
            para_indent_in=para_indent_in,
            first_line_indent_in=first_line_indent_in,
            detect_headings=detect_headings,
            ai_provider=ai_provider,
            heading_threshold=heading_threshold,
            confirmed_headings=confirmed_headings,
            heading_accuracy_level=heading_accuracy,
        )


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
    from acb_large_print.ai_provider import is_ai_available

    return render_template("fix_form.html", ai_available=is_ai_available())


def _parse_form_options(form):
    """Extract fix options from the submitted form (used by both submit and confirm)."""
    bound = form.get("bound") == "on"
    flush_lists = form.get("flush_lists") == "on"
    mode = form.get("mode", "full")

    if flush_lists:
        list_indent_in = 0.0
        list_hanging_in = 0.0
    else:
        try:
            list_indent_in = float(form.get("list_indent", "0.5"))
        except (ValueError, TypeError):
            list_indent_in = 0.5
        try:
            list_hanging_in = float(form.get("list_hanging", "0.25"))
        except (ValueError, TypeError):
            list_hanging_in = 0.25
        list_indent_in = max(0.0, min(2.0, list_indent_in))
        list_hanging_in = max(0.0, min(2.0, list_hanging_in))

    flush_paragraphs = form.get("flush_paragraphs") == "on"
    if flush_paragraphs:
        para_indent_in = 0.0
        first_line_indent_in = 0.0
    else:
        try:
            para_indent_in = float(form.get("para_indent", "0.0"))
        except (ValueError, TypeError):
            para_indent_in = 0.0
        try:
            first_line_indent_in = float(form.get("first_line_indent", "0.0"))
        except (ValueError, TypeError):
            first_line_indent_in = 0.0
        para_indent_in = max(0.0, min(2.0, para_indent_in))
        first_line_indent_in = max(0.0, min(2.0, first_line_indent_in))

    detect_headings = form.get("detect_headings") == "on"
    use_ai = form.get("use_ai") == "on"
    try:
        heading_threshold = int(form.get("heading_threshold", "50"))
        heading_threshold = max(0, min(100, heading_threshold))
    except (ValueError, TypeError):
        heading_threshold = 50
    
    heading_accuracy = form.get("heading_accuracy", "balanced")
    if heading_accuracy not in ("conservative", "balanced", "thorough"):
        heading_accuracy = "balanced"

    return {
        "bound": bound,
        "mode": mode,
        "list_indent_in": list_indent_in,
        "list_hanging_in": list_hanging_in,
        "para_indent_in": para_indent_in,
        "first_line_indent_in": first_line_indent_in,
        "detect_headings": detect_headings,
        "use_ai": use_ai,
        "heading_threshold": heading_threshold,
        "heading_accuracy": heading_accuracy,
    }


def _run_fix_and_render(saved_path, token, opts, *, confirmed_headings=None):
    """Run the fixer and render fix_result.html. Shared by submit and confirm."""
    doc_format = _format_from_path(saved_path)
    pre_audit = _audit_by_extension(saved_path)

    ext = saved_path.suffix.lower()
    output_name = saved_path.stem + "-fixed" + ext
    output_path = saved_path.parent / output_name

    _, total_fixes, fix_records, post_audit, warnings = _fix_by_extension(
        saved_path,
        output_path,
        bound=opts["bound"],
        list_indent_in=opts["list_indent_in"],
        list_hanging_in=opts["list_hanging_in"],
        para_indent_in=opts["para_indent_in"],
        first_line_indent_in=opts["first_line_indent_in"],
        detect_headings=opts["detect_headings"],
        use_ai=opts["use_ai"],
        heading_threshold=opts["heading_threshold"],
        confirmed_headings=confirmed_headings,
        heading_accuracy=opts["heading_accuracy"],
    )

    categories = request.form.getlist("category") or ["acb", "msac"]
    category_rule_ids = get_rule_ids_by_category(*categories)
    format_rule_ids = get_rule_ids_by_format(doc_format)
    mode = opts["mode"]

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
        fix_records=fix_records,
        remaining=len(post_audit.findings),
        post_findings=post_findings,
        warnings=warnings,
        mode_label=mode_label,
        download_name=output_name,
        token=token,
    )


@fix_bp.route("/", methods=["POST"])
def fix_submit():
    token = None
    try:
        token, saved_path = validate_upload(request.files.get("document"))
        opts = _parse_form_options(request.form)
        ext = saved_path.suffix.lower()

        # Interactive heading review: detect candidates first for .docx
        if opts["detect_headings"] and ext == ".docx":
            from docx import Document as _Document
            from acb_large_print.heading_detector import detect_headings as _detect

            ai_provider = None
            if opts["use_ai"]:
                try:
                    from acb_large_print.ai_provider import get_provider

                    ai_provider = get_provider()
                except Exception:
                    pass

            doc = _Document(str(saved_path))
            candidates = _detect(
                doc,
                ai_provider=ai_provider,
                threshold=opts["heading_threshold"],
            )

            if candidates:
                # Build hidden form fields to preserve all original options
                form_fields = {}
                for key in request.form:
                    values = request.form.getlist(key)
                    if len(values) == 1:
                        form_fields[key] = values[0]
                    else:
                        form_fields[key] = values
                return render_template(
                    "fix_review_headings.html",
                    candidates=candidates,
                    token=token,
                    filename=saved_path.name,
                    form_fields=form_fields,
                )

        return _run_fix_and_render(saved_path, token, opts)

    except UploadError as e:
        if token:
            cleanup_token(token)
        from acb_large_print.ai_provider import is_ai_available

        return (
            render_template(
                "fix_form.html", error=str(e), ai_available=is_ai_available()
            ),
            400,
        )
    except Exception:
        if token:
            cleanup_token(token)
        from acb_large_print.ai_provider import is_ai_available

        return (
            render_template(
                "fix_form.html",
                error="An error occurred while fixing the document. "
                "Please ensure it is a valid Office file and try again.",
                ai_available=is_ai_available(),
            ),
            500,
        )
    # Note: do NOT clean up here -- the temp dir must survive for the download


@fix_bp.route("/confirm", methods=["POST"])
def fix_confirm():
    """Apply fixes with user-confirmed heading selections."""
    token = request.form.get("token", "")
    temp_dir = get_temp_dir(token)
    if temp_dir is None:
        from acb_large_print.ai_provider import is_ai_available

        return (
            render_template(
                "fix_form.html",
                error="Your session has expired or the uploaded file is no longer available. "
                      "This can happen if the review took more than 24 hours or the server was restarted. "
                      "Please upload and fix the document again.",
                ai_available=is_ai_available(),
            ),
            400,
        )

    # Find the uploaded file in the temp dir
    saved_path = None
    for f in temp_dir.iterdir():
        if f.is_file() and f.suffix.lower() in {
            ".docx",
            ".xlsx",
            ".pptx",
            ".md",
            ".pdf",
            ".epub",
        }:
            saved_path = f
            break
    if saved_path is None:
        cleanup_token(token)
        from acb_large_print.ai_provider import is_ai_available

        return (
            render_template(
                "fix_form.html",
                error="Uploaded file not found. Please upload and fix the document again.",
                ai_available=is_ai_available(),
            ),
            400,
        )

    try:
        opts = _parse_form_options(request.form)

        # Parse confirmed headings from the review form
        confirmed_headings = []
        count = int(request.form.get("candidate_count", "0"))
        for i in range(count):
            level = request.form.get(f"level_{i}")
            if level == "skip":
                continue
            try:
                level_int = int(level)
            except (ValueError, TypeError):
                continue
            if not 1 <= level_int <= 6:
                continue
            idx = int(request.form.get(f"idx_{i}", "-1"))
            text = request.form.get(f"text_{i}", "")
            if idx >= 0 and text:
                confirmed_headings.append((idx, level_int, text))

        return _run_fix_and_render(
            saved_path,
            token,
            opts,
            confirmed_headings=confirmed_headings if confirmed_headings else None,
        )

    except Exception:
        cleanup_token(token)
        from acb_large_print.ai_provider import is_ai_available

        return (
            render_template(
                "fix_form.html",
                error="An error occurred while fixing the document. "
                "Please try again.",
                ai_available=is_ai_available(),
            ),
            500,
        )


@fix_bp.route("/download", methods=["POST"])
def fix_download():
    """Serve the fixed file and clean up."""
    token = request.form.get("token", "")
    raw_name = request.form.get("download_name", "fixed.docx")
    download_name = secure_filename(raw_name) or "fixed.docx"

    temp_dir = get_temp_dir(token)
    if temp_dir is None:
        return (
            render_template(
                "error.html",
                title="Download Failed",
                message="The fixed file is no longer available. Please run the fix again.",
            ),
            404,
        )

    file_path = temp_dir / download_name
    # Ensure resolved path stays inside the temp directory (prevent traversal)
    try:
        file_path.resolve().relative_to(temp_dir.resolve())
    except ValueError:
        cleanup_token(token)
        return (
            render_template(
                "error.html",
                title="Download Failed",
                message="Invalid file name.",
            ),
            400,
        )

    if not file_path.exists():
        cleanup_token(token)
        return (
            render_template(
                "error.html",
                title="Download Failed",
                message="The fixed file is no longer available. Please run the fix again.",
            ),
            404,
        )

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
