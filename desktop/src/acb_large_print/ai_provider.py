"""Abstract base for AI heading classification providers.

Uses Ollama as the AI backend for heading detection refinement.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .heading_detector import HeadingCandidate

log = logging.getLogger("acb_large_print.ai")

# ---------------------------------------------------------------------------
# AI result model
# ---------------------------------------------------------------------------


@dataclass
class AIResult:
    """Classification result from an AI provider."""

    is_heading: bool
    level: int | None = None
    confidence: float = 0.0
    reasoning: str = ""


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

DEFAULT_PROMPT_TEMPLATE = """\
You are a document structure analyst. Given a paragraph from a Word document \
and its surrounding context, determine whether it is a heading and if so, \
what heading level (1-6).

CANDIDATE PARAGRAPH:
"{paragraph_text}"

FORMATTING EVIDENCE (treat as strong signals):
- Font size: {font_size}pt
- Document body text font size: {body_font_size}pt
- Bold: {is_bold}
- All caps: {is_caps}
- Length: {char_count} characters

CONTEXT (paragraphs before):
{before}

CONTEXT (paragraphs after):
{after}

Heuristic signals detected: {signals_list}

OTHER HEADINGS ALREADY IDENTIFIED IN THIS DOCUMENT:
{existing_headings}

RULES:
- Heading 1 is reserved for the document title or top-level sections
- Heading levels must not skip (no H1 -> H3 without H2)
- Headings are typically short (under 80 characters), do not end with \
sentence punctuation, and introduce subsequent content
- Body text that happens to be bold or short is NOT a heading

Respond with ONLY a JSON object:
{{"is_heading": true/false, "level": 1-6 or null, "confidence": 0.0-1.0, \
"reasoning": "brief explanation"}}"""

# Users can replace the template entirely as long as they include these
# placeholders (all optional -- missing ones are silently ignored):
#   {paragraph_text}  -- candidate text
#   {font_size}        -- font size in pt
#   {is_bold}          -- True/False
#   {is_caps}          -- True/False
#   {char_count}       -- character count
#   {body_font_size}   -- document body text font size
#   {before}           -- preceding paragraphs
#   {after}            -- following paragraphs
#   {signals_list}     -- heuristic signals
#   {existing_headings}-- headings already identified


def build_prompt(
    candidate: HeadingCandidate,
    context: dict,
    *,
    body_font_size: float | None = None,
    system_prompt: str | None = None,
) -> str:
    """Build the classification prompt for a single candidate.

    Args:
        candidate: The paragraph to classify.
        context: Context dict with before/after/existing_headings.
        body_font_size: The document's body text font size in pt.
            Used to help the model reason about relative font sizes.
        system_prompt: Custom prompt template.  If *None* the built-in
            ``DEFAULT_PROMPT_TEMPLATE`` is used.  The template may
            contain any subset of the placeholder variables listed in
            the module docstring -- missing ones are silently ignored.
    """
    template = system_prompt if system_prompt else DEFAULT_PROMPT_TEMPLATE

    signals_str = ", ".join(f"{name} (+{pts})" for name, pts in candidate.signals)
    before_str = "\n".join(context.get("before", [])) or "(start of document)"
    after_str = "\n".join(context.get("after", [])) or "(end of document)"
    headings_str = "\n".join(context.get("existing_headings", [])) or "(none yet)"

    # Use safe formatting: ignore placeholders not present in the template
    values = {
        "paragraph_text": candidate.text[:500],
        "font_size": candidate.font_size_pt or "unknown",
        "is_bold": candidate.is_bold,
        "is_caps": candidate.is_all_caps,
        "char_count": candidate.char_count,
        "before": before_str,
        "after": after_str,
        "signals_list": signals_str,
        "existing_headings": headings_str,
        "body_font_size": body_font_size or "unknown",
    }

    try:
        return template.format(**values)
    except KeyError:
        # User template may have custom placeholders -- fall back to
        # format_map which ignores missing keys
        class _SafeDict(dict):
            def __missing__(self, key: str) -> str:
                return "{" + key + "}"

        return template.format_map(_SafeDict(**values))


def parse_ai_response(text: str) -> AIResult | None:
    """Parse the JSON response from an AI model. Returns None on failure."""
    try:
        # Strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        data = json.loads(cleaned)
        if not isinstance(data, dict):
            log.warning("AI response is not a JSON object: %s", text[:200])
            return None
        return AIResult(
            is_heading=bool(data.get("is_heading", False)),
            level=data.get("level"),
            confidence=float(data.get("confidence", 0.0)),
            reasoning=str(data.get("reasoning", "")),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        log.warning("Failed to parse AI response: %s", text[:200])
        return None


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------


class AIProvider(ABC):
    """Base class for AI heading classification providers."""

    def __init__(self, *, system_prompt: str | None = None) -> None:
        self.system_prompt = system_prompt

    @abstractmethod
    def classify_candidates(
        self,
        candidates: list[HeadingCandidate],
        contexts: list[dict],
        *,
        body_font_size: float | None = None,
    ) -> list[AIResult | None]:
        """Classify a batch of candidates.

        Args:
            candidates: Paragraphs to classify.
            contexts: Matching list of context dicts (before/after/headings).
            body_font_size: The document's body text font size in pt.

        Returns:
            List of AIResult (or None on per-candidate failure), same length
            as *candidates*.
        """
        ...


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_provider(
    *,
    model: str | None = None,
    endpoint: str | None = None,
    system_prompt: str | None = None,
    keep_alive: str | None = None,
) -> AIProvider:
    """Create the Ollama AI provider.

    Args:
        model: Model name override (default ``phi4-mini``).
        endpoint: Ollama API endpoint URL (default ``http://localhost:11434``).
        system_prompt: Custom prompt template. Uses the built-in default
            when *None*.
        keep_alive: How long Ollama keeps the model in RAM after the last
            request (default ``30m``).  Accepts Ollama duration strings
            like ``"5m"``, ``"1h"``, ``"0"`` (unload immediately).

    Raises:
        ImportError: ``ollama`` package not installed.
    """
    from .ai_providers.ollama_provider import OllamaProvider

    return OllamaProvider(
        model=model,
        endpoint=endpoint,
        system_prompt=system_prompt,
        keep_alive=keep_alive,
    )


def is_ai_available() -> bool:
    """Return *True* if the Ollama package is installed and the server responds.

    Performs a lightweight HTTP check against the default endpoint so callers
    can pre-check the AI checkbox in the UI without instantiating a full
    provider.
    """
    try:
        import ollama as _ollama  # noqa: F401
    except ImportError:
        return False
    try:
        from .ai_providers.ollama_provider import DEFAULT_ENDPOINT
        import urllib.request

        req = urllib.request.Request(DEFAULT_ENDPOINT, method="HEAD")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except Exception:
        return False
