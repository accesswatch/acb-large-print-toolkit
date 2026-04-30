"""Convert route -- convert documents via MarkItDown, Pandoc, WeasyPrint, or DAISY Pipeline.

Seven conversion directions:
1. To Markdown (MarkItDown): .docx, .xlsx, .pptx, .pdf, .html, .csv, etc.
2. To ACB HTML (Pandoc, or MarkItDown→Pandoc): .md, .rst, .odt, .rtf, .docx, .epub,
   plus chained: .pptx, .xlsx, .xls, .pdf, .csv, .html, .htm, .json, .xml
3. To Word .docx (Pandoc, or MarkItDown→Pandoc): .md, .rst, .odt, .rtf, .epub,
   plus chained: .pptx, .xlsx, .xls, .pdf, .csv, .html, .htm, .json, .xml
4. To EPUB 3 (Pandoc, or MarkItDown→Pandoc): .md, .rst, .odt, .rtf, .docx,
   plus chained: .pptx, .xlsx, .xls, .pdf, .csv, .html, .htm, .json, .xml
5. To PDF (Pandoc + WeasyPrint, or MarkItDown→Pandoc+WeasyPrint): .md, .rst, .odt,
   .rtf, .docx, .epub, plus chained: .pptx, .xlsx, .xls, .pdf, .csv, .html, .htm
6. To EPUB / DAISY (Pipeline): .docx, .html, .epub (when Pipeline is installed)

Two-stage chaining: formats not natively supported by Pandoc are first extracted to
Markdown via MarkItDown, then that Markdown is fed to Pandoc. This transparently
extends Pandoc output to PowerPoint, Excel, PDF, and other MarkItDown-readable formats.

Audio transcription has its own dedicated route at /whisperer (BITS Whisperer).
"""

from flask import Blueprint, abort, current_app, render_template, request, send_file, url_for

from werkzeug.utils import secure_filename as _secure_filename

from acb_large_print.converter import (
    CONVERTIBLE_EXTENSIONS,
    convert_to_markdown,
)
from acb_large_print.exporter import export_cms_fragment
from acb_large_print.pandoc_converter import (
    PANDOC_INPUT_EXTENSIONS,
    convert_to_html,
    convert_to_docx,
    convert_to_epub,
    convert_to_pdf,
    pandoc_available,
    weasyprint_available,
)
from acb_large_print.pipeline_converter import (
    PIPELINE_INPUT_EXTENSIONS,
    get_available_conversions,
    convert_with_pipeline,
    pipeline_available,
)

from ..upload import (
    CONVERT_EXTENSIONS,
    UploadError,
    cleanup_token,
    get_temp_dir,
    validate_upload,
)
from ..feature_flags import get_all_flags

from pathlib import Path

convert_bp = Blueprint("convert", __name__)

# Sentinel path used to signal "skip ACB CSS" to pandoc_converter
_NO_ACB_CSS_SENTINEL = Path("__no_acb_css__")


# Allowed MIME types for the download/preview routes
_DOWNLOAD_MIMETYPES: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".epub": "application/epub+zip",
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".epub": "application/epub+zip",
}


def _resolve_convert_file(token: str, filename: str):
    """Resolve a convert download/preview request to a safe file path.

    Returns (file_path, mimetype) or aborts 404 on any failure.
    """
    safe_name = _secure_filename(filename)
    if not safe_name:
        abort(404)
    temp_dir = get_temp_dir(token)
    if not temp_dir:
        abort(404)
    file_path = temp_dir / safe_name
    # Verify the resolved path is still inside the temp dir (traversal guard)
    try:
        file_path.resolve().relative_to(temp_dir.resolve())
    except ValueError:
        abort(404)
    if not file_path.exists() or not file_path.is_file():
        abort(404)
    ext = file_path.suffix.lower()
    mimetype = _DOWNLOAD_MIMETYPES.get(ext, "application/octet-stream")
    return file_path, mimetype


@convert_bp.route("/download/<token>/<filename>", methods=["GET"])
def convert_download(token: str, filename: str):
    """Serve a previously converted file as a download."""
    file_path, mimetype = _resolve_convert_file(token, filename)
    return send_file(
        str(file_path),
        mimetype=mimetype,
        as_attachment=True,
        download_name=file_path.name,
    )


@convert_bp.route("/preview/<token>/<filename>", methods=["GET"])
def convert_preview(token: str, filename: str):
    """Serve a previously converted HTML file inline (for iframe preview)."""
    file_path, mimetype = _resolve_convert_file(token, filename)
    if file_path.suffix.lower() != ".html":
        abort(404)
    return send_file(str(file_path), mimetype=mimetype, as_attachment=False)

# Document-type formats in CONVERTIBLE_EXTENSIONS that Pandoc cannot read directly
# but are worth chaining via Markdown (excludes .zip and image formats).
# These get a two-stage conversion: MarkItDown → .md → Pandoc.
_CHAIN_VIA_MARKDOWN: frozenset[str] = frozenset({
    ".pptx",  # PowerPoint
    ".xlsx",  # Excel
    ".xls",   # Excel (legacy)
    ".pdf",   # PDF (text-based)
    ".csv",   # CSV data
    ".html",  # HTML (re-encode with ACB styling via Pandoc)
    ".htm",   # HTML (alternate extension)
    ".json",  # JSON data
    ".xml",   # XML data
})

# All formats accepted by Pandoc outputs after chaining is accounted for
_PANDOC_EFFECTIVE_EXTENSIONS: frozenset[str] = (
    PANDOC_INPUT_EXTENSIONS | _CHAIN_VIA_MARKDOWN
)

# Build the accept strings for the file inputs
_MD_ACCEPT = ",".join(sorted(CONVERTIBLE_EXTENSIONS))
_HTML_ACCEPT = ",".join(sorted(_PANDOC_EFFECTIVE_EXTENSIONS))
# Union of all for a single file input (no audio -- that's /whisperer)
_ALL_ACCEPT = ",".join(
    sorted(CONVERTIBLE_EXTENSIONS | PANDOC_INPUT_EXTENSIONS | PIPELINE_INPUT_EXTENSIONS)
)


def _is_auditable_output(filename: str) -> bool:
    """Return True if the converted output's extension is supported by Audit."""
    from ..upload import ALLOWED_EXTENSIONS

    suffix = Path(filename).suffix.lower()
    return suffix in ALLOWED_EXTENSIONS


def _convert_result_response(
    token_value: str,
    *,
    download_name: str,
    preview_type: str,
    original_stem: str,
    cms_content: str | None = None,
):
    """Render the shared convert_result.html for a finished conversion.

    Used by every direction that produces a downloadable artefact, so the
    user lands on a page with explicit Download and (optionally) Audit
    actions instead of being thrown into a browser save dialog.
    """
    return render_template(
        "convert_result.html",
        token=token_value,
        download_name=download_name,
        preview_type=preview_type,
        original_stem=original_stem,
        cms_content=cms_content,
        auditable_output=_is_auditable_output(download_name),
    )


def _template_context(**extra):
    """Common template variables for the convert form."""
    all_flags = get_all_flags()
    convert_enabled = bool(all_flags.get("GLOW_ENABLE_CONVERTER", True))
    convert_to_markdown_enabled = bool(all_flags.get("GLOW_ENABLE_CONVERT_TO_MARKDOWN", True))
    convert_to_html_enabled = bool(all_flags.get("GLOW_ENABLE_CONVERT_TO_HTML", True))
    convert_to_docx_enabled = bool(all_flags.get("GLOW_ENABLE_CONVERT_TO_DOCX", True))
    convert_to_epub_enabled = bool(all_flags.get("GLOW_ENABLE_CONVERT_TO_EPUB", True))
    convert_to_pdf_enabled = bool(all_flags.get("GLOW_ENABLE_CONVERT_TO_PDF", True))
    convert_to_pipeline_enabled = bool(all_flags.get("GLOW_ENABLE_CONVERT_TO_PIPELINE", True))

    pipeline_conversions = (
        get_available_conversions() if convert_to_pipeline_enabled else {}
    )
    return dict(
        md_accept=_MD_ACCEPT,
        html_accept=_HTML_ACCEPT,
        all_accept=_ALL_ACCEPT,
        pandoc_installed=pandoc_available(),
        weasyprint_installed=weasyprint_available(),
        pipeline_installed=pipeline_available(),
        pipeline_conversions=pipeline_conversions,
        convert_enabled=convert_enabled,
        convert_to_markdown_enabled=convert_to_markdown_enabled,
        convert_to_html_enabled=convert_to_html_enabled,
        convert_to_docx_enabled=convert_to_docx_enabled,
        convert_to_epub_enabled=convert_to_epub_enabled,
        convert_to_pdf_enabled=convert_to_pdf_enabled,
        convert_to_pipeline_enabled=convert_to_pipeline_enabled,
        export_html_enabled=bool(all_flags.get("GLOW_ENABLE_EXPORT_HTML", True)),
        # Extension sets for JS-driven UI filtering
        chain_via_markdown_exts=sorted(_CHAIN_VIA_MARKDOWN),
        pandoc_native_exts=sorted(PANDOC_INPUT_EXTENSIONS),
        pandoc_effective_exts=sorted(_PANDOC_EFFECTIVE_EXTENSIONS),
        markitdown_exts=sorted(CONVERTIBLE_EXTENSIONS),
        pipeline_exts=sorted(PIPELINE_INPUT_EXTENSIONS),
        **extra,
    )


@convert_bp.route("/", methods=["GET"])
def convert_form():
    ctx = _template_context()
    if not ctx["convert_enabled"]:
        abort(404)

    # Quick Start handoff: ?token=... pre-fills with already-uploaded file.
    from ..upload import get_temp_dir
    prefill_token = (request.args.get("token") or "").strip()
    prefill_filename = None
    if prefill_token:
        temp_dir = get_temp_dir(prefill_token)
        if temp_dir is not None:
            for f in sorted(temp_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in CONVERT_EXTENSIONS:
                    prefill_filename = f.name
                    break
        if prefill_filename is None:
            prefill_token = None

    return render_template(
        "convert_form.html",
        prefill_token=prefill_token or None,
        prefill_filename=prefill_filename,
        **ctx,
    )


@convert_bp.route("/", methods=["POST"])
def convert_submit():
    token = None
    ctx = _template_context()
    try:
        if not ctx["convert_enabled"]:
            abort(404)

        # Quick Start handoff: re-use a previously uploaded file when the
        # form posts a session token rather than a new upload.
        from ..upload import get_temp_dir
        saved_path = None
        prefill_token = (request.form.get("token") or "").strip()
        if prefill_token and request.form.get("prefill") == "1":
            temp_dir = get_temp_dir(prefill_token)
            if temp_dir is not None:
                for f in sorted(temp_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() in CONVERT_EXTENSIONS:
                        saved_path = f
                        break
            if saved_path is not None:
                token = prefill_token

        if saved_path is None:
            token, saved_path = validate_upload(
                request.files.get("document"),
                allowed_extensions=CONVERT_EXTENSIONS,
            )
        ext = saved_path.suffix.lower()
        direction = request.form.get("direction", "to-markdown")

        direction_flags = {
            "to-markdown": ctx["convert_to_markdown_enabled"],
            "to-html": ctx["convert_to_html_enabled"],
            "to-html-cms": ctx["export_html_enabled"],
            "to-docx": ctx["convert_to_docx_enabled"],
            "to-epub": ctx["convert_to_epub_enabled"],
            "to-pdf": ctx["convert_to_pdf_enabled"],
            "to-pipeline": ctx["convert_to_pipeline_enabled"],
        }
        if direction.startswith("pipeline-") and not ctx["convert_to_pipeline_enabled"]:
            raise UploadError("DAISY Pipeline conversion is disabled on this server.")
        if direction in direction_flags and not direction_flags[direction]:
            raise UploadError("That conversion direction is disabled on this server.")

        from ..tool_usage import record as _record_usage
        _record_usage("convert", detail=direction)

        temp_dir = get_temp_dir(token)

        if direction == "to-html":
            # Pandoc (or MarkItDown→Pandoc): document -> ACB HTML
            if not pandoc_available():
                raise UploadError(
                    "Pandoc is not installed on the server. "
                    "HTML conversion is unavailable."
                )
            if ext not in _PANDOC_EFFECTIVE_EXTENSIONS:
                raise UploadError(
                    f"File type '{ext}' cannot be converted to HTML. "
                    f"Supported: {', '.join(sorted(_PANDOC_EFFECTIVE_EXTENSIONS))}."
                )
            # Two-stage chain: MarkItDown -> Markdown -> Pandoc HTML
            pandoc_input = saved_path
            if ext in _CHAIN_VIA_MARKDOWN:
                md_intermediate = temp_dir / f"{saved_path.stem}-extracted.md"
                current_app.logger.info(
                    "CONVERT two_stage ext=%s stage1=markitdown->md", ext
                )
                pandoc_input, _ = convert_to_markdown(
                    saved_path, output_path=md_intermediate
                )
            html_output = temp_dir / f"{saved_path.stem}.html"

            # Read form options
            user_title = request.form.get("title", "").strip()
            title = user_title or saved_path.stem.replace("-", " ").replace("_", " ")
            acb_format = request.form.get("acb_format") == "on"
            binding_margin = request.form.get("binding_margin") == "on"
            print_ready = request.form.get("print_ready") == "on"

            # Build CSS path: None means use built-in ACB CSS,
            # pass a blank sentinel to skip ACB CSS when unchecked
            css_path = None  # default: built-in ACB CSS
            if not acb_format:
                css_path = _NO_ACB_CSS_SENTINEL

            output_path, text = convert_to_html(
                pandoc_input,
                output_path=html_output,
                title=title,
                css_path=css_path,
            )

            # Post-process: inject binding margin and/or strip print stylesheet
            if acb_format and (binding_margin or not print_ready):
                html_text = output_path.read_text(encoding="utf-8")
                if binding_margin:
                    html_text = html_text.replace(
                        "padding: 1rem 1rem;",
                        "padding: 1rem 1rem 1rem 1.5rem;",
                        1,
                    )
                if not print_ready:
                    # Remove the @media print block from embedded CSS
                    import re

                    html_text = re.sub(
                        r"@media\s+print\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}",
                        "",
                        html_text,
                    )
                output_path.write_text(html_text, encoding="utf-8")

            # Preserve the temp dir for the result page download/preview routes.
            result_token = token
            token = None
            return _convert_result_response(
                result_token,
                download_name=f"{saved_path.stem}.html",
                preview_type="html",
                original_stem=saved_path.stem,
            )
        elif direction == "to-docx":
            if not pandoc_available():
                raise UploadError(
                    "Pandoc is not installed on the server. "
                    "Word conversion is unavailable."
                )
            if ext not in _PANDOC_EFFECTIVE_EXTENSIONS:
                raise UploadError(
                    f"File type '{ext}' cannot be converted to Word. "
                    f"Supported: {', '.join(sorted(_PANDOC_EFFECTIVE_EXTENSIONS))}."
                )
            if ext == ".docx":
                raise UploadError(
                    "The input file is already a Word document (.docx). "
                    "Choose a different input format."
                )
            # Two-stage chain: MarkItDown -> Markdown -> Pandoc .docx
            pandoc_input = saved_path
            if ext in _CHAIN_VIA_MARKDOWN:
                md_intermediate = temp_dir / f"{saved_path.stem}-extracted.md"
                current_app.logger.info(
                    "CONVERT two_stage ext=%s stage1=markitdown->md", ext
                )
                pandoc_input, _ = convert_to_markdown(
                    saved_path, output_path=md_intermediate
                )
            docx_output = temp_dir / f"{saved_path.stem}.docx"
            user_title = request.form.get("title", "").strip()
            title = user_title or saved_path.stem.replace("-", " ").replace("_", " ")
            output_path, _ = convert_to_docx(
                pandoc_input,
                output_path=docx_output,
                title=title,
            )
            result_token = token
            token = None
            return _convert_result_response(
                result_token,
                download_name=output_path.name,
                preview_type="binary",
                original_stem=saved_path.stem,
            )
        elif direction == "to-epub":
            # Pandoc (or MarkItDown->Pandoc): document -> EPUB 3
            if not pandoc_available():
                raise UploadError(
                    "Pandoc is not installed on the server. "
                    "EPUB conversion is unavailable."
                )
            if ext not in _PANDOC_EFFECTIVE_EXTENSIONS:
                raise UploadError(
                    f"File type '{ext}' cannot be converted to EPUB. "
                    f"Supported: {', '.join(sorted(_PANDOC_EFFECTIVE_EXTENSIONS))}."
                )
            if ext == ".epub":
                raise UploadError(
                    "The input file is already an EPUB. "
                    "Choose a different input format."
                )
            # Two-stage chain: MarkItDown -> Markdown -> Pandoc EPUB
            pandoc_input = saved_path
            if ext in _CHAIN_VIA_MARKDOWN:
                md_intermediate = temp_dir / f"{saved_path.stem}-extracted.md"
                current_app.logger.info(
                    "CONVERT two_stage ext=%s stage1=markitdown->md", ext
                )
                pandoc_input, _ = convert_to_markdown(
                    saved_path, output_path=md_intermediate
                )
            epub_output = temp_dir / f"{saved_path.stem}.epub"
            user_title = request.form.get("title", "").strip()
            title = user_title or saved_path.stem.replace("-", " ").replace("_", " ")
            acb_format = request.form.get("acb_format") == "on"
            css_path = None
            if not acb_format:
                css_path = _NO_ACB_CSS_SENTINEL
            output_path, _ = convert_to_epub(
                pandoc_input,
                output_path=epub_output,
                title=title,
                css_path=css_path,
            )
            result_token = token
            token = None
            return _convert_result_response(
                result_token,
                download_name=output_path.name,
                preview_type="binary",
                original_stem=saved_path.stem,
            )
        elif direction == "to-pdf":
            # Pandoc + WeasyPrint (or MarkItDown->Pandoc+WeasyPrint): document -> PDF
            if not pandoc_available():
                raise UploadError(
                    "Pandoc is not installed on the server. "
                    "PDF conversion is unavailable."
                )
            if not weasyprint_available():
                raise UploadError(
                    "WeasyPrint is not installed on the server. "
                    "PDF conversion is unavailable."
                )
            if ext not in _PANDOC_EFFECTIVE_EXTENSIONS:
                raise UploadError(
                    f"File type '{ext}' cannot be converted to PDF. "
                    f"Supported: {', '.join(sorted(_PANDOC_EFFECTIVE_EXTENSIONS))}."
                )
            # Two-stage chain: MarkItDown -> Markdown -> Pandoc PDF
            pandoc_input = saved_path
            if ext in _CHAIN_VIA_MARKDOWN:
                md_intermediate = temp_dir / f"{saved_path.stem}-extracted.md"
                current_app.logger.info(
                    "CONVERT two_stage ext=%s stage1=markitdown->md", ext
                )
                pandoc_input, _ = convert_to_markdown(
                    saved_path, output_path=md_intermediate
                )
            pdf_output = temp_dir / f"{saved_path.stem}.pdf"
            user_title = request.form.get("title", "").strip()
            title = user_title or saved_path.stem.replace("-", " ").replace("_", " ")
            acb_format = request.form.get("acb_format") == "on"
            binding_margin = request.form.get("binding_margin") == "on"
            css_path = None
            if not acb_format:
                css_path = _NO_ACB_CSS_SENTINEL
            output_path, _ = convert_to_pdf(
                pandoc_input,
                output_path=pdf_output,
                title=title,
                css_path=css_path,
                binding_margin=binding_margin,
            )
            result_token = token
            token = None
            return _convert_result_response(
                result_token,
                download_name=output_path.name,
                preview_type="binary",
                original_stem=saved_path.stem,
            )
        elif direction == "to-html-cms":
            # Exporter: .docx -> ACB-styled HTML CMS fragment for WordPress/Drupal
            if not ctx["export_html_enabled"]:
                raise UploadError("CMS Fragment export is disabled on this server.")
            if ext != ".docx":
                raise UploadError(
                    "CMS Fragment export only accepts Word (.docx) files. "
                    f"Received '{ext}'."
                )
            user_title = request.form.get("title", "").strip()
            title = user_title or None
            cms_output = temp_dir / f"{saved_path.stem}-cms.html"
            export_cms_fragment(saved_path, cms_output, title=title)
            cms_content = cms_output.read_text(encoding="utf-8")
            # Preserve the temp dir for the result page download route.
            result_token = token
            token = None
            return _convert_result_response(
                result_token,
                download_name=f"{saved_path.stem}-cms.html",
                preview_type="cms",
                original_stem=saved_path.stem,
                cms_content=cms_content,
            )
        elif direction == "to-pipeline" or direction.startswith("pipeline-"):
            # DAISY Pipeline conversion
            if direction == "to-pipeline":
                conversion_key = request.form.get("pipeline_conversion", "")
            else:
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
                saved_path,
                conversion_key,
                output_dir=temp_dir,
            )
            if output_path.is_file():
                mimetype = (
                    "application/epub+zip"
                    if output_path.suffix == ".epub"
                    else "application/octet-stream"
                )
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
                _shutil.make_archive(
                    str(zip_path.with_suffix("")), "zip", str(output_path)
                )
                return send_file(
                    str(zip_path),
                    mimetype="application/zip",
                    as_attachment=True,
                    download_name=zip_path.name,
                )
        else:
            # MarkItDown: document -> Markdown (default / to-markdown direction)
            if ext not in CONVERTIBLE_EXTENSIONS:
                raise UploadError(
                    f"File type '{ext}' cannot be converted to Markdown. "
                    f"Supported: {', '.join(sorted(CONVERTIBLE_EXTENSIONS))}. "
                    "To transcribe audio, use BITS Whisperer."
                )
            md_output = temp_dir / f"{saved_path.stem}.md"
            output_path, _ = convert_to_markdown(
                saved_path,
                output_path=md_output,
            )
            result_token = token
            token = None
            return _convert_result_response(
                result_token,
                download_name=output_path.name,
                preview_type="binary",
                original_stem=saved_path.stem,
            )

    except UploadError as exc:
        return (
            render_template(
                "convert_form.html",
                error=str(exc),
                **ctx,
            ),
            400,
        )
    except RuntimeError as exc:
        return (
            render_template(
                "convert_form.html",
                error=str(exc),
                **ctx,
            ),
            500,
        )
    except Exception as exc:
        current_app.logger.exception("CONVERT_SUBMIT unexpected_error")
        return (
            render_template(
                "convert_form.html",
                error=str(exc) or "An error occurred while converting the document. Please try again.",
                **ctx,
            ),
            500,
        )
    finally:
        if token:
            cleanup_token(token)
