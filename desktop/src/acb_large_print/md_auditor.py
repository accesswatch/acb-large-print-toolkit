"""Audit Markdown files for ACB Large Print and WCAG accessibility compliance.

Checks heading hierarchy, emphasis violations, bare URLs, ambiguous links,
missing alt text, emoji, em-dashes, and table descriptions.

Optionally runs markdownlint-cli as a subprocess for structural checks.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from . import constants as C
from .auditor import AuditResult, Finding

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_ATX_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_ITALIC_SINGLE_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_ITALIC_UNDER_RE = re.compile(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_BARE_URL_RE = re.compile(r"(?<!\()\bhttps?://\S+(?!\))")
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]+\)")
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_TABLE_LINE_RE = re.compile(r"^\|.+\|$")
_TABLE_SEP_RE = re.compile(r"^\|[\s:|-]+\|$")
_EM_DASH_RE = re.compile(r"[\u2014\u2013]")
_EMOJI_RE = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols and pictographs
    "\U0001f680-\U0001f6ff"  # transport and map
    "\U0001f900-\U0001f9ff"  # supplemental
    "\U0001fa00-\U0001fa6f"  # chess/extended-A
    "\U0001fa70-\U0001faff"  # extended-A cont.
    "\U00002702-\U000027b0"  # dingbats
    "\U000024c2-\U0001f251"  # enclosed
    "]+",
    re.UNICODE,
)

_AMBIGUOUS_LINK_TEXTS = frozenset(
    {
        "click here",
        "here",
        "link",
        "read more",
        "learn more",
        "more",
        "this",
        "this link",
        "this page",
        "more info",
        "info",
    }
)


def audit_markdown(file_path: str | Path) -> AuditResult:
    """Audit a Markdown file for accessibility issues.

    Returns an AuditResult compatible with the existing audit pipeline.
    """
    file_path = Path(file_path)
    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    result = AuditResult(file_path=str(file_path))

    _check_headings(lines, result)
    _check_emphasis(lines, result)
    _check_links(lines, result)
    _check_images(lines, result)
    _check_emoji(lines, result)
    _check_em_dashes(lines, result)
    _check_tables(lines, result)

    return result


def _check_headings(lines: list[str], result: AuditResult) -> None:
    """Check heading hierarchy and multiple H1s."""
    levels: list[tuple[int, int]] = []  # (line_num, level)
    for i, line in enumerate(lines, 1):
        m = _ATX_HEADING_RE.match(line)
        if m:
            levels.append((i, len(m.group(1))))

    if not levels:
        return

    # Multiple H1s
    h1_count = sum(1 for _, lvl in levels if lvl == 1)
    if h1_count > 1:
        result.add(
            "MD-MULTIPLE-H1",
            f"Found {h1_count} H1 headings; document should have only one",
        )

    # Skipped levels
    for idx in range(1, len(levels)):
        prev_line, prev_lvl = levels[idx - 1]
        curr_line, curr_lvl = levels[idx]
        if curr_lvl > prev_lvl + 1:
            result.add(
                "MD-HEADING-HIERARCHY",
                f"Heading level skips from H{prev_lvl} to H{curr_lvl}",
                location=f"Line {curr_line}",
            )


def _check_emphasis(lines: list[str], result: AuditResult) -> None:
    """Check for italic and bold-as-emphasis violations."""
    for i, line in enumerate(lines, 1):
        # Skip headings, code blocks, links
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("```"):
            continue

        # Italic: *text* (not **bold**)
        for m in _ITALIC_SINGLE_RE.finditer(line):
            result.add(
                "MD-NO-ITALIC",
                f"Italic emphasis found: *{m.group(1)}*",
                location=f"Line {i}",
            )
        for m in _ITALIC_UNDER_RE.finditer(line):
            result.add(
                "MD-NO-ITALIC",
                f"Italic emphasis found: _{m.group(1)}_",
                location=f"Line {i}",
            )

        # Bold in body text (not headings)
        if not stripped.startswith("#"):
            for m in _BOLD_RE.finditer(line):
                # Only flag if the entire line isn't a heading
                result.add(
                    "MD-BOLD-EMPHASIS",
                    f"Bold used for emphasis: **{m.group(1)}**",
                    location=f"Line {i}",
                )


def _check_links(lines: list[str], result: AuditResult) -> None:
    """Check for bare URLs and ambiguous link text."""
    in_code_block = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Bare URLs (not inside markdown link syntax)
        cleaned = _MD_LINK_RE.sub("", line)
        cleaned = _MD_IMAGE_RE.sub("", cleaned)
        for m in _BARE_URL_RE.finditer(cleaned):
            result.add(
                "MD-BARE-URL",
                f"Bare URL should have descriptive link text: {m.group()[:60]}",
                location=f"Line {i}",
            )

        # Ambiguous link text
        for m in _MD_LINK_RE.finditer(line):
            text = m.group(1).strip().lower()
            if text in _AMBIGUOUS_LINK_TEXTS:
                result.add(
                    "MD-AMBIGUOUS-LINK",
                    f"Ambiguous link text: [{m.group(1)}]",
                    location=f"Line {i}",
                )


def _check_images(lines: list[str], result: AuditResult) -> None:
    """Check for images with missing or empty alt text."""
    for i, line in enumerate(lines, 1):
        for m in _MD_IMAGE_RE.finditer(line):
            alt = m.group(1).strip()
            if not alt:
                result.add(
                    "MD-MISSING-ALT-TEXT",
                    "Image has no alternative text",
                    location=f"Line {i}",
                )


def _check_emoji(lines: list[str], result: AuditResult) -> None:
    """Check for emoji characters that should be removed."""
    in_code_block = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        for m in _EMOJI_RE.finditer(line):
            result.add(
                "MD-NO-EMOJI",
                f"Emoji found: {m.group()}",
                location=f"Line {i}",
            )


def _check_em_dashes(lines: list[str], result: AuditResult) -> None:
    """Check for em-dashes and en-dashes."""
    in_code_block = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if _EM_DASH_RE.search(line):
            result.add(
                "MD-EM-DASH",
                "Em-dash or en-dash found; use a plain dash instead",
                location=f"Line {i}",
            )


def _check_tables(lines: list[str], result: AuditResult) -> None:
    """Check that tables have a preceding text description."""
    in_table = False
    table_start: int | None = None
    for i, line in enumerate(lines, 1):
        is_table_line = bool(_TABLE_LINE_RE.match(line.strip()))
        if is_table_line and not in_table:
            in_table = True
            table_start = i
            # Check the line before the table for descriptive text
            if i >= 2:
                prev = lines[i - 2].strip()
                if not prev or _TABLE_LINE_RE.match(prev) or _TABLE_SEP_RE.match(prev):
                    result.add(
                        "MD-TABLE-NO-DESCRIPTION",
                        "Table has no preceding text description",
                        location=f"Line {i}",
                    )
            else:
                result.add(
                    "MD-TABLE-NO-DESCRIPTION",
                    "Table at start of document has no preceding description",
                    location=f"Line {i}",
                )
        elif not is_table_line and in_table:
            in_table = False
            table_start = None


def run_markdownlint(file_path: str | Path) -> list[str]:
    """Run markdownlint-cli on a file and return raw output lines.

    Returns an empty list if markdownlint is not installed.
    """
    markdownlint = shutil.which("markdownlint")
    if not markdownlint:
        return []
    try:
        proc = subprocess.run(
            [markdownlint, str(file_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # markdownlint exits non-zero when issues are found
        output = proc.stdout.strip() or proc.stderr.strip()
        return output.splitlines() if output else []
    except (subprocess.TimeoutExpired, OSError):
        return []
