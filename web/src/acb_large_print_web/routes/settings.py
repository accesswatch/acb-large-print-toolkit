"""Settings route -- user preference controls with opt-in persistence."""

from flask import Blueprint, render_template

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET"])
def settings_page():
    return render_template("settings.html")
