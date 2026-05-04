"""Tests for PDF table-aware Markdown extraction in converter.py.

These tests use mocks so they run without PyMuPDF or a real PDF file.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from acb_large_print.converter import (
    _bbox_overlaps_table,
    _format_table_as_markdown,
    _pdf_to_markdown_with_tables,
    convert_to_markdown,
)


# ---------------------------------------------------------------------------
# _bbox_overlaps_table
# ---------------------------------------------------------------------------


class TestBboxOverlapsTable:
    def test_fully_inside_returns_true(self):
        text_bbox = (10, 10, 50, 30)
        table_bbox = (5, 5, 60, 40)
        assert _bbox_overlaps_table(text_bbox, table_bbox) is True

    def test_completely_outside_returns_false(self):
        text_bbox = (0, 0, 10, 10)
        table_bbox = (100, 100, 200, 200)
        assert _bbox_overlaps_table(text_bbox, table_bbox) is False

    def test_small_overlap_under_threshold_returns_false(self):
        # 1-unit overlap, text block is 10x10 = 100 area, overlap area = 10
        # 10/100 = 10% < 40% threshold
        text_bbox = (0, 0, 10, 10)
        table_bbox = (9, 0, 100, 10)
        assert _bbox_overlaps_table(text_bbox, table_bbox) is False

    def test_majority_overlap_returns_true(self):
        # text block (0,0)-(10,10) = 100 area
        # table covers (0,0)-(10,7) = 70 area overlap → 70% > 40%
        text_bbox = (0, 0, 10, 10)
        table_bbox = (0, 0, 10, 7)
        assert _bbox_overlaps_table(text_bbox, table_bbox) is True

    def test_zero_height_text_block_returns_false(self):
        text_bbox = (0, 5, 10, 5)  # zero height
        table_bbox = (0, 0, 100, 100)
        assert _bbox_overlaps_table(text_bbox, table_bbox) is False


# ---------------------------------------------------------------------------
# _format_table_as_markdown
# ---------------------------------------------------------------------------


def _make_table_mock(rows: list[list[str | None]], bbox=(0, 0, 100, 50)):
    tbl = MagicMock()
    tbl.extract.return_value = rows
    tbl.bbox = bbox
    return tbl


class TestFormatTableAsMarkdown:
    def test_basic_two_row_table(self):
        tbl = _make_table_mock([["Name", "Age"], ["Alice", "30"], ["Bob", "25"]])
        result = _format_table_as_markdown(tbl)
        lines = result.splitlines()
        assert lines[0] == "| Name | Age |"
        assert lines[1] == "| --- | --- |"
        assert lines[2] == "| Alice | 30 |"
        assert lines[3] == "| Bob | 25 |"

    def test_pipe_in_cell_is_escaped(self):
        tbl = _make_table_mock([["A | B", "C"], ["x", "y"]])
        result = _format_table_as_markdown(tbl)
        assert "A \\| B" in result

    def test_none_cell_rendered_as_empty(self):
        tbl = _make_table_mock([["Col1", None], ["val", None]])
        result = _format_table_as_markdown(tbl)
        assert "| Col1 |  |" in result

    def test_empty_table_returns_empty_string(self):
        tbl = _make_table_mock([])
        assert _format_table_as_markdown(tbl) == ""

    def test_irregular_row_lengths_padded(self):
        # Row 0 has 3 cols, row 1 has 2 – should pad row 1
        tbl = _make_table_mock([["A", "B", "C"], ["x", "y"]])
        result = _format_table_as_markdown(tbl)
        lines = result.splitlines()
        assert lines[0] == "| A | B | C |"
        assert lines[2] == "| x | y |  |"

    def test_newline_in_cell_normalised_to_space(self):
        tbl = _make_table_mock([["Header"], ["line1\nline2"]])
        result = _format_table_as_markdown(tbl)
        assert "line1 line2" in result


# ---------------------------------------------------------------------------
# _pdf_to_markdown_with_tables
# ---------------------------------------------------------------------------


class TestPdfToMarkdownWithTables:
    def test_returns_none_when_fitz_unavailable(self, tmp_path: Path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        with patch.dict("sys.modules", {"fitz": None}):
            result = _pdf_to_markdown_with_tables(pdf)

        assert result is None

    def test_returns_none_when_fitz_open_fails(self, tmp_path: Path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"not a pdf")

        fitz_mod = MagicMock()
        fitz_mod.open.side_effect = RuntimeError("bad pdf")

        with patch.dict("sys.modules", {"fitz": fitz_mod}):
            result = _pdf_to_markdown_with_tables(pdf)

        assert result is None

    def test_plain_text_page_no_tables(self, tmp_path: Path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        page_mock = MagicMock()
        tbl_finder_mock = MagicMock()
        tbl_finder_mock.tables = []
        page_mock.find_tables.return_value = tbl_finder_mock
        page_mock.get_text.return_value = "Hello world"

        doc_mock = MagicMock()
        doc_mock.__iter__ = MagicMock(return_value=iter([page_mock]))
        doc_mock.close = MagicMock()

        fitz_mod = MagicMock()
        fitz_mod.open.return_value = doc_mock

        with patch.dict("sys.modules", {"fitz": fitz_mod}):
            result = _pdf_to_markdown_with_tables(pdf)

        assert result == "Hello world"

    def test_page_with_table_produces_pipe_table(self, tmp_path: Path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        table_mock = _make_table_mock(
            [["Name", "Score"], ["Alice", "95"], ["Bob", "82"]],
            bbox=(0, 50, 200, 150),
        )

        page_mock = MagicMock()
        tbl_finder_mock = MagicMock()
        tbl_finder_mock.tables = [table_mock]
        page_mock.find_tables.return_value = tbl_finder_mock
        # No text blocks outside the table
        page_mock.get_text.return_value = []

        doc_mock = MagicMock()
        doc_mock.__iter__ = MagicMock(return_value=iter([page_mock]))
        doc_mock.close = MagicMock()

        fitz_mod = MagicMock()
        fitz_mod.open.return_value = doc_mock

        with patch.dict("sys.modules", {"fitz": fitz_mod}):
            result = _pdf_to_markdown_with_tables(pdf)

        assert result is not None
        assert "| Name | Score |" in result
        assert "| --- | --- |" in result
        assert "| Alice | 95 |" in result
        assert "| Bob | 82 |" in result

    def test_text_inside_table_bbox_is_not_duplicated(self, tmp_path: Path):
        """Text blocks that overlap with a table's bbox must be excluded."""
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        table_mock = _make_table_mock(
            [["Col"], ["val"]],
            bbox=(0, 0, 100, 100),
        )

        page_mock = MagicMock()
        tbl_finder_mock = MagicMock()
        tbl_finder_mock.tables = [table_mock]
        page_mock.find_tables.return_value = tbl_finder_mock

        # A text block that is fully inside the table bbox (should be skipped)
        inside_block = (10, 10, 90, 90, "table cell text", 0, 0)
        # A text block outside the table bbox (should be included)
        outside_block = (0, 200, 100, 220, "paragraph below table", 1, 0)
        page_mock.get_text.return_value = [inside_block, outside_block]

        doc_mock = MagicMock()
        doc_mock.__iter__ = MagicMock(return_value=iter([page_mock]))
        doc_mock.close = MagicMock()

        fitz_mod = MagicMock()
        fitz_mod.open.return_value = doc_mock

        with patch.dict("sys.modules", {"fitz": fitz_mod}):
            result = _pdf_to_markdown_with_tables(pdf)

        assert result is not None
        assert "table cell text" not in result
        assert "paragraph below table" in result


# ---------------------------------------------------------------------------
# convert_to_markdown – PDF path integration
# ---------------------------------------------------------------------------


class TestConvertToMarkdownPdfPath:
    def test_uses_pymupdf_tables_when_available(self, tmp_path: Path):
        """convert_to_markdown() should use _pdf_to_markdown_with_tables() for PDFs."""
        pdf = tmp_path / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        expected_md = "| A | B |\n| --- | --- |\n| 1 | 2 |"

        with patch(
            "acb_large_print.converter._pdf_to_markdown_with_tables",
            return_value=expected_md,
        ) as mock_fn:
            out_path, text = convert_to_markdown(pdf, tmp_path / "report.md")

        mock_fn.assert_called_once_with(pdf)
        assert text == expected_md
        assert out_path.read_text(encoding="utf-8") == expected_md

    def test_falls_back_to_markitdown_when_pymupdf_returns_none(
        self, tmp_path: Path, monkeypatch
    ):
        """If _pdf_to_markdown_with_tables returns None, MarkItDown must be used."""
        import acb_large_print.converter as conv_mod

        pdf = tmp_path / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        fallback_text = "Fallback text from MarkItDown"

        # Patch _pdf_to_markdown_with_tables to simulate PyMuPDF being absent
        monkeypatch.setattr(conv_mod, "_pdf_to_markdown_with_tables", lambda p: None)

        # Patch MarkItDown to return a predictable result
        fake_result = SimpleNamespace(text_content=fallback_text)
        fake_md_instance = MagicMock()
        fake_md_instance.convert.return_value = fake_result
        FakeMarkItDown = MagicMock(return_value=fake_md_instance)

        with patch.dict("sys.modules", {"markitdown": MagicMock(MarkItDown=FakeMarkItDown)}):
            out_path, text = conv_mod.convert_to_markdown(pdf, tmp_path / "report.md")

        assert text == fallback_text
        assert out_path.read_text(encoding="utf-8") == fallback_text
