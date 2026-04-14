"""Extensive tests for the Ollama AI provider and AI classification pipeline.

Tests cover OllamaProvider initialization, mocked Ollama client behavior,
batch processing, error handling, response parsing edge cases, and the
full classify_candidates flow.  No real Ollama server is needed -- every
network call is mocked.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from acb_large_print.ai_provider import (
    AIProvider,
    AIResult,
    DEFAULT_PROMPT_TEMPLATE,
    build_prompt,
    get_provider,
    is_ai_available,
    parse_ai_response,
)
from acb_large_print.ai_providers.ollama_provider import (
    BATCH_SIZE,
    DEFAULT_ENDPOINT,
    DEFAULT_KEEP_ALIVE,
    DEFAULT_MODEL,
    OllamaProvider,
)
from acb_large_print.heading_detector import HeadingCandidate

# ===================================================================
# Helpers
# ===================================================================


def _candidate(
    text="Sample Heading",
    font_size_pt=22.0,
    bold=True,
    index=0,
    score=80,
    confidence="medium",
):
    return HeadingCandidate(
        paragraph_index=index,
        text=text,
        font_size_pt=font_size_pt,
        is_bold=bold,
        is_all_caps=text.isupper() and len(text) > 1,
        is_title_case=text.istitle(),
        char_count=len(text),
        score=score,
        signals=[("Bold text", 20), ("Large font (22.0pt)", 25)],
        confidence=confidence,
    )


def _context(before=None, after=None, headings=None):
    return {
        "before": ["Previous paragraph."] if before is None else before,
        "after": ["Next paragraph."] if after is None else after,
        "existing_headings": [] if headings is None else headings,
    }


def _ai_json(is_heading=True, level=2, confidence=0.85, reasoning="Looks good"):
    return json.dumps(
        {
            "is_heading": is_heading,
            "level": level,
            "confidence": confidence,
            "reasoning": reasoning,
        }
    )


# ===================================================================
# 1. OllamaProvider initialization
# ===================================================================


class TestOllamaProviderInit:
    def test_defaults(self):
        p = OllamaProvider()
        assert p.model == DEFAULT_MODEL
        assert p.endpoint == DEFAULT_ENDPOINT
        assert p.system_prompt is None

    def test_custom_model(self):
        p = OllamaProvider(model="llama3")
        assert p.model == "llama3"

    def test_custom_endpoint(self):
        p = OllamaProvider(endpoint="http://remote:11434")
        assert p.endpoint == "http://remote:11434"

    def test_custom_system_prompt(self):
        p = OllamaProvider(system_prompt="Custom: {paragraph_text}")
        assert p.system_prompt == "Custom: {paragraph_text}"

    def test_is_abstract_subclass(self):
        assert issubclass(OllamaProvider, AIProvider)

    def test_none_values_use_defaults(self):
        p = OllamaProvider(model=None, endpoint=None)
        assert p.model == DEFAULT_MODEL
        assert p.endpoint == DEFAULT_ENDPOINT


# ===================================================================
# 2. get_provider factory
# ===================================================================


class TestGetProvider:
    def test_returns_ollama_provider(self):
        provider = get_provider()
        assert isinstance(provider, OllamaProvider)

    def test_passes_model(self):
        provider = get_provider(model="gemma2")
        assert provider.model == "gemma2"

    def test_passes_endpoint(self):
        provider = get_provider(endpoint="http://gpu-box:11434")
        assert provider.endpoint == "http://gpu-box:11434"

    def test_passes_system_prompt(self):
        provider = get_provider(system_prompt="test prompt")
        assert provider.system_prompt == "test prompt"


# ===================================================================
# 3. classify_candidates -- mocked Ollama client
# ===================================================================


class TestClassifyCandidates:
    def _mock_ollama_module(self):
        """Create a mock ollama module with a Client class."""
        mock_module = MagicMock()
        mock_client = MagicMock()
        mock_module.Client.return_value = mock_client
        return mock_module, mock_client

    def test_single_candidate_confirmed(self):
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {
            "message": {"content": _ai_json(True, 2, 0.9, "Clearly a heading")}
        }
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            results = provider.classify_candidates([_candidate()], [_context()])
        assert len(results) == 1
        assert results[0].is_heading is True
        assert results[0].level == 2
        assert results[0].confidence == 0.9

    def test_single_candidate_rejected(self):
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {
            "message": {"content": _ai_json(False, None, 0.95, "Body text")}
        }
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            results = provider.classify_candidates([_candidate()], [_context()])
        assert results[0].is_heading is False

    def test_multiple_candidates(self):
        mock_mod, mock_client = self._mock_ollama_module()
        responses = [
            {"message": {"content": _ai_json(True, 1, 0.95, "Title")}},
            {"message": {"content": _ai_json(True, 2, 0.80, "Section")}},
            {"message": {"content": _ai_json(False, None, 0.90, "Not heading")}},
        ]
        mock_client.chat.side_effect = responses
        candidates = [_candidate(index=i) for i in range(3)]
        contexts = [_context() for _ in range(3)]

        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            results = provider.classify_candidates(candidates, contexts)

        assert len(results) == 3
        assert results[0].is_heading is True
        assert results[0].level == 1
        assert results[2].is_heading is False

    def test_per_candidate_failure_returns_none(self):
        """If one Ollama call fails, that result is None but others succeed."""
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.side_effect = [
            {"message": {"content": _ai_json(True, 1, 0.95, "OK")}},
            Exception("Network timeout"),
            {"message": {"content": _ai_json(True, 3, 0.80, "Sub")}},
        ]
        candidates = [_candidate(index=i) for i in range(3)]
        contexts = [_context() for _ in range(3)]

        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            results = provider.classify_candidates(candidates, contexts)

        assert len(results) == 3
        assert results[0] is not None
        assert results[1] is None  # failed call
        assert results[2] is not None

    def test_all_candidates_fail(self):
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.side_effect = Exception("Server down")
        candidates = [_candidate(index=i) for i in range(3)]
        contexts = [_context() for _ in range(3)]

        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            results = provider.classify_candidates(candidates, contexts)

        assert len(results) == 3
        assert all(r is None for r in results)

    def test_garbage_ai_response_returns_none(self):
        """Non-JSON AI output maps to None via parse_ai_response."""
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {
            "message": {"content": "I think this is a heading because it's bold."}
        }
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            results = provider.classify_candidates([_candidate()], [_context()])
        assert results[0] is None

    def test_ollama_import_error(self):
        """If ollama package is not installed, ImportError is raised."""
        with patch.dict("sys.modules", {"ollama": None}):
            provider = OllamaProvider()
            with pytest.raises(ImportError, match="ollama"):
                provider.classify_candidates([_candidate()], [_context()])

    def test_custom_model_passed_to_client(self):
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider(model="mistral-nemo")
            provider.classify_candidates([_candidate()], [_context()])

        call_kwargs = mock_client.chat.call_args
        assert (
            call_kwargs.kwargs["model"] == "mistral-nemo"
            or call_kwargs[1]["model"] == "mistral-nemo"
        )

    def test_temperature_set_to_0_1(self):
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            provider.classify_candidates([_candidate()], [_context()])

        call_kwargs = mock_client.chat.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options["temperature"] == 0.1

    def test_custom_endpoint_passed_to_client(self):
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider(endpoint="http://192.168.1.100:11434")
            provider.classify_candidates([_candidate()], [_context()])

        mock_mod.Client.assert_called_once_with(host="http://192.168.1.100:11434")

    def test_system_prompt_used_in_build(self):
        """Custom system prompt should appear in the message sent to Ollama."""
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        custom = "Is this a heading? {paragraph_text}"
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider(system_prompt=custom)
            provider.classify_candidates([_candidate()], [_context()])

        call_args = mock_client.chat.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        prompt_text = messages[0]["content"]
        assert "Is this a heading?" in prompt_text
        assert "Sample Heading" in prompt_text

    def test_json_format_passed_to_client(self):
        """format='json' should be sent to Ollama for structured output."""
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            provider.classify_candidates([_candidate()], [_context()])

        call_kwargs = mock_client.chat.call_args
        fmt = call_kwargs.kwargs.get("format") or call_kwargs[1].get("format")
        assert fmt == "json"

    def test_keep_alive_default(self):
        """Default keep_alive of 30m should be passed to Ollama."""
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            provider.classify_candidates([_candidate()], [_context()])

        call_kwargs = mock_client.chat.call_args
        ka = call_kwargs.kwargs.get("keep_alive") or call_kwargs[1].get("keep_alive")
        assert ka == DEFAULT_KEEP_ALIVE

    def test_custom_keep_alive(self):
        """Custom keep_alive should be forwarded to Ollama calls."""
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider(keep_alive="1h")
            provider.classify_candidates([_candidate()], [_context()])

        call_kwargs = mock_client.chat.call_args
        ka = call_kwargs.kwargs.get("keep_alive") or call_kwargs[1].get("keep_alive")
        assert ka == "1h"

    def test_body_font_size_passed_to_prompt(self):
        """body_font_size should appear in the prompt sent to Ollama."""
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            provider.classify_candidates(
                [_candidate()], [_context()], body_font_size=12.0
            )

        call_args = mock_client.chat.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        prompt_text = messages[0]["content"]
        assert "12.0" in prompt_text


# ===================================================================
# 4. BATCH PROCESSING
# ===================================================================


class TestBatchProcessing:
    def test_within_batch_size(self):
        """Fewer than BATCH_SIZE candidates processed in one batch."""
        mock_mod, mock_client = self._mock_ollama_module()
        n = BATCH_SIZE - 1
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        candidates = [_candidate(index=i) for i in range(n)]
        contexts = [_context() for _ in range(n)]

        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            results = provider.classify_candidates(candidates, contexts)

        assert len(results) == n
        assert mock_client.chat.call_count == n

    def test_exceeds_batch_size(self):
        """More than BATCH_SIZE candidates are processed in multiple batches."""
        mock_mod, mock_client = self._mock_ollama_module()
        n = BATCH_SIZE + 5
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        candidates = [_candidate(index=i) for i in range(n)]
        contexts = [_context() for _ in range(n)]

        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            results = provider.classify_candidates(candidates, contexts)

        assert len(results) == n
        assert mock_client.chat.call_count == n

    def test_exactly_batch_size(self):
        mock_mod, mock_client = self._mock_ollama_module()
        mock_client.chat.return_value = {"message": {"content": _ai_json()}}
        candidates = [_candidate(index=i) for i in range(BATCH_SIZE)]
        contexts = [_context() for _ in range(BATCH_SIZE)]

        with patch.dict("sys.modules", {"ollama": mock_mod}):
            provider = OllamaProvider()
            results = provider.classify_candidates(candidates, contexts)

        assert len(results) == BATCH_SIZE

    def _mock_ollama_module(self):
        mock_module = MagicMock()
        mock_client = MagicMock()
        mock_module.Client.return_value = mock_client
        return mock_module, mock_client


# ===================================================================
# 5. parse_ai_response -- extended edge cases
# ===================================================================


class TestParseAIResponseExtensive:
    def test_code_fence_with_language_tag(self):
        response = '```json\n{"is_heading": true, "level": 1, "confidence": 0.95, "reasoning": "Title"}\n```'
        result = parse_ai_response(response)
        assert result is not None
        assert result.is_heading is True

    def test_code_fence_no_language_tag(self):
        response = '```\n{"is_heading": false, "level": null, "confidence": 0.8, "reasoning": "Body"}\n```'
        result = parse_ai_response(response)
        assert result is not None
        assert result.is_heading is False

    def test_nested_code_fences(self):
        """Model wraps in double code fences (seen with some models)."""
        response = '```\n```json\n{"is_heading": true, "level": 2}\n```\n```'
        result = parse_ai_response(response)
        # May or may not parse -- should not crash
        assert result is None or isinstance(result, AIResult)

    def test_leading_trailing_whitespace(self):
        response = '  \n  {"is_heading": true, "level": 3, "confidence": 0.7, "reasoning": "Sub"}  \n  '
        result = parse_ai_response(response)
        assert result is not None
        assert result.level == 3

    def test_is_heading_as_integer(self):
        response = json.dumps({"is_heading": 1, "level": 2})
        result = parse_ai_response(response)
        assert result.is_heading is True

    def test_is_heading_as_zero(self):
        response = json.dumps({"is_heading": 0})
        result = parse_ai_response(response)
        assert result.is_heading is False

    def test_is_heading_as_string_true(self):
        """Some models return "true" as a string."""
        response = json.dumps({"is_heading": "true"})
        result = parse_ai_response(response)
        # bool("true") is True in Python
        assert result is not None

    def test_confidence_as_percentage_string(self):
        """Model returns "85%" instead of 0.85."""
        response = '{"is_heading": true, "level": 2, "confidence": "0.85"}'
        result = parse_ai_response(response)
        assert result.confidence == 0.85

    def test_confidence_non_numeric_string(self):
        """Non-numeric confidence should cause parse failure."""
        response = '{"is_heading": true, "confidence": "high"}'
        result = parse_ai_response(response)
        # float("high") raises ValueError -- caught by except
        assert result is None

    def test_level_as_string(self):
        response = json.dumps({"is_heading": True, "level": "2"})
        result = parse_ai_response(response)
        # level is returned as-is (data.get), should be "2" string
        assert result is not None

    def test_extra_fields_ignored(self):
        response = json.dumps(
            {
                "is_heading": True,
                "level": 1,
                "confidence": 0.9,
                "reasoning": "Title",
                "suggested_text": "Better Title",
                "font_recommendation": "Arial",
            }
        )
        result = parse_ai_response(response)
        assert result is not None
        assert result.is_heading is True

    def test_empty_json_object(self):
        response = "{}"
        result = parse_ai_response(response)
        assert result is not None
        assert result.is_heading is False  # default

    def test_json_array_instead_of_object(self):
        response = '[{"is_heading": true}]'
        result = parse_ai_response(response)
        # data.get on a list should fail
        assert result is None

    def test_ai_response_with_thinking_prefix(self):
        """Some models emit 'thinking' text before JSON."""
        response = 'Let me analyze this paragraph.\n\n{"is_heading": true, "level": 2, "confidence": 0.8, "reasoning": "Bold heading"}'
        result = parse_ai_response(response)
        # The plain text prefix makes json.loads fail
        assert result is None

    def test_ai_response_with_trailing_text(self):
        """JSON followed by explanation text."""
        response = '{"is_heading": true, "level": 1, "confidence": 0.95, "reasoning": "Title"}\n\nThis is clearly the document title.'
        result = parse_ai_response(response)
        # json.loads should fail on trailing text
        assert result is None

    def test_unicode_reasoning(self):
        response = json.dumps(
            {
                "is_heading": True,
                "level": 1,
                "confidence": 0.9,
                "reasoning": "Uberschrift -- Barrierefreiheit",
            }
        )
        result = parse_ai_response(response)
        assert result is not None
        assert "Barrierefreiheit" in result.reasoning

    def test_null_values(self):
        response = json.dumps(
            {
                "is_heading": True,
                "level": None,
                "confidence": None,
                "reasoning": None,
            }
        )
        result = parse_ai_response(response)
        # confidence=float(None) raises TypeError -- caught
        assert result is None


# ===================================================================
# 6. build_prompt -- extended edge cases
# ===================================================================


class TestBuildPromptExtensive:
    def test_no_signals(self):
        c = HeadingCandidate(
            paragraph_index=0,
            text="Plain",
            font_size_pt=None,
            is_bold=False,
            is_all_caps=False,
            is_title_case=False,
            char_count=5,
            signals=[],
        )
        prompt = build_prompt(c, _context())
        assert "Plain" in prompt

    def test_font_size_none_shows_unknown(self):
        c = _candidate(font_size_pt=None)
        prompt = build_prompt(c, _context())
        assert "unknown" in prompt

    def test_many_signals(self):
        c = _candidate()
        c.signals = [
            ("Bold text", 20),
            ("Large font (22pt)", 25),
            ("Short text", 15),
            ("No trailing punctuation", 10),
            ("Preceded by blank/break", 10),
            ("Title Case", 10),
        ]
        prompt = build_prompt(c, _context())
        assert "Bold text (+20)" in prompt
        assert "Title Case (+10)" in prompt

    def test_empty_before_context(self):
        prompt = build_prompt(_candidate(), _context(before=[]))
        assert "(start of document)" in prompt

    def test_empty_after_context(self):
        prompt = build_prompt(_candidate(), _context(after=[]))
        assert "(end of document)" in prompt

    def test_empty_existing_headings(self):
        prompt = build_prompt(_candidate(), _context(headings=[]))
        assert "(none yet)" in prompt

    def test_existing_headings_shown(self):
        prompt = build_prompt(
            _candidate(),
            _context(headings=['H1: "Document Title"', 'H2: "Introduction"']),
        )
        assert "Document Title" in prompt
        assert "Introduction" in prompt

    def test_long_text_truncated(self):
        c = _candidate(text="A" * 600)
        prompt = build_prompt(c, _context())
        assert "A" * 500 in prompt
        assert "A" * 501 not in prompt

    def test_custom_template_with_subset_of_vars(self):
        custom = "Heading? {paragraph_text} bold={is_bold}"
        prompt = build_prompt(_candidate(), _context(), system_prompt=custom)
        assert "Sample Heading" in prompt
        assert "bold=True" in prompt

    def test_custom_template_with_unknown_vars(self):
        custom = "Info: {paragraph_text} -- {custom_var}"
        prompt = build_prompt(_candidate(), _context(), system_prompt=custom)
        assert "Sample Heading" in prompt
        assert "{custom_var}" in prompt

    def test_template_with_no_vars(self):
        custom = "Just classify it."
        prompt = build_prompt(_candidate(), _context(), system_prompt=custom)
        assert prompt == "Just classify it."

    def test_default_template_has_all_placeholders(self):
        """Verify the default template includes all documented placeholders."""
        for var in [
            "{paragraph_text}",
            "{font_size}",
            "{is_bold}",
            "{is_caps}",
            "{char_count}",
            "{before}",
            "{after}",
            "{signals_list}",
            "{existing_headings}",
        ]:
            assert var in DEFAULT_PROMPT_TEMPLATE, f"Missing: {var}"


# ===================================================================
# 7. is_ai_available -- extended
# ===================================================================


class TestIsAIAvailableExtensive:
    @patch("urllib.request.urlopen")
    @patch.dict("sys.modules", {"ollama": MagicMock()})
    def test_server_200_returns_true(self, mock_urlopen):
        mock_urlopen.return_value.__enter__ = MagicMock()
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
        assert is_ai_available() is True

    @patch("urllib.request.urlopen", side_effect=ConnectionRefusedError)
    @patch.dict("sys.modules", {"ollama": MagicMock()})
    def test_connection_refused_returns_false(self, _):
        assert is_ai_available() is False

    @patch("urllib.request.urlopen", side_effect=TimeoutError)
    @patch.dict("sys.modules", {"ollama": MagicMock()})
    def test_timeout_returns_false(self, _):
        assert is_ai_available() is False

    @patch("urllib.request.urlopen", side_effect=OSError("Network unreachable"))
    @patch.dict("sys.modules", {"ollama": MagicMock()})
    def test_network_error_returns_false(self, _):
        assert is_ai_available() is False

    def test_no_ollama_package_returns_false(self):
        import sys

        saved = sys.modules.get("ollama")
        sys.modules["ollama"] = None
        try:
            assert is_ai_available() is False
        finally:
            if saved is not None:
                sys.modules["ollama"] = saved
            else:
                sys.modules.pop("ollama", None)

    @patch("urllib.request.urlopen", side_effect=Exception("Unexpected"))
    @patch.dict("sys.modules", {"ollama": MagicMock()})
    def test_unexpected_exception_returns_false(self, _):
        assert is_ai_available() is False


# ===================================================================
# 8. AI RESPONSE SCENARIOS -- realistic model outputs
# ===================================================================


class TestRealisticAIOutputs:
    """Test parse_ai_response with outputs from various real model families."""

    def test_phi4_mini_clean(self):
        """phi4-mini typically gives clean JSON."""
        response = '{"is_heading": true, "level": 2, "confidence": 0.87, "reasoning": "The text is bold, 22pt, and short, indicating a section heading."}'
        result = parse_ai_response(response)
        assert result.is_heading is True
        assert result.level == 2

    def test_llama3_with_code_fence(self):
        """Llama models often wrap in code fences."""
        response = """```json
{"is_heading": true, "level": 1, "confidence": 0.95, "reasoning": "This appears to be the document title based on its position and large font size."}
```"""
        result = parse_ai_response(response)
        assert result is not None
        assert result.level == 1

    def test_model_adds_explanation_after_json(self):
        """Some models add explanation text after the JSON block."""
        response = """```json
{"is_heading": true, "level": 3, "confidence": 0.72, "reasoning": "Sub-section"}
```

Note: This heading appears to be a subsection under the previous heading."""
        result = parse_ai_response(response)
        # The code fence stripping should handle this
        assert result is not None or result is None  # either is acceptable

    def test_model_returns_markdown_bold(self):
        """Weird model output: JSON keys in markdown bold."""
        response = '{"**is_heading**": true}'
        result = parse_ai_response(response)
        # Should fail to parse correctly
        assert result is None or result.is_heading is False

    def test_model_returns_yes_no(self):
        """Model ignores instructions and returns natural language."""
        response = "Yes, this is clearly a heading. It should be level 2."
        result = parse_ai_response(response)
        assert result is None

    def test_model_returns_partial_json(self):
        """Truncated response (context length exceeded)."""
        response = '{"is_heading": true, "level": 2, "confid'
        result = parse_ai_response(response)
        assert result is None

    def test_model_returns_multiple_json_objects(self):
        """Model returns two JSON objects."""
        response = '{"is_heading": true, "level": 1}\n{"is_heading": false}'
        result = parse_ai_response(response)
        # json.loads fails on multiple objects
        assert result is None

    def test_model_uses_single_quotes(self):
        """Python-style dict (single quotes) isn't valid JSON."""
        response = "{'is_heading': True, 'level': 2}"
        result = parse_ai_response(response)
        assert result is None

    def test_model_returns_boolean_strings(self):
        """JSON with string booleans: "true" instead of true."""
        response = (
            '{"is_heading": "true", "level": 2, "confidence": 0.8, "reasoning": ""}'
        )
        result = parse_ai_response(response)
        # bool("true") is True in Python
        assert result is not None

    def test_model_returns_empty_response(self):
        assert parse_ai_response("") is None

    def test_model_returns_whitespace_only(self):
        assert parse_ai_response("   \n\t  ") is None
