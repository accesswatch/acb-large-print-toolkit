"""Tests for alt-text handling in Word auditor."""

from __future__ import annotations

from lxml import etree

from acb_large_print.auditor import AuditResult, _check_alt_text


class _FakeElement:
    def __init__(self, body):
        self.body = body


class _FakeDoc:
    def __init__(self, body):
        self.element = _FakeElement(body)


def _make_body_with_vml_shape(*, alt_attr: str | None) -> etree._Element:
    nsmap = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "v": "urn:schemas-microsoft-com:vml",
    }
    body = etree.Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body", nsmap=nsmap)
    shape = etree.SubElement(body, "{urn:schemas-microsoft-com:vml}shape")
    shape.set("id", "shape-1")
    if alt_attr is not None:
        shape.set("alt", alt_attr)
    return body


def test_vml_shape_with_missing_alt_is_flagged() -> None:
    doc = _FakeDoc(_make_body_with_vml_shape(alt_attr=None))
    result = AuditResult(file_path="test.docx")

    _check_alt_text(doc, result)

    assert any(f.rule_id == "ACB-MISSING-ALT-TEXT" for f in result.findings)


def test_vml_shape_with_empty_alt_is_treated_as_decorative() -> None:
    doc = _FakeDoc(_make_body_with_vml_shape(alt_attr=""))
    result = AuditResult(file_path="test.docx")

    _check_alt_text(doc, result)

    assert not any(f.rule_id == "ACB-MISSING-ALT-TEXT" for f in result.findings)
