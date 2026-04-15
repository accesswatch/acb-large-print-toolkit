"""Template route -- generate an ACB-compliant Word template (.dotx)."""

from flask import Blueprint, render_template, request, send_file

from acb_large_print.template import create_template

from ..upload import UPLOAD_TEMP_BASE, cleanup_tempdir

import uuid
from pathlib import Path

template_bp = Blueprint("template", __name__)


@template_bp.route("/", methods=["GET"])
def template_form():
    return render_template("template_form.html")


@template_bp.route("/", methods=["POST"])
def template_submit():
    temp_dir = None
    try:
        title = request.form.get("title", "").strip() or "ACB Large Print Document"
        bound = request.form.get("bound") == "on"
        include_sample = request.form.get("include_sample") == "on"
        standards_profile = request.form.get("standards_profile", "acb_2025")

        # Create a temp dir for the output
        token = str(uuid.uuid4())
        temp_dir = UPLOAD_TEMP_BASE / token
        temp_dir.mkdir(parents=True, exist_ok=True)

        output_path = temp_dir / "ACB-Large-Print-Template.dotx"

        create_template(
            output_path,
            bound=bound,
            include_sample=include_sample,
            title=title,
            standards_profile=standards_profile,
        )

        response = send_file(
            str(output_path),
            as_attachment=True,
            download_name="ACB-Large-Print-Template.dotx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.template",
        )

        @response.call_on_close
        def _cleanup():
            cleanup_tempdir(temp_dir)

        return response

    except Exception as exc:
        import logging

        logging.getLogger("acb_large_print").exception(
            "Template creation failed: %s", exc
        )
        if temp_dir:
            cleanup_tempdir(temp_dir)
        return (
            render_template(
                "template_form.html",
                error="An error occurred while creating the template. Please try again.",
            ),
            500,
        )
