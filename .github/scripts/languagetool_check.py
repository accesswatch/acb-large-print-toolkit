#!/usr/bin/env python3
"""Run lightweight LanguageTool checks for docs with false-positive filtering.

This script is intentionally conservative: it strips code blocks/inline code,
limits checks to markdown docs and README, and ignores known project terms.
"""

from __future__ import annotations

import re
from pathlib import Path

import language_tool_python

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [ROOT / "README.md", *sorted((ROOT / "docs").glob("**/*.md"))]

# Domain-specific terms that commonly trigger spelling false positives.
ALLOW_TERMS = {
    "acb",
    "aph",
    "bits",
    "cms",
    "daisy",
    "docx",
    "epub",
    "glow",
    "markitdown",
    "openrouter",
    "pdf",
    "pymupdf",
    "uarizona",
    "wcag",
    "weasyprint",
    "whisperer",
    "wxpython",
}

# Rules that tend to produce noisy markdown false positives for this repository.
IGNORE_RULE_IDS = {
    "WHITESPACE_RULE",
    "EN_UNPAIRED_BRACKETS",
    "COMMA_PARENTHESIS_WHITESPACE",
}


CODE_FENCE_RE = re.compile(r"```[\s\S]*?```", flags=re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`]+`")
URL_RE = re.compile(r"https?://\S+")


def sanitize_markdown(text: str) -> str:
    text = CODE_FENCE_RE.sub(" ", text)
    text = INLINE_CODE_RE.sub(" ", text)
    text = URL_RE.sub(" ", text)
    return text


def should_ignore(match: language_tool_python.Match) -> bool:
    if match.ruleId in IGNORE_RULE_IDS:
        return True

    matched = (match.matchedText or "").strip().lower()
    if matched in ALLOW_TERMS:
        return True

    # Ignore all-caps tokens and path-ish fragments.
    if matched.isupper() or "/" in matched or "\\" in matched:
        return True

    return False


def main() -> int:
    try:
        # Prefer local LanguageTool server (CI-friendly, no public API rate limits).
        tool = language_tool_python.LanguageTool("en-US")
    except Exception:
        # Fallback for environments where local backend cannot initialize.
        tool = language_tool_python.LanguageToolPublicAPI("en-US")
    total = 0

    for path in TARGETS:
        if not path.exists():
            continue

        text = sanitize_markdown(path.read_text(encoding="utf-8", errors="ignore"))
        matches = [m for m in tool.check(text) if not should_ignore(m)]

        for m in matches:
            total += 1
            message = m.message.replace("\n", " ")
            short = f"{message} (rule: {m.ruleId})"
            rel = path.relative_to(ROOT).as_posix()
            print(f"::warning file={rel}::{short}")

    print(f"LanguageTool findings: {total}")
    return 1 if total > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
