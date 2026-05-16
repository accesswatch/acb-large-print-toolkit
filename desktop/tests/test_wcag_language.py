from __future__ import annotations

from acb_large_print.wcag_language import analyze_text_for_wcag_language


def test_wcag_language_reports_missing_language_declaration():
    report = analyze_text_for_wcag_language("This is a short document.", stage="output")
    rule_ids = {f.rule_id for f in report.findings}
    assert "WCAG-LANG-DECLARATION" in rule_ids
    assert report.error_count >= 1


def test_wcag_language_accepts_yaml_lang_and_flags_ambiguous_link():
    text = "---\nlang: en\n---\n\n[click here](https://example.com)\n"
    report = analyze_text_for_wcag_language(text, stage="output")
    rule_ids = {f.rule_id for f in report.findings}
    assert "WCAG-LANG-DECLARATION" not in rule_ids
    assert "WCAG-DESCRIPTIVE-LINK-TEXT" in rule_ids
