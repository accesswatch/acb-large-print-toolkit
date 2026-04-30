"""Speech synthesis engine abstraction for GLOW.

Tier 1: Kokoro ONNX  (pip install kokoro-onnx, models in instance/speech_models/)
Tier 2: Piper TTS    (pip install piper-tts, models in instance/speech_models/piper/)

All synthesis is synchronous and suitable for demo-length texts (≤500 chars).
Document-to-audio conversion is deferred to v3.0.0.
"""

from __future__ import annotations

import io
import os
import threading
import wave as _wave
from pathlib import Path

# ---------------------------------------------------------------------------
# Voice catalogues
# ---------------------------------------------------------------------------

KOKORO_VOICES: list[dict] = [
    {"id": "af_bella",    "label": "Bella",    "engine": "kokoro", "accent": "American", "gender": "Female"},
    {"id": "af_sarah",    "label": "Sarah",    "engine": "kokoro", "accent": "American", "gender": "Female"},
    {"id": "af_nicole",   "label": "Nicole",   "engine": "kokoro", "accent": "American", "gender": "Female"},
    {"id": "af_sky",      "label": "Sky",      "engine": "kokoro", "accent": "American", "gender": "Female"},
    {"id": "am_adam",     "label": "Adam",     "engine": "kokoro", "accent": "American", "gender": "Male"},
    {"id": "am_michael",  "label": "Michael",  "engine": "kokoro", "accent": "American", "gender": "Male"},
    {"id": "bf_emma",     "label": "Emma",     "engine": "kokoro", "accent": "British",  "gender": "Female"},
    {"id": "bf_isabella", "label": "Isabella", "engine": "kokoro", "accent": "British",  "gender": "Female"},
    {"id": "bm_george",   "label": "George",   "engine": "kokoro", "accent": "British",  "gender": "Male"},
    {"id": "bm_lewis",    "label": "Lewis",    "engine": "kokoro", "accent": "British",  "gender": "Male"},
]

PIPER_VOICES: list[dict] = [
    {"id": "en_US-lessac-medium",               "label": "Lessac (US)",            "engine": "piper", "accent": "American", "gender": "Male",   "sample_rate": 22050},
    {"id": "en_US-amy-medium",                  "label": "Amy (US)",               "engine": "piper", "accent": "American", "gender": "Female", "sample_rate": 22050},
    {"id": "en_US-ryan-high",                   "label": "Ryan (US, High)",        "engine": "piper", "accent": "American", "gender": "Male",   "sample_rate": 22050},
    {"id": "en_US-hfc_female-medium",           "label": "HFC Female (US)",        "engine": "piper", "accent": "American", "gender": "Female", "sample_rate": 22050},
    {"id": "en_GB-alan-medium",                 "label": "Alan (GB)",              "engine": "piper", "accent": "British",  "gender": "Male",   "sample_rate": 22050},
    {"id": "en_GB-southern_english_female-low", "label": "Southern English (GB)",  "engine": "piper", "accent": "British",  "gender": "Female", "sample_rate": 16000},
]

# ---------------------------------------------------------------------------
# Model directory configuration
# ---------------------------------------------------------------------------

_model_dir: Path | None = None


def configure(model_dir: str | Path) -> None:
    """Set the root directory where speech models are stored.

    Call this once at app startup with ``Path(app.instance_path) / "speech_models"``.
    """
    global _model_dir
    _model_dir = Path(model_dir)


def _get_model_dir() -> Path:
    if _model_dir is not None:
        return _model_dir
    return Path(os.environ.get("GLOW_SPEECH_MODEL_DIR", "./instance/speech_models"))


# ---------------------------------------------------------------------------
# Kokoro engine (Tier 1)
# ---------------------------------------------------------------------------

_kokoro_instance = None
_kokoro_lock = threading.Lock()

_KOKORO_MODEL_FILE = "kokoro-v1.0.onnx"
_KOKORO_VOICES_FILE = "voices-v1.0.bin"


def _kokoro_model_path() -> Path:
    return _get_model_dir() / _KOKORO_MODEL_FILE


def _kokoro_voices_path() -> Path:
    return _get_model_dir() / _KOKORO_VOICES_FILE


def _kokoro_models_present() -> bool:
    return _kokoro_model_path().exists() and _kokoro_voices_path().exists()


def _get_kokoro():
    """Return a loaded Kokoro instance, or None if unavailable."""
    global _kokoro_instance
    if _kokoro_instance is not None:
        return _kokoro_instance
    with _kokoro_lock:
        if _kokoro_instance is not None:
            return _kokoro_instance
        try:
            from kokoro_onnx import Kokoro  # type: ignore[import]
            if not _kokoro_models_present():
                return None
            _kokoro_instance = Kokoro(
                str(_kokoro_model_path()),
                str(_kokoro_voices_path()),
            )
        except Exception:
            return None
    return _kokoro_instance


def _kokoro_installed() -> bool:
    try:
        import kokoro_onnx  # noqa: F401  # type: ignore[import]
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Piper engine (Tier 2)
# ---------------------------------------------------------------------------

def _piper_model_dir() -> Path:
    return _get_model_dir() / "piper"


def _piper_model_path(voice_id: str) -> Path:
    return _piper_model_dir() / f"{voice_id}.onnx"


def _piper_config_path(voice_id: str) -> Path:
    return _piper_model_dir() / f"{voice_id}.onnx.json"


def _piper_voice_present(voice_id: str) -> bool:
    return _piper_model_path(voice_id).exists() and _piper_config_path(voice_id).exists()


def _piper_installed() -> bool:
    """Piper TTS is a CLI binary, not a Python import. Check if 'piper' is on PATH."""
    import shutil
    return shutil.which("piper") is not None


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def _ndarray_to_wav_bytes(samples, sample_rate: int) -> bytes:
    """Convert float32 numpy array [-1, 1] to 16-bit mono PCM WAV bytes."""
    import numpy as np  # kokoro-onnx already requires numpy

    pcm = np.clip(samples.flatten(), -1.0, 1.0)
    pcm_int16 = (pcm * 32767).astype(np.int16)
    buf = io.BytesIO()
    with _wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_int16.tobytes())
    return buf.getvalue()


def _pitch_shift_wav(wav_bytes: bytes, semitones: float) -> bytes:
    """Shift pitch by resampling (also slightly changes speed — acceptable for demo).

    Positive semitones = higher pitch. Range typically −20 to +20.
    """
    if abs(semitones) < 0.05:
        return wav_bytes
    buf = io.BytesIO(wav_bytes)
    with _wave.open(buf, "rb") as wf:
        params = wf.getparams()
        frames = wf.readframes(wf.getnframes())
    factor = 2 ** (semitones / 12.0)
    new_framerate = max(1000, int(params.framerate * factor))
    buf_out = io.BytesIO()
    with _wave.open(buf_out, "wb") as wf_out:
        wf_out.setnchannels(params.nchannels)
        wf_out.setsampwidth(params.sampwidth)
        wf_out.setframerate(new_framerate)
        wf_out.writeframes(frames)
    return buf_out.getvalue()


def wav_bytes_to_mp3(wav_bytes: bytes) -> bytes | None:
    """Encode WAV bytes to MP3 at 192 kbps using pydub (requires ffmpeg).

    Returns None if pydub or ffmpeg is unavailable.
    """
    try:
        from pydub import AudioSegment  # type: ignore[import]
        audio = AudioSegment.from_wav(io.BytesIO(wav_bytes))
        mp3_buf = io.BytesIO()
        audio.export(mp3_buf, format="mp3", bitrate="192k")
        return mp3_buf.getvalue()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Engine status
# ---------------------------------------------------------------------------

def get_engine_status() -> dict:
    """Return availability status for each engine.

    Returns a dict with keys ``kokoro`` and ``piper``, each containing:
    - ``installed`` (bool)
    - ``models_present`` (bool) — True if required model files are on disk
    - ``ready`` (bool) — installed AND models present
    - ``voices_available`` (list[str]) — voice IDs that are ready to use
    - ``model_dir`` (str) — where models are expected
    - ``setup_commands`` (list[str]) — human-readable install/download instructions
    """
    model_dir = _get_model_dir()

    kokoro_installed = _kokoro_installed()
    kokoro_models = _kokoro_models_present() if kokoro_installed else False

    piper_installed = _piper_installed()
    piper_voices_available = [
        v["id"] for v in PIPER_VOICES if _piper_voice_present(v["id"])
    ] if piper_installed else []

    kokoro_setup = []
    if not kokoro_installed:
        kokoro_setup.append("pip install kokoro-onnx")
    if not kokoro_models:
        kokoro_setup += [
            f"mkdir -p {model_dir}",
            f"# Download {_KOKORO_MODEL_FILE} and {_KOKORO_VOICES_FILE} to {model_dir}/",
            "# See docs/speech.md for download commands",
        ]

    piper_setup = []
    if not piper_installed:
        piper_setup.append("pip install piper-tts")
    if not piper_voices_available:
        piper_setup += [
            f"mkdir -p {model_dir / 'piper'}",
            "# Download .onnx and .onnx.json for each voice to instance/speech_models/piper/",
            "# See docs/speech.md for download commands",
        ]

    return {
        "kokoro": {
            "installed": kokoro_installed,
            "models_present": kokoro_models,
            "ready": kokoro_installed and kokoro_models,
            "voices_available": [v["id"] for v in KOKORO_VOICES] if (kokoro_installed and kokoro_models) else [],
            "model_dir": str(model_dir),
            "setup_commands": kokoro_setup,
        },
        "piper": {
            "installed": piper_installed,
            "models_present": bool(piper_voices_available),
            "ready": piper_installed and bool(piper_voices_available),
            "voices_available": piper_voices_available,
            "model_dir": str(model_dir / "piper"),
            "setup_commands": piper_setup,
        },
    }


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------

class SpeechError(Exception):
    """Raised when synthesis fails."""


def synthesize(voice_id: str, text: str, speed: float = 1.0, pitch: int = 0) -> tuple[bytes, str]:
    """Synthesize *text* with the given *voice_id* and return ``(wav_bytes, suggested_filename)``.

    *voice_id* format: ``"kokoro:af_bella"`` or ``"piper:en_US-lessac-medium"``.
    *speed*: 0.5–2.0 (default 1.0).
    *pitch*: −20 to +20 semitones (default 0).

    Raises :exc:`SpeechError` on failure.
    """
    if not text or not text.strip():
        raise SpeechError("Text must not be empty.")
    text = text.strip()[:500]  # hard cap; routes also validate

    speed = max(0.5, min(2.0, float(speed)))
    pitch = max(-20, min(20, int(pitch)))

    if ":" not in voice_id:
        raise SpeechError(f"Invalid voice_id format: {voice_id!r}. Expected 'engine:voice'.")
    engine, voice = voice_id.split(":", 1)

    if engine == "kokoro":
        wav_bytes = _synthesize_kokoro(voice, text, speed)
    elif engine == "piper":
        wav_bytes = _synthesize_piper(voice, text, speed)
    else:
        raise SpeechError(f"Unknown engine: {engine!r}")

    if pitch != 0:
        wav_bytes = _pitch_shift_wav(wav_bytes, pitch)

    safe_voice = voice.replace("/", "_").replace("\\", "_")
    filename = f"glow-speech-{safe_voice}.wav"
    return wav_bytes, filename


def _synthesize_kokoro(voice: str, text: str, speed: float) -> bytes:
    kokoro = _get_kokoro()
    if kokoro is None:
        if not _kokoro_installed():
            raise SpeechError(
                "Kokoro engine is not installed. Run: pip install kokoro-onnx"
            )
        raise SpeechError(
            f"Kokoro model files not found in {_get_model_dir()}. "
            "See docs/speech.md for download instructions."
        )
    try:
        samples, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
        return _ndarray_to_wav_bytes(samples, sample_rate)
    except Exception as exc:
        raise SpeechError(f"Kokoro synthesis failed: {exc}") from exc


def _synthesize_piper(voice: str, text: str, speed: float) -> bytes:
    if not _piper_installed():
        raise SpeechError("Piper engine is not installed. Run: pip install piper-tts")
    if not _piper_voice_present(voice):
        raise SpeechError(
            f"Piper model for voice '{voice}' not found in {_piper_model_dir()}. "
            "See docs/speech.md for download instructions."
        )
    try:
        from piper.voice import PiperVoice  # type: ignore[import]
        pv = PiperVoice.load(
            str(_piper_model_path(voice)),
            config_path=str(_piper_config_path(voice)),
        )
        length_scale = 1.0 / max(0.1, speed)  # Piper: higher = slower
        wav_buf = io.BytesIO()
        with _wave.open(wav_buf, "wb") as wf:
            pv.synthesize(text, wf, length_scale=length_scale)
        return wav_buf.getvalue()
    except Exception as exc:
        raise SpeechError(f"Piper synthesis failed: {exc}") from exc
