"""About page route -- attributions, dependencies, and version info."""

from flask import Blueprint, render_template

about_bp = Blueprint("about", __name__)


@about_bp.route("/")
def about_page():
    return render_template("about.html")
