"""Concurrency gating for resource-intensive server operations.

GLOW 2.0 runs on a 10-core / 12 GB server.  Two operations are
CPU/memory-intensive enough to need hard concurrency caps:

  • AI heading detection (Ollama / llama3 -- 2-3 cores, ~5 GB)
  • BITS Whisperer audio transcription (faster-whisper medium -- 3-4 cores, ~3 GB)

Caps are controlled by environment variables so the operator can tune them
without rebuilding the image:

  GLOW_MAX_AI_SESSIONS    -- max simultaneous AI heading-detection jobs (default 3)
  GLOW_MAX_AUDIO_SESSIONS -- max simultaneous Whisper transcription jobs (default 2)

When a slot is not immediately available, the route returns a 503 "Server Busy"
response with a Retry-After header rather than queuing the request.  This keeps
the UX honest and avoids unbounded memory growth from a request queue.

Usage (in a route handler)::

    from .gating import ai_gate, audio_gate, GatingError

    try:
        with ai_gate():
            result = run_ai_fix(...)
    except GatingError:
        return busy_response("AI heading detection")

    try:
        with audio_gate():
            result = whisper_convert(...)
    except GatingError:
        return busy_response("BITS Whisperer transcription")
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Generator

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_MAX_AI: int = int(os.environ.get("GLOW_MAX_AI_SESSIONS", "3"))
_MAX_AUDIO: int = int(os.environ.get("GLOW_MAX_AUDIO_SESSIONS", "2"))

# Retry-After hint sent to clients when a gate is full (seconds)
RETRY_AFTER_SECONDS: int = 90


# ---------------------------------------------------------------------------
# Semaphores (module-level singletons, shared across all Gunicorn threads
# within a single worker process)
# ---------------------------------------------------------------------------

_ai_semaphore = threading.BoundedSemaphore(_MAX_AI)
_audio_semaphore = threading.BoundedSemaphore(_MAX_AUDIO)

# Live counters for the /health endpoint
_ai_active: int = 0
_audio_active: int = 0
_lock = threading.Lock()


class GatingError(Exception):
    """Raised when no slot is available for a gated operation."""

    def __init__(self, operation: str) -> None:
        self.operation = operation
        super().__init__(
            f"No capacity available for '{operation}'. "
            f"Please try again in {RETRY_AFTER_SECONDS} seconds."
        )


# ---------------------------------------------------------------------------
# Context managers
# ---------------------------------------------------------------------------

@contextmanager
def ai_gate() -> Generator[None, None, None]:
    """Acquire one AI session slot.  Raises GatingError if none available."""
    global _ai_active
    acquired = _ai_semaphore.acquire(blocking=False)
    if not acquired:
        raise GatingError("AI heading detection")
    with _lock:
        _ai_active += 1
    try:
        yield
    finally:
        _ai_semaphore.release()
        with _lock:
            _ai_active -= 1


@contextmanager
def audio_gate() -> Generator[None, None, None]:
    """Acquire one BITS Whisperer slot.  Raises GatingError if none available."""
    global _audio_active
    acquired = _audio_semaphore.acquire(blocking=False)
    if not acquired:
        raise GatingError("BITS Whisperer transcription")
    with _lock:
        _audio_active += 1
    try:
        yield
    finally:
        _audio_semaphore.release()
        with _lock:
            _audio_active -= 1


# ---------------------------------------------------------------------------
# Metrics (consumed by /health)
# ---------------------------------------------------------------------------

def get_capacity_metrics() -> dict:
    """Return a snapshot of current gating counters for the health endpoint."""
    with _lock:
        return {
            "ai": {
                "active": _ai_active,
                "limit": _MAX_AI,
                "available": _MAX_AI - _ai_active,
            },
            "audio": {
                "active": _audio_active,
                "limit": _MAX_AUDIO,
                "available": _MAX_AUDIO - _audio_active,
            },
        }
