"""Convert route -- convert documents via MarkItDown, Pandoc, or DAISY Pipeline.

Three conversion directions:
1. To Markdown (MarkItDown): .docx, .xlsx, .pptx, .pdf, .html, .csv, etc.
2. To ACB HTML (Pandoc): .md, .rst, .odt, .rtf, .docx
3. To EPUB / DAISY (Pipeline): .docx, .html, .epub (when Pipeline is installed)
"""

from flask import Blueprint, render_template, request, send_file

from acb_large_print.converter import CONVERTIBLE_EXTENSIONS, convert_to_markdown
from acb_large_print.pandoc_converter import (
    PANDOC_INPUT_EXTENSIONS,
    convert_to_html,
    pandoc_available,
)
from acb_large_print.pipeline_converter import (
    PIPELINE_INPUT_EXTENSIONS,
    get_available_conversions,
    convert_with_pipeline,
    pipeline_available,
)

from ..upload import CONVERT_EXTENSIONS, UploadError, cleanup_token, get_temp_dir, validate_upload

from pathlib import Path

convert_bp = Blueprint("convert", __name__)

# Build the accept strings for the file inputs
_MD_ACCEPT = ",".join(sorted(CONVERTIBLE_EXTENSIONS))
_HTML_ACCEPT = ",".join(sorted(PANDOC_INPUT_EXTENSIONS))
# Union of all for a single file input
_ALL_ACCEPT = ",".join(sorted(CONVERTIBLE_EXTENSIONS | PANDOC_INPUT_EXTENSIONS | PIPELINE_INPUT_EXTENSIONS))


def _template_context(**extra):
    """Common template variables for the convert form."""
    pipeline_conversions = get_available_conversions()
    return dict(
        md_accept=_MD_ACCEPT,
        html_accept=_HTML_ACCEPT,
        all_accept=_ALL_ACCEPT,
        pandoc_installed=pandoc_available(),
        pipeline_installed=pipeline_available(),
        pipeline_conversions=pipeline_conversions,
        **extra,
    )


@convert_bp.route("/", methods=["GET"])
def convert_form():
    return render_template("convert_form.html", **_template_context())


@convert_bp.route("/", methods=["POST"])
def convert_submit():
    token = None
    try:
        token, saved_path = validate_upload(
            request.files.get("document"),
            allowed_extensions=CONVERT_EXTENSIONS,
        )
        ext = saved_path.suffix.lower()
        direction = request.form.get("direction", "to-markdown")

        temp_dir = get_temp_dir(token)

        if direction == "to-html":
            # Pandoc: document -> ACB HTML
            if not pandoc_available():
                raise UploadError(
                    "Pandoc is not installed on the server. "
                    "HTML conversion is unavailable."
                )
            if ext not in PANDOC_INPUT_EXTENSIONS:
                raise UploadError(
                    f"File type '{ext}' cannot be converted to HTML. "
                    f"Supported: {', '.join(sorted(PANDOC_INPUT_EXTENSIONS))}."
                )
            html_output = temp_dir / f"{saved_path.stem}.html"
            title = saved_path.stem.replace("-", " ").replace("_", " ")
            output_path, text = convert_to_html(
                saved_path, output_path=html_output, title=title,
            )
            return send_file(
                str(output_path),
                mimetype="text/html; charset=utf-8",
                as_attachment=True,
                download_name=f"{saved_path.stem}.html",
            )
        elif direction.startswith("pipeline-"):
            # DAISY Pipeline conversion
            conversion_key = direction.replace("pipeline-", "")
            if not pipeline_available():
                raise UploadError(
                    "DAISY Pipeline is not installed on the server. "
                    "Pipeline conversions are unavailable."
                )
            available = get_available_conversions()
            if conversion_key not in available:
                raise UploadError(
                    f"Pipeline conversion '{conversion_key}' is not available."
                )
            output_path, summary = convert_with_pipeline(
                saved_path, conversion_key, output_dir=temp_dir,
            )
            if output_path.is_file():
                mimetype = "application/epub+zip" if output_path.suffix == ".epub" else "application/octet-stream"
                return send_file(
                    str(output_path),
                    mimetype=mimetype,
                    as_attachment=True,
                    download_name=output_path.name,
                )
            else:
                # Directory output -- package as zip
                import shutil as _shutil
                zip_path = temp_dir / f"{saved_path.stem}-{conversion_key}.zip"
                _shutil.make_archive(str(zip_path.with_suffix("")), "zip", str(output_path))
                return send_file(
                    str(zip_path),
                    mimetype="application/zip",
                    as_attachment=True,
                    download_name=zip_path.name,
                )
        else:
            # MarkItDown: document -> Markdown (default)
            if ext not in CONVERTIBLE_EXTENSIONS:
                raise UploadError(
                    f"File type '{ext}' cannot be converted to Markdown. "
                    f"Supported: {', '.join(sorted(CONVERTIBLE_EXTENSIONS))}."
                )
            md_output = temp_dir / f"{saved_path.stem}.md"
            output_path, text = convert_to_markdown(
                saved_path, output_path=md_output,
            )
            return send_file(
                str(output_path),
                mimetype="text/markdown; charset=utf-8",
                as_attachment=True,
                download_name=f"{saved_path.stem}.md",
            )

    except UploadError as exc:
        return render_template(
            "convert_form.html",
            error=str(exc),
            **_template_context(),
        ), 400
    except RuntimeError as exc:
        return render_template(
            "convert_form.html",
            error=str(exc),
            **_template_context(),
        ), 500
    finally:
        if token:
            cleanup_token(token)
