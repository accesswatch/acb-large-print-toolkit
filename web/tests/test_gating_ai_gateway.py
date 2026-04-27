"""Tests for AI queue gating and OpenRouter retry behavior."""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest

from acb_large_print_web.gating import GatingError, ai_gate, get_capacity_metrics
from acb_large_print_web.ai_gateway import _openrouter_post_chat


def test_ai_gate_reports_active_and_queue_fields() -> None:
    metrics_before = get_capacity_metrics()
    assert "queued" in metrics_before["ai"]
    assert "queue_wait_seconds" in metrics_before["ai"]

    with ai_gate(wait_seconds=0):
        metrics = get_capacity_metrics()
        assert metrics["ai"]["active"] >= 1


def test_ai_gate_waits_and_acquires_when_slot_frees() -> None:
    acquired_second = {"ok": False}

    with ai_gate(wait_seconds=0):
        def _worker() -> None:
            with ai_gate(wait_seconds=2):
                acquired_second["ok"] = True

        t = threading.Thread(target=_worker)
        t.start()
        time.sleep(0.2)
    t.join(timeout=5)

    assert acquired_second["ok"] is True


def test_openrouter_retry_on_429_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    class _Resp:
        def __init__(self, code: int, payload: dict | None = None):
            self.status_code = code
            self._payload = payload or {}

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

        def json(self) -> dict:
            return self._payload

    def _fake_post(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _Resp(429)
        return _Resp(200, {"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("acb_large_print_web.ai_gateway.requests.post", _fake_post)
    monkeypatch.setattr("acb_large_print_web.ai_gateway.time.sleep", lambda _s: None)

    data = _openrouter_post_chat({"model": "m", "messages": []}, {"Authorization": "Bearer x"})
    assert calls["n"] == 2
    assert "choices" in data
