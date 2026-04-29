"""Feature parity tests for Markdown rules inspired by extCheck."""

from __future__ import annotations

from pathlib import Path

from acb_large_print.md_auditor import audit_markdown


def _audit_text(tmp_path: Path, text: str):
    path = tmp_path / "sample.md"
    path.write_text(text, encoding="utf-8")
    result = audit_markdown(path)
    return {f.rule_id for f in result.findings}


def test_missing_yaml_author_and_description(tmp_path: Path) -> None:
    rule_ids = _audit_text(
        tmp_path,
        """---
title: Sample
lang: en
---

# Heading
Body.
""",
    )

    assert "MD-YAML-MISSING-AUTHOR" in rule_ids
    assert "MD-YAML-MISSING-DESCRIPTION" in rule_ids


def test_link_rules_for_empty_and_url_as_text(tmp_path: Path) -> None:
    rule_ids = _audit_text(
        tmp_path,
        """# Links

[](https://example.com)
[https://example.com](https://example.com)
""",
    )

    assert "MD-EMPTY-LINK-TEXT" in rule_ids
    assert "MD-URL-AS-LINK-TEXT" in rule_ids


def test_heading_and_section_structure_rules(tmp_path: Path) -> None:
    long_body = "\n\n".join(f"Paragraph {i}." for i in range(1, 22))
    rule_ids = _audit_text(
        tmp_path,
        f"""{long_body}

## Repeated
Text.

## Repeated
More text.
""",
    )

    assert "MD-DUPLICATE-HEADING-TEXT" in rule_ids
    assert "MD-LONG-SECTION-WITHOUT-HEADING" in rule_ids


def test_no_headings_detected_for_substantial_content(tmp_path: Path) -> None:
    body = "\n\n".join(f"Paragraph {i}." for i in range(1, 8))
    rule_ids = _audit_text(tmp_path, body)

    assert "MD-NO-HEADINGS" in rule_ids


def test_raw_html_and_formatting_parity_rules(tmp_path: Path) -> None:
    rule_ids = _audit_text(
        tmp_path,
        """# Formatting

**This whole line is bold**

Line one with trailing spaces.   



Paragraph with inline bullet like this: item • detail.

<div>Container</div>
<span>Inline span</span>
<font>Legacy</font>
<center>Centered</center>
<br>
""",
    )

    assert "MD-ENTIRE-LINE-BOLDED" in rule_ids
    assert "MD-EXCESSIVE-TRAILING-SPACES" in rule_ids
    assert "MD-EXCESSIVE-BLANK-LINES" in rule_ids
    assert "MD-FAKE-INLINE-BULLET" in rule_ids
    assert "MD-RAW-BR-TAG" in rule_ids
    assert "MD-RAW-HTML-GENERIC-CONTAINER" in rule_ids
    assert "MD-RAW-HTML-PRESENTATIONAL" in rule_ids
