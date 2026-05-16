"""Celery tasks for long-running document conversion jobs.

Job lifecycle
─────────────
  PENDING  → job created, Celery task dispatched
  STARTED  → worker picked up the task
  PROGRESS → worker emitting progress updates
  SUCCESS  → conversion complete; result_file set
  FAILURE  → unrecoverable error; error message set

Progress is written to ``instance/jobs/<job_id>/status.json`` on the
*filesystem* so that the SSE endpoint (running in the web process) can read
it without a Redis round-trip.  This works because the Celery worker mounts
the same ``feedback-data`` volume as the web container.

Result files are stored in ``instance/jobs/<job_id>/result.<ext>`` and served
by the ``/job/<id>/result`` route with a signed filename parameter.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from ..async_orchestration import deadline_exceeded, load_policy
from . import celery_app

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Job state helpers
# ---------------------------------------------------------------------------

_JOB_DIR_ENV = "GLOW_JOBS_DIR"  # Override instance/jobs with env var
_JOB_META_NAME = "job-meta.json"


def _jobs_root() -> Path:
    from flask import current_app
    base = os.environ.get(_JOB_DIR_ENV, "")
    if base:
        root = Path(base)
    else:
        root = Path(current_app.instance_path) / "jobs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_job_id(job_id: str) -> str:
    safe = "".join(c for c in job_id if c.isalnum() or c == "-")
    # Reject IDs that would be rewritten by sanitization.
    if not safe or safe != job_id:
        raise ValueError(f"Invalid job_id: {job_id!r}")
    return safe


def _job_dir(job_id: str, *, create: bool = True) -> Path:
    safe = _safe_job_id(job_id)
    d = _jobs_root() / safe
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def _status_path(job_id: str, *, create: bool = True) -> Path:
    return _job_dir(job_id, create=create) / "status.json"


def _meta_path(job_id: str, *, create: bool = True) -> Path:
    return _job_dir(job_id, create=create) / _JOB_META_NAME


def write_status(job_id: str, **fields) -> None:
    """Atomically update the job status file with *fields*."""
    path = _status_path(job_id)
    try:
        existing: dict = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text())
            except (ValueError, OSError):
                pass
        existing.update(fields)
        existing["updated_at"] = time.time()
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(existing))
        tmp.replace(path)
    except Exception:
        log.exception("write_status failed for job %s", job_id)


def read_status(job_id: str) -> dict:
    """Read the job status file.  Returns ``{"state": "MISSING"}`` if absent."""
    try:
        path = _status_path(job_id, create=False)
    except ValueError:
        return {"state": "MISSING"}
    if not path.exists():
        return {"state": "MISSING"}
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        return {"state": "ERROR", "error": "Status file unreadable"}


def write_job_meta(job_id: str, data: dict[str, Any]) -> None:
    path = _meta_path(job_id)
    payload = dict(data or {})
    payload["updated_at"] = time.time()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload))
    tmp.replace(path)


def read_job_meta(job_id: str) -> dict[str, Any]:
    try:
        path = _meta_path(job_id, create=False)
    except ValueError:
        return {}
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        return {}


def create_job(job_id: str, op: str, filename: str, *, meta: dict[str, Any] | None = None) -> None:
    """Initialise a job status file before dispatching the Celery task."""
    policy = load_policy("CONVERT")
    write_status(
        job_id,
        state="PENDING",
        op=op,
        filename=filename,
        progress=0,
        message="Queued…",
        result_file=None,
        error=None,
        attempt=0,
        max_attempts=policy.max_attempts,
        deadline_at=policy.deadline_at,
        cancel_requested=False,
        retryable=True,
        created_at=time.time(),
    )
    if meta:
        write_job_meta(job_id, meta)


class JobCancelled(RuntimeError):
    pass


class JobDeadlineExceeded(RuntimeError):
    pass


def _assert_job_active(job_id: str) -> None:
    status = read_status(job_id)
    if bool(status.get("cancel_requested")):
        raise JobCancelled("Cancellation requested.")
    if deadline_exceeded(status.get("deadline_at")):
        raise JobDeadlineExceeded("Job exceeded deadline.")


def request_cancel(job_id: str) -> dict[str, Any]:
    status = read_status(job_id)
    if status.get("state") == "MISSING":
        return {"ok": False, "reason": "missing"}
    state = str(status.get("state", ""))
    if state in {"SUCCESS", "FAILURE", "CANCELLED"}:
        return {"ok": False, "reason": "terminal"}
    write_status(
        job_id,
        cancel_requested=True,
        state="CANCELLING",
        message="Cancellation requested…",
    )
    return {"ok": True}


def can_retry(job_id: str) -> bool:
    status = read_status(job_id)
    state = str(status.get("state", ""))
    if state not in {"FAILURE", "CANCELLED"}:
        return False
    attempt = int(status.get("attempt", 0))
    max_attempts = int(status.get("max_attempts", 1))
    if attempt >= max_attempts:
        return False
    if deadline_exceeded(status.get("deadline_at")):
        return False
    return True


def retry_convert_job(job_id: str) -> bool:
    if not can_retry(job_id):
        return False
    meta = read_job_meta(job_id)
    if not meta:
        return False
    op = str(meta.get("op", ""))
    upload_token = str(meta.get("upload_token", ""))
    input_filename = str(meta.get("input_filename", ""))
    options = meta.get("options", {})
    if not op or not upload_token or not input_filename:
        return False
    write_status(
        job_id,
        state="PENDING",
        progress=0,
        message="Queued for retry…",
        cancel_requested=False,
        error=None,
    )
    run_convert_job.delay(job_id, op, upload_token, input_filename, options)
    return True


# ---------------------------------------------------------------------------
# Task: run_convert_job
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="glow.convert")  # type: ignore[misc]
def run_convert_job(
    self,
    job_id: str,
    op: str,
    upload_token: str,
    input_filename: str,
    options: dict[str, Any],
) -> dict[str, Any]:
    """Run a document conversion asynchronously.

    Parameters
    ----------
    job_id:
        UUID created by the web route; used to name the status/result files.
    op:
        Conversion operation: one of 'to_markdown', 'to_html', 'to_docx',
        'to_epub', 'to_pdf', 'to_odt', 'pipeline'.
    upload_token:
        Session upload token used to locate the source file.
    input_filename:
        Original filename (used to derive output name and detect extension).
    options:
        Op-specific options forwarded to the converter functions.
    """
    status = read_status(job_id)
    max_attempts = max(1, int(status.get("max_attempts", 1)))
    start_attempt = max(1, int(status.get("attempt", 0)) + 1)

    for attempt in range(start_attempt, max_attempts + 1):
        write_status(
            job_id,
            state="STARTED",
            progress=2,
            message="Starting conversion…",
            attempt=attempt,
            error=None,
            retryable=attempt < max_attempts,
        )
        try:
            _assert_job_active(job_id)
            result_path = _dispatch_conversion(job_id, op, upload_token, input_filename, options)
            result_name = Path(result_path).name
            write_status(
                job_id,
                state="SUCCESS",
                progress=100,
                message="Done.",
                result_file=result_name,
                retryable=False,
            )
            return {"state": "SUCCESS", "result_file": result_name}
        except JobCancelled as exc:
            write_status(
                job_id,
                state="CANCELLED",
                progress=0,
                error=str(exc),
                message="Conversion cancelled.",
                retryable=attempt < max_attempts and not deadline_exceeded(read_status(job_id).get("deadline_at")),
            )
            return {"state": "CANCELLED"}
        except JobDeadlineExceeded as exc:
            write_status(
                job_id,
                state="FAILURE",
                progress=0,
                error=str(exc),
                message="Conversion timed out.",
                retryable=False,
            )
            return {"state": "FAILURE"}
        except Exception as exc:
            err_msg = str(exc) or type(exc).__name__
            if attempt < max_attempts and not deadline_exceeded(read_status(job_id).get("deadline_at")):
                write_status(
                    job_id,
                    state="RETRYING",
                    progress=0,
                    error=err_msg,
                    message=f"Retrying conversion ({attempt}/{max_attempts})…",
                    retryable=True,
                )
                continue
            write_status(
                job_id,
                state="FAILURE",
                progress=0,
                error=err_msg,
                message="Conversion failed.",
                retryable=False,
            )
            log.exception("convert job %s (%s) failed", job_id, op)
            raise
    return {"state": "FAILURE"}


# ---------------------------------------------------------------------------
# Conversion dispatch
# ---------------------------------------------------------------------------

def _progress(job_id: str, pct: int, msg: str) -> None:
    _assert_job_active(job_id)
    write_status(job_id, state="PROGRESS", progress=pct, message=msg)


def _dispatch_conversion(
    job_id: str,
    op: str,
    upload_token: str,
    input_filename: str,
    options: dict[str, Any],
) -> str:
    """Run the conversion and return the absolute path of the result file."""
    from ..upload import get_temp_dir
    from acb_large_print.converter import CONVERTIBLE_EXTENSIONS, convert_to_markdown
    from acb_large_print.pandoc_converter import (
        PANDOC_INPUT_EXTENSIONS,
        LIBREOFFICE_CONVERSIONS,
        preconvert_via_libreoffice,
    )

    _progress(job_id, 10, "Locating source file…")
    temp_dir = get_temp_dir(upload_token)
    if not temp_dir:
        raise FileNotFoundError(f"Upload token {upload_token!r} not found or expired")

    from pathlib import Path as _Path
    source = _Path(temp_dir) / input_filename
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    job_out_dir = _job_dir(job_id)
    _progress(job_id, 20, f"Running {op} conversion…")

    # Match the synchronous convert route's pre-conversion behavior.
    if source.suffix.lower() in LIBREOFFICE_CONVERSIONS:
        lo_path = preconvert_via_libreoffice(
            source,
            LIBREOFFICE_CONVERSIONS[source.suffix.lower()],
            source.parent,
        )
        if lo_path is not None:
            source = lo_path

    chain_via_markdown = {
        ".doc",
        ".ppt",
        ".pptx",
        ".xlsx",
        ".xls",
        ".pdf",
        ".csv",
        ".html",
        ".htm",
        ".json",
        ".xml",
        ".ods",
        ".fods",
        ".odp",
        ".fodp",
    }
    pandoc_effective_extensions = PANDOC_INPUT_EXTENSIONS | chain_via_markdown

    if op == "to_markdown" and source.suffix.lower() not in CONVERTIBLE_EXTENSIONS:
        raise ValueError(
            f"File type '{source.suffix.lower()}' cannot be converted to Markdown."
        )

    if op in {"to_html", "to_docx", "to_epub", "to_pdf", "to_odt"}:
        ext = source.suffix.lower()
        if ext not in pandoc_effective_extensions:
            raise ValueError(
                f"File type '{ext}' cannot be converted with Pandoc pipeline."
            )
        if ext in chain_via_markdown:
            md_intermediate = source.parent / f"{source.stem}-extracted.md"
            source, _ = convert_to_markdown(source, output_path=md_intermediate)

    if op == "pipeline":
        return _run_pipeline(job_id, source, job_out_dir, options)
    elif op == "to_markdown":
        return _run_to_markdown(job_id, source, job_out_dir, options)
    elif op == "to_html":
        return _run_to_html(job_id, source, job_out_dir, options)
    elif op == "to_docx":
        return _run_to_docx(job_id, source, job_out_dir, options)
    elif op == "to_epub":
        return _run_to_epub(job_id, source, job_out_dir, options)
    elif op == "to_pdf":
        return _run_to_pdf(job_id, source, job_out_dir, options)
    elif op == "to_odt":
        return _run_to_odt(job_id, source, job_out_dir, options)
    else:
        raise ValueError(f"Unknown conversion op: {op!r}")


def _run_pipeline(job_id, source, out_dir, options):
    from acb_large_print.pipeline_converter import convert_with_pipeline
    from acb_large_print.pipeline_converter import get_available_conversions
    _progress(job_id, 30, "Sending to DAISY Pipeline…")
    conversion_key = options.get("pipeline_conversion", "")
    available = get_available_conversions()
    if conversion_key not in available:
        raise ValueError(
            f"Pipeline conversion '{conversion_key}' is not available."
        )
    out_path, _ = convert_with_pipeline(
        source,
        conversion_key,
        output_dir=out_dir,
        title=options.get("title"),
    )
    _progress(job_id, 85, "Pipeline finished.")
    return str(out_path)


def _run_to_markdown(job_id, source, out_dir, options):
    from acb_large_print.converter import convert_to_markdown
    _progress(job_id, 40, "Extracting content to Markdown…")
    dest = out_dir / (source.stem + ".md")
    output_path, _ = convert_to_markdown(source, output_path=dest)
    return str(output_path)


def _run_to_html(job_id, source, out_dir, options):
    import re
    from acb_large_print.pandoc_converter import convert_to_html
    _progress(job_id, 40, "Converting to HTML…")
    css_path = None if options.get("acb_format", True) else Path("__no_acb_css__")
    output_path, _ = convert_to_html(
        source,
        output_path=out_dir / (source.stem + ".html"),
        title=options.get("title"),
        css_path=css_path,
    )

    # Preserve convert route options when using background conversion.
    if options.get("acb_format", True) and (
        options.get("binding_margin", False) or not options.get("print_ready", False)
    ):
        html_text = output_path.read_text(encoding="utf-8")
        if options.get("binding_margin", False):
            html_text = html_text.replace(
                "padding: 1rem 1rem;",
                "padding: 1rem 1rem 1rem 1.5rem;",
                1,
            )
        if not options.get("print_ready", False):
            html_text = re.sub(
                r"@media\s+print\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}",
                "",
                html_text,
            )
        output_path.write_text(html_text, encoding="utf-8")

    return str(output_path)


def _run_to_docx(job_id, source, out_dir, options):
    from acb_large_print.pandoc_converter import convert_to_docx
    _progress(job_id, 40, "Converting to Word document…")
    result_path = out_dir / (source.stem + ".docx")
    output_path, _ = convert_to_docx(
        source,
        output_path=result_path,
        title=options.get("title"),
    )
    return str(output_path)


def _run_to_epub(job_id, source, out_dir, options):
    from acb_large_print.pandoc_converter import convert_to_epub
    _progress(job_id, 40, "Converting to EPUB…")
    result_path = out_dir / (source.stem + ".epub")
    css_path = None if options.get("acb_format", True) else Path("__no_acb_css__")
    output_path, _ = convert_to_epub(
        source,
        output_path=result_path,
        title=options.get("title"),
        css_path=css_path,
    )
    return str(output_path)


def _run_to_pdf(job_id, source, out_dir, options):
    from acb_large_print.pandoc_converter import convert_to_pdf
    _progress(job_id, 40, "Converting to PDF…")
    result_path = out_dir / (source.stem + ".pdf")
    css_path = None if options.get("acb_format", True) else Path("__no_acb_css__")
    output_path, _ = convert_to_pdf(
        source,
        output_path=result_path,
        title=options.get("title"),
        css_path=css_path,
        binding_margin=bool(options.get("binding_margin", False)),
    )
    return str(output_path)


def _run_to_odt(job_id, source, out_dir, options):
    from acb_large_print.pandoc_converter import convert_to_odt
    _progress(job_id, 40, "Converting to ODT…")
    result_path = out_dir / (source.stem + ".odt")
    output_path, _ = convert_to_odt(
        source,
        output_path=result_path,
        title=options.get("title"),
    )
    return str(output_path)


# ---------------------------------------------------------------------------
# Task: run_speech_job
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="glow.speech")  # type: ignore[misc]
def run_speech_job(
    self,
    job_id: str,
    upload_token: str,
    input_filename: str,
    voice_id: str,
    speed: float,
    pitch: int,
    output_format: str = "mp3",
) -> dict[str, Any]:
    """Synthesize an uploaded document to speech asynchronously.

    Parameters
    ----------
    job_id:
        UUID created by the web route.
    upload_token:
        Session upload token used to locate the extracted text.
    input_filename:
        Original document filename (used to derive the audio output name).
    voice_id:
        Engine:voice identifier, e.g. ``"kokoro:af_sky"`` or ``"piper:en_US-amy-medium"``.
    speed:
        Playback speed multiplier (0.5–2.0).
    pitch:
        Pitch shift in semitones (-20 to 20).
    output_format:
        ``"mp3"`` (default) or ``"wav"``.
    """
    status = read_status(job_id)
    max_attempts = max(1, int(status.get("max_attempts", 1)))
    start_attempt = max(1, int(status.get("attempt", 0)) + 1)

    for attempt in range(start_attempt, max_attempts + 1):
        write_status(
            job_id,
            state="STARTED",
            progress=2,
            message="Starting speech synthesis…",
            attempt=attempt,
            error=None,
            retryable=attempt < max_attempts,
        )
        try:
            _assert_job_active(job_id)
            result_path = _run_speech(
                job_id, upload_token, input_filename, voice_id, speed, pitch, output_format
            )
            result_name = Path(result_path).name
            write_status(
                job_id,
                state="SUCCESS",
                progress=100,
                message="Done.",
                result_file=result_name,
                retryable=False,
            )
            return {"state": "SUCCESS", "result_file": result_name}
        except JobCancelled as exc:
            write_status(
                job_id,
                state="CANCELLED",
                progress=0,
                error=str(exc),
                message="Speech synthesis cancelled.",
                retryable=attempt < max_attempts and not deadline_exceeded(read_status(job_id).get("deadline_at")),
            )
            return {"state": "CANCELLED"}
        except JobDeadlineExceeded as exc:
            write_status(
                job_id,
                state="FAILURE",
                progress=0,
                error=str(exc),
                message="Speech synthesis timed out.",
                retryable=False,
            )
            return {"state": "FAILURE"}
        except Exception as exc:
            err_msg = str(exc) or type(exc).__name__
            if attempt < max_attempts and not deadline_exceeded(read_status(job_id).get("deadline_at")):
                write_status(
                    job_id,
                    state="RETRYING",
                    progress=0,
                    error=err_msg,
                    message=f"Retrying speech synthesis ({attempt}/{max_attempts})…",
                    retryable=True,
                )
                continue
            write_status(
                job_id,
                state="FAILURE",
                progress=0,
                error=err_msg,
                message="Speech synthesis failed.",
                retryable=False,
            )
            log.exception("speech job %s failed", job_id)
            raise
    return {"state": "FAILURE"}


def _run_speech(
    job_id: str,
    upload_token: str,
    input_filename: str,
    voice_id: str,
    speed: float,
    pitch: int,
    output_format: str,
) -> str:
    """Run full-document speech synthesis and return the output file path."""
    from ..upload import get_temp_dir
    from acb_large_print_web.speech import (
        SpeechError,
        normalize_document_text,
        synthesize_document_text,
        wav_bytes_to_mp3,
        wav_duration_seconds,
    )

    _progress(job_id, 10, "Locating extracted document text…")

    # load pre-extracted text written by /speech/prepare
    _DOC_RENDERED_NAME = "speech_rendered.txt"
    _DOC_EXTRACT_NAME = "speech_source.txt"

    temp_dir = get_temp_dir(upload_token)
    if not temp_dir:
        raise FileNotFoundError(f"Upload token {upload_token!r} not found or expired")

    rendered_path = temp_dir / _DOC_RENDERED_NAME
    extract_path = temp_dir / _DOC_EXTRACT_NAME

    if rendered_path.exists():
        raw_text = rendered_path.read_text(encoding="utf-8")
    elif extract_path.exists():
        raw_text = extract_path.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError("Document text not found; please re-upload via Speech Studio.")

    text = normalize_document_text(raw_text)
    if not text.strip():
        raise ValueError("Document appears to contain no readable text.")

    # Optionally apply pronunciation dictionary if enabled
    try:
        from acb_large_print_web.magic_features import apply_pronunciation_dictionary
        from acb_large_print_web import feature_flags as _ff
        if _ff.get_all_flags().get("GLOW_ENABLE_SPEECH_PRONUNCIATION_DICTIONARY", True):
            text = apply_pronunciation_dictionary(text)
    except Exception:
        pass

    word_count = len(text.split())
    _progress(job_id, 20, f"Synthesizing {word_count:,} words — this may take a few minutes…")

    try:
        wav_bytes, wav_filename = synthesize_document_text(
            voice_id,
            text,
            speed=speed,
            pitch=pitch,
            progress_callback=lambda pct, msg: _progress(job_id, 20 + int(pct * 0.75), msg),
        )
    except SpeechError as exc:
        raise RuntimeError(str(exc)) from exc

    _progress(job_id, 96, "Encoding audio…")

    job_out_dir = _job_dir(job_id)
    stem = Path(input_filename).stem

    if output_format == "mp3":
        mp3_bytes = wav_bytes_to_mp3(wav_bytes)
        if mp3_bytes is not None:
            out_path = job_out_dir / f"{stem}.mp3"
            out_path.write_bytes(mp3_bytes)
            return str(out_path)
        # ffmpeg not available, fall back to WAV
        log.warning("speech job %s: mp3 encoding unavailable, saving wav", job_id)

    out_path = job_out_dir / f"{stem}.wav"
    out_path.write_bytes(wav_bytes)
    return str(out_path)
