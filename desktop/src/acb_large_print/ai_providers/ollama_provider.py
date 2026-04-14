"""Ollama-based AI provider for heading classification."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..ai_provider import AIProvider, AIResult, build_prompt, parse_ai_response

if TYPE_CHECKING:
    from ..heading_detector import HeadingCandidate

log = logging.getLogger("acb_large_print.ai.ollama")

DEFAULT_MODEL = "phi4-mini"
DEFAULT_ENDPOINT = "http://localhost:11434"
DEFAULT_KEEP_ALIVE = "30m"
BATCH_SIZE = 20


class OllamaProvider(AIProvider):
    """Classify heading candidates using a local Ollama instance."""

    def __init__(
        self,
        *,
        model: str | None = None,
        endpoint: str | None = None,
        system_prompt: str | None = None,
        keep_alive: str | None = None,
    ) -> None:
        super().__init__(system_prompt=system_prompt)
        self.model = model or DEFAULT_MODEL
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        self.keep_alive = keep_alive or DEFAULT_KEEP_ALIVE

    def classify_candidates(
        self,
        candidates: list[HeadingCandidate],
        contexts: list[dict],
        *,
        body_font_size: float | None = None,
    ) -> list[AIResult | None]:
        try:
            import ollama as _ollama
        except ImportError:
            raise ImportError(
                "The 'ollama' package is required for the Ollama provider. "
                "Install it with: pip install ollama>=0.4"
            )

        client = _ollama.Client(host=self.endpoint)
        results: list[AIResult | None] = []

        for i in range(0, len(candidates), BATCH_SIZE):
            batch_c = candidates[i : i + BATCH_SIZE]
            batch_ctx = contexts[i : i + BATCH_SIZE]

            for candidate, ctx in zip(batch_c, batch_ctx):
                prompt = build_prompt(
                    candidate,
                    ctx,
                    body_font_size=body_font_size,
                    system_prompt=self.system_prompt,
                )
                try:
                    response = client.chat(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        options={"temperature": 0.1},
                        format="json",
                        keep_alive=self.keep_alive,
                    )
                    text = response["message"]["content"]
                    results.append(parse_ai_response(text))
                except Exception:
                    log.warning(
                        "Ollama request failed for paragraph %d",
                        candidate.paragraph_index,
                        exc_info=True,
                    )
                    results.append(None)

        return results
