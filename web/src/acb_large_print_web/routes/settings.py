"""Settings route -- user preference controls with opt-in persistence."""

from flask import Blueprint, render_template

from acb_large_print_web.rules import get_all_rule_ids

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET"])
def settings_page():
    return render_template(
        "settings.html",
        total_rules=len(get_all_rule_ids()),
    )
