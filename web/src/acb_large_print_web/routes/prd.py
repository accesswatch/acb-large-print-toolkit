"""Product Requirements Document (PRD) route -- renders the PRD from prd.md."""

from __future__ import annotations

import re
from pathlib import Path

from flask import Blueprint, render_template
from markupsafe import Markup

prd_bp = Blueprint("prd", __name__)


def _find_prd() -> Path:
    """Locate prd.md -- works both in dev (repo checkout) and Docker.

    Search order:
    1. PRD_PATH environment variable (explicit override)
    2. Traverse parents of this file looking for prd.md (dev checkout)
    3. /app/prd.md (Docker default from Dockerfile COPY)
    """
    import os

    env_path = os.environ.get("PRD_PATH")
    if env_path:
        return Path(env_path)

    # Walk up from this file to find repo root
    p = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = p / "prd.md"
        if candidate.is_file():
            return candidate
        # Also check in docs/ subdirectory
        candidate = p / "docs" / "prd.md"
        if candidate.is_file():
            return candidate
        p = p.parent

    # Docker fallback: COPY docs/prd.md /app/
    return Path("/app/prd.md")


_PRD_PATH = _find_prd()


def _slugify_heading(text: str) -> str:
    """Create the same heading slug used by _md_to_html for anchor links."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"\s+", "-", slug.strip())


def _extract_section_links(md: str) -> list[tuple[str, str]]:
    """Extract level-2 PRD section headings to build a table of contents."""
    links: list[tuple[str, str]] = []
    for line in md.splitlines():
        match = re.match(r"^##\s+(.+)$", line.strip())
        if not match:
            continue
        heading_text = match.group(1).strip()
        links.append((heading_text, _slugify_heading(heading_text)))
    return links


def _md_to_html(md: str) -> str:
    """Minimal Markdown-to-HTML for the PRD.

    Handles headings (##, ###, ####), unordered lists, ordered lists,
    bold, inline code, links, horizontal rules, tables, and paragraphs.
    No external dependency required.
    """
    lines = md.split("\n")
    html_parts: list[str] = []
    in_ul = False
    in_ol = False
    in_table = False
    table_header_done = False

    def _close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    def _close_table() -> None:
        nonlocal in_table, table_header_done
        if in_table:
            html_parts.append("</tbody>")
            html_parts.append("</table>")
            in_table = False
            table_header_done = False

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
            if in_table:
                _close_table()
            _close_lists()
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            if in_table:
                _close_table()
            _close_lists()
            html_parts.append("<hr>")
            continue

        # Table separator (ignore, handled by table detection)
        if in_table and re.match(r"^\|.*\|$", stripped):
            if re.match(r"^\|\s*[-:]+\s*\|", stripped):
                table_header_done = True
                continue
            # Regular table row
            cols = [cell.strip() for cell in stripped.split("|")[1:-1]]
            if not table_header_done:
                html_parts.append("<thead><tr>")
                for col in cols:
                    html_parts.append(f"<th scope='col'>{_inline(col)}</th>")
                html_parts.append("</tr></thead><tbody>")
                table_header_done = True
            else:
                html_parts.append("<tr>")
                for col in cols:
                    html_parts.append(f"<td>{_inline(col)}</td>")
                html_parts.append("</tr>")
            continue

        # Start table
        if re.match(r"^\|.*\|$", stripped) and not in_table:
            _close_lists()
            in_table = True
            html_parts.append("<table>")
            cols = [cell.strip() for cell in stripped.split("|")[1:-1]]
            html_parts.append("<thead><tr>")
            for col in cols:
                html_parts.append(f"<th scope='col'>{_inline(col)}</th>")
            html_parts.append("</tr></thead><tbody>")
            table_header_done = True
            continue

        # Headings
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            if in_table:
                _close_table()
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
            if in_table:
                _close_table()
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
            if in_table:
                _close_table()
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
        if in_table:
            _close_table()
        _close_lists()
        html_parts.append(f"<p>{_inline(stripped)}</p>")

    if in_table:
        _close_table()
    _close_lists()
    return "\n".join(html_parts)


@prd_bp.route("/")
def prd_page():
    """Render the PRD from prd.md."""
    try:
        md_content = _PRD_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        md_content = "# Product Requirements Document\n\nPRD file not found."

    html_content = Markup(_md_to_html(md_content))
    section_links = _extract_section_links(md_content)
    return render_template(
        "prd.html",
        prd_html=html_content,
        section_links=section_links,
    )
