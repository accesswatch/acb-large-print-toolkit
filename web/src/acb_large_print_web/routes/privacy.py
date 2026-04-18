"""Data Storage, Use, and Retention Policy route."""

from flask import Blueprint, render_template

from ..email import email_configured

privacy_bp = Blueprint("privacy", __name__)


@privacy_bp.route("/")
def privacy_page():
    return render_template("privacy.html", email_configured=email_configured())
