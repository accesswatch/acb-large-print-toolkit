"""About page route -- attributions, dependencies, and version info."""

import os

from flask import Blueprint, current_app, render_template

from acb_large_print.stress_profiles import describe_stress_corpus

about_bp = Blueprint("about", __name__)


@about_bp.route("/")
def about_page():
    from ..tool_usage import (
        get_all as _get_tool_usage,
        get_detail_counts as _get_detail_counts,
        get_total as _get_tool_total,
    )
    from ..visitor_counter import get_count as _get_visitor_count
    from ..speech_metrics import get_summary as _get_speech_metrics_summary
    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    return render_template(
        "about.html",
        stress_summary=describe_stress_corpus(),
        tool_usage=_get_tool_usage(),
        total_uses=_get_tool_total(),
        visitor_count=_get_visitor_count(),
        speech_metrics_summary=_get_speech_metrics_summary(),
        anthem_downloads=_get_detail_counts("anthem_download", "detail", limit=1),
        speech_modes=_get_detail_counts("speech", "mode", limit=10),
        speech_voices=_get_detail_counts("speech", "voice", limit=10),
        speech_speeds=_get_detail_counts("speech", "speed", limit=10),
        speech_pitches=_get_detail_counts("speech", "pitch", limit=10),
        firebase_auth_enabled=(os.environ.get("FIREBASE_AUTH_ENABLED", "0") == "1"),
        postgres_backend_enabled=db_uri.startswith("postgresql"),
    )
