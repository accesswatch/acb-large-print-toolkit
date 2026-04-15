"""Template generation profile tests."""

from __future__ import annotations

from pathlib import Path
import tempfile
import zipfile

import pytest
from docx import Document

from acb_large_print import constants as C
from acb_large_print.template import create_template


def _normal_style(path: Path):
    # python-docx cannot open template content types directly, so clone the
    # package as a .docx view for style inspection.
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        docx_path = Path(tmp.name)
    try:
        with zipfile.ZipFile(str(path), "r") as zin:
            with zipfile.ZipFile(str(docx_path), "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "[Content_Types].xml":
                        data = data.replace(
                            b"application/vnd.openxmlformats-officedocument"
                            b".wordprocessingml.template.main+xml",
                            b"application/vnd.openxmlformats-officedocument"
                            b".wordprocessingml.document.main+xml",
                        )
                    zout.writestr(item, data)
        doc = Document(str(docx_path))
        return doc.styles["Normal"]
    finally:
        docx_path.unlink(missing_ok=True)


def test_create_template_acb_profile_defaults(tmp_path: Path):
    out = tmp_path / "acb-template.dotx"

    create_template(out, include_sample=False, standards_profile=C.StandardsProfile.ACB_2025.value)

    normal = _normal_style(out)
    assert normal.font.name == C.FONT_FAMILY
    assert normal.paragraph_format.line_spacing == pytest.approx(C.LINE_SPACING_MULTIPLE)


def test_create_template_aph_profile_overrides(tmp_path: Path):
    out = tmp_path / "aph-template.dotx"

    create_template(out, include_sample=False, standards_profile=C.StandardsProfile.APH_SUBMISSION.value)

    normal = _normal_style(out)
    assert normal.font.name == C.APH_ACCEPTED_FONT_FAMILIES[0]
    assert normal.paragraph_format.line_spacing == pytest.approx(C.APH_LINE_SPACING_RECOMMENDED)


def test_create_template_combined_profile_keeps_acb_defaults(tmp_path: Path):
    out = tmp_path / "combined-template.dotx"

    create_template(out, include_sample=False, standards_profile=C.StandardsProfile.COMBINED_STRICT.value)

    normal = _normal_style(out)
    assert normal.font.name == C.FONT_FAMILY
    assert normal.paragraph_format.line_spacing == pytest.approx(C.LINE_SPACING_MULTIPLE)
