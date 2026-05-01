"""Braille Studio route -- text-to-braille and braille-to-text translation.

Conforms to BANA (Braille Authority of North America) standards via liblouis:
  - UEB Grade 1/2 (current BANA literary standard, adopted 2016)
  - BANA Computer Braille Code (8-dot)
  - Legacy EBAE Grade 1/2 (pre-2016, interoperability only)
  - BRF output wrapped at the BANA-standard 40 cells per line

Routes:
    GET  /braille/         -- Braille Studio form
    POST /braille/         -- Run text-to-braille or braille-to-text
    GET  /braille/download -- Download last translation result as a file
"""

from __future__ import annotations

from flask import (
    Blueprint,
    Response,
    current_app,
    render_template,
    request,
    session,
)

from acb_large_print.braille_converter import (
    DEFAULT_GRADE,
    GRADES,
    OUTPUT_FORMATS,
    BrailleError,
    braille_available,
    braille_to_text,
    get_unavailability_reason,
    louis_version,
    text_to_braille,
)

from ..app import limiter
from ..upload import UploadError, cleanup_token, validate_upload

braille_bp = Blueprint("braille", __name__)

_TEXT_MAX_LEN = 50_000
_FILE_MAX_BYTES = 512 * 1024  # 512 KiB -- generous for text/BRF files
_ALLOWED_EXTENSIONS = {".txt", ".brf", ".brl", ".md"}
_ACCEPT_STR = ",".join(sorted(_ALLOWED_EXTENSIONS))

# Session keys
_SK_RESULT = "braille_result"
_SK_DIRECTION = "braille_direction"
_SK_GRADE = "braille_grade"
_SK_FORMAT = "braille_output_format"
_SK_FILENAME = "braille_filename"

_EMPTY_FORM: dict = {}


def _render(
    lib_available: bool,
    *,
    result: str | None = None,
    error: str | None = None,
    form_values: dict | None = None,
    filename: str | None = None,
) -> str:
    return render_template(
        "braille_form.html",
        available=lib_available,
        unavailability_reason=get_unavailability_reason() if not lib_available else "",
        grades=GRADES,
        output_formats=OUTPUT_FORMATS,
        default_grade=DEFAULT_GRADE,
        louis_version=louis_version(),
        result=result,
        error=error,
        form_values=form_values or _EMPTY_FORM,
        filename=filename,
    )


@braille_bp.route("/", methods=["GET", "POST"])
@limiter.limit("30 per minute")
def braille_form():
    """Braille Studio -- BANA-compliant text ↔ braille translation."""

    # Feature-gate: GLOW_ENABLE_BRAILLE
    try:
        from .. import feature_flags as _ff
        _flags = _ff.get_all_flags()
        if not _flags.get("GLOW_ENABLE_BRAILLE", True):
            return _render(
                False,
                error="Braille Studio is currently disabled by the site administrator.",
            )
    except Exception:
        _flags = {}

    lib_available = braille_available()

    if request.method == "GET":
        session.pop(_SK_RESULT, None)
        session.pop(_SK_FILENAME, None)
        return _render(lib_available)

    # ---- POST ----
    direction = request.form.get("direction", "text-to-braille").strip()
    grade = request.form.get("grade", DEFAULT_GRADE).strip()
    output_format = request.form.get("output_format", "unicode").strip()
    input_text = request.form.get("input_text", "").strip()

    # Sanitise selects to known-good values
    if direction not in ("text-to-braille", "braille-to-text"):
        direction = "text-to-braille"
    if grade not in GRADES:
        grade = DEFAULT_GRADE
    if output_format not in OUTPUT_FORMATS:
        output_format = "unicode"

    form_values = {
        "direction": direction,
        "grade": grade,
        "output_format": output_format,
        "input_text": input_text,
    }

    error: str | None = None
    result: str | None = None
    filename: str | None = None

    # Prefer file upload over textarea
    uploaded_file = request.files.get("input_file")
    upload_token: str | None = None
    if uploaded_file and uploaded_file.filename:
        try:
            token, saved_path = validate_upload(
                uploaded_file, allowed_extensions=_ALLOWED_EXTENSIONS
            )
            upload_token = token
            raw = saved_path.read_bytes()
            if len(raw) > _FILE_MAX_BYTES:
                raise UploadError(
                    f"File too large ({len(raw):,} bytes). "
                    f"Maximum is {_FILE_MAX_BYTES:,} bytes."
                )
            input_text = raw.decode("utf-8", errors="replace").strip()
            form_values["input_text"] = input_text
        except UploadError as exc:
            error = str(exc)
        except Exception as exc:
            error = f"Could not read uploaded file: {exc}"
        finally:
            if upload_token:
                cleanup_token(upload_token)

    # Feature-gate: GLOW_ENABLE_CONVERT_TO_BRAILLE
    if not error and not _flags.get("GLOW_ENABLE_CONVERT_TO_BRAILLE", True):
        error = "Braille translation is currently disabled by the site administrator."

    if not error and not input_text:
        error = "Please enter text in the input box or upload a file."

    if not error and len(input_text) > _TEXT_MAX_LEN:
        error = (
            f"Input is too long ({len(input_text):,} characters). "
            f"Maximum is {_TEXT_MAX_LEN:,} characters per request."
        )

    if not error and not lib_available:
        error = (
            "Braille translation is not available on this server. "
            + get_unavailability_reason()
        )

    if not error:
        try:
            if direction == "text-to-braille":
                result = text_to_braille(
                    input_text,
                    grade=grade,
                    output_format=output_format,  # type: ignore[arg-type]
                )
                filename = "braille_output.brf" if output_format == "brf" else "braille_output.brl"
            else:
                result = braille_to_text(input_text, grade=grade)
                filename = "back_translation.txt"
        except BrailleError as exc:
            error = str(exc)
        except Exception:
            current_app.logger.exception("Unexpected braille translation error")
            error = "An unexpected error occurred during translation."

    # Persist result for the download endpoint
    if result is not None:
        session[_SK_RESULT] = result
        session[_SK_DIRECTION] = direction
        session[_SK_GRADE] = grade
        session[_SK_FORMAT] = output_format
        session[_SK_FILENAME] = filename
    else:
        session.pop(_SK_RESULT, None)
        session.pop(_SK_FILENAME, None)

    return _render(
        lib_available,
        result=result,
        error=error,
        form_values=form_values,
        filename=filename,
    )


@braille_bp.route("/download")
@limiter.limit("30 per minute")
def braille_download():
    """Return the last braille translation result as a file download."""
    # Feature-gate: GLOW_ENABLE_EXPORT_BRAILLE
    try:
        from .. import feature_flags as _ff
        if not _ff.get_all_flags().get("GLOW_ENABLE_EXPORT_BRAILLE", True):
            return Response(
                "Braille export is currently disabled by the site administrator.",
                status=403,
                mimetype="text/plain",
            )
    except Exception:
        pass

    result = session.get(_SK_RESULT)
    filename = session.get(_SK_FILENAME, "braille_output.brl")
    output_format = session.get(_SK_FORMAT, "unicode")
    direction = session.get(_SK_DIRECTION, "text-to-braille")

    if not result:
        return Response(
            "No result to download. Please submit the form first.",
            status=400,
            mimetype="text/plain",
        )

    # BRF files are ASCII text; everything else is UTF-8.
    if direction == "text-to-braille" and output_format == "brf":
        content_type = "text/plain; charset=us-ascii"
    else:
        content_type = "text/plain; charset=utf-8"

    return Response(
        result,
        status=200,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": content_type,
        },
    )
