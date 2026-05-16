from __future__ import annotations

from acb_large_print.converter import CONVERTIBLE_EXTENSIONS
from acb_large_print.pandoc_converter import LIBREOFFICE_CONVERSIONS, PANDOC_INPUT_EXTENSIONS


def test_convertible_extensions_include_legacy_and_plain_text():
    assert ".doc" in CONVERTIBLE_EXTENSIONS
    assert ".ppt" in CONVERTIBLE_EXTENSIONS
    assert ".txt" in CONVERTIBLE_EXTENSIONS


def test_pandoc_pipeline_supports_plain_text_and_legacy_preconvert():
    assert ".txt" in PANDOC_INPUT_EXTENSIONS
    assert LIBREOFFICE_CONVERSIONS.get(".doc") == ".docx"
    assert LIBREOFFICE_CONVERSIONS.get(".ppt") == ".pptx"
