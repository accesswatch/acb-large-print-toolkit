"""Tests for the AI provider module -- prompt building, response parsing, availability."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from acb_large_print.ai_provider import (
    AIResult,
    DEFAULT_PROMPT_TEMPLATE,
    build_prompt,
    is_ai_available,
    parse_ai_response,
)
from acb_large_print.heading_detector import HeadingCandidate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _candidate(text="Test Heading", font_size_pt=22.0, bold=True) -> HeadingCandidate:
    return HeadingCandidate(
        paragraph_index=0,
        text=text,
        font_size_pt=font_size_pt,
        is_bold=bold,
        is_all_caps=False,
        is_title_case=True,
        char_count=len(text),
        score=80,
        signals=[("Bold text", 20), ("Large font (22.0pt)", 25)],
        confidence="high",
    )


def _context():
    return {
        "before": ["Previous paragraph."],
        "after": ["Next paragraph."],
        "existing_headings": ['H1: "Document Title"'],
    }


# ---------------------------------------------------------------------------
# AIResult dataclass
# ---------------------------------------------------------------------------


class TestAIResult:
    def test_defaults(self):
        r = AIResult(is_heading=True)
        assert r.level is None
        assert r.confidence == 0.0
        assert r.reasoning == ""

    def test_full(self):
        r = AIResult(
            is_heading=True, level=2, confidence=0.95, reasoning="Clearly a heading"
        )
        assert r.is_heading is True
        assert r.level == 2


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    def test_contains_candidate_text(self):
        prompt = build_prompt(_candidate(), _context())
        assert "Test Heading" in prompt

    def test_contains_context(self):
        prompt = build_prompt(_candidate(), _context())
        assert "Previous paragraph." in prompt
        assert "Next paragraph." in prompt

    def test_contains_signals(self):
        prompt = build_prompt(_candidate(), _context())
        assert "Bold text" in prompt

    def test_custom_template(self):
        custom = "Classify: {paragraph_text} (bold={is_bold})"
        prompt = build_prompt(_candidate(), _context(), system_prompt=custom)
        assert prompt == "Classify: Test Heading (bold=True)"

    def test_missing_placeholder_in_custom_template(self):
        custom = "Text: {paragraph_text}, Custom: {custom_field}"
        prompt = build_prompt(_candidate(), _context(), system_prompt=custom)
        assert "Test Heading" in prompt
        assert "{custom_field}" in prompt  # preserved, not crashing

    def test_empty_context(self):
        ctx = {"before": [], "after": [], "existing_headings": []}
        prompt = build_prompt(_candidate(), ctx)
        assert "(start of document)" in prompt
        assert "(end of document)" in prompt
        assert "(none yet)" in prompt

    def test_text_truncated_at_500(self):
        long_text = "A" * 600
        c = _candidate(text=long_text)
        prompt = build_prompt(c, _context())
        # The template uses candidate.text[:500]
        assert "A" * 500 in prompt
        assert "A" * 501 not in prompt

    def test_body_font_size_in_prompt(self):
        prompt = build_prompt(_candidate(), _context(), body_font_size=12.0)
        assert "12.0" in prompt
        assert "body text font size" in prompt.lower()

    def test_body_font_size_unknown_when_none(self):
        prompt = build_prompt(_candidate(), _context())
        assert "unknown" in prompt


# ---------------------------------------------------------------------------
# parse_ai_response
# ---------------------------------------------------------------------------


class TestParseAIResponse:
    def test_valid_json(self):
        response = json.dumps(
            {
                "is_heading": True,
                "level": 2,
                "confidence": 0.85,
                "reasoning": "Bold and short",
            }
        )
        result = parse_ai_response(response)
        assert result is not None
        assert result.is_heading is True
        assert result.level == 2
        assert result.confidence == 0.85
        assert result.reasoning == "Bold and short"

    def test_not_heading(self):
        response = json.dumps(
            {
                "is_heading": False,
                "level": None,
                "confidence": 0.9,
                "reasoning": "Body text",
            }
        )
        result = parse_ai_response(response)
        assert result is not None
        assert result.is_heading is False
        assert result.level is None

    def test_code_fenced_json(self):
        response = '```json\n{"is_heading": true, "level": 1, "confidence": 0.95, "reasoning": "Title"}\n```'
        result = parse_ai_response(response)
        assert result is not None
        assert result.is_heading is True
        assert result.level == 1

    def test_invalid_json_returns_none(self):
        result = parse_ai_response("This is not JSON")
        assert result is None

    def test_empty_string_returns_none(self):
        result = parse_ai_response("")
        assert result is None

    def test_missing_fields_use_defaults(self):
        response = json.dumps({"is_heading": True})
        result = parse_ai_response(response)
        assert result is not None
        assert result.level is None
        assert result.confidence == 0.0
        assert result.reasoning == ""

    def test_non_boolean_is_heading_coerced(self):
        response = json.dumps({"is_heading": 1, "level": 3})
        result = parse_ai_response(response)
        assert result is not None
        assert result.is_heading is True

    def test_confidence_as_string_coerced(self):
        response = json.dumps({"is_heading": True, "confidence": "0.7"})
        result = parse_ai_response(response)
        assert result is not None
        assert result.confidence == 0.7


# ---------------------------------------------------------------------------
# is_ai_available
# ---------------------------------------------------------------------------


class TestIsAIAvailable:
    @patch("urllib.request.urlopen")
    @patch.dict("sys.modules", {"ollama": MagicMock()})
    def test_available_when_server_responds(self, mock_urlopen):
        mock_urlopen.return_value.__enter__ = MagicMock()
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
        assert is_ai_available() is True

    def test_unavailable_when_ollama_not_installed(self):
        import sys

        saved = sys.modules.get("ollama")
        sys.modules["ollama"] = None
        try:
            result = is_ai_available()
            assert isinstance(result, bool)
        finally:
            if saved is not None:
                sys.modules["ollama"] = saved
            else:
                sys.modules.pop("ollama", None)

    @patch("urllib.request.urlopen", side_effect=Exception("Connection refused"))
    @patch.dict("sys.modules", {"ollama": MagicMock()})
    def test_unavailable_when_server_down(self, mock_urlopen):
        assert is_ai_available() is False
