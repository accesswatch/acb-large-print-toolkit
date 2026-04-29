"""Tests for OpenRouter AI provider implementation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from acb_large_print.ai_provider import AIResult
from acb_large_print.ai_providers.openrouter_provider import OpenRouterProvider
from acb_large_print.heading_detector import HeadingCandidate


def _candidate(index: int = 0) -> HeadingCandidate:
    return HeadingCandidate(
        paragraph_index=index,
        text="Executive Summary",
        font_size_pt=22.0,
        is_bold=True,
        is_all_caps=False,
        is_title_case=True,
        char_count=17,
        score=80,
        signals=[("Bold text", 20), ("Large font (22.0pt)", 25)],
        confidence="high",
    )


def _context() -> dict:
    return {
        "before": ["Previous paragraph."],
        "after": ["Next paragraph."],
        "existing_headings": ['H1: "Document Title"'],
    }


class TestOpenRouterProvider:
    def test_requires_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OpenRouter API key is required"):
                OpenRouterProvider(api_key=None)

    @patch("acb_large_print.ai_providers.openrouter_provider.requests.post")
    def test_classify_candidates_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"is_heading": true, "level": 1, "confidence": 0.9, "reasoning": "Looks like a heading"}'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        provider = OpenRouterProvider(api_key="test-key")
        results = provider.classify_candidates([_candidate()], [_context()])

        assert len(results) == 1
        assert isinstance(results[0], AIResult)
        assert results[0].is_heading is True
        assert results[0].level == 1

    @patch("acb_large_print.ai_providers.openrouter_provider.requests.post")
    def test_classify_candidates_failure_returns_none(self, mock_post):
        mock_post.side_effect = Exception("network error")

        provider = OpenRouterProvider(api_key="test-key")
        results = provider.classify_candidates([_candidate()], [_context()])

        assert len(results) == 1
        assert results[0] is None
