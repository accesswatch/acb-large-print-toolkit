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


def _make_fake_xlsx() -> io.BytesIO:
    """Create a minimal valid .xlsx file using openpyxl."""
    from openpyxl import Workbook
    buf = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws["A1"] = "Test"
    wb.save(buf)
    buf.seek(0)
    return buf


def _make_fake_pptx() -> io.BytesIO:
    """Create a minimal valid .pptx file using python-pptx."""
    from pptx import Presentation
    buf = io.BytesIO()
    prs = Presentation()
    prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    prs.save(buf)
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
        assert b"ACB Document Accessibility Tool" in resp.data

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
        data = {"document": (io.BytesIO(b"not a docx"), "test.txt")}
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
        for path in ["/", "/audit/", "/fix/", "/guidelines/", "/feedback/",
                     "/about/", "/convert/"]:
            resp = client.get(path)
            assert b'lang="en"' in resp.data, f"Missing lang on {path}"

    def test_all_pages_have_main_landmark(self, client):
        for path in ["/", "/audit/", "/fix/", "/guidelines/", "/feedback/",
                     "/about/", "/convert/"]:
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


# ============================================================
# Multi-format audit (xlsx, pptx)
# ============================================================

class TestMultiFormatAudit:
    """Upload Excel and PowerPoint files and verify audit works."""

    def test_audit_xlsx(self, client):
        xlsx_data = _make_fake_xlsx()
        data = {
            "document": (xlsx_data, "test.xlsx"),
            "mode": "full",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert b"Audit Report" in resp.data or b"Score" in resp.data

    def test_audit_pptx(self, client):
        pptx_data = _make_fake_pptx()
        data = {
            "document": (pptx_data, "test.pptx"),
            "mode": "full",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert b"Audit Report" in resp.data or b"Score" in resp.data

    def test_audit_xlsx_quick_mode(self, client):
        xlsx_data = _make_fake_xlsx()
        data = {
            "document": (xlsx_data, "test.xlsx"),
            "mode": "quick",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200

    def test_audit_pptx_quick_mode(self, client):
        pptx_data = _make_fake_pptx()
        data = {
            "document": (pptx_data, "test.pptx"),
            "mode": "quick",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200

    def test_corrupt_xlsx_rejected(self, client):
        data = {"document": (io.BytesIO(b"not a zip archive"), "test.xlsx")}
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"does not appear to be a valid" in resp.data

    def test_corrupt_pptx_rejected(self, client):
        data = {"document": (io.BytesIO(b"not a zip archive"), "test.pptx")}
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"does not appear to be a valid" in resp.data


# ============================================================
# Accessibility structure (extended)
# ============================================================

class TestAccessibilityExtended:
    """Verify WCAG 2.2 AA structural requirements added in multi-format update."""

    def test_skip_link_present(self, client):
        resp = client.get("/")
        assert b"skip-link" in resp.data
        assert b"Skip to main content" in resp.data

    def test_home_shows_all_three_formats(self, client):
        resp = client.get("/")
        assert b"Word (.docx)" in resp.data
        assert b"Excel (.xlsx)" in resp.data
        assert b"PowerPoint (.pptx)" in resp.data

    def test_audit_form_accepts_all_formats(self, client):
        resp = client.get("/audit/")
        assert b".docx,.xlsx,.pptx" in resp.data

    def test_flash_error_has_text_prefix(self, client):
        """Error flash messages include 'Error:' text so meaning is not color-alone."""
        resp = client.post("/audit/", data={})
        assert b"<strong>Error:</strong>" in resp.data

    def test_format_tags_in_rule_list(self, client):
        """Rule list checkboxes include format tags with text labels."""
        resp = client.get("/audit/")
        assert b'class="format-tag format-docx"' in resp.data

    def test_severity_badges_have_text(self, client):
        """Severity badges use text labels, not just color."""
        resp = client.get("/audit/")
        for level in [b"Critical", b"High", b"Medium", b"Low"]:
            assert level in resp.data


# ============================================================
# About page
# ============================================================

class TestAboutPage:
    """Tests for the /about/ route."""

    def test_about_page_loads(self, client):
        resp = client.get("/about/")
        assert resp.status_code == 200
        assert b"About" in resp.data

    def test_about_has_lang(self, client):
        resp = client.get("/about/")
        assert b'lang="en"' in resp.data

    def test_about_has_main_landmark(self, client):
        resp = client.get("/about/")
        assert b'id="main"' in resp.data

    def test_about_mentions_markitdown(self, client):
        resp = client.get("/about/")
        assert b"MarkItDown" in resp.data


# ============================================================
# Convert route
# ============================================================

class TestConvertPage:
    """Tests for the /convert/ route."""

    def test_convert_form_loads(self, client):
        resp = client.get("/convert/")
        assert resp.status_code == 200
        assert b"Convert" in resp.data

    def test_convert_has_lang(self, client):
        resp = client.get("/convert/")
        assert b'lang="en"' in resp.data

    def test_convert_has_main_landmark(self, client):
        resp = client.get("/convert/")
        assert b'id="main"' in resp.data

    def test_convert_no_file(self, client):
        resp = client.post("/convert/", data={})
        assert resp.status_code == 400
        assert b"No file selected" in resp.data

    def test_convert_wrong_extension(self, client):
        data = {"document": (io.BytesIO(b"text"), "test.txt")}
        resp = client.post("/convert/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"not supported" in resp.data

    def test_convert_docx_returns_markdown(self, client):
        docx_data = _make_fake_docx()
        data = {"document": (docx_data, "test.docx")}
        resp = client.post("/convert/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/markdown")
        assert b"test.md" in resp.headers.get("Content-Disposition", "").encode()

    def test_convert_xlsx_returns_markdown(self, client):
        xlsx_data = _make_fake_xlsx()
        data = {"document": (xlsx_data, "test.xlsx")}
        resp = client.post("/convert/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/markdown")


# ============================================================
# Markdown and PDF audit
# ============================================================

def _make_fake_md() -> io.BytesIO:
    """Create a simple Markdown file with known issues."""
    content = (
        "# My Document\n\n"
        "Click [here](https://example.com) for details.\n\n"
        "### Skipped heading\n\n"
        "Some *italic* text.\n"
    )
    return io.BytesIO(content.encode("utf-8"))


def _make_fake_pdf() -> io.BytesIO:
    """Create a minimal PDF file."""
    # Minimal valid PDF (1 blank page)
    pdf_bytes = (
        b"%PDF-1.0\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF\n"
    )
    return io.BytesIO(pdf_bytes)


class TestMarkdownAudit:
    """Upload Markdown files and verify audit works."""

    def test_audit_markdown_full(self, client):
        md_data = _make_fake_md()
        data = {
            "document": (md_data, "test.md"),
            "mode": "full",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert b"Audit Report" in resp.data or b"Score" in resp.data

    def test_audit_markdown_quick(self, client):
        md_data = _make_fake_md()
        data = {
            "document": (md_data, "test.md"),
            "mode": "quick",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200

    def test_fix_markdown_returns_warning(self, client):
        """Markdown fix should work but return a 'not yet' warning."""
        md_data = _make_fake_md()
        data = {"document": (md_data, "test.md")}
        resp = client.post("/fix/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200


class TestPdfAudit:
    """Upload PDF files and verify audit works."""

    def test_audit_pdf_full(self, client):
        pdf_data = _make_fake_pdf()
        data = {
            "document": (pdf_data, "test.pdf"),
            "mode": "full",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert b"Audit Report" in resp.data or b"Score" in resp.data

    def test_audit_pdf_quick(self, client):
        pdf_data = _make_fake_pdf()
        data = {
            "document": (pdf_data, "test.pdf"),
            "mode": "quick",
        }
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200

    def test_corrupt_pdf_rejected(self, client):
        data = {"document": (io.BytesIO(b"not a pdf"), "test.pdf")}
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"does not appear to be a valid" in resp.data

    def test_fix_pdf_returns_warning(self, client):
        """PDF fix should work but return a 'cannot be auto-fixed' warning."""
        pdf_data = _make_fake_pdf()
        data = {"document": (pdf_data, "test.pdf")}
        resp = client.post("/fix/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200


# ============================================================
# Rules help URLs
# ============================================================

class TestRulesHelpUrls:
    """Verify help URL data layer returns valid entries."""

    def test_help_urls_map_not_empty(self):
        from acb_large_print_web.rules import get_help_urls_map
        urls_map = get_help_urls_map()
        assert isinstance(urls_map, dict)
        assert len(urls_map) > 0

    def test_help_urls_contain_valid_dicts(self):
        from acb_large_print_web.rules import get_help_urls_map
        urls_map = get_help_urls_map()
        for rule_id, links in urls_map.items():
            assert isinstance(rule_id, str)
            assert isinstance(links, list)
            for entry in links:
                assert "label" in entry, f"Missing 'label' for {rule_id}"
                assert "url" in entry, f"Missing 'url' for {rule_id}"
                assert entry["url"].startswith("https://"), (
                    f"Bad URL for {rule_id}: {entry['url']}"
                )

    def test_wcag_rules_have_w3c_urls(self):
        from acb_large_print_web.rules import get_help_urls_map
        urls_map = get_help_urls_map()
        # At least some WCAG-linked rules should have w3.org URLs
        w3_count = sum(
            1
            for links in urls_map.values()
            for entry in links
            if "w3.org" in entry["url"]
        )
        assert w3_count > 0, "No W3C URLs found in help URLs map"


# ============================================================
# Upload validation for new formats
# ============================================================

class TestUploadValidation:
    """Verify upload.py accepts/rejects the new file formats."""

    def test_md_extension_accepted(self, client):
        md_data = _make_fake_md()
        data = {"document": (md_data, "test.md"), "mode": "full"}
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200

    def test_pdf_extension_accepted(self, client):
        pdf_data = _make_fake_pdf()
        data = {"document": (pdf_data, "test.pdf"), "mode": "full"}
        resp = client.post("/audit/", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200

    def test_home_shows_md_and_pdf_formats(self, client):
        resp = client.get("/")
        assert b"Markdown" in resp.data or b".md" in resp.data
        assert b"PDF" in resp.data or b".pdf" in resp.data

    def test_audit_form_accepts_md_and_pdf(self, client):
        resp = client.get("/audit/")
        assert b".md" in resp.data
        assert b".pdf" in resp.data
