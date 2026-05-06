from __future__ import annotations

from pathlib import Path

import pytest
from flask import Flask

from acb_large_print_web.app import create_app
import acb_large_print_web.routes.site_audit as site_audit_route


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


def test_site_audit_form_loads(client):
    res = client.get("/site-audit/")
    assert res.status_code == 200
    assert "Site Audit" in res.get_data(as_text=True)


def test_site_audit_requires_valid_source(client):
    res = client.post(
        "/site-audit/",
        data={
            "sources": "",
            "sitemap_url": "",
        },
    )
    assert res.status_code == 400
    body = res.get_data(as_text=True)
    assert "Provide at least one valid URL" in body


def test_site_audit_submit_with_stubbed_runner(client, monkeypatch: pytest.MonkeyPatch):
    def _fake_run_site_audit(*, run_id, base_dir, sources, options):
        return {
            "run_id": run_id,
            "elapsed_ms": 25,
            "totals": {
                "pages_total": 1,
                "scanned": 1,
                "failed": 0,
                "skipped": 0,
                "findings": 1,
            },
            "wcag_rollup": {"wcag2aa": 1},
            "pages": [
                {
                    "index": 1,
                    "url": "https://example.com",
                    "title": "Example Domain",
                    "result": "ok",
                    "finding_count": 1,
                }
            ],
        }

    monkeypatch.setattr(site_audit_route, "run_site_audit", _fake_run_site_audit)

    res = client.post(
        "/site-audit/",
        data={
            "sources": "https://example.com",
            "max_pages": "10",
            "crawl_links": "on",
        },
    )
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Run Summary" in body
    assert "Example Domain" in body


def test_site_audit_artifact_download(client, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    run_id = "11111111-1111-1111-1111-111111111111"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "summary.json").write_text('{"ok": true}', encoding="utf-8")
    (run_dir / "findings.csv").write_text("a,b\n", encoding="utf-8")
    (run_dir / "session.log").write_text("log\n", encoding="utf-8")
    (run_dir / "artifacts.zip").write_bytes(b"PK\x03\x04")

    monkeypatch.setattr(site_audit_route, "_runs_root", lambda: tmp_path / "runs")

    res = client.get(f"/site-audit/runs/{run_id}/download/summary")
    assert res.status_code == 200
    assert res.mimetype == "application/json"

    res_csv = client.get(f"/site-audit/runs/{run_id}/download/csv")
    assert res_csv.status_code == 200
    assert res_csv.mimetype in {"text/csv", "text/plain"}


def test_site_audit_feature_flag_404(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(site_audit_route, "_enabled", lambda: False)
    res = client.get("/site-audit/")
    assert res.status_code == 404
