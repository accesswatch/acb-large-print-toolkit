"""Quick Start process route -- universal upload + action chooser.

Users upload any document, and we show them contextual actions based on file type.
A beginner-friendly alternative to the tabs for users unsure where to start.

Routes:
  GET  /process           -- upload form
  POST /process           -- validate, save, redirect to choose-action
  GET  /process/choose    -- show available actions for the uploaded file
"""

from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for

from ..ai_features import ai_chat_enabled, ai_whisperer_enabled
from ..feature_flags import get_all_flags
from ..upload import (
    AUDIO_EXTENSIONS,
    CONVERT_EXTENSIONS,
    ALLOWED_EXTENSIONS,
    UploadError,
    get_temp_dir,
    validate_upload,
)

process_bp = Blueprint("process", __name__)


def _all_processable_extensions() -> set[str]:
    """Return the currently allowed upload extensions for Quick Start."""
    allowed = set(CONVERT_EXTENSIONS)
    if ai_whisperer_enabled():
        allowed.update(AUDIO_EXTENSIONS)
    return allowed


def _get_available_actions(file_ext: str) -> dict[str, dict]:
    """Return available actions for a given file extension.
    
    Each action is a dict with:
      - "name": human-readable action name
      - "route": blueprint.function endpoint
      - "description": short explanation
      - "enabled": True if available for this file type
    """
    ext = file_ext.lower()
    chat_enabled = ai_chat_enabled()
    whisperer_enabled = ai_whisperer_enabled()
    all_flags = get_all_flags()

    convert_directions_enabled = any(
        bool(all_flags.get(k, True))
        for k in (
            "GLOW_ENABLE_CONVERT_TO_MARKDOWN",
            "GLOW_ENABLE_CONVERT_TO_HTML",
            "GLOW_ENABLE_CONVERT_TO_DOCX",
            "GLOW_ENABLE_CONVERT_TO_EPUB",
            "GLOW_ENABLE_CONVERT_TO_PDF",
            "GLOW_ENABLE_CONVERT_TO_PIPELINE",
        )
    )

    actions = {
        "audit": {
            "name": "Audit",
            "route": "audit.audit_form",
            "icon": "🔍",
            "description": "Check for accessibility compliance issues",
            "enabled": bool(all_flags.get("GLOW_ENABLE_AUDIT", True))
            and (
                ext in {".docx", ".xlsx", ".pptx", ".md", ".pdf", ".epub"}
                or ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
            ),
        },
        "fix": {
            "name": "Fix",
            "route": "fix.fix_form",
            "icon": "🔧",
            "description": "Auto-fix accessibility problems (Word only)",
            "enabled": bool(all_flags.get("GLOW_ENABLE_CHECKER", True)) and ext == ".docx",
        },
        "convert": {
            "name": "Convert",
            "route": "convert.convert_form",
            "icon": "📄",
            "description": "Convert to Markdown, accessible HTML, Word, EPUB, or PDF. PowerPoint, Excel, and PDF files use a smart two-stage extraction — GLOW handles it automatically.",
            "enabled": bool(all_flags.get("GLOW_ENABLE_CONVERTER", True))
            and convert_directions_enabled
            and ext in CONVERT_EXTENSIONS,
        },
        "chat": {
            "name": "Document Chat",
            "route": "chat.chat_form",
            "icon": "💬",
            "description": "Ask questions about this document with accessibility-focused AI assistance",
            "enabled": chat_enabled and ext in (CONVERT_EXTENSIONS | ALLOWED_EXTENSIONS),
        },
        "export": {
            "name": "Export",
            "route": "export.export_form",
            "icon": "📤",
            "description": "Convert Word document to accessible HTML with ACB styles",
            "enabled": bool(all_flags.get("GLOW_ENABLE_EXPORT_HTML", True)) and ext == ".docx",
        },
        "template": {
            "name": "Create Template",
            "route": "template.template_form",
            "icon": "📋",
            "description": "Generate a pre-formatted Word template (.dotx) with ACB styles",
            "enabled": bool(all_flags.get("GLOW_ENABLE_TEMPLATE_BUILDER", True)) and ext == ".docx",
        },
    }

    # Special handling for audio
    if ext in AUDIO_EXTENSIONS:
        actions = {
            "whisperer": {
                "name": "BITS Whisperer",
                "route": "whisperer.whisperer_form",
                "icon": "🎤",
                "description": "Transcribe to Markdown or Word document using secure cloud transcription",
                "enabled": whisperer_enabled,
            }
        }

    return actions


@process_bp.route("/", methods=["GET"])
def process_form():
    """Show the universal upload form."""
    return render_template("process_form.html")


@process_bp.route("/", methods=["POST"])
def process_submit():
    """Validate and save the uploaded file, redirect to action chooser."""
    try:
        # Validate and save
        token, saved_path = validate_upload(
            request.files.get("file"),
            allowed_extensions=_all_processable_extensions(),
        )
        # Redirect to action chooser
        return redirect(url_for("process.process_choose", token=token))

    except UploadError as exc:
        return (
            render_template(
                "process_form.html",
                error=str(exc),
            ),
            400,
        )
    except RuntimeError as exc:
        return (
            render_template(
                "process_form.html",
                error=str(exc),
            ),
            500,
        )


@process_bp.route("/choose", methods=["GET"])
def process_choose():
    """Show available actions based on the uploaded file type."""
    token = request.args.get("token")
    if not token:
        return redirect(url_for("process.process_form"))

    try:
        temp_dir = get_temp_dir(token)
        saved_files = list(temp_dir.glob("*"))
        if not saved_files:
            raise UploadError("Upload session expired or not found.")

        saved_path = saved_files[0]
        ext = saved_path.suffix.lower()
        filename = saved_path.name

        actions = _get_available_actions(ext)
        enabled_actions = [
            (key, info)
            for key, info in actions.items()
            if info["enabled"]
        ]

        if not enabled_actions:
            raise UploadError(
                f"No actions available for '{ext}' files. "
                "This file type is not supported."
            )

        return render_template(
            "process_choose.html",
            token=token,
            filename=filename,
            file_ext=ext,
            actions=enabled_actions,
        )

    except UploadError as exc:
        return (
            render_template(
                "process_form.html",
                error=str(exc),
            ),
            400,
        )
    finally:
        # Don't cleanup yet — the user will click an action that uses the token
        pass


@process_bp.route("/go/<action>", methods=["POST"])
def process_go(action: str):
    """Redirect to the chosen action with the upload token."""
    token = request.form.get("token")
    if not token:
        return redirect(url_for("process.process_form"))

    # Map action names to route endpoints
    action_routes = {
        "audit": "audit.audit_form",
        "fix": "fix.fix_form",
        "convert": "convert.convert_form",
        "export": "export.export_form",
        "template": "template.template_form",
        "chat": "chat.chat_form",
        "whisperer": "whisperer.whisperer_form",
    }

    route = action_routes.get(action)
    if not route:
        return redirect(url_for("process.process_form"))

    return redirect(url_for(route, token=token))
