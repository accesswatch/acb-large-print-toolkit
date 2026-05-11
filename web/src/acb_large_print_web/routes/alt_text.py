"""AI-assisted alt-text helper for images and visual-rich documents."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for

from ..ai_features import AIFeatureDisabled, require_ai_feature
from ..ai_gateway import chat as gateway_chat
from ..ai_gateway import describe_image, make_session_hash
from ..app import limiter
from ..gating import GatingError, RETRY_AFTER_SECONDS, ai_gate, vision_gate
from ..upload import ALT_TEXT_SOURCE_EXTENSIONS, UploadError, get_temp_dir, validate_upload
from ..user_ai import build_alt_text_prompt, get_user_ai_provider_and_model_for
from ..visual_items import extract_visual_items

alt_text_bp = Blueprint("alt_text", __name__)


def _busy_json(operation: str):
    return (
        jsonify(
            {
                "error": f"{operation} is busy right now. Please retry shortly.",
                "retry_seconds": RETRY_AFTER_SECONDS,
            }
        ),
        503,
        {"Retry-After": str(RETRY_AFTER_SECONDS)},
    )


def _find_source_path(token: str) -> Path:
    temp_dir = get_temp_dir(token)
    if temp_dir is None:
        raise UploadError("Your upload session expired. Upload the file again to continue.")

    candidates = [
        item
        for item in sorted(temp_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if item.is_file() and item.suffix.lower() in ALT_TEXT_SOURCE_EXTENSIONS
    ]
    if not candidates:
        raise UploadError(
            "No supported visual source was found in this session. Upload an image, Word, Excel, PowerPoint, PDF, or EPUB file."
        )
    return candidates[0]


def _sanitize_suggestion(text: str) -> str:
    suggestion = str(text or "").strip()
    for prefix in ("alt text:", "suggested alt text:", "description:"):
        if suggestion.lower().startswith(prefix):
            suggestion = suggestion[len(prefix):].strip()
    if suggestion.startswith('"') and suggestion.endswith('"') and len(suggestion) > 1:
        suggestion = suggestion[1:-1].strip()
    return suggestion


def _template_items(items: list[dict]) -> list[dict]:
    rendered: list[dict] = []
    for item in items:
        rendered.append(
            {
                "index": item.get("index"),
                "total_items": item.get("total_items"),
                "label": item.get("label"),
                "location": item.get("location"),
                "source_type": item.get("source_type"),
                "preview_data_uri": item.get("preview_data_uri"),
                "mime_type": item.get("mime_type"),
                "width": item.get("width"),
                "height": item.get("height"),
                "current_alt_text": item.get("current_alt_text"),
                "context_lines": list(item.get("context_lines") or []),
                "text_only": bool(item.get("text_only")),
            }
        )
    return rendered


def _render_page(*, token: str = "", error: str = ""):
    source_name = ""
    items: list[dict] = []
    selected_provider, selected_model = get_user_ai_provider_and_model_for("alt_text")
    if token:
        source_path = _find_source_path(token)
        source_name = source_path.name
        items = _template_items(extract_visual_items(source_path))
    return render_template(
        "alt_text_helper.html",
        error=error,
        token=token,
        source_name=source_name,
        visual_items=items,
        supported_exts=sorted(ALT_TEXT_SOURCE_EXTENSIONS),
        ai_alt_text_provider=selected_provider or "",
        ai_alt_text_model=selected_model or "",
    )


@alt_text_bp.route("/", methods=["GET", "POST"])
def alt_text_form():
    try:
        require_ai_feature("alt_text")
    except AIFeatureDisabled:
        abort(404)

    token = (request.values.get("token") or "").strip()

    if request.method == "POST" and request.files.get("document"):
        try:
            new_token, _saved_path = validate_upload(
                request.files.get("document"),
                allowed_extensions=ALT_TEXT_SOURCE_EXTENSIONS,
            )
            return redirect(url_for("alt_text.alt_text_form", token=new_token))
        except UploadError as exc:
            return _render_page(error=str(exc)), 400

    try:
        return _render_page(token=token)
    except UploadError as exc:
        return _render_page(error=str(exc)), 400


@alt_text_bp.route("/suggest", methods=["POST"])
@limiter.limit("20 per minute")
def alt_text_suggest():
    try:
        require_ai_feature("alt_text")
    except AIFeatureDisabled:
        abort(404)

    token = (request.form.get("token") or "").strip()
    extra_instruction = (request.form.get("extra_instruction") or "").strip()
    try:
        item_index = int(request.form.get("item_index") or "0")
    except ValueError:
        return jsonify({"error": "Invalid visual item selection."}), 400

    if not token:
        return jsonify({"error": "Session token required."}), 400

    try:
        source_path = _find_source_path(token)
        items = extract_visual_items(source_path)
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 410

    if not items:
        return jsonify({"error": "No visual items could be extracted from this file."}), 404
    if item_index < 0 or item_index >= len(items):
        return jsonify({"error": "Requested visual item is out of range."}), 400

    item = items[item_index]
    prompt = build_alt_text_prompt(
        document_name=source_path.name,
        image_index=item_index,
        total_images=len(items),
        current_alt_text=str(item.get("current_alt_text") or ""),
        surrounding_text=list(item.get("context_lines") or []),
        extra_instruction=extra_instruction,
    )

    sess_id = session.get("_id", "")
    sess_hash = make_session_hash(sess_id) if sess_id else "anonymous"

    try:
        if item.get("text_only"):
            with ai_gate(wait_seconds=30):
                suggestion, _ = gateway_chat(
                    question=prompt,
                    system_prompt=(
                        "You draft WCAG 2.2 AA-conformant alternative text. "
                        "Return only the alt text string requested by the user."
                    ),
                    session_hash=sess_hash,
                    feature="alt_text",
                )
        else:
            with vision_gate(wait_seconds=20):
                suggestion = describe_image(
                    image_bytes=bytes(item.get("image_bytes") or b""),
                    mime_type=str(item.get("mime_type") or "image/png"),
                    prompt=prompt,
                    session_hash=sess_hash,
                )
    except GatingError:
        return _busy_json("Vision processing")
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    cleaned = _sanitize_suggestion(suggestion)
    return jsonify(
        {
            "ok": True,
            "suggestion": cleaned,
            "item_index": item_index,
            "label": item.get("label"),
            "source_type": item.get("source_type"),
        }
    )
