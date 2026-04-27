"""Concurrency gating for outbound AI API calls.

GLOW 2.0 routes all AI inference through OpenRouter (cloud) rather than
on-device models.  Gating here limits simultaneous outbound API calls to
prevent runaway spend and respect provider rate limits.

Caps are controlled by environment variables:

  GLOW_MAX_AI_SESSIONS    -- max simultaneous chat/fix API calls (default 10)
  GLOW_MAX_AUDIO_SESSIONS -- max simultaneous Whisper transcription calls (default 3)
  GLOW_MAX_VISION_SESSIONS -- max simultaneous vision API calls (default 5)

When a slot is not immediately available the route returns 503 with
Retry-After rather than queuing unbounded requests.

Usage (in a route handler)::

    from .gating import ai_gate, audio_gate, GatingError

    try:
        with ai_gate():
            result = gateway.chat(...)
    except GatingError:
        return busy_response("AI assistant")
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Generator

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_MAX_AI: int = int(os.environ.get("GLOW_MAX_AI_SESSIONS", "10"))
_MAX_VISION: int = int(os.environ.get("GLOW_MAX_VISION_SESSIONS", "5"))
_MAX_AUDIO: int = int(os.environ.get("GLOW_MAX_AUDIO_SESSIONS", "3"))

# Optional bounded queue wait times (seconds). A value of 0 keeps fail-fast behavior.
_AI_QUEUE_WAIT_SECONDS: int = int(os.environ.get("GLOW_AI_QUEUE_WAIT_SECONDS", "25"))
_VISION_QUEUE_WAIT_SECONDS: int = int(os.environ.get("GLOW_VISION_QUEUE_WAIT_SECONDS", "20"))
_AUDIO_QUEUE_WAIT_SECONDS: int = int(os.environ.get("GLOW_AUDIO_QUEUE_WAIT_SECONDS", "0"))

# Retry-After hint sent to clients when a gate is full (seconds)
RETRY_AFTER_SECONDS: int = 90


# ---------------------------------------------------------------------------
# Semaphores (module-level singletons, shared across all Gunicorn threads
# within a single worker process)
# ---------------------------------------------------------------------------

_ai_semaphore = threading.BoundedSemaphore(_MAX_AI)
_vision_semaphore = threading.BoundedSemaphore(_MAX_VISION)
_audio_semaphore = threading.BoundedSemaphore(_MAX_AUDIO)

# Live counters for the /health endpoint
_ai_active: int = 0
_vision_active: int = 0
_audio_active: int = 0
_ai_waiting: int = 0
_vision_waiting: int = 0
_audio_waiting: int = 0
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
def ai_gate(wait_seconds: int | None = None) -> Generator[None, None, None]:
    """Acquire one AI API call slot. Raises GatingError if unavailable."""
    global _ai_active, _ai_waiting
    wait = _AI_QUEUE_WAIT_SECONDS if wait_seconds is None else max(0, int(wait_seconds))
    if wait > 0:
        with _lock:
            _ai_waiting += 1
        try:
            acquired = _ai_semaphore.acquire(timeout=wait)
        finally:
            with _lock:
                _ai_waiting -= 1
    else:
        acquired = _ai_semaphore.acquire(blocking=False)
    if not acquired:
        raise GatingError("AI assistant")
    with _lock:
        _ai_active += 1
    try:
        yield
    finally:
        _ai_semaphore.release()
        with _lock:
            _ai_active -= 1


@contextmanager
def audio_gate(wait_seconds: int | None = None) -> Generator[None, None, None]:
    """Acquire one BITS Whisperer API call slot. Raises GatingError if unavailable."""
    global _audio_active, _audio_waiting
    wait = _AUDIO_QUEUE_WAIT_SECONDS if wait_seconds is None else max(0, int(wait_seconds))
    if wait > 0:
        with _lock:
            _audio_waiting += 1
        try:
            acquired = _audio_semaphore.acquire(timeout=wait)
        finally:
            with _lock:
                _audio_waiting -= 1
    else:
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


@contextmanager
def vision_gate(wait_seconds: int | None = None) -> Generator[None, None, None]:
    """Acquire one vision API call slot. Raises GatingError if unavailable."""
    global _vision_active, _vision_waiting
    wait = _VISION_QUEUE_WAIT_SECONDS if wait_seconds is None else max(0, int(wait_seconds))
    if wait > 0:
        with _lock:
            _vision_waiting += 1
        try:
            acquired = _vision_semaphore.acquire(timeout=wait)
        finally:
            with _lock:
                _vision_waiting -= 1
    else:
        acquired = _vision_semaphore.acquire(blocking=False)
    if not acquired:
        raise GatingError("Vision processing")
    with _lock:
        _vision_active += 1
    try:
        yield
    finally:
        _vision_semaphore.release()
        with _lock:
            _vision_active -= 1


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
                "queued": _ai_waiting,
                "queue_wait_seconds": _AI_QUEUE_WAIT_SECONDS,
            },
            "vision": {
                "active": _vision_active,
                "limit": _MAX_VISION,
                "available": _MAX_VISION - _vision_active,
                "queued": _vision_waiting,
                "queue_wait_seconds": _VISION_QUEUE_WAIT_SECONDS,
            },
            "audio": {
                "active": _audio_active,
                "limit": _MAX_AUDIO,
                "available": _MAX_AUDIO - _audio_active,
                "queued": _audio_waiting,
                "queue_wait_seconds": _AUDIO_QUEUE_WAIT_SECONDS,
            },
        }
