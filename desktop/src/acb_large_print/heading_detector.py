"""Detect faux headings in Word documents using heuristic scoring.

Tier 1: Heuristic detection -- scores each paragraph against visual
signals (bold, font size, length, casing, position) to identify text
that looks like a heading but lacks a heading style.

Tier 2: Optional AI refinement -- sends medium-confidence candidates
to an AI provider for classification.  AI is never required.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from docx import Document

from . import constants as C

if TYPE_CHECKING:
    from .ai_provider import AIProvider


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class HeadingCandidate:
    """A paragraph detected as a potential heading."""

    paragraph_index: int
    text: str
    font_size_pt: float | None
    is_bold: bool
    is_all_caps: bool
    is_title_case: bool
    char_count: int
    score: int = 0
    signals: list[tuple[str, int]] = field(default_factory=list)
    suggested_level: int = 0
    confidence: str = "low"  # "high", "medium", "low"
    ai_reasoning: str | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_TRAILING_PUNCT = re.compile(r"[.,;:!?]$")
_NUMBERING = re.compile(
    r"^(\d+[\.\)]\s+|[A-Z][\.\)]\s+|(Chapter|Section|Part)\s+\d+)",
    re.IGNORECASE,
)
_SIGNATURE_LINE = re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}[.,]?$")
_CALLOUT_OR_SALUTATION = re.compile(
    r"^(Please\s+Note|Note|Reminder|Thanks|Sincerely|Regards|Respectfully)[:,-]?\s",
    re.IGNORECASE,
)
# Pattern filters for Conservative mode
_TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}\s*(AM|PM|am|pm)?$")
_SHORT_NAME_PATTERN = re.compile(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+)?$")  # John or John Smith
_INITIALS_PATTERN = re.compile(r"^[A-Z]\.(\s+[A-Z]\.)*$")  # J. D. M.


def _is_likely_false_positive(text: str) -> bool:
    """True if text matches common false positive patterns (name, time, etc)."""
    if _TIME_PATTERN.match(text):
        return True
    if len(text) <= 30 and _SHORT_NAME_PATTERN.match(text):
        return True
    if _INITIALS_PATTERN.match(text):
        return True
    return False


def _get_body_font_size(doc: Document) -> float:
    """Return the most common font size in the document (proxy for body size)."""
    sizes: Counter[float] = Counter()
    for para in doc.paragraphs:
        for run in para.runs:
            if run.font.size is not None:
                sizes[run.font.size.pt] += len(run.text)
    if sizes:
        return sizes.most_common(1)[0][0]
    return C.BODY_SIZE_PT


def _para_is_bold(para) -> bool:
    """True if every non-empty run in the paragraph is bold."""
    runs = [r for r in para.runs if r.text.strip()]
    if not runs:
        return False
    return all(r.font.bold for r in runs)


def _para_font_size(para) -> float | None:
    """Get the dominant font size of a paragraph's runs."""
    for run in para.runs:
        if run.text.strip() and run.font.size is not None:
            return run.font.size.pt
    return None


def _is_heading_style(style_name: str) -> bool:
    return bool(re.match(r"^Heading \d+$", style_name))


def _prev_is_blank_or_break(paragraphs: list, index: int) -> bool:
    """Check if previous paragraph is blank or contains a page break."""
    if index == 0:
        return True  # first paragraph gets this signal
    prev = paragraphs[index - 1]
    if not prev.text.strip():
        return True
    # Check for page break in XML
    xml = prev._element.xml
    if "w:br" in xml and 'w:type="page"' in xml:
        return True
    return False


def _next_is_body(paragraphs: list, index: int) -> bool:
    """Check if next paragraph looks like body text (long, not bold)."""
    if index >= len(paragraphs) - 1:
        return False
    nxt = paragraphs[index + 1]
    if len(nxt.text.strip()) > 80 and not _para_is_bold(nxt):
        return True
    return False


# ---------------------------------------------------------------------------
# Core scoring engine
# ---------------------------------------------------------------------------


def _score_paragraph(
    para,
    index: int,
    paragraphs: list,
    body_font_size: float,
) -> HeadingCandidate | None:
    """Score a single paragraph for heading likelihood. Returns candidate or None."""
    style_name = para.style.name if para.style else "Normal"

    # Skip already-styled headings and list styles
    if _is_heading_style(style_name):
        return None
    if style_name.startswith("List "):
        return None

    text = para.text.strip()
    if not text:
        return None
    # Skip very long text -- headings are short
    if len(text) > 200:
        return None

    is_bold = _para_is_bold(para)
    font_size = _para_font_size(para)
    is_all_caps = text.isupper() and len(text) > 1
    is_title_case = text.istitle() and not is_all_caps
    char_count = len(text)

    signals: list[tuple[str, int]] = []
    score = 0

    # Signal 1: Bold text (+20)
    if is_bold:
        signals.append(("Bold text", 20))
        score += 20

    # Signal 2: Large font size (+25 scaled)
    if font_size is not None:
        if font_size >= C.HEADING1_SIZE_PT:  # 22pt+
            signals.append((f"Large font ({font_size}pt)", 25))
            score += 25
        elif font_size >= C.HEADING3_SIZE_PT:  # 20pt+
            signals.append((f"Large font ({font_size}pt)", 20))
            score += 20

    # Signal 3: Short text (+15)
    if char_count <= 80:
        signals.append((f"Short text ({char_count} chars)", 15))
        score += 15

    # Signal 4: No trailing punctuation (+10)
    if not _TRAILING_PUNCT.search(text):
        signals.append(("No trailing punctuation", 10))
        score += 10

    # Signal 5: Preceded by blank/break (+10)
    if _prev_is_blank_or_break(paragraphs, index):
        signals.append(("Preceded by blank/break", 10))
        score += 10

    # Signal 6: Followed by body text (+5)
    if _next_is_body(paragraphs, index):
        signals.append(("Followed by body text", 5))
        score += 5

    # Signal 7: ALL CAPS or Title Case (+10)
    if is_all_caps:
        signals.append(("ALL CAPS", 10))
        score += 10
    elif is_title_case:
        signals.append(("Title Case", 10))
        score += 10

    # Signal 8: Different font size from body (+5)
    if font_size is not None and abs(font_size - body_font_size) > 0.5:
        signals.append(("Different from body size", 5))
        score += 5

    # Signal 9: Single-line paragraph (+5)
    if "\n" not in para.text and "\r" not in para.text:
        signals.append(("Single-line", 5))
        score += 5

    # Signal 10: Numbering pattern (+5)
    if _NUMBERING.match(text):
        signals.append(("Numbering pattern", 5))
        score += 5

    # Penalty 1: Signature-like line (e.g., "Jane Smith")
    if char_count <= 40 and _SIGNATURE_LINE.match(text):
        signals.append(("Signature-like line", -20))
        score -= 20

    # Penalty 2: Callout/salutation prefix (e.g., "Please Note:")
    if char_count <= 80 and _CALLOUT_OR_SALUTATION.match(text):
        signals.append(("Callout or salutation prefix", -15))
        score -= 15

    # Must reach minimum threshold to be a candidate
    if score < C.HEADING_CONFIDENCE_THRESHOLD:
        return None

    has_strong_structure_signal = (
        is_bold
        or (font_size is not None and font_size >= C.HEADING3_SIZE_PT)
        or bool(_NUMBERING.match(text))
    )
    confidence = (
        "high"
        if score >= C.HEADING_HIGH_CONFIDENCE and has_strong_structure_signal
        else "medium"
    )

    return HeadingCandidate(
        paragraph_index=index,
        text=text,
        font_size_pt=font_size,
        is_bold=is_bold,
        is_all_caps=is_all_caps,
        is_title_case=is_title_case,
        char_count=char_count,
        score=score,
        signals=signals,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Heading level assignment
# ---------------------------------------------------------------------------


def _assign_heading_levels(candidates: list[HeadingCandidate]) -> None:
    """Assign heading levels based on font size and visual weight."""
    if not candidates:
        return

    # Collect unique font sizes, sorted descending
    sizes = sorted(
        {c.font_size_pt for c in candidates if c.font_size_pt is not None},
        reverse=True,
    )

    # Build size-to-level map
    size_to_level: dict[float, int] = {}
    for i, size in enumerate(sizes):
        if i == 0:
            size_to_level[size] = 1
        elif i == 1:
            size_to_level[size] = 2
        elif i == 2:
            size_to_level[size] = 3
        else:
            size_to_level[size] = min(i + 1, 6)

    for c in candidates:
        if c.font_size_pt is not None and c.font_size_pt in size_to_level:
            c.suggested_level = size_to_level[c.font_size_pt]
        else:
            # No font size info -- assign based on visual weight
            if c.is_bold and c.is_all_caps:
                c.suggested_level = 1
            elif c.is_bold:
                c.suggested_level = 2
            elif c.is_all_caps or c.is_title_case:
                c.suggested_level = 3
            else:
                c.suggested_level = 3

    # First candidate bias: if first candidate isn't level 1, promote it
    if candidates and candidates[0].suggested_level > 1:
        candidates[0].suggested_level = 1

    # Validate hierarchy: no skipped levels
    _fix_hierarchy_gaps(candidates)


def _fix_hierarchy_gaps(candidates: list[HeadingCandidate]) -> None:
    """Adjust levels so no heading level is skipped."""
    if len(candidates) < 2:
        return
    prev_level = candidates[0].suggested_level
    for c in candidates[1:]:
        if c.suggested_level > prev_level + 1:
            c.suggested_level = prev_level + 1
        prev_level = c.suggested_level


def _apply_accuracy_filters(
    candidates: list[HeadingCandidate],
    accuracy_level: str = "balanced",
) -> list[HeadingCandidate]:
    """Filter candidates based on accuracy_level preference.
    
    Args:
        candidates: List of HeadingCandidate objects.
        accuracy_level: "conservative", "balanced", or "thorough".
    
    Returns:
        Filtered list of candidates.
    """
    if accuracy_level == "conservative":
        # Strict filtering: remove short text, patterns, medium confidence
        filtered = []
        for c in candidates:
            # Skip very short text (likely names, times, single words)
            word_count = len(c.text.split())
            if word_count < 4:
                continue
            # Skip obvious false positive patterns
            if _is_likely_false_positive(c.text):
                continue
            # Keep only high confidence in conservative mode
            if c.confidence == "high":
                filtered.append(c)
        return filtered
    elif accuracy_level == "thorough":
        # Minimal filtering: keep all medium + high confidence
        return [c for c in candidates if c.confidence in ("high", "medium")]
    else:  # balanced (default)
        # Keep all candidates for user review
        return candidates


# ---------------------------------------------------------------------------
# Context builder for AI prompts
# ---------------------------------------------------------------------------


def _build_context(
    paragraphs: list,
    index: int,
    existing_headings: list[HeadingCandidate],
) -> dict:
    """Build context dict for an AI prompt."""
    before = []
    for i in range(max(0, index - 3), index):
        before.append(paragraphs[i].text.strip()[:200])
    after = []
    for i in range(index + 1, min(len(paragraphs), index + 4)):
        after.append(paragraphs[i].text.strip()[:200])

    headings_summary = [
        f'H{h.suggested_level}: "{h.text[:80]}"' for h in existing_headings
    ]

    return {
        "before": before,
        "after": after,
        "existing_headings": headings_summary,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_headings(
    doc: Document,
    *,
    ai_provider: AIProvider | None = None,
    threshold: int = C.HEADING_CONFIDENCE_THRESHOLD,
    system_prompt: str | None = None,
    accuracy_level: str = "balanced",
) -> list[HeadingCandidate]:
    """Detect faux headings in a Word document.

    Args:
        doc: An opened python-docx Document.
        ai_provider: Optional AI provider for Tier 2 refinement.
        threshold: Minimum confidence score (0--100). Default 50.
            Ignore if accuracy_level is set (uses level-specific threshold).
        system_prompt: Custom AI prompt template.  Uses the built-in
            default when *None*.  Only relevant when *ai_provider*
            is supplied.
        accuracy_level: "conservative" (heuristics only, no AI, high threshold),
                        "balanced" (heuristics + optional AI, default threshold),
                        "thorough" (heuristics + required AI if available, low threshold).
                        Default "balanced".

    Returns:
        List of HeadingCandidate objects sorted by document position.
    """
    # Map accuracy level to threshold and AI behavior
    if accuracy_level == "conservative":
        threshold = 70
        use_ai = False
    elif accuracy_level == "thorough":
        threshold = 40
        use_ai = True  # Try to use AI if available
    else:  # balanced
        # Respect caller-supplied threshold in balanced mode.
        use_ai = None  # Use AI only if available
    
    paragraphs = list(doc.paragraphs)
    body_font_size = _get_body_font_size(doc)

    # Tier 1: Heuristic scoring
    candidates: list[HeadingCandidate] = []
    for i, para in enumerate(paragraphs):
        candidate = _score_paragraph(para, i, paragraphs, body_font_size)
        if candidate and candidate.score >= threshold:
            candidates.append(candidate)

    # Assign heading levels
    _assign_heading_levels(candidates)

    # Apply accuracy-level filters
    candidates = _apply_accuracy_filters(candidates, accuracy_level)

    # Tier 2: AI refinement for medium-confidence candidates
    # Skip AI for conservative mode; use if available for balanced/thorough
    should_use_ai = ai_provider is not None and (use_ai is True or use_ai is None)
    
    if should_use_ai:
        # Pass system_prompt to the provider so it uses the user's
        # custom template (or the default) when building prompts.
        if system_prompt is not None:
            ai_provider.system_prompt = system_prompt

        high = [c for c in candidates if c.confidence == "high"]
        medium = [c for c in candidates if c.confidence == "medium"]

        if medium:
            contexts = [
                _build_context(paragraphs, c.paragraph_index, high) for c in medium
            ]
            try:
                results = ai_provider.classify_candidates(
                    medium, contexts, body_font_size=body_font_size
                )
                for candidate, result in zip(medium, results):
                    if result is not None:
                        if not result.is_heading:
                            candidates.remove(candidate)
                        else:
                            if result.level is not None:
                                candidate.suggested_level = result.level
                            candidate.confidence = (
                                "high" if result.confidence >= 0.75 else "medium"
                            )
                            candidate.ai_reasoning = result.reasoning
            except Exception:
                # Fallback: keep Tier 1 scores, mark AI unavailable
                for c in medium:
                    c.ai_reasoning = "AI analysis unavailable -- review suggested"

    return candidates
