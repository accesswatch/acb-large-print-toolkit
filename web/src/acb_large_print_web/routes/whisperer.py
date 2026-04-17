"""BITS Whisperer route -- on-server audio transcription to Markdown or Word.

BITS Whisperer uses faster-whisper (Whisper medium model, CTranslate2 int8)
running entirely on the GLOW server.  Audio is never sent to any external
service or cloud API.

Outputs:
  - Markdown (.md) -- plain ACB-compliant transcript ready to edit or convert
  - Word (.docx) -- Markdown transcript passed through Pandoc for an editable
    Word document (requires Pandoc to be installed)

Route:
  GET  /whisperer           -- upload form
  POST /whisperer           -- process audio, return file download
"""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, make_response, render_template, request, send_file, url_for

from acb_large_print.converter import (
    AUDIO_EXTENSIONS,
    whisper_available,
    whisper_convert,
)
from acb_large_print.pandoc_converter import convert_to_docx, pandoc_available

from ..gating import RETRY_AFTER_SECONDS, GatingError, audio_gate
from ..upload import UploadError, cleanup_token, get_temp_dir, validate_upload

whisperer_bp = Blueprint("whisperer", __name__)

# Accept string for the file input
_AUDIO_ACCEPT = ",".join(sorted(AUDIO_EXTENSIONS))

# Language choices shown in the form (BCP-47 code -> display label)
# Sorted by global speaker population for quick scanning
_LANGUAGE_CHOICES: list[tuple[str, str]] = [
    ("", "Auto-detect (recommended)"),
    ("en", "English"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("nl", "Dutch"),
    ("pl", "Polish"),
    ("ru", "Russian"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("zh", "Chinese (Mandarin)"),
    ("ar", "Arabic"),
    ("hi", "Hindi"),
    ("tr", "Turkish"),
    ("sv", "Swedish"),
    ("da", "Danish"),
    ("no", "Norwegian"),
    ("fi", "Finnish"),
]


def _template_context(**extra):
    return dict(
        audio_accept=_AUDIO_ACCEPT,
        whisper_installed=whisper_available(),
        pandoc_installed=pandoc_available(),
        language_choices=_LANGUAGE_CHOICES,
        **extra,
    )


def _busy_response():
    resp = make_response(
        render_template(
            "busy.html",
            operation="BITS Whisperer transcription",
            retry_seconds=RETRY_AFTER_SECONDS,
            back_url=url_for("whisperer.whisperer_form"),
        ),
        503,
    )
    resp.headers["Retry-After"] = str(RETRY_AFTER_SECONDS)
    return resp


@whisperer_bp.route("/", methods=["GET"])
def whisperer_form():
    return render_template("whisperer_form.html", **_template_context())


@whisperer_bp.route("/", methods=["POST"])
def whisperer_submit():
    token = None
    try:
        token, saved_path = validate_upload(
            request.files.get("audio"),
            allowed_extensions=AUDIO_EXTENSIONS,
        )
        ext = saved_path.suffix.lower()

        if not whisper_available():
            raise UploadError(
                "BITS Whisperer (faster-whisper) is not installed on this server. "
                "Audio transcription is unavailable."
            )

        if ext not in AUDIO_EXTENSIONS:
            raise UploadError(
                f"'{ext}' is not a supported audio format. "
                f"Supported: {', '.join(sorted(AUDIO_EXTENSIONS))}."
            )

        temp_dir = get_temp_dir(token)
        language = request.form.get("language") or None
        output_format = request.form.get("output_format", "markdown")

        md_output = temp_dir / f"{saved_path.stem}.md"

        try:
            with audio_gate():
                transcript_path, _ = whisper_convert(
                    saved_path,
                    output_path=md_output,
                    language=language,
                )
        except GatingError:
            return _busy_response()

        if output_format == "word":
            if not pandoc_available():
                raise UploadError(
                    "Pandoc is not installed on this server. "
                    "Audio-to-Word conversion requires Pandoc for the final step. "
                    "Choose Markdown output instead."
                )
            user_title = request.form.get("title", "").strip()
            title = user_title or saved_path.stem.replace("-", " ").replace("_", " ")
            docx_output = temp_dir / f"{saved_path.stem}.docx"
            output_path, _ = convert_to_docx(
                transcript_path,
                output_path=docx_output,
                title=title,
            )
            return send_file(
                str(output_path),
                mimetype=(
                    "application/vnd.openxmlformats-officedocument"
                    ".wordprocessingml.document"
                ),
                as_attachment=True,
                download_name=f"{saved_path.stem}.docx",
            )
        else:
            # Markdown (default)
            return send_file(
                str(transcript_path),
                mimetype="text/markdown; charset=utf-8",
                as_attachment=True,
                download_name=f"{saved_path.stem}.md",
            )

    except UploadError as exc:
        return (
            render_template(
                "whisperer_form.html",
                error=str(exc),
                **_template_context(),
            ),
            400,
        )
    except RuntimeError as exc:
        return (
            render_template(
                "whisperer_form.html",
                error=str(exc),
                **_template_context(),
            ),
            500,
        )
    finally:
        if token:
            cleanup_token(token)
