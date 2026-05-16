from __future__ import annotations

import os
import time
from dataclasses import dataclass


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class AsyncPolicy:
    max_attempts: int
    deadline_seconds: int

    @property
    def deadline_at(self) -> float:
        return time.time() + float(self.deadline_seconds)


def load_policy(job_family: str) -> AsyncPolicy:
    family = (job_family or "").strip().upper().replace("-", "_")

    max_attempts = _env_int("GLOW_ASYNC_MAX_ATTEMPTS", 2, 1, 5)
    deadline_seconds = _env_int("GLOW_ASYNC_DEADLINE_SECONDS", 1800, 60, 7200)

    max_attempts = _env_int(
        f"GLOW_ASYNC_{family}_MAX_ATTEMPTS",
        max_attempts,
        1,
        5,
    )
    deadline_seconds = _env_int(
        f"GLOW_ASYNC_{family}_DEADLINE_SECONDS",
        deadline_seconds,
        60,
        7200,
    )
    return AsyncPolicy(max_attempts=max_attempts, deadline_seconds=deadline_seconds)


def deadline_exceeded(deadline_at: float | int | None, *, now: float | None = None) -> bool:
    if deadline_at is None:
        return False
    current = time.time() if now is None else now
    return float(deadline_at) <= current

