"""Static documentation pages.

All long-form docs are built locally from Markdown into committed HTML partials
by scripts/build-doc-pages.py. At runtime, routes render lightweight wrapper
templates that include those partials.
"""

from flask import Blueprint, render_template


guide_bp = Blueprint("guide", __name__)
faq_bp = Blueprint("faq", __name__)
changelog_bp = Blueprint("changelog", __name__)
prd_bp = Blueprint("prd", __name__)
announcement_bp = Blueprint("announcement", __name__)


@guide_bp.route("/", methods=["GET"])
def guide_page():
    return render_template("guide.html")


@faq_bp.route("/", methods=["GET"])
def faq_page():
    return render_template("faq.html")


@changelog_bp.route("/", methods=["GET"])
def changelog_page():
    return render_template("changelog.html")


@prd_bp.route("/", methods=["GET"])
def prd_page():
    return render_template("prd.html")


@announcement_bp.route("/", methods=["GET"])
def announcement_page():
    return render_template("announcement.html")
