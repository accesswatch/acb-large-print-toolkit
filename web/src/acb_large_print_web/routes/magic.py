from __future__ import annotations

from pathlib import Path

from flask import Blueprint, Response, abort, jsonify, render_template, request

from ..feature_flags import get_all_flags
from ..magic_features import (
    analyze_tables,
    apply_pronunciation_dictionary,
    compare_documents,
    delete_pronunciation,
    detect_reading_order_pdf,
    import_pronunciations_csv,
    list_pronunciations,
    list_rule_proposals,
    ocr_pdf,
    pronunciations_to_csv,
    submit_rule_proposal,
    upsert_pronunciation,
)
from ..upload import UploadError, cleanup_token, validate_upload

magic_bp = Blueprint("magic", __name__)

_COMPARE_ALLOWED_EXTENSIONS = {
    ".docx",
    ".xlsx",
    ".pptx",
    ".md",
    ".pdf",
    ".epub",
    ".txt",
    ".html",
    ".htm",
    ".csv",
    ".json",
    ".xml",
    ".rst",
    ".odt",
    ".rtf",
}


def _enabled(flag: str) -> bool:
    return bool(get_all_flags().get(flag, True))


def _require(flag: str) -> None:
    if not _enabled(flag):
        abort(404)


@magic_bp.route("/", methods=["GET"])
def magic_home():
    flags = get_all_flags()
    proposals = []
    if flags.get("GLOW_ENABLE_RULE_CONTRIBUTIONS", True):
        proposals = list_rule_proposals(limit=20)
    return render_template(
        "magic_lab.html",
        flags=flags,
        proposals=proposals,
        pronunciations=list_pronunciations() if flags.get("GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY", True) else [],
    )


@magic_bp.route("/table-advisor", methods=["POST"])
def table_advisor():
    _require("GLOW_ENABLE_TABLE_ADVISOR")
    text = (request.form.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Provide HTML or Markdown table text."}), 400
    return jsonify(analyze_tables(text))


@magic_bp.route("/reading-order", methods=["POST"])
def reading_order():
    _require("GLOW_ENABLE_READING_ORDER_DETECTION")
    token = None
    try:
        token, saved = validate_upload(request.files.get("document"), allowed_extensions={".pdf"})
        result = detect_reading_order_pdf(Path(saved))
        return jsonify(result)
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    finally:
        if token:
            cleanup_token(token)


@magic_bp.route("/ocr", methods=["POST"])
def ocr_route():
    _require("GLOW_ENABLE_PDF_OCR")
    token = None
    try:
        token, saved = validate_upload(request.files.get("document"), allowed_extensions={".pdf"})
        result = ocr_pdf(Path(saved))
        return jsonify(result)
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    finally:
        if token:
            cleanup_token(token)


@magic_bp.route("/compare", methods=["POST"])
def compare_route():
    _require("GLOW_ENABLE_DOCUMENT_COMPARE")
    token_a = token_b = None
    try:
        token_a, path_a = validate_upload(
            request.files.get("document_a"), allowed_extensions=_COMPARE_ALLOWED_EXTENSIONS
        )
        token_b, path_b = validate_upload(
            request.files.get("document_b"), allowed_extensions=_COMPARE_ALLOWED_EXTENSIONS
        )
        result = compare_documents(Path(path_a), Path(path_b))
        return jsonify(result)
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    finally:
        if token_a:
            cleanup_token(token_a)
        if token_b:
            cleanup_token(token_b)


@magic_bp.route("/pronunciation", methods=["POST"])
def pronunciation_upsert():
    _require("GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY")
    term = (request.form.get("term") or "").strip()
    replacement = (request.form.get("replacement") or "").strip()
    notes = (request.form.get("notes") or "").strip()
    if not term or not replacement:
        return jsonify({"error": "term and replacement are required"}), 400
    upsert_pronunciation(term, replacement, notes)
    return jsonify({"ok": True})


@magic_bp.route("/pronunciation/delete", methods=["POST"])
def pronunciation_delete():
    _require("GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY")
    term = (request.form.get("term") or "").strip()
    if not term:
        return jsonify({"error": "term is required"}), 400
    delete_pronunciation(term)
    return jsonify({"ok": True})


@magic_bp.route("/pronunciation/import", methods=["POST"])
def pronunciation_import():
    _require("GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY")
    text = (request.form.get("csv") or "")
    imported = import_pronunciations_csv(text)
    return jsonify({"ok": True, "imported": imported})


@magic_bp.route("/pronunciation/export.csv", methods=["GET"])
def pronunciation_export():
    _require("GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY")
    csv_text = pronunciations_to_csv()
    return Response(
        csv_text,
        headers={
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": 'attachment; filename="pronunciation-dictionary.csv"',
        },
    )


@magic_bp.route("/pronunciation/preview", methods=["POST"])
def pronunciation_preview():
    _require("GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY")
    text = (request.form.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    return jsonify({"ok": True, "text": apply_pronunciation_dictionary(text)})


@magic_bp.route("/rules/propose", methods=["POST"])
def rules_propose():
    _require("GLOW_ENABLE_RULE_CONTRIBUTIONS")
    title = (request.form.get("title") or "").strip()
    rationale = (request.form.get("rationale") or "").strip()
    severity = (request.form.get("severity") or "medium").strip().lower()
    rule_id = (request.form.get("suggested_rule_id") or "").strip()
    submitted_by = (request.form.get("submitted_by") or "").strip()
    try:
        proposal_id = submit_rule_proposal(
            title=title,
            rationale=rationale,
            severity=severity,
            suggested_rule_id=rule_id,
            submitted_by=submitted_by,
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True, "proposal_id": proposal_id})


@magic_bp.route("/rules/proposals", methods=["GET"])
def rules_proposals():
    _require("GLOW_ENABLE_RULE_CONTRIBUTIONS")
    return jsonify({"ok": True, "proposals": list_rule_proposals(limit=200)})
