"""Guidelines route -- full ACB specification reference page."""

from flask import Blueprint, render_template

guidelines_bp = Blueprint("guidelines", __name__)


@guidelines_bp.route("/", methods=["GET"])
def guidelines_page():
    return render_template("guidelines.html")
