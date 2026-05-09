"""Feedback route -- collect and review user feedback (SQLite-backed)."""

import json
import hmac
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

from flask import Blueprint, abort, current_app, render_template, request

from ..app import limiter

feedback_bp = Blueprint("feedback", __name__)

log = logging.getLogger(__name__)


def _get_db_path() -> Path:
    """Return the path to the feedback SQLite database."""
    instance_path = Path(current_app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)
    return instance_path / "feedback.db"


def _get_db() -> sqlite3.Connection:
    """Open (and auto-create) the feedback database."""
    db_path = _get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")  # safe for concurrent reads
    conn.execute(
        "CREATE TABLE IF NOT EXISTS feedback ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  timestamp TEXT NOT NULL,"
        "  name TEXT,"
        "  email TEXT,"
        "  rating TEXT NOT NULL,"
        "  task TEXT,"
        "  message TEXT NOT NULL,"
        "  github_issue_number INTEGER,"
        "  github_issue_url TEXT,"
        "  github_sync_status TEXT,"
        "  github_sync_error TEXT,"
        "  github_synced_at TEXT"
        ")"
    )
    _ensure_feedback_schema(conn)
    conn.commit()
    return conn


def _ensure_feedback_schema(conn: sqlite3.Connection) -> None:
    """Add missing columns for GitHub sync and contributor info when upgrading older databases."""
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(feedback)").fetchall()
    }
    required = {
        "name": "TEXT",
        "email": "TEXT",
        "github_issue_number": "INTEGER",
        "github_issue_url": "TEXT",
        "github_sync_status": "TEXT",
        "github_sync_error": "TEXT",
        "github_synced_at": "TEXT",
    }
    for col, col_type in required.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE feedback ADD COLUMN {col} {col_type}")


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


def _create_feedback_issue(entry: dict) -> tuple[int | None, str | None, str | None]:
    """Create a GitHub issue for a feedback entry.

    Returns (issue_number, issue_url, error_message).
    """
    cfg = _feedback_github_config()
    if not cfg["token"]:
        return None, None, "FEEDBACK_GITHUB_TOKEN not configured"

    repo = cfg["repo"]
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"[Feedback] {entry['rating'].capitalize()} | {entry['task'] or 'general'} | {now_date}"
    
    body_parts = [
        "## User Feedback Submission\n",
        f"- Feedback ID: `{entry['id']}`\n",
        f"- Submitted at (UTC): `{entry['timestamp']}`\n",
        f"- Rating: `{entry['rating']}`\n",
        f"- Task: `{entry['task'] or 'not specified'}`\n",
    ]
    
    if entry.get("name") or entry.get("email"):
        body_parts.append("- **Contributor contact:**\n")
        if entry.get("name"):
            body_parts.append(f"  - Name: {entry['name']}\n")
        if entry.get("email"):
            body_parts.append(f"  - Email: {entry['email']}\n")
    
    body_parts.extend([
        "\n### Message\n",
        f"{entry['message']}\n",
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

    timestamp = datetime.now(timezone.utc).isoformat()

    issue_url = None
    try:
        conn = _get_db()
        cur = conn.execute(
            "INSERT INTO feedback (timestamp, name, email, rating, task, message) VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, name, email, rating, task, message),
        )
        feedback_id = cur.lastrowid

        entry = {
            "id": feedback_id,
            "timestamp": timestamp,
            "name": name,
            "email": email,
            "rating": rating,
            "task": task,
            "message": message,
        }
        issue_number, issue_url, sync_error = _create_feedback_issue(entry)
        if issue_number and issue_url:
            conn.execute(
                "UPDATE feedback SET github_issue_number=?, github_issue_url=?, github_sync_status=?, github_sync_error=?, github_synced_at=? WHERE id=?",
                (issue_number, issue_url, "synced", None, datetime.now(timezone.utc).isoformat(), feedback_id),
            )
        else:
            conn.execute(
                "UPDATE feedback SET github_sync_status=?, github_sync_error=? WHERE id=?",
                ("failed", sync_error, feedback_id),
            )
            if sync_error:
                log.warning("Feedback GitHub sync failed for id=%s: %s", feedback_id, sync_error)

        conn.commit()
        conn.close()
    except (sqlite3.Error, OSError):
        log.exception("Failed to save feedback")

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
        conn = _get_db()
        cursor = conn.execute(
            "SELECT id, timestamp, name, email, rating, task, message, github_issue_number, github_issue_url, github_sync_status, github_sync_error "
            "FROM feedback ORDER BY id DESC"
        )
        rows = [
            {
                "id": r[0],
                "timestamp": r[1],
                "name": r[2],
                "email": r[3],
                "rating": r[4],
                "task": r[5],
                "message": r[6],
                "github_issue_number": r[7],
                "github_issue_url": r[8],
                "github_sync_status": r[9],
                "github_sync_error": r[10],
            }
            for r in cursor.fetchall()
        ]
        conn.close()
    except (sqlite3.Error, OSError):
        log.exception("Failed to load feedback")
        rows = []

    response = render_template("feedback_review.html", entries=rows)
    resp = current_app.make_response(response)
    resp.headers["Cache-Control"] = "no-store"
    return resp
