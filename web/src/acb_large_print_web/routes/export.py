"""Export route -- convert a .docx to ACB-compliant HTML."""

from flask import Blueprint, render_template, request, send_file

from acb_large_print.exporter import export_cms_fragment, export_standalone_html

from ..upload import UploadError, cleanup_token, get_temp_dir, validate_upload

import zipfile
from pathlib import Path

export_bp = Blueprint("export", __name__)


@export_bp.route("/", methods=["GET"])
def export_form():
    return render_template("export_form.html")


@export_bp.route("/", methods=["POST"])
def export_submit():
    token = None
    try:
        token, saved_path = validate_upload(request.files.get("document"))

        title = request.form.get("title", "").strip()
        mode = request.form.get("mode", "standalone")

        temp_dir = get_temp_dir(token)

        if mode == "cms":
            output_path = temp_dir / "output.html"
            export_cms_fragment(saved_path, output_path, title=title)

            response = send_file(
                str(output_path),
                as_attachment=True,
                download_name=(saved_path.stem + "-cms.html"),
                mimetype="text/html",
            )
        else:
            # Standalone: HTML + CSS, bundled as a ZIP
            html_path = temp_dir / "output.html"
            export_standalone_html(saved_path, html_path, title=title)
            css_path = temp_dir / "acb-large-print.css"

            zip_path = temp_dir / "export.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                html_name = saved_path.stem + ".html"
                zf.write(html_path, html_name)
                if css_path.exists():
                    zf.write(css_path, "acb-large-print.css")

            response = send_file(
                str(zip_path),
                as_attachment=True,
                download_name=(saved_path.stem + "-acb-html.zip"),
                mimetype="application/zip",
            )

        @response.call_on_close
        def _cleanup():
            cleanup_token(token)

        return response

    except UploadError as e:
        if token:
            cleanup_token(token)
        return render_template("export_form.html", error=str(e)), 400
    except Exception:
        if token:
            cleanup_token(token)
        return render_template(
            "export_form.html",
            error="An error occurred while exporting the document. "
            "Please ensure it is a valid .docx file and try again.",
        ), 500
