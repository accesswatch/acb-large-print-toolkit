"""User guide route -- comprehensive help and how-to documentation."""

from flask import Blueprint, render_template

guide_bp = Blueprint("guide", __name__)


@guide_bp.route("/", methods=["GET"])
def guide_page():
    return render_template("guide.html")
