"""Changelog route -- renders the project changelog from CHANGELOG.md."""

from __future__ import annotations

import re
from pathlib import Path

from flask import Blueprint, render_template
from markupsafe import Markup

changelog_bp = Blueprint("changelog", __name__)


def _find_changelog() -> Path:
    """Locate CHANGELOG.md -- works both in dev (repo checkout) and Docker.

    Search order:
    1. CHANGELOG_PATH environment variable (explicit override)
    2. Traverse parents of this file looking for CHANGELOG.md (dev checkout)
    3. /app/CHANGELOG.md (Docker default from Dockerfile COPY)
    """
    import os

    env_path = os.environ.get("CHANGELOG_PATH")
    if env_path:
        return Path(env_path)

    # Walk up from this file to find repo root
    p = Path(__file__).resolve().parent
    for _ in range(8):
        candidate = p / "CHANGELOG.md"
        if candidate.is_file():
            return candidate
        p = p.parent

    # Docker fallback: COPY CHANGELOG.md /app/
    return Path("/app/CHANGELOG.md")


_CHANGELOG_PATH = _find_changelog()


def _md_to_html(md: str) -> str:
    """Minimal Markdown-to-HTML for the changelog.

    Handles headings (##, ###, ####), unordered lists, ordered lists,
    bold, inline code, links, horizontal rules, and paragraphs.
    No external dependency required.
    """
    lines = md.split("\n")
    html_parts: list[str] = []
    in_ul = False
    in_ol = False

    def _close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    def _inline(text: str) -> str:
        # Links: [text](url)
        text = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            r'<a href="\2">\1</a>',
            text,
        )
        # Bold: **text** or __text__
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
        # Inline code: `text`
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        # Em-dashes
        text = text.replace(" -- ", " \u2014 ")
        return text

    for line in lines:
        stripped = line.strip()

        # Blank line
        if not stripped:
            _close_lists()
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            _close_lists()
            html_parts.append("<hr>")
            continue

        # Headings
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            _close_lists()
            level = len(heading_match.group(1))
            text = _inline(heading_match.group(2))
            # Strip [x.y.z] version anchors for id generation
            slug = re.sub(r"[^\w\s-]", "", heading_match.group(2).lower())
            slug = re.sub(r"\s+", "-", slug.strip())
            html_parts.append(f'<h{level} id="{slug}">{text}</h{level}>')
            continue

        # Unordered list items
        ul_match = re.match(r"^[-*+]\s+(.+)$", stripped)
        if ul_match:
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"<li>{_inline(ul_match.group(1))}</li>")
            continue

        # Ordered list items
        ol_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ol_match:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            html_parts.append(f"<li>{_inline(ol_match.group(1))}</li>")
            continue

        # Continuation of list item (indented line)
        if (in_ul or in_ol) and line.startswith("  "):
            # Append to previous list item
            if html_parts and html_parts[-1].startswith("<li>"):
                html_parts[-1] = html_parts[-1][:-5] + " " + _inline(stripped) + "</li>"
            continue

        # Paragraph
        _close_lists()
        html_parts.append(f"<p>{_inline(stripped)}</p>")

    _close_lists()
    return "\n".join(html_parts)


@changelog_bp.route("/")
def changelog_page():
    """Render the changelog from CHANGELOG.md."""
    try:
        md_content = _CHANGELOG_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        md_content = "# Changelog\n\nChangelog file not found."

    html_content = Markup(_md_to_html(md_content))
    return render_template("changelog.html", changelog_html=html_content)
