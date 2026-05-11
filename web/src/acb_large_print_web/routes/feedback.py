"""Feedback route -- collect and review user feedback (SQLAlchemy-backed)."""

import json
import hmac
import logging
import os
from datetime import UTC, datetime
from urllib import error as urlerror
from urllib import request as urlrequest

from flask import Blueprint, abort, current_app, render_template, request

from ..app import limiter
from ..db import db
from ..models import Feedback

feedback_bp = Blueprint("feedback", __name__)

log = logging.getLogger(__name__)


def _feedback_github_config() -> dict:
    """Return GitHub sync settings from environment variables."""
    token = os.environ.get("FEEDBACK_GITHUB_TOKEN", "").strip()
    repo = os.environ.get("FEEDBACK_GITHUB_REPO", "Community-Access/glow").strip()
    assignee = os.environ.get("FEEDBACK_GITHUB_ASSIGNEE", "accesswatch").strip()
    labels_raw = os.environ.get("FEEDBACK_GITHUB_LABELS", "feedback,user-feedback").strip()
    labels = [x.strip() for x in labels_raw.split(",") if x.strip()]
    return {
        "token": token,
        "repo": repo,
        "assignee": assignee,
        "labels": labels,
    }


def _create_feedback_issue(feedback_entry: Feedback) -> tuple[int | None, str | None, str | None]:
    """Create a GitHub issue for a feedback entry.

    Returns (issue_number, issue_url, error_message).
    """
    cfg = _feedback_github_config()
    if not cfg["token"]:
        return None, None, "FEEDBACK_GITHUB_TOKEN not configured"

    repo = cfg["repo"]
    timestamp_str = feedback_entry.timestamp.isoformat() if feedback_entry.timestamp else ""
    now_date = datetime.now(UTC).strftime("%Y-%m-%d")
    title = f"[Feedback] {feedback_entry.rating.capitalize()} | {feedback_entry.task or 'general'} | {now_date}"
    
    body_parts = [
        "## User Feedback Submission\n",
        f"- Feedback ID: `{feedback_entry.id}`\n",
        f"- Submitted at (UTC): `{timestamp_str}`\n",
        f"- Rating: `{feedback_entry.rating}`\n",
        f"- Task: `{feedback_entry.task or 'not specified'}`\n",
    ]
    
    if feedback_entry.name or feedback_entry.email:
        body_parts.append("- **Contributor contact:**\n")
        if feedback_entry.name:
            body_parts.append(f"  - Name: {feedback_entry.name}\n")
        if feedback_entry.email:
            body_parts.append(f"  - Email: {feedback_entry.email}\n")
    
    body_parts.extend([
        "\n### Message\n",
        f"{feedback_entry.message}\n",
        "\n---\n",
        "Source: GLOW web feedback form.",
    ])
    
    body = "".join(body_parts)
    
    payload = {
        "title": title,
        "body": body,
        "labels": cfg["labels"],
    }
    if cfg["assignee"]:
        payload["assignees"] = [cfg["assignee"]]

    req = urlrequest.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {cfg['token']}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "glow-feedback-sync",
        },
    )
    try:
        with urlrequest.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("number"), data.get("html_url"), None
    except urlerror.HTTPError as exc:
        details = ""
        try:
            details = exc.read().decode("utf-8")
        except Exception:
            details = str(exc)
        return None, None, f"GitHub API error: {exc.code} {details}"
    except Exception as exc:
        return None, None, f"GitHub sync failed: {exc}"


@feedback_bp.route("/", methods=["GET"])
def feedback_form():
    return render_template("feedback_form.html")


@feedback_bp.route("/", methods=["POST"])
@limiter.limit("10 per hour", error_message="Too many feedback submissions. Please try again later.")
def feedback_submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    rating = request.form.get("rating", "").strip()
    task = request.form.get("task", "").strip()
    message = request.form.get("message", "").strip()

    errors = []
    if not rating:
        errors.append("Please select a rating.")
    if not message:
        errors.append("Please enter your feedback.")
    if len(message) > 5000:
        errors.append("Feedback is limited to 5,000 characters.")
    if rating and rating not in ("excellent", "good", "fair", "poor"):
        errors.append("Invalid rating value.")
    if email and "@" not in email:
        errors.append("Please provide a valid email address.")

    if errors:
        return (
            render_template(
                "feedback_form.html",
                error=" ".join(errors),
                name=name,
                email=email,
                rating=rating,
                task=task,
                message=message,
            ),
            400,
        )

    issue_url = None
    try:
        feedback_entry = Feedback.create_from_form(name, email, rating, task, message)
        db.session.commit()

        issue_number, issue_url, sync_error = _create_feedback_issue(feedback_entry)
        feedback_entry.sync_github(issue_number, issue_url, sync_error)
        db.session.commit()

        if sync_error:
            log.warning("Feedback GitHub sync failed for id=%s: %s", feedback_entry.id, sync_error)
    except Exception:
        log.exception("Failed to save feedback")
        db.session.rollback()

    return render_template("feedback_thanks.html", issue_url=issue_url)


@feedback_bp.route("/review")
def feedback_review():
    """Display all feedback entries. Protected by FEEDBACK_PASSWORD env var."""
    expected = os.environ.get("FEEDBACK_PASSWORD", "")
    if not expected:
        abort(404)  # review disabled when no password is configured

    provided = request.args.get("key", "")
    if not provided or not hmac.compare_digest(provided, expected):
        abort(403)

    try:
        rows = db.session.execute(
            db.select(Feedback).order_by(Feedback.id.desc())
        ).scalars().all()
        
        entries = [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                "name": r.name,
                "email": r.email,
                "rating": r.rating,
                "task": r.task,
                "message": r.message,
                "github_issue_number": r.github_issue_number,
                "github_issue_url": r.github_issue_url,
                "github_sync_status": r.github_sync_status,
                "github_sync_error": r.github_sync_error,
            }
            for r in rows
        ]
    except Exception:
        log.exception("Failed to load feedback")
        entries = []

    response = render_template("feedback_review.html", entries=entries)
    resp = current_app.make_response(response)
    resp.headers["Cache-Control"] = "no-store"
    return resp
