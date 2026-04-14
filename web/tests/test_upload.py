"""Tests for the file upload validation and temp directory management."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

from acb_large_print_web.upload import (
    ALLOWED_EXTENSIONS,
    CONVERT_EXTENSIONS,
    UploadError,
    cleanup_token,
    get_temp_dir,
    validate_upload,
)

# ---------------------------------------------------------------------------
# validate_upload
# ---------------------------------------------------------------------------


class TestValidateUpload:
    def _file(self, content: bytes, filename: str) -> FileStorage:
        return FileStorage(stream=io.BytesIO(content), filename=filename)

    def test_none_file_raises(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)
        with pytest.raises(UploadError, match="No file selected"):
            validate_upload(None)

    def test_empty_filename_raises(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)
        f = FileStorage(stream=io.BytesIO(b"data"), filename="")
        with pytest.raises(UploadError, match="No file selected"):
            validate_upload(f)

    def test_unsupported_extension_raises(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)
        f = self._file(b"data", "test.exe")
        with pytest.raises(UploadError, match="not supported"):
            validate_upload(f)

    def test_valid_docx_returns_token_and_path(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)

        # Build minimal zip to pass the PK check
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("test.txt", "content")
        buf.seek(0)

        f = FileStorage(stream=buf, filename="report.docx")
        token, path = validate_upload(f)
        assert token
        assert path.suffix == ".docx"
        assert path.exists()

    def test_corrupt_docx_raises(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)
        f = self._file(b"not a zip", "bad.docx")
        with pytest.raises(UploadError, match="does not appear to be a valid"):
            validate_upload(f)

    def test_corrupt_pdf_raises(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)
        f = self._file(b"not a pdf", "bad.pdf")
        with pytest.raises(UploadError, match="does not appear to be a valid"):
            validate_upload(f)

    def test_valid_md_no_magic_check(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)
        f = self._file(b"# Hello World\n\nSome content.", "readme.md")
        token, path = validate_upload(f)
        assert path.suffix == ".md"
        assert path.exists()

    def test_custom_allowed_extensions(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)
        f = self._file(b"data", "test.rst")
        with pytest.raises(UploadError):
            validate_upload(f)  # .rst not in ALLOWED_EXTENSIONS
        # But with custom extensions it works
        f2 = self._file(b"data", "test.rst")
        token, path = validate_upload(f2, allowed_extensions={".rst"})
        assert path.suffix == ".rst"


# ---------------------------------------------------------------------------
# get_temp_dir
# ---------------------------------------------------------------------------


class TestGetTempDir:
    def test_invalid_token_format(self):
        assert get_temp_dir("not-a-uuid") is None

    def test_empty_token(self):
        assert get_temp_dir("") is None

    def test_nonexistent_dir(self):
        assert get_temp_dir("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee") is None

    def test_valid_token(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)
        token = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        (tmp_path / token).mkdir()
        result = get_temp_dir(token)
        assert result is not None
        assert result.is_dir()


# ---------------------------------------------------------------------------
# cleanup_token
# ---------------------------------------------------------------------------


class TestCleanupToken:
    def test_cleanup_removes_dir(self, tmp_path, monkeypatch):
        import acb_large_print_web.upload as mod

        monkeypatch.setattr(mod, "UPLOAD_TEMP_BASE", tmp_path)
        token = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        token_dir = tmp_path / token
        token_dir.mkdir()
        (token_dir / "test.docx").write_bytes(b"data")

        cleanup_token(token)
        assert not token_dir.exists()

    def test_cleanup_invalid_token_no_crash(self):
        cleanup_token("not-a-valid-uuid")  # should not raise


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestUploadConstants:
    def test_allowed_extensions_has_all_formats(self):
        assert ".docx" in ALLOWED_EXTENSIONS
        assert ".xlsx" in ALLOWED_EXTENSIONS
        assert ".pptx" in ALLOWED_EXTENSIONS
        assert ".md" in ALLOWED_EXTENSIONS
        assert ".pdf" in ALLOWED_EXTENSIONS
        assert ".epub" in ALLOWED_EXTENSIONS

    def test_convert_extensions_superset(self):
        assert ALLOWED_EXTENSIONS.issubset(CONVERT_EXTENSIONS)
        assert ".rst" in CONVERT_EXTENSIONS
        assert ".html" in CONVERT_EXTENSIONS
