"""Tests for v2.7.0 features:

- :mod:`acb_large_print_web.report_cache` extensions (findings + PDF cache)
- :mod:`acb_large_print_web.csv_export` (findings -> CSV bytes)
- ``audit.shared_report_csv``  (GET /audit/share/<token>/csv)
- ``audit.shared_report_pdf``  (GET /audit/share/<token>/pdf)
- ``audit.audit_from_convert`` (POST /audit/from-convert) error paths
- CSS guard: no ``outline: none`` regression in shipped stylesheets
"""

from __future__ import annotations

import re
import time
import uuid
from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web.app import create_app
from acb_large_print_web import csv_export, report_cache


# ---------------------------------------------------------------------------
# Fixtures (mirror conftest pattern in test_app.py)
# ---------------------------------------------------------------------------


@pytest.fixture()
def app(tmp_path: Path) -> Flask:
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "MAX_CONTENT_LENGTH": 50 * 1024 * 1024,
        }
    )
    application.instance_path = str(tmp_path / "instance")
    Path(application.instance_path).mkdir(parents=True, exist_ok=True)
    return application


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def _new_share_token() -> str:
    """Return a fresh UUID4 string acceptable to report_cache._UUID_RE."""
    return str(uuid.uuid4())


def _seed_share(token: str, *, html: str = "<html><body>Test</body></html>",
                findings_data: dict | None = None) -> None:
    """Seed the share cache with HTML and (optionally) findings JSON."""
    report_cache.save_report(token, html)
    if findings_data is not None:
        report_cache.save_findings_data(token, findings_data)


def _sample_findings_data() -> dict:
    return {
        "filename": "demo report.docx",
        "doc_format": "docx",
        "score": 78,
        "grade": "C",
        "profile_label": "ACB 2025",
        "mode_label": "Full audit",
        "findings": [
            {
                "severity": "high",
                "rule_id": "DOCX-MISSING-ALT",
                "message": "Image 1 has no alt text",
                "location": "Page 2",
                "acb_reference": "ACB 4.2",
                "auto_fixable": True,
                "help_urls": [{"label": "Microsoft", "url": "https://example.com/alt"}],
            },
            {
                "severity": "low",
                "rule_id": "DOCX-FONT-SIZE",
                "message": "Body text smaller than 18pt",
                "location": "Section 3",
                "acb_reference": "ACB 1.1",
                "auto_fixable": False,
                "help_urls": [],
            },
        ],
    }


# ---------------------------------------------------------------------------
# report_cache extensions
# ---------------------------------------------------------------------------


class TestReportCacheFindings:
    def test_save_and_load_findings_data_roundtrips(self):
        token = _new_share_token()
        _seed_share(token, findings_data=_sample_findings_data())
        loaded = report_cache.load_findings_data(token)
        assert loaded is not None
        assert loaded["filename"] == "demo report.docx"
        assert loaded["score"] == 78
        assert len(loaded["findings"]) == 2

    def test_load_findings_data_rejects_bad_token(self):
        assert report_cache.load_findings_data("not-a-uuid") is None
        assert report_cache.load_findings_data("") is None

    def test_load_findings_data_returns_none_when_missing(self):
        # Valid UUID syntax but never seeded
        token = _new_share_token()
        assert report_cache.load_findings_data(token) is None

    def test_save_findings_data_silently_skips_when_share_dir_missing(self):
        # No save_report() was called, so share_dir does not exist.
        token = _new_share_token()
        report_cache.save_findings_data(token, {"foo": "bar"})  # must not raise
        assert report_cache.load_findings_data(token) is None

    def test_load_findings_data_expires(self, tmp_path, monkeypatch):
        token = _new_share_token()
        _seed_share(token, findings_data=_sample_findings_data())

        # Simulate clock moving past TTL by rewriting expires.txt.
        share_dir = report_cache._share_dir(token)
        (share_dir / "expires.txt").write_text(str(time.time() - 1), encoding="utf-8")

        assert report_cache.load_findings_data(token) is None
        # Expired entry should also have been cleaned up.
        assert not share_dir.exists()


class TestReportCachePDF:
    def test_save_and_load_pdf_roundtrips(self):
        token = _new_share_token()
        _seed_share(token)
        report_cache.save_pdf(token, b"%PDF-fake-bytes")
        assert report_cache.load_pdf(token) == b"%PDF-fake-bytes"

    def test_load_pdf_rejects_bad_token(self):
        assert report_cache.load_pdf("not-a-uuid") is None

    def test_load_pdf_returns_none_when_missing(self):
        token = _new_share_token()
        _seed_share(token)
        # No save_pdf yet
        assert report_cache.load_pdf(token) is None

    def test_save_pdf_silently_skips_when_share_dir_missing(self):
        token = _new_share_token()
        report_cache.save_pdf(token, b"x")  # must not raise
        assert report_cache.load_pdf(token) is None


# ---------------------------------------------------------------------------
# csv_export
# ---------------------------------------------------------------------------


class TestCsvExport:
    def test_findings_to_csv_bytes_has_utf8_bom_and_preamble(self):
        data = _sample_findings_data()
        csv_bytes = csv_export.findings_to_csv_bytes(
            data["findings"],
            filename=data["filename"],
            doc_format=data["doc_format"],
            score=data["score"],
            grade=data["grade"],
            profile_label=data["profile_label"],
            mode_label=data["mode_label"],
        )
        # UTF-8 BOM so Excel opens UTF-8 cleanly
        assert csv_bytes[:3] == b"\xef\xbb\xbf"
        text = csv_bytes.decode("utf-8-sig")
        # Comment preamble at top
        assert text.lstrip().startswith("# filename,")
        assert "demo report.docx" in text
        assert "ACB 2025" in text

    def test_findings_to_csv_bytes_columns_and_values(self):
        data = _sample_findings_data()
        csv_bytes = csv_export.findings_to_csv_bytes(
            data["findings"],
            filename=data["filename"],
            doc_format=data["doc_format"],
            score=data["score"],
            grade=data["grade"],
            profile_label=data["profile_label"],
            mode_label=data["mode_label"],
        )
        text = csv_bytes.decode("utf-8-sig")
        # auto_fixable rendered as yes/no
        assert "yes" in text
        assert "no" in text
        # rule ids and severities present
        assert "DOCX-MISSING-ALT" in text
        assert "DOCX-FONT-SIZE" in text
        assert "high" in text
        assert "low" in text
        # help_urls joined as "label: url"
        assert "Microsoft: https://example.com/alt" in text

    def test_findings_to_csv_bytes_handles_empty_list(self):
        csv_bytes = csv_export.findings_to_csv_bytes(
            [],
            filename="empty.docx",
            doc_format="docx",
            score=100,
            grade="A",
            profile_label="ACB 2025",
            mode_label="Full audit",
        )
        text = csv_bytes.decode("utf-8-sig")
        # Header preamble present even when no findings
        assert "# filename," in text
        # Column header row from CSV_COLUMNS still emitted
        assert "severity" in text and "rule_id" in text

    def test_safe_filename_stem_strips_unsafe_chars(self):
        assert csv_export.safe_filename_stem("My File / Report") == "My_File__Report" or \
            re.fullmatch(r"[A-Za-z0-9._-]+", csv_export.safe_filename_stem("My File / Report"))
        assert csv_export.safe_filename_stem("") == "audit-findings"
        assert csv_export.safe_filename_stem("../../etc/passwd") not in ("", None)
        # No path separators leak through
        assert "/" not in csv_export.safe_filename_stem("../../etc/passwd")
        assert "\\" not in csv_export.safe_filename_stem("..\\..\\evil")


# ---------------------------------------------------------------------------
# shared_report_csv route
# ---------------------------------------------------------------------------


class TestSharedReportCsv:
    def test_csv_route_serves_cached_findings(self, client):
        token = _new_share_token()
        _seed_share(token, findings_data=_sample_findings_data())
        resp = client.get(f"/audit/share/{token}/csv")
        assert resp.status_code == 200
        assert resp.mimetype == "text/csv"
        # Filename derived from cached `filename` stem, sanitised
        cd = resp.headers.get("Content-Disposition", "")
        assert "demo" in cd  # safe_filename_stem keeps "demo" or "demo_report"
        assert cd.endswith('-findings.csv"')
        body = resp.data.decode("utf-8-sig")
        assert "DOCX-MISSING-ALT" in body
        assert "# filename," in body

    def test_csv_route_404_for_unknown_token(self, client):
        resp = client.get(f"/audit/share/{_new_share_token()}/csv")
        assert resp.status_code == 404

    def test_csv_route_404_for_malformed_token(self, client):
        resp = client.get("/audit/share/not-a-uuid/csv")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# shared_report_pdf route
# ---------------------------------------------------------------------------


class TestSharedReportPdf:
    def test_pdf_route_returns_cached_pdf_without_weasyprint(self, client):
        # Pre-seed report.pdf so the route never imports WeasyPrint.
        token = _new_share_token()
        _seed_share(token, findings_data=_sample_findings_data())
        report_cache.save_pdf(token, b"%PDF-1.4\nfake\n")
        resp = client.get(f"/audit/share/{token}/pdf")
        assert resp.status_code == 200
        assert resp.mimetype == "application/pdf"
        assert resp.data.startswith(b"%PDF")
        cd = resp.headers.get("Content-Disposition", "")
        assert cd.endswith('-audit-report.pdf"')

    def test_pdf_route_404_for_unknown_token(self, client):
        resp = client.get(f"/audit/share/{_new_share_token()}/pdf")
        assert resp.status_code == 404

    def test_pdf_route_503_when_weasyprint_missing(self, client, monkeypatch):
        # Cached HTML present but no cached PDF, and WeasyPrint import fails.
        token = _new_share_token()
        _seed_share(token)

        import builtins

        real_import = builtins.__import__

        def _fake_import(name, *args, **kwargs):
            if name == "weasyprint":
                raise ImportError("weasyprint not installed (test stub)")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _fake_import)
        resp = client.get(f"/audit/share/{token}/pdf")
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Passphrase-protected shares (added in [Unreleased])
# ---------------------------------------------------------------------------


class TestSharePassphrase:
    def test_set_and_verify_passphrase(self):
        token = _new_share_token()
        _seed_share(token)
        assert report_cache.set_share_passphrase(token, "open sesame!")
        assert report_cache.share_requires_passphrase(token)
        assert report_cache.verify_share_passphrase(token, "open sesame!")
        assert not report_cache.verify_share_passphrase(token, "wrong")

    def test_unset_share_does_not_require(self):
        token = _new_share_token()
        _seed_share(token)
        assert not report_cache.share_requires_passphrase(token)
        # No passphrase configured -> any input is treated as success.
        assert report_cache.verify_share_passphrase(token, "")

    def test_set_passphrase_rejects_empty_or_missing_share(self):
        assert not report_cache.set_share_passphrase(_new_share_token(), "x")
        token = _new_share_token()
        _seed_share(token)
        assert not report_cache.set_share_passphrase(token, "")

    def test_protected_share_returns_unlock_form(self, client):
        token = _new_share_token()
        _seed_share(token)
        report_cache.set_share_passphrase(token, "letmein")
        resp = client.get(f"/audit/share/{token}")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "Unlock shared audit report" in body
        assert "name=\"share_passphrase\"" in body

    def test_protected_share_unlocks_with_correct_passphrase(self, client):
        token = _new_share_token()
        _seed_share(token, html="<html><body>SECRET REPORT</body></html>")
        report_cache.set_share_passphrase(token, "letmein")
        resp = client.post(
            f"/audit/share/{token}",
            data={"share_passphrase": "letmein"},
        )
        assert resp.status_code == 200
        assert b"SECRET REPORT" in resp.data

    def test_protected_share_rejects_wrong_passphrase(self, client):
        token = _new_share_token()
        _seed_share(token, html="<html><body>SECRET REPORT</body></html>")
        report_cache.set_share_passphrase(token, "letmein")
        resp = client.post(
            f"/audit/share/{token}",
            data={"share_passphrase": "nope"},
        )
        assert resp.status_code == 401
        assert b"SECRET REPORT" not in resp.data
        assert b"Incorrect passphrase" in resp.data

    def test_protected_csv_requires_passphrase_via_query(self, client):
        token = _new_share_token()
        _seed_share(token, findings_data=_sample_findings_data())
        report_cache.set_share_passphrase(token, "letmein")
        # Without ?p= the CSV endpoint serves the unlock form with 401.
        resp_locked = client.get(f"/audit/share/{token}/csv")
        assert resp_locked.status_code == 401
        # With correct ?p= the actual CSV is served.
        resp_ok = client.get(f"/audit/share/{token}/csv?p=letmein")
        assert resp_ok.status_code == 200
        assert resp_ok.mimetype.startswith("text/csv")


# ---------------------------------------------------------------------------
# Quick Start handoff: prefill audit/convert forms with an existing upload
# ---------------------------------------------------------------------------


def _seed_upload_session(filename: str = "demo.docx",
                         payload: bytes = b"PK\x03\x04 fake docx") -> str:
    """Create an upload session under UPLOAD_TEMP_BASE and return the token."""
    from acb_large_print_web.upload import UPLOAD_TEMP_BASE
    token = _new_share_token()
    session_dir = UPLOAD_TEMP_BASE / token
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / filename).write_bytes(payload)
    return token


class TestQuickStartHandoff:
    def test_audit_form_prefills_when_token_resolves(self, client):
        token = _seed_upload_session("acb-handoff.docx")
        resp = client.get(f"/audit/?token={token}")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "Ready to audit" in body
        assert "acb-handoff.docx" in body
        assert f'value="{token}"' in body

    def test_audit_form_falls_back_when_token_invalid(self, client):
        resp = client.get(f"/audit/?token={_new_share_token()}")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "Ready to audit" not in body
        # Standard upload UI is shown.
        assert 'name="document"' in body

    def test_convert_form_prefills_when_token_resolves(self, client):
        token = _seed_upload_session("convert-handoff.docx")
        resp = client.get(f"/convert/?token={token}")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "Ready to convert" in body
        assert "convert-handoff.docx" in body
        assert f'value="{token}"' in body




# ---------------------------------------------------------------------------
# audit_from_convert error paths (happy path needs a converter, tested elsewhere)
# ---------------------------------------------------------------------------


class TestAuditFromConvertErrors:
    def test_from_convert_expired_token_renders_error(self, client):
        # No upload happened -> get_temp_dir returns None
        resp = client.post(
            "/audit/from-convert",
            data={"token": _new_share_token(), "download_name": "anything.html"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert b"session has expired" in resp.data.lower() or \
            b"please upload" in resp.data.lower()

    def test_from_convert_missing_token_renders_error(self, client):
        resp = client.post(
            "/audit/from-convert",
            data={"download_name": "something.docx"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# CSS guard: no `outline: none` / `outline: 0` in shipped stylesheets.
# This protects the global :focus-visible ring shipped in v2.7.0.
# ---------------------------------------------------------------------------


class TestCssFocusGuard:
    def test_no_outline_none_in_static_css(self):
        static_dir = Path(__file__).resolve().parent.parent / "src" / \
            "acb_large_print_web" / "static"
        offenders: list[str] = []
        pattern = re.compile(r"outline\s*:\s*(none|0|0px|transparent)\b", re.IGNORECASE)
        # The standard `:focus:not(:focus-visible)` recipe is allowed because
        # `:focus-visible` then provides the keyboard focus indicator.
        in_allowed_block = False
        for css in static_dir.glob("*.css"):
            text = css.read_text(encoding="utf-8")
            depth = 0
            allow_until_depth = -1
            for lineno, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if ":focus:not(:focus-visible)" in stripped and "{" in stripped:
                    in_allowed_block = True
                    allow_until_depth = depth
                if "{" in stripped:
                    depth += stripped.count("{")
                if "}" in stripped:
                    depth -= stripped.count("}")
                    if in_allowed_block and depth <= allow_until_depth:
                        in_allowed_block = False
                if pattern.search(line) and not in_allowed_block:
                    offenders.append(f"{css.name}:{lineno}: {line.strip()}")
        assert not offenders, (
            "Found focus-suppressing outline rules in static CSS. "
            "These break the global :focus-visible ring shipped in v2.7.0:\n  "
            + "\n  ".join(offenders)
        )
