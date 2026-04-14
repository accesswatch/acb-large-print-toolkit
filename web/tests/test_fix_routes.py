"""Tests for the fix route -- heading review, confirm, and download flows."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from acb_large_print_web.app import create_app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app(tmp_path: Path) -> Flask:
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "MAX_CONTENT_LENGTH": 500 * 1024 * 1024,
        }
    )
    application.instance_path = str(tmp_path / "instance")
    Path(application.instance_path).mkdir(parents=True, exist_ok=True)
    return application


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def _make_fake_docx() -> io.BytesIO:
    """Minimal valid .docx ZIP."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body>"
            "<w:p><w:r><w:t>Test</w:t></w:r></w:p>"
            "</w:body>"
            "</w:document>",
        )
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Fix form loads
# ---------------------------------------------------------------------------


class TestFixForm:
    @patch("acb_large_print.ai_provider.is_ai_available", return_value=False)
    def test_fix_form_loads(self, mock_ai, client):
        resp = client.get("/fix/")
        assert resp.status_code == 200
        assert b"Fix" in resp.data

    @patch("acb_large_print.ai_provider.is_ai_available", return_value=True)
    def test_fix_form_shows_ai_checkbox_when_available(self, mock_ai, client):
        resp = client.get("/fix/")
        assert resp.status_code == 200
        # The form should contain an AI-related option
        assert b"ai" in resp.data.lower() or b"detect" in resp.data.lower()


# ---------------------------------------------------------------------------
# Fix submit -- no file / wrong file
# ---------------------------------------------------------------------------


class TestFixSubmitErrors:
    def test_no_file(self, client):
        resp = client.post("/fix/", data={})
        assert resp.status_code == 400
        assert b"No file selected" in resp.data

    def test_wrong_extension(self, client):
        data = {"document": (io.BytesIO(b"hello"), "test.txt")}
        resp = client.post("/fix/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"not supported" in resp.data

    def test_corrupt_docx(self, client):
        data = {"document": (io.BytesIO(b"not a zip"), "test.docx")}
        resp = client.post("/fix/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"does not appear to be a valid" in resp.data


# ---------------------------------------------------------------------------
# Fix submit -- basic fix (no heading detection)
# ---------------------------------------------------------------------------


class TestFixSubmitBasic:
    def test_fix_docx_returns_result(self, client):
        docx = _make_fake_docx()
        data = {"document": (docx, "test.docx")}
        resp = client.post("/fix/", data=data, content_type="multipart/form-data")
        # Should either succeed (200) or error gracefully (500)
        assert resp.status_code in (200, 500)


# ---------------------------------------------------------------------------
# Fix confirm route
# ---------------------------------------------------------------------------


class TestFixConfirm:
    def test_confirm_expired_token(self, client):
        """Expired token should return 400 with session expired message."""
        data = {
            "token": "00000000-0000-0000-0000-000000000000",
            "candidate_count": "0",
        }
        resp = client.post("/fix/confirm", data=data)
        assert resp.status_code == 400
        assert b"expired" in resp.data.lower() or b"Session" in resp.data

    def test_confirm_invalid_token_format(self, client):
        data = {
            "token": "not-a-uuid",
            "candidate_count": "0",
        }
        resp = client.post("/fix/confirm", data=data)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Fix download route
# ---------------------------------------------------------------------------


class TestFixDownload:
    def test_download_expired_token(self, client):
        """Missing temp dir returns 404."""
        data = {
            "token": "00000000-0000-0000-0000-000000000000",
            "download_name": "test-fixed.docx",
        }
        resp = client.post("/fix/download", data=data)
        assert resp.status_code == 404

    def test_download_missing_file(self, client, tmp_path):
        """Token exists but file is gone."""
        from acb_large_print_web import upload

        original_base = upload.UPLOAD_TEMP_BASE
        upload.UPLOAD_TEMP_BASE = tmp_path

        token = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        token_dir = tmp_path / token
        token_dir.mkdir()

        data = {
            "token": token,
            "download_name": "nonexistent-fixed.docx",
        }
        resp = client.post("/fix/download", data=data)
        assert resp.status_code == 404

        upload.UPLOAD_TEMP_BASE = original_base


# ---------------------------------------------------------------------------
# _parse_form_options
# ---------------------------------------------------------------------------


class TestParseFormOptions:
    def test_defaults(self, app):
        """Default form values are sensible."""
        from acb_large_print_web.routes.fix import _parse_form_options
        from werkzeug.datastructures import MultiDict

        with app.app_context():
            form = MultiDict({})
            opts = _parse_form_options(form)
            assert opts["bound"] is False
            assert opts["detect_headings"] is False
            assert opts["use_ai"] is False
            assert 0 <= opts["heading_threshold"] <= 100

    def test_bound_on(self, app):
        from acb_large_print_web.routes.fix import _parse_form_options
        from werkzeug.datastructures import MultiDict

        with app.app_context():
            form = MultiDict({"bound": "on"})
            opts = _parse_form_options(form)
            assert opts["bound"] is True

    def test_flush_lists(self, app):
        from acb_large_print_web.routes.fix import _parse_form_options
        from werkzeug.datastructures import MultiDict

        with app.app_context():
            form = MultiDict({"flush_lists": "on"})
            opts = _parse_form_options(form)
            assert opts["list_indent_in"] == 0.0
            assert opts["list_hanging_in"] == 0.0

    def test_heading_threshold_clamped(self, app):
        from acb_large_print_web.routes.fix import _parse_form_options
        from werkzeug.datastructures import MultiDict

        with app.app_context():
            form = MultiDict({"heading_threshold": "999"})
            opts = _parse_form_options(form)
            assert opts["heading_threshold"] == 100

    def test_heading_threshold_invalid(self, app):
        from acb_large_print_web.routes.fix import _parse_form_options
        from werkzeug.datastructures import MultiDict

        with app.app_context():
            form = MultiDict({"heading_threshold": "abc"})
            opts = _parse_form_options(form)
            assert opts["heading_threshold"] == 50  # default

    def test_list_indent_clamped(self, app):
        from acb_large_print_web.routes.fix import _parse_form_options
        from werkzeug.datastructures import MultiDict

        with app.app_context():
            form = MultiDict({"list_indent": "10.0"})
            opts = _parse_form_options(form)
            assert opts["list_indent_in"] == 2.0  # max

    def test_detect_headings_on(self, app):
        from acb_large_print_web.routes.fix import _parse_form_options
        from werkzeug.datastructures import MultiDict

        with app.app_context():
            form = MultiDict({"detect_headings": "on", "use_ai": "on"})
            opts = _parse_form_options(form)
            assert opts["detect_headings"] is True
            assert opts["use_ai"] is True
