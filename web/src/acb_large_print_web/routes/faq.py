"""FAQ route -- focused answers for common workflow questions."""

from flask import Blueprint, render_template

faq_bp = Blueprint("faq", __name__)


@faq_bp.route("/", methods=["GET"])
def faq_page():
    return render_template("faq.html")
