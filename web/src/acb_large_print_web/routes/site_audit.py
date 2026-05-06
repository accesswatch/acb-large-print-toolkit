"""Site-audit route -- scan web pages for accessibility issues and export artifacts."""

from __future__ import annotations

from pathlib import Path
import uuid

from flask import Blueprint, Response, abort, current_app, render_template, request, send_file, url_for

from ..feature_flags import get_flag
from ..site_audit import SiteAuditOptions, get_run_dir, parse_input_urls, run_site_audit


site_audit_bp = Blueprint("site_audit", __name__)


def _enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_SITE_AUDIT", True))


def _runs_root() -> Path:
    root = Path(current_app.instance_path) / "site_audit_runs"
    root.mkdir(parents=True, exist_ok=True)
    return root


@site_audit_bp.route("/", methods=["GET"])
def site_audit_form():
    if not _enabled():
        abort(404)
    return render_template("site_audit_form.html")


@site_audit_bp.route("/", methods=["POST"])
def site_audit_submit():
    if not _enabled():
        abort(404)

    sources_raw = (request.form.get("sources") or "").strip()
    sitemap_raw = (request.form.get("sitemap_url") or "").strip()

    max_pages_raw = (request.form.get("max_pages") or "10").strip()
    try:
        max_pages = int(max_pages_raw)
    except ValueError:
        max_pages = 10
    max_pages = max(1, min(50, max_pages))

    crawl_links = bool(request.form.get("crawl_links"))
    include_subdomains = bool(request.form.get("include_subdomains"))
    force = bool(request.form.get("force"))

    urls = parse_input_urls(sources_raw, sitemap_raw)
    if not urls:
        return render_template(
            "site_audit_form.html",
            error="Provide at least one valid URL or sitemap URL.",
            sources=sources_raw,
            sitemap_url=sitemap_raw,
            max_pages=max_pages,
            crawl_links=crawl_links,
            include_subdomains=include_subdomains,
            force=force,
        ), 400

    run_id = str(uuid.uuid4())
    options = SiteAuditOptions(
        max_pages=max_pages,
        crawl_links=crawl_links,
        include_subdomains=include_subdomains,
        force=force,
    )
    summary = run_site_audit(
        run_id=run_id,
        base_dir=_runs_root(),
        sources=urls,
        options=options,
    )

    return render_template(
        "site_audit_result.html",
        summary=summary,
        run_id=run_id,
    )


@site_audit_bp.route("/runs/<run_id>", methods=["GET"])
def site_audit_run(run_id: str):
    if not _enabled():
        abort(404)
    run_dir = get_run_dir(_runs_root(), run_id)
    if run_dir is None:
        abort(404)
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        abort(404)
    import json

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return render_template("site_audit_result.html", summary=summary, run_id=run_id)


@site_audit_bp.route("/runs/<run_id>/download/<artifact>", methods=["GET"])
def site_audit_download(run_id: str, artifact: str):
    if not _enabled():
        abort(404)
    run_dir = get_run_dir(_runs_root(), run_id)
    if run_dir is None:
        abort(404)

    mapping = {
        "summary": (run_dir / "summary.json", "application/json", f"site-audit-{run_id}-summary.json"),
        "csv": (run_dir / "findings.csv", "text/csv", f"site-audit-{run_id}-findings.csv"),
        "log": (run_dir / "session.log", "text/plain", f"site-audit-{run_id}-session.log"),
        "zip": (run_dir / "artifacts.zip", "application/zip", f"site-audit-{run_id}-artifacts.zip"),
    }
    item = mapping.get(artifact)
    if item is None:
        abort(404)

    file_path, mime, filename = item
    if not file_path.exists():
        abort(404)
    return send_file(file_path, mimetype=mime, as_attachment=True, download_name=filename)


@site_audit_bp.route("/runs/<run_id>/summary", methods=["GET"])
def site_audit_summary_json(run_id: str):
    if not _enabled():
        abort(404)
    run_dir = get_run_dir(_runs_root(), run_id)
    if run_dir is None:
        abort(404)
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        abort(404)
    return Response(summary_path.read_text(encoding="utf-8"), mimetype="application/json")
