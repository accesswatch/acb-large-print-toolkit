"""Speech Studio route and synthesis endpoints -- v2.9.0.

Provides:
    GET  /speech/          -- Speech Studio page
    POST /speech/preview   -- synthesize text, return WAV for inline playback
    POST /speech/download  -- synthesize text, return MP3/WAV as attachment
"""

from __future__ import annotations

import io

from flask import Blueprint, current_app, jsonify, make_response, render_template, request

from ..app import limiter
from ..speech import (
    KOKORO_VOICES,
    PIPER_VOICES,
    SpeechError,
    get_engine_status,
    synthesize,
    wav_bytes_to_mp3,
)

speech_bp = Blueprint("speech", __name__)

_TEXT_MAX_LEN = 500
_DEFAULT_DEMO_TEXT = (
    "Welcome to Speech Studio. "
    "Choose a voice, tune speed and pitch, and create clear narration for your audience."
)


# ---------------------------------------------------------------------------
# Speech Studio page
# ---------------------------------------------------------------------------


@speech_bp.route("/", methods=["GET"])
def speech_form():
    status = get_engine_status()
    any_ready = status["kokoro"]["ready"] or status["piper"]["ready"]
    return render_template(
        "speech.html",
        kokoro_voices=KOKORO_VOICES,
        piper_voices=PIPER_VOICES,
        engine_status=status,
        any_engine_ready=any_ready,
        default_text=_DEFAULT_DEMO_TEXT,
        text_max_len=_TEXT_MAX_LEN,
    )


# ---------------------------------------------------------------------------
# Preview -- returns WAV bytes for inline <audio> player via JS fetch
# ---------------------------------------------------------------------------


@speech_bp.route("/preview", methods=["POST"])
@limiter.limit("15 per minute")
def speech_preview():
    voice_id = (request.form.get("voice") or "").strip()
    text = (request.form.get("text") or "").strip()[:_TEXT_MAX_LEN]
    speed = _parse_float(request.form.get("speed"), default=1.0, lo=0.5, hi=2.0)
    pitch = _parse_int(request.form.get("pitch"), default=0, lo=-20, hi=20)

    if not voice_id:
        return jsonify({"error": "No voice selected."}), 400
    if not text:
        return jsonify({"error": "Text must not be empty."}), 400

    try:
        wav_bytes, _ = synthesize(voice_id, text, speed=speed, pitch=pitch)
    except SpeechError as exc:
        return jsonify({"error": str(exc)}), 503

    resp = make_response(wav_bytes)
    resp.headers["Content-Type"] = "audio/wav"
    resp.headers["Content-Length"] = len(wav_bytes)
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------------------------------------------------------
# Download -- returns MP3 (or WAV fallback) as a file attachment
# ---------------------------------------------------------------------------


@speech_bp.route("/download", methods=["POST"])
@limiter.limit("10 per minute")
def speech_download():
    voice_id = (request.form.get("voice") or "").strip()
    text = (request.form.get("text") or "").strip()[:_TEXT_MAX_LEN]
    speed = _parse_float(request.form.get("speed"), default=1.0, lo=0.5, hi=2.0)
    pitch = _parse_int(request.form.get("pitch"), default=0, lo=-20, hi=20)

    if not voice_id:
        return jsonify({"error": "No voice selected."}), 400
    if not text:
        return jsonify({"error": "Text must not be empty."}), 400

    try:
        wav_bytes, wav_filename = synthesize(voice_id, text, speed=speed, pitch=pitch)
    except SpeechError as exc:
        # Redirect back with an error flash
        from flask import flash, redirect, url_for
        flash(str(exc), "error")
        return redirect(url_for("speech.speech_form"))

    # Attempt MP3 encoding; fall back to WAV if pydub/ffmpeg unavailable
    mp3_bytes = wav_bytes_to_mp3(wav_bytes)
    if mp3_bytes is not None:
        content = mp3_bytes
        content_type = "audio/mpeg"
        filename = wav_filename.replace(".wav", ".mp3")
    else:
        content = wav_bytes
        content_type = "audio/wav"
        filename = wav_filename

    resp = make_response(content)
    resp.headers["Content-Type"] = content_type
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp.headers["Content-Length"] = len(content)
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_float(value, *, default: float, lo: float, hi: float) -> float:
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return default


def _parse_int(value, *, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default
