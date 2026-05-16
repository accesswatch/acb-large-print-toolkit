from __future__ import annotations

from types import SimpleNamespace

import acb_large_print.pdf_forms as pdf_forms


class _FakeWidget:
    def __init__(
        self,
        *,
        name: str,
        field_type: int,
        value: str = "",
        label: str = "",
        alt: str = "",
        options: list[str] | None = None,
        xref: int = 1,
    ):
        self.field_name = name
        self.field_type = field_type
        self.field_value = value
        self.field_label = label
        self.field_name_alt = alt
        self.choice_values = options or []
        self.xref = xref


class _FakePage:
    def __init__(self, widgets: list[_FakeWidget]):
        self._widgets = widgets

    def widgets(self):
        return list(self._widgets)


class _FakeDoc:
    def __init__(self, pages: list[_FakePage], *, is_form_pdf: int = 1, xfa=False):
        self._pages = pages
        self.page_count = len(pages)
        self.is_form_pdf = is_form_pdf
        self._xfa = xfa

    def __getitem__(self, idx: int):
        return self._pages[idx]

    def close(self):
        return None

    def pdf_catalog(self):
        return 1

    def xref_get_key(self, _catalog, key):
        if key == "XFA" and self._xfa:
            return ("name", "/XFA")
        return ("null", "")


def _patch_fitz(monkeypatch, fake_doc: _FakeDoc):
    fake_fitz = SimpleNamespace(
        PDF_WIDGET_TYPE_TEXT=1,
        PDF_WIDGET_TYPE_CHECKBOX=2,
        PDF_WIDGET_TYPE_RADIOBUTTON=3,
        PDF_WIDGET_TYPE_LISTBOX=4,
        PDF_WIDGET_TYPE_COMBOBOX=5,
        PDF_WIDGET_TYPE_SIGNATURE=6,
        PDF_WIDGET_TYPE_BUTTON=7,
        open=lambda _path: fake_doc,
    )
    monkeypatch.setattr(pdf_forms, "HAS_PYMUPDF", True)
    monkeypatch.setattr(pdf_forms, "fitz", fake_fitz)


def test_inspect_pdf_form_supported_acroform(monkeypatch):
    doc = _FakeDoc(
        [
            _FakePage(
                [
                    _FakeWidget(
                        name="firstName",
                        field_type=1,
                        label="First Name",
                        xref=11,
                    ),
                    _FakeWidget(
                        name="agreeTerms",
                        field_type=2,
                        value="Yes",
                        xref=12,
                    ),
                ]
            )
        ]
    )
    _patch_fitz(monkeypatch, doc)

    out = pdf_forms.inspect_pdf_form("sample.pdf")
    assert out["classification"]["class"] == "acroform_supported"
    assert out["classification"]["supported"] is True
    assert out["summary"]["total_fields"] == 2
    assert out["summary"]["field_type_counts"]["text"] == 1
    assert out["summary"]["field_type_counts"]["checkbox"] == 1


def test_inspect_pdf_form_xfa_unsupported(monkeypatch):
    doc = _FakeDoc([], xfa=True)
    _patch_fitz(monkeypatch, doc)

    out = pdf_forms.inspect_pdf_form("xfa.pdf")
    assert out["classification"]["class"] == "xfa_unsupported"
    assert out["classification"]["supported"] is False
    assert "xfa_form_not_supported" in out["warnings"]


def test_inspect_pdf_form_no_fields_is_unsupported(monkeypatch):
    doc = _FakeDoc([_FakePage([])])
    _patch_fitz(monkeypatch, doc)

    out = pdf_forms.inspect_pdf_form("flat.pdf")
    assert out["classification"]["class"] == "static_or_flattened"
    assert out["summary"]["total_fields"] == 0


def test_inspect_pdf_form_signature_blocks_roundtrip(monkeypatch):
    doc = _FakeDoc([_FakePage([_FakeWidget(name="sig1", field_type=6)])])
    _patch_fitz(monkeypatch, doc)

    out = pdf_forms.inspect_pdf_form("signed.pdf")
    assert out["classification"]["class"] == "signed_or_signature_fields"
    assert out["classification"]["round_trip_support"] == "limited"

