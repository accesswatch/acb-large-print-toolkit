"""Workshop mode routes for training and conference delivery (7.3.0)."""

from __future__ import annotations

from flask import Blueprint, Response, abort, redirect, render_template_string, request, url_for

from ..feature_flags import get_flag
from ..workshop_store import (
    add_feedback,
    ensure_session,
    export_session_markdown,
    get_session,
    list_feedback_for_session,
    list_submissions,
    normalize_session_code,
    save_submission,
)

workshop_bp = Blueprint("workshop", __name__)

ACTIVITY_ORDER = [
    "journey_check_in",
    "problem_statement",
    "teach_vs_fix",
    "ai_boundary_map",
    "agent_formula",
    "lab_accessible_communication",
    "lab_alt_text_decision",
    "lab_remediation_plan",
    "champion_studio",
    "capstone_shareout",
    "action_plan_30_day",
]

ACTIVITY_PROMPTS = {
    "journey_check_in": "What kind of accessibility work do you do, where do partners get stuck, and what would change if more people became accessibility champions?",
    "problem_statement": "State the surface problem, deeper capacity problem, who needs to learn, and what repeatable success looks like.",
    "teach_vs_fix": "Rewrite a 'fix it for me' request into a coaching response that solves today and teaches for next time.",
    "ai_boundary_map": "Classify tasks as helpful for AI, risky without review, or human required, and list safeguards.",
    "agent_formula": "Define Role + Task + Trusted Guidance + Output Format + Human Review for a partner-facing accessibility helper.",
    "lab_accessible_communication": "Revise a communication sample for plain language, structure, meaningful links, and inclusive access language.",
    "lab_alt_text_decision": "Document image purpose, what matters, what to omit, and what human validation must verify.",
    "lab_remediation_plan": "Create a prioritized remediation and coaching plan for a realistic document, slide, or course content scenario.",
    "champion_studio": "Design a reusable workflow that teaches partner ownership and includes explicit human-review safeguards.",
    "capstone_shareout": "Summarize your workflow, who it helps, and how it supports sustained accessibility practice.",
    "action_plan_30_day": "Commit to one workflow, one partner/team, one safeguard, and one concrete next step in 30 days.",
}


def _workshop_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_WORKSHOP_MODE", True))


def _lab_hub_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_WORKSHOP_LAB_HUB", True))


def _gallery_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_WORKSHOP_GALLERY", True))


def _peer_review_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_WORKSHOP_PEER_REVIEW", True))


@workshop_bp.route("/", methods=["GET", "POST"])
def workshop_home():
    if not _workshop_enabled():
        abort(404)

    error = ""
    if request.method == "POST":
        raw_code = (request.form.get("session_code") or "").strip()
        title = (request.form.get("session_title") or "GLOW Workshop Session").strip() or "GLOW Workshop Session"
        try:
            code = normalize_session_code(raw_code)
            ensure_session(code, title=title)
            return redirect(url_for("workshop.workshop_activity", session_code=code, activity_key=ACTIVITY_ORDER[0]))
        except ValueError as exc:
            error = str(exc)

    schedule = [
        {"time": "8:30-8:50", "title": "Welcome and Accessibility Journey Check-In", "mode": "Reflection and group share"},
        {"time": "8:50-9:25", "title": "What Problem Are We Solving?", "mode": "Problem framing"},
        {"time": "9:25-10:00", "title": "From Fixing Everything to Teaching Partners to Fish", "mode": "Coaching practice"},
        {"time": "10:10-10:45", "title": "Human-Centered AI Boundaries", "mode": "Helpful, risky, human-required map"},
        {"time": "10:45-11:20", "title": "Accessibility Agents in Plain Language", "mode": "Role + Task + Guidance + Output + Human Review"},
        {"time": "11:20-12:15", "title": "GLOW Lab 1: Accessible Communications", "mode": "Hands-on lab"},
        {"time": "1:15-2:05", "title": "GLOW Lab 2: Alt Text and Human Judgment", "mode": "Hands-on lab"},
        {"time": "2:05-2:55", "title": "GLOW Lab 3: Remediation Planning", "mode": "Hands-on lab"},
        {"time": "3:05-3:50", "title": "Accessibility Champion Studio", "mode": "Workflow design"},
        {"time": "3:50-4:15", "title": "Peer Review and Scaling Path", "mode": "Feedback and refinement"},
        {"time": "4:15-4:30", "title": "Capstone and 30-Day Action Plan", "mode": "Commitment and share-out"},
    ]

    outcomes = [
        "Frame accessibility work around a real human problem before selecting tools.",
        "Use AI support responsibly with explicit human-review safeguards.",
        "Build repeatable partner-facing workflows that teach, not only fix.",
        "Leave with reusable artifacts such as prompts, checklists, and action plans.",
    ]

    return render_template_string(
        """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Workshop Mode | GLOW</title>
  <style>
    body { font-family: system-ui, sans-serif; line-height: 1.5; margin: 0; }
    .page { max-width: 72rem; margin: 0 auto; padding: 1rem; }
    .skip-link { position: absolute; left: -9999px; top: auto; }
    .skip-link:focus { left: 1rem; top: 1rem; background: #fff; border: 2px solid #000; padding: .5rem; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #666; padding: .5rem; text-align: left; }
    th { background: #f2f2f2; }
    .error { color: #8b0000; font-weight: 600; }
    .join-box { border: 1px solid #444; padding: 1rem; margin: 1rem 0; }
    label { display: block; margin-top: .5rem; }
    input[type=text] { width: min(36rem, 100%); }
  </style>
</head>
<body>
  <a class=\"skip-link\" href=\"#main\">Skip to main content</a>
  <main id=\"main\" class=\"page\">
    <h1>Accessibility Agents in Action</h1>
    <p>
      A hands-on GLOW workshop for human-centered accessibility workflows.
      Participants are guided through practical labs and leave with reusable
      artifacts that help partners become accessibility champions.
    </p>

    <section aria-labelledby=\"join-heading\" class=\"join-box\">
      <h2 id=\"join-heading\">Start or Join a Workshop Session</h2>
      {% if error %}<p class=\"error\" role=\"alert\">{{ error }}</p>{% endif %}
      <form method=\"post\" action=\"{{ url_for('workshop.workshop_home') }}\">
        <input type=\"hidden\" name=\"csrf_token\" value=\"{{ csrf_token() }}\">
        <label for=\"session_code\">Session code</label>
        <input id=\"session_code\" name=\"session_code\" type=\"text\" required aria-describedby=\"session-help\">
        <p id=\"session-help\">Use 3-64 characters: letters, numbers, dash, or underscore.</p>
        <label for=\"session_title\">Session title</label>
        <input id=\"session_title\" name=\"session_title\" type=\"text\" value=\"GLOW Workshop Session\">
        <p><button type=\"submit\">Enter workshop session</button></p>
      </form>
    </section>

    <section aria-labelledby=\"outcomes-heading\">
      <h2 id=\"outcomes-heading\">Learning Outcomes</h2>
      <ul>
        {% for outcome in outcomes %}
        <li>{{ outcome }}</li>
        {% endfor %}
      </ul>
    </section>

    <section aria-labelledby=\"agenda-heading\">
      <h2 id=\"agenda-heading\">One-Day Agenda</h2>
      <table>
        <caption>Workshop timeline and activity mode</caption>
        <thead>
          <tr><th scope=\"col\">Time</th><th scope=\"col\">Session</th><th scope=\"col\">Primary Mode</th></tr>
        </thead>
        <tbody>
          {% for item in schedule %}
          <tr><th scope=\"row\">{{ item.time }}</th><td>{{ item.title }}</td><td>{{ item.mode }}</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>""",
        schedule=schedule,
        outcomes=outcomes,
        error=error,
    )


@workshop_bp.route("/session/<session_code>/activity/<activity_key>", methods=["GET", "POST"])
def workshop_activity(session_code: str, activity_key: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    if activity_key not in ACTIVITY_PROMPTS:
        abort(404)

    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)

    if get_session(code) is None:
        ensure_session(code)

    message = ""
    if request.method == "POST":
        display_name = (request.form.get("display_name") or "Participant").strip() or "Participant"
        content_text = (request.form.get("content_text") or "").strip()
        anonymity_mode = bool(request.form.get("anonymity_mode"))
        if not content_text:
            message = "Please enter your response before submitting."
        else:
            save_submission(code, activity_key, display_name, content_text, anonymity_mode=anonymity_mode)
            message = "Saved. Continue to the next activity or review the gallery."

    idx = ACTIVITY_ORDER.index(activity_key)
    prev_key = ACTIVITY_ORDER[idx - 1] if idx > 0 else None
    next_key = ACTIVITY_ORDER[idx + 1] if idx < len(ACTIVITY_ORDER) - 1 else None
    count = len(list_submissions(code, activity_key=activity_key))

    return render_template_string(
        """<!doctype html>
<html lang=\"en\"><head>
  <meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{{ activity_key }} | Workshop Session {{ session_code }}</title>
  <style>
    body { font-family: system-ui, sans-serif; line-height: 1.5; margin: 0; }
    .page { max-width: 72rem; margin: 0 auto; padding: 1rem; }
    .skip-link { position: absolute; left: -9999px; top: auto; }
    .skip-link:focus { left: 1rem; top: 1rem; background: #fff; border: 2px solid #000; padding: .5rem; }
    textarea { width: min(72rem, 100%); min-height: 14rem; }
    .msg { font-weight: 600; }
    nav a { margin-right: .75rem; }
  </style>
</head>
<body>
  <a class=\"skip-link\" href=\"#main\">Skip to main content</a>
  <main id=\"main\" class=\"page\">
    <h1>Workshop Activity: {{ activity_key }}</h1>
    <p><strong>Session:</strong> {{ session_code }}</p>
    <p>{{ prompt_text }}</p>
    {% if message %}<p class=\"msg\" role=\"status\">{{ message }}</p>{% endif %}

    <form method=\"post\" action=\"{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key=activity_key) }}\">
      <input type=\"hidden\" name=\"csrf_token\" value=\"{{ csrf_token() }}\">
      <label for=\"display_name\">Display name</label>
      <input id=\"display_name\" name=\"display_name\" type=\"text\" value=\"Participant\">
      <p><label><input type=\"checkbox\" name=\"anonymity_mode\"> Share anonymously in gallery</label></p>
      <label for=\"content_text\">Response</label>
      <textarea id=\"content_text\" name=\"content_text\" required></textarea>
      <p><button type=\"submit\">Save activity response</button></p>
    </form>

    <p>Total submissions for this activity: {{ count }}</p>
    <nav aria-label=\"Activity navigation\">
      <a href=\"{{ url_for('workshop.workshop_home') }}\">Workshop home</a>
      {% if prev_key %}<a href=\"{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key=prev_key) }}\">Previous activity</a>{% endif %}
      {% if next_key %}<a href=\"{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key=next_key) }}\">Next activity</a>{% endif %}
      {% if gallery_enabled %}<a href=\"{{ url_for('workshop.workshop_gallery', session_code=session_code) }}\">Open gallery</a>{% endif %}
    </nav>
  </main>
</body></html>""",
        session_code=code,
        activity_key=activity_key,
        prompt_text=ACTIVITY_PROMPTS[activity_key],
        message=message,
        prev_key=prev_key,
        next_key=next_key,
        count=count,
        gallery_enabled=_gallery_enabled(),
    )


@workshop_bp.route("/session/<session_code>/gallery", methods=["GET"])
def workshop_gallery(session_code: str):
    if not _workshop_enabled() or not _gallery_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    if get_session(code) is None:
        abort(404)

    submissions = list_submissions(code)
    feedback = list_feedback_for_session(code)

    return render_template_string(
        """<!doctype html>
<html lang=\"en\"><head>
  <meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Workshop Gallery | {{ session_code }}</title>
  <style>
    body { font-family: system-ui, sans-serif; line-height: 1.5; margin: 0; }
    .page { max-width: 72rem; margin: 0 auto; padding: 1rem; }
    .card { border: 1px solid #555; padding: .75rem; margin: .75rem 0; }
    textarea { width: min(72rem, 100%); min-height: 4rem; }
  </style>
</head>
<body><main class=\"page\" id=\"main\">
  <h1>Workshop Gallery</h1>
  <p><strong>Session:</strong> {{ session_code }}</p>
  <p><a href=\"{{ url_for('workshop.workshop_export_markdown', session_code=session_code) }}\">Export Markdown artifacts</a></p>
  {% if not submissions %}
    <p>No submissions yet.</p>
  {% else %}
    {% for s in submissions %}
      <article class=\"card\" aria-labelledby=\"submission-{{ s.id }}\">
        <h2 id=\"submission-{{ s.id }}\">{{ s.activity_key }}</h2>
        <p><strong>Submitter:</strong> {% if s.anonymity_mode %}Anonymous participant{% else %}{{ s.display_name }}{% endif %}</p>
        <p><strong>Updated:</strong> {{ s.updated_at_utc }}</p>
        <pre>{{ s.content_text }}</pre>

        {% set items = feedback.get(s.id, []) %}
        {% if items %}
          <h3>Peer feedback</h3>
          <ul>
          {% for f in items %}
            <li>
              <strong>{{ f.reviewer_display_name }}</strong>: {{ f.strength }}
              (Risk/gap: {{ f.risk_or_gap }}; Safeguard: {{ f.recommended_safeguard }})
            </li>
          {% endfor %}
          </ul>
        {% endif %}

        {% if peer_review_enabled %}
        <h3>Add peer feedback</h3>
        <form method=\"post\" action=\"{{ url_for('workshop.workshop_peer_feedback', session_code=session_code, submission_id=s.id) }}\">
          <input type=\"hidden\" name=\"csrf_token\" value=\"{{ csrf_token() }}\">
          <label>Reviewer name <input type=\"text\" name=\"reviewer_display_name\" value=\"Peer Reviewer\"></label>
          <label>Strength<textarea name=\"strength\" required></textarea></label>
          <label>Risk or gap<textarea name=\"risk_or_gap\" required></textarea></label>
          <label>Recommended safeguard<textarea name=\"recommended_safeguard\" required></textarea></label>
          <label>Reuse suggestion<textarea name=\"reuse_suggestion\" required></textarea></label>
          <p><button type=\"submit\">Save peer feedback</button></p>
        </form>
        {% endif %}
      </article>
    {% endfor %}
  {% endif %}
  <p><a href=\"{{ url_for('workshop.workshop_home') }}\">Back to workshop home</a></p>
</main></body></html>
""",
        session_code=code,
        submissions=submissions,
        feedback=feedback,
        peer_review_enabled=_peer_review_enabled(),
    )


@workshop_bp.route("/session/<session_code>/submission/<int:submission_id>/feedback", methods=["POST"])
def workshop_peer_feedback(session_code: str, submission_id: int):
    if not _workshop_enabled() or not _peer_review_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)

    reviewer = (request.form.get("reviewer_display_name") or "Peer Reviewer").strip() or "Peer Reviewer"
    strength = (request.form.get("strength") or "").strip()
    risk_or_gap = (request.form.get("risk_or_gap") or "").strip()
    recommended_safeguard = (request.form.get("recommended_safeguard") or "").strip()
    reuse_suggestion = (request.form.get("reuse_suggestion") or "").strip()

    if not (strength and risk_or_gap and recommended_safeguard and reuse_suggestion):
        return redirect(url_for("workshop.workshop_gallery", session_code=code))

    add_feedback(
        code,
        submission_id,
        reviewer,
        strength,
        risk_or_gap,
        recommended_safeguard,
        reuse_suggestion,
    )
    return redirect(url_for("workshop.workshop_gallery", session_code=code))


@workshop_bp.route("/session/<session_code>/export/markdown", methods=["GET"])
def workshop_export_markdown(session_code: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    session_meta = get_session(code)
    if session_meta is None:
        abort(404)

    markdown = export_session_markdown(code, session_title=session_meta.get("title", "GLOW Workshop Session"))
    return Response(
        markdown,
        mimetype="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{code}-workshop-artifacts.md"'},
    )
