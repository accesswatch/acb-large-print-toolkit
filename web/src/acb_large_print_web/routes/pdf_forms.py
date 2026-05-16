"""PDF forms beta routes (v1 slice 1: inspect + classify + extract)."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, render_template, request

from acb_large_print.pdf_forms import inspect_pdf_form

from ..feature_flags import get_flag
from ..upload import UploadError, cleanup_token, validate_upload

pdf_forms_bp = Blueprint("pdf_forms", __name__)


def _beta_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_PDF_FORM_ROUNDTRIP_BETA", False))


@pdf_forms_bp.route("/", methods=["GET"])
def pdf_forms_home():
    """Render the PDF forms inspection page."""
    if not _beta_enabled():
        abort(404)
    return render_template("pdf_forms_form.html")


@pdf_forms_bp.route("/inspect", methods=["POST"])
def pdf_forms_inspect():
    """Inspect uploaded PDF and render classification + extracted fields."""
    if not _beta_enabled():
        abort(404)

    uploaded = request.files.get("document") or request.files.get("file")
    try:
        token, path = validate_upload(uploaded, allowed_extensions={".pdf"})
    except UploadError as exc:
        return render_template("pdf_forms_form.html", error=str(exc)), 200

    try:
        inspection = inspect_pdf_form(path)
    finally:
        cleanup_token(token)

    return render_template(
        "pdf_forms_form.html",
        inspection=inspection,
        source_filename=path.name,
    )


@pdf_forms_bp.route("/api/inspect", methods=["POST"])
def api_pdf_forms_inspect():
    """JSON inspection endpoint for PDF forms."""
    if not _beta_enabled():
        abort(404)

    uploaded = request.files.get("document") or request.files.get("file")
    try:
        token, path = validate_upload(uploaded, allowed_extensions={".pdf"})
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        inspection = inspect_pdf_form(path)
    finally:
        cleanup_token(token)

    return jsonify(inspection)

