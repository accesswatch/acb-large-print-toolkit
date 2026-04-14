"""About page route -- attributions, dependencies, and version info."""

from flask import Blueprint, render_template

from acb_large_print.stress_profiles import describe_stress_corpus

about_bp = Blueprint("about", __name__)


@about_bp.route("/")
def about_page():
    return render_template("about.html", stress_summary=describe_stress_corpus())
