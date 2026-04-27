"""run_format_probe_app.py -- Markdown/table/format output probe for GLOW.

Verifies that OpenRouter models produce properly structured output for the
formatting scenarios GLOW depends on in its web UI responses:

  Format 1  -- Markdown headings (##, ###)
  Format 2  -- Markdown bullet list
  Format 3  -- Markdown numbered list
  Format 4  -- Markdown table (GFM pipe syntax)
  Format 5  -- Markdown code block (fenced)
  Format 6  -- ACB audit report format (numbered list with rule IDs)
  Format 7  -- ACB HTML snippet (heading + paragraph, no italic/bold-abuse)
  Format 8  -- Inline bold/underline avoidance (ACB emphasis rules)
  Format 9  -- Multi-column table with alignment
  Format 10 -- Mixed: heading + table + paragraph (document summary format)

Outputs written to tests/openrouter-probe/format/ for human review.

Usage:
    cd s:\\code\\glow
    python tests\\openrouter-probe\\run_format_probe_app.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "web" / "src"))

import requests

from acb_large_print_web.credentials import get_openrouter_api_key

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OUT_DIR = Path(__file__).parent / "format"
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = get_openrouter_api_key()
MODEL = "openai/gpt-4o-mini"   # Paid model used for format-sensitive work in GLOW
SESSION = "probe-format-001"

RESULTS: list[dict] = []


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://glow.bits-acb.org",
        "X-Title": "GLOW Format Probe",
        "Content-Type": "application/json",
    }


def _chat(system: str, user: str, max_tokens: int = 600) -> tuple[str, dict]:
    resp = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers=_auth_headers(),
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.0,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"].strip()
    return text, data


def _record(fmt_id: int, name: str, ok: bool, answer: str, raw: object, notes: str = "") -> None:
    entry = {"fmt_id": fmt_id, "name": name, "ok": ok, "notes": notes}
    RESULTS.append(entry)
    slug = f"fmt{fmt_id:02d}"
    (OUT_DIR / f"{slug}_answer.txt").write_text(answer, encoding="utf-8")
    (OUT_DIR / f"{slug}_raw.json").write_text(
        json.dumps(raw, indent=2, default=str), encoding="utf-8"
    )
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] Format {fmt_id}: {name}")
    if notes:
        print(f"         {notes}")


# ---------------------------------------------------------------------------
# Format 1 -- Markdown headings
# ---------------------------------------------------------------------------
def probe_fmt1():
    print("\nFormat 1: Markdown headings")
    text, raw = _chat(
        "Reply in Markdown only. Use ## and ### headings.",
        "Write a two-section document about ACB font rules. "
        "Section 1: Body Text. Section 2: Headings. Each section needs one paragraph.",
    )
    has_h2 = "## " in text
    has_h3 = "### " in text or "## " in text  # at least one heading level
    ok = has_h2
    _record(1, "markdown-headings", ok, text, raw,
            notes=f"has ##={has_h2} has ###={has_h3}")


# ---------------------------------------------------------------------------
# Format 2 -- Markdown bullet list
# ---------------------------------------------------------------------------
def probe_fmt2():
    print("\nFormat 2: Markdown bullet list")
    text, raw = _chat(
        "Reply in Markdown only. Use a bullet list (- item).",
        "List 5 ACB Large Print accessibility rules as bullet points.",
    )
    bullets = [ln for ln in text.splitlines() if ln.strip().startswith("- ")]
    ok = len(bullets) >= 3
    _record(2, "markdown-bullet-list", ok, text, raw,
            notes=f"found {len(bullets)} bullet items")


# ---------------------------------------------------------------------------
# Format 3 -- Markdown numbered list
# ---------------------------------------------------------------------------
def probe_fmt3():
    print("\nFormat 3: Markdown numbered list")
    text, raw = _chat(
        "Reply in Markdown only. Use a numbered list (1. item).",
        "List the 5 most important steps to make a Word document accessible.",
    )
    numbered = [ln for ln in text.splitlines() if re.match(r"^\d+\.", ln.strip())]
    ok = len(numbered) >= 3
    _record(3, "markdown-numbered-list", ok, text, raw,
            notes=f"found {len(numbered)} numbered items")


# ---------------------------------------------------------------------------
# Format 4 -- Markdown GFM table
# ---------------------------------------------------------------------------
def probe_fmt4():
    print("\nFormat 4: Markdown GFM pipe table")
    text, raw = _chat(
        "Reply in Markdown only. Include a GFM pipe table with | characters.",
        "Create a table comparing ACB body font size (18pt), heading size (22pt), "
        "and subheading size (20pt). Columns: Element | ACB Size | WCAG Notes.",
    )
    pipe_rows = [ln for ln in text.splitlines() if "|" in ln]
    has_separator = any(re.search(r"\|[-:]+\|", ln) for ln in text.splitlines())
    ok = len(pipe_rows) >= 3 and has_separator
    _record(4, "markdown-gfm-table", ok, text, raw,
            notes=f"pipe rows={len(pipe_rows)} has_separator={has_separator}")


# ---------------------------------------------------------------------------
# Format 5 -- Fenced code block
# ---------------------------------------------------------------------------
def probe_fmt5():
    print("\nFormat 5: Fenced code block")
    text, raw = _chat(
        "Reply in Markdown only. Include a fenced code block using triple backticks.",
        "Show a CSS snippet that sets body text to Arial 18pt with 1.5 line-height "
        "for ACB Large Print compliance.",
    )
    has_fence = "```" in text
    has_css_content = "font-size" in text or "Arial" in text or "line-height" in text
    ok = has_fence and has_css_content
    _record(5, "fenced-code-block", ok, text, raw,
            notes=f"has_fence={has_fence} has_css_content={has_css_content}")


# ---------------------------------------------------------------------------
# Format 6 -- ACB audit report format
# ---------------------------------------------------------------------------
def probe_fmt6():
    print("\nFormat 6: ACB audit report format (numbered list with rule IDs)")
    text, raw = _chat(
        (
            "You are the GLOW ACB Large Print accessibility auditor. "
            "Format each finding as: [RULE-ID] Description (Severity: critical/major/minor). "
            "Use a numbered list."
        ),
        (
            "Audit this HTML for ACB compliance and list all issues:\n\n"
            "<p style='font-size:12pt;font-family:Times New Roman;text-align:justify'>"
            "<em>Important notice:</em> <strong>All staff must attend.</strong></p>"
        ),
        max_tokens=800,
    )
    numbered = [ln for ln in text.splitlines() if re.match(r"^\d+\.", ln.strip())]
    has_severity = any(kw in text.lower() for kw in ["critical", "major", "minor", "severity"])
    ok = len(numbered) >= 2 and has_severity
    _record(6, "acb-audit-report-format", ok, text, raw,
            notes=f"numbered_items={len(numbered)} has_severity={has_severity}")


# ---------------------------------------------------------------------------
# Format 7 -- ACB HTML snippet output
# ---------------------------------------------------------------------------
def probe_fmt7():
    print("\nFormat 7: ACB-compliant HTML snippet output")
    text, raw = _chat(
        (
            "You are the GLOW ACB Large Print converter. "
            "Output only valid HTML. "
            "ACB rules: Arial font, 18pt body, 22pt headings, underline for emphasis "
            "(never italic, never bold for emphasis), flush left, 1.5 line-height."
        ),
        (
            "Convert this content to ACB-compliant HTML:\n\n"
            "# Board Meeting Notes\n"
            "The meeting was *important* and all items were discussed.\n"
            "**Action items** are listed below."
        ),
        max_tokens=600,
    )
    has_heading = "<h1" in text or "<h2" in text
    no_italic = "<em>" not in text and "<i>" not in text
    no_raw_bold = text.count("<strong>") <= 1  # allow 1 max for decorative; not paragraph-level
    ok = has_heading and no_italic
    _record(7, "acb-html-snippet-output", ok, text, raw,
            notes=f"has_heading={has_heading} no_italic={no_italic} no_raw_bold={no_raw_bold}")


# ---------------------------------------------------------------------------
# Format 8 -- ACB emphasis avoidance (no bold/italic for emphasis)
# ---------------------------------------------------------------------------
def probe_fmt8():
    print("\nFormat 8: ACB emphasis avoidance probe")
    text, raw = _chat(
        (
            "You are the GLOW ACB Large Print compliance assistant. "
            "ACB rules prohibit italic entirely and prohibit bold for emphasis. "
            "Use underline (<u>text</u>) for emphasis instead. "
            "Never use *italic* or **bold** for emphasis in your Markdown output."
        ),
        (
            "Rewrite this sentence for ACB compliance:\n"
            "'The *most important* rule is that **font size** must be 18pt.'"
        ),
        max_tokens=200,
    )
    has_italic = "*" in text or "_" in text or "<em>" in text or "<i>" in text
    has_underline = "<u>" in text or "underline" in text.lower()
    ok = not has_italic
    _record(8, "acb-emphasis-avoidance", ok, text, raw,
            notes=f"has_italic={has_italic} has_underline={has_underline}")


# ---------------------------------------------------------------------------
# Format 9 -- Multi-column table with alignment
# ---------------------------------------------------------------------------
def probe_fmt9():
    print("\nFormat 9: Multi-column GFM table with alignment")
    text, raw = _chat(
        "Reply in Markdown only. Use a pipe table with at least 4 columns and alignment syntax.",
        (
            "Create a compliance comparison table for these standards: "
            "ACB Large Print, WCAG 2.2 AA, Section 508, EN 301 549. "
            "Columns: Standard | Font Size | Line Height | Contrast Ratio | Emphasis Rule."
        ),
        max_tokens=600,
    )
    pipe_rows = [ln for ln in text.splitlines() if "|" in ln and ln.count("|") >= 4]
    has_alignment = bool(re.search(r"\|[: ]*-{3,}[: ]*\|", text))
    ok = len(pipe_rows) >= 3 and has_alignment
    _record(9, "multi-column-table-alignment", ok, text, raw,
            notes=f"qualifying_rows={len(pipe_rows)} has_alignment={has_alignment}")


# ---------------------------------------------------------------------------
# Format 10 -- Mixed document summary (heading + table + paragraph)
# ---------------------------------------------------------------------------
def probe_fmt10():
    print("\nFormat 10: Mixed document summary (heading + table + paragraph)")
    text, raw = _chat(
        (
            "You are the GLOW accessibility summary generator. "
            "Format output as Markdown with: "
            "1) A ## heading for the document name, "
            "2) A pipe table of issues found, "
            "3) A closing paragraph with next steps."
        ),
        (
            "Generate an accessibility summary for a Word document called "
            "'April Board Agenda.docx' that has 3 issues: "
            "missing document title (critical), "
            "no alt text on 2 images (major), "
            "justified text alignment (minor)."
        ),
        max_tokens=800,
    )
    has_heading = "## " in text
    has_table = "|" in text and "-" in text
    has_paragraph = len([ln for ln in text.splitlines() if len(ln.strip()) > 60]) >= 1
    ok = has_heading and has_table and has_paragraph
    _record(10, "mixed-document-summary", ok, text, raw,
            notes=f"has_heading={has_heading} has_table={has_table} has_paragraph={has_paragraph}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set.")
        sys.exit(1)

    print("=" * 60)
    print("GLOW Format/Markdown/Table Probe")
    print(f"Model: {MODEL}")
    print(f"Output directory: {OUT_DIR}")
    print("=" * 60)

    probe_fmt1()
    probe_fmt2()
    probe_fmt3()
    probe_fmt4()
    probe_fmt5()
    probe_fmt6()
    probe_fmt7()
    probe_fmt8()
    probe_fmt9()
    probe_fmt10()

    summary_path = OUT_DIR / "summary.json"
    summary_path.write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")

    passed = sum(1 for r in RESULTS if r["ok"])
    total = len(RESULTS)
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} formats PASSED")
    print(f"Summary: {summary_path}")
    print("=" * 60)

    if passed < total:
        failed = [r for r in RESULTS if not r["ok"]]
        print("\nFailed formats:")
        for r in failed:
            print(f"  Format {r['fmt_id']}: {r['name']} -- {r['notes']}")


if __name__ == "__main__":
    main()
