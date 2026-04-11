"""Tests for the ACB Large Print web application."""

from __future__ import annotations

import io
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web.app import create_app


@pytest.fixture()
def app(tmp_path: Path) -> Flask:
    """Create a test Flask application with a temporary instance folder."""
    application = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
    })
    application.instance_path = str(tmp_path / "instance")
    Path(application.instance_path).mkdir(parents=True, exist_ok=True)
    return application


@pytest.fixture()
def client(app: Flask):
    """Flask test client."""
    return app.test_client()


def _make_fake_docx() -> io.BytesIO:
    """Create a minimal valid .docx file (ZIP with correct structure)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        # Minimal [Content_Types].xml
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
        # Minimal relationships
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/>'
            "</Relationships>",
        )
        # Minimal document.xml
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


# ============================================================
# Smoke tests -- every page loads
# ============================================================

class TestPageLoads:
    """Every GET endpoint should return 200."""

    def test_home(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"ACB Large Print Tool" in resp.data

    def test_audit_form(self, client):
        resp = client.get("/audit/")
        assert resp.status_code == 200
        assert b"Audit" in resp.data

    def test_fix_form(self, client):
        resp = client.get("/fix/")
        assert resp.status_code == 200
        assert b"Fix" in resp.data

    def test_template_form(self, client):
        resp = client.get("/template/")
        assert resp.status_code == 200
        assert b"Template" in resp.data

    def test_export_form(self, client):
        resp = client.get("/export/")
        assert resp.status_code == 200
        assert b"Export" in resp.data

    def test_guidelines(self, client):
        resp = client.get("/guidelines/")
        assert resp.status_code == 200
        assert b"Guidelines" in resp.data

    def test_feedback_form(self, client):
        resp = client.get("/feedback/")
        assert resp.status_code == 200
        assert b"Feedback" in resp.data

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.data == b"ok"


# ============================================================
# Error handling
# ============================================================

class TestErrors:
    def test_404(self, client):
        resp = client.get("/nonexistent-page/")
        assert resp.status_code == 404
        assert b"Page Not Found" in resp.data

    def test_audit_no_file(self, client):
        resp = client.post("/audit/", data={})
        assert resp.status_code == 400
        assert b"No file selected" in resp.data

    def test_fix_no_file(self, client):
        resp = client.post("/fix/", data={})
        assert resp.status_code == 400
        assert b"No file selected" in resp.data

    def test_audit_wrong_extension(self, client):
        data = {"document": (io.BytesIO(b"not a docx"), "test.txt")}
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"not supported" in resp.data

    def test_fix_wrong_extension(self, client):
        data = {"document": (io.BytesIO(b"not a docx"), "test.pdf")}
        resp = client.post("/fix/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"not supported" in resp.data

    def test_audit_corrupt_file(self, client):
        """A .docx that isn't a valid ZIP should be rejected."""
        data = {"document": (io.BytesIO(b"not a zip archive"), "test.docx")}
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"does not appear to be a valid" in resp.data


# ============================================================
# Feedback
# ============================================================

class TestFeedback:
    def test_submit_feedback(self, app, client):
        resp = client.post("/feedback/", data={
            "rating": "good",
            "task": "audit",
            "message": "Works great!",
        })
        assert resp.status_code == 200
        assert b"Thank You" in resp.data

        # Verify it was saved in SQLite
        db_path = Path(app.instance_path) / "feedback.db"
        assert db_path.exists()
        conn = sqlite3.connect(str(db_path))
        rows = conn.execute("SELECT rating, message FROM feedback").fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0][0] == "good"
        assert rows[0][1] == "Works great!"

    def test_submit_feedback_missing_rating(self, client):
        resp = client.post("/feedback/", data={
            "message": "Some feedback",
        })
        assert resp.status_code == 400
        assert b"select a rating" in resp.data

    def test_submit_feedback_missing_message(self, client):
        resp = client.post("/feedback/", data={
            "rating": "excellent",
        })
        assert resp.status_code == 400
        assert b"enter your feedback" in resp.data

    def test_review_no_password_configured(self, client):
        """Review returns 404 when FEEDBACK_PASSWORD is not set."""
        resp = client.get("/feedback/review")
        assert resp.status_code == 404

    def test_review_wrong_password(self, app, client):
        app.config["FEEDBACK_PASSWORD"] = "secret123"
        import os
        os.environ["FEEDBACK_PASSWORD"] = "secret123"
        resp = client.get("/feedback/review?key=wrong")
        assert resp.status_code == 403
        os.environ.pop("FEEDBACK_PASSWORD", None)

    def test_review_correct_password(self, app, client):
        import os
        os.environ["FEEDBACK_PASSWORD"] = "secret123"
        # Submit a feedback entry first
        client.post("/feedback/", data={
            "rating": "excellent",
            "task": "fix",
            "message": "Love it",
        })
        resp = client.get("/feedback/review?key=secret123")
        assert resp.status_code == 200
        assert b"Love it" in resp.data
        assert b"Excellent" in resp.data
        os.environ.pop("FEEDBACK_PASSWORD", None)


# ============================================================
# Accessibility checks on rendered HTML
# ============================================================

class TestAccessibility:
    """Basic structural accessibility checks on rendered pages."""

    def test_all_pages_have_lang(self, client):
        for path in ["/", "/audit/", "/fix/", "/guidelines/", "/feedback/"]:
            resp = client.get(path)
            assert b'lang="en"' in resp.data, f"Missing lang on {path}"

    def test_all_pages_have_main_landmark(self, client):
        for path in ["/", "/audit/", "/fix/", "/guidelines/", "/feedback/"]:
            resp = client.get(path)
            assert b'id="main"' in resp.data, f"Missing main landmark on {path}"

    def test_nav_has_aria_label(self, client):
        resp = client.get("/")
        assert b"aria-label" in resp.data

    def test_footer_has_role(self, client):
        resp = client.get("/")
        assert b'role="contentinfo"' in resp.data

    def test_bits_renamed_to_solutions(self, client):
        resp = client.get("/")
        assert b"Solutions" in resp.data
        assert b"Specialists" not in resp.data


# ============================================================
# Upload + audit integration (with real docx)
# ============================================================

class TestAuditIntegration:
    def test_audit_full_mode(self, client):
        docx_data = _make_fake_docx()
        data = {
            "document": (docx_data, "test.docx"),
            "mode": "full",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert b"Audit Report" in resp.data or b"Score" in resp.data

    def test_audit_quick_mode(self, client):
        docx_data = _make_fake_docx()
        data = {
            "document": (docx_data, "test.docx"),
            "mode": "quick",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200


# ============================================================
# Template generation
# ============================================================

class TestTemplateGeneration:
    def test_generate_template(self, client):
        resp = client.post("/template/", data={
            "title": "Test Template",
        })
        # Should return 200 with a result page or a download
        assert resp.status_code == 200
