"""Feedback route -- collect and review user feedback (SQLite-backed)."""

import hashlib
import hmac
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, request

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
        "  rating TEXT NOT NULL,"
        "  task TEXT,"
        "  message TEXT NOT NULL"
        ")"
    )
    conn.commit()
    return conn


@feedback_bp.route("/", methods=["GET"])
def feedback_form():
    return render_template("feedback_form.html")


@feedback_bp.route("/", methods=["POST"])
def feedback_submit():
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

    if errors:
        return (
            render_template(
                "feedback_form.html",
                error=" ".join(errors),
                rating=rating,
                task=task,
                message=message,
            ),
            400,
        )

    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        conn = _get_db()
        conn.execute(
            "INSERT INTO feedback (timestamp, rating, task, message) VALUES (?, ?, ?, ?)",
            (timestamp, rating, task, message),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error:
        log.exception("Failed to save feedback")

    return render_template("feedback_thanks.html")


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
            "SELECT id, timestamp, rating, task, message "
            "FROM feedback ORDER BY id DESC"
        )
        rows = [
            {
                "id": r[0],
                "timestamp": r[1],
                "rating": r[2],
                "task": r[3],
                "message": r[4],
            }
            for r in cursor.fetchall()
        ]
        conn.close()
    except sqlite3.Error:
        log.exception("Failed to load feedback")
        rows = []

    response = render_template("feedback_review.html", entries=rows)
    resp = current_app.make_response(response)
    resp.headers["Cache-Control"] = "no-store"
    return resp
