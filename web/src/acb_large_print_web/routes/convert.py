"""Convert route -- convert documents to Markdown via MarkItDown."""

from flask import Blueprint, render_template, request, send_file

from acb_large_print.converter import CONVERTIBLE_EXTENSIONS, convert_to_markdown

from ..upload import UploadError, cleanup_token, get_temp_dir, validate_upload

from pathlib import Path

convert_bp = Blueprint("convert", __name__)

# Build the accept string for the file input
_ACCEPT_EXTENSIONS = ",".join(sorted(CONVERTIBLE_EXTENSIONS))


@convert_bp.route("/", methods=["GET"])
def convert_form():
    return render_template("convert_form.html", accept_extensions=_ACCEPT_EXTENSIONS)


@convert_bp.route("/", methods=["POST"])
def convert_submit():
    token = None
    try:
        token, saved_path = validate_upload(request.files.get("document"))
        ext = saved_path.suffix.lower()

        if ext not in CONVERTIBLE_EXTENSIONS:
            raise UploadError(
                f"File type '{ext}' cannot be converted to Markdown. "
                f"Supported: {', '.join(sorted(CONVERTIBLE_EXTENSIONS))}."
            )

        temp_dir = get_temp_dir(token)
        md_output = temp_dir / f"{saved_path.stem}.md"

        output_path, text = convert_to_markdown(saved_path, output_path=md_output)

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
            accept_extensions=_ACCEPT_EXTENSIONS,
        ), 400
    except RuntimeError as exc:
        return render_template(
            "convert_form.html",
            error=str(exc),
            accept_extensions=_ACCEPT_EXTENSIONS,
        ), 500
    finally:
        if token:
            cleanup_token(token)
