"""OpenRouter-based AI provider for heading classification."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import requests

from ..ai_provider import AIProvider, AIResult, build_prompt, parse_ai_response

if TYPE_CHECKING:
    from ..heading_detector import HeadingCandidate

log = logging.getLogger("acb_large_print.ai.openrouter")

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 30
BATCH_SIZE = 20


class OpenRouterProvider(AIProvider):
    """Classify heading candidates using OpenRouter chat completions."""

    def __init__(
        self,
        *,
        model: str | None = None,
        endpoint: str | None = None,
        system_prompt: str | None = None,
        api_key: str | None = None,
    ) -> None:
        super().__init__(system_prompt=system_prompt)
        self.model = model or DEFAULT_MODEL
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY or pass api_key."
            )

    def classify_candidates(
        self,
        candidates: list[HeadingCandidate],
        contexts: list[dict],
        *,
        body_font_size: float | None = None,
    ) -> list[AIResult | None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
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

                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                }

                try:
                    response = requests.post(
                        self.endpoint,
                        headers=headers,
                        json=payload,
                        timeout=REQUEST_TIMEOUT_SECONDS,
                    )
                    response.raise_for_status()
                    data = response.json()
                    text = data["choices"][0]["message"]["content"]
                    results.append(parse_ai_response(text))
                except Exception:
                    log.warning(
                        "OpenRouter request failed for paragraph %d",
                        candidate.paragraph_index,
                        exc_info=True,
                    )
                    results.append(None)

        return results
