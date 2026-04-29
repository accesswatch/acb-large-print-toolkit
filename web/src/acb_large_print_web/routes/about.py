"""About page route -- attributions, dependencies, and version info."""

from flask import Blueprint, render_template

from acb_large_print.stress_profiles import describe_stress_corpus

about_bp = Blueprint("about", __name__)


@about_bp.route("/")
def about_page():
    from ..tool_usage import get_all as _get_tool_usage, get_total as _get_tool_total
    from ..visitor_counter import get_count as _get_visitor_count
    return render_template(
        "about.html",
        stress_summary=describe_stress_corpus(),
        tool_usage=_get_tool_usage(),
        total_uses=_get_tool_total(),
        visitor_count=_get_visitor_count(),
    )
