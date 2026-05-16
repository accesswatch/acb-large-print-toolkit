"""Workshop mode routes for training and conference delivery (7.3.0)."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, Response, abort, current_app, g, make_response, redirect, render_template_string, request, send_file, url_for
from markupsafe import Markup, escape

from ..feature_flags import get_flag
from ..workshop_store import (
    add_feedback,
    bind_participant_login,
    create_or_update_participant,
    ensure_session,
    export_follow_through_markdown,
    export_session_docx_bytes,
    export_session_html,
    export_session_json,
    export_session_markdown,
    get_conference_code,
    get_participant,
    get_session,
    list_submissions_for_participant,
    load_conference_codes_from_env,
    load_conference_codes_from_file,
    list_feedback_for_session,
    list_follow_through_items,
    list_submissions,
    normalize_session_code,
    save_submission,
    save_follow_through_item,
    update_follow_through_status,
)

workshop_bp = Blueprint("workshop", __name__)
PARTICIPANT_COOKIE = "glow_workshop_participant"

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

ACTIVITY_META = {
    "journey_check_in": {"title": "Accessibility Journey Check-In", "time": "20 minutes", "badge": "Journey Mapper"},
    "problem_statement": {"title": "What Problem Are We Solving?", "time": "35 minutes", "badge": "Problem Framer"},
    "teach_vs_fix": {"title": "Fix It for Me vs Teach Me to Improve It", "time": "35 minutes", "badge": "Coaching Catalyst"},
    "ai_boundary_map": {"title": "Helpful, Risky, or Human Required?", "time": "35 minutes", "badge": "Boundary Builder"},
    "agent_formula": {"title": "Accessibility Agent Formula", "time": "35 minutes", "badge": "Agent Architect"},
    "lab_accessible_communication": {"title": "GLOW Lab 1: Accessible Communications", "time": "55 minutes", "badge": "Communication Coach"},
    "lab_alt_text_decision": {"title": "GLOW Lab 2: Alt Text and Human Judgment", "time": "50 minutes", "badge": "Meaning Mapper"},
    "lab_remediation_plan": {"title": "GLOW Lab 3: Remediation Planning", "time": "50 minutes", "badge": "Remediation Planner"},
    "champion_studio": {"title": "Accessibility Champion Studio", "time": "45 minutes", "badge": "Champion Designer"},
    "capstone_shareout": {"title": "Capstone Share-Out", "time": "25 minutes", "badge": "Story Sharer"},
    "action_plan_30_day": {"title": "30-Day Action Plan", "time": "15 minutes", "badge": "Momentum Builder"},
}

ACTIVITY_FIELDS = {
    "journey_check_in": [
        {"name": "work_type", "label": "What kind of accessibility work do you do?", "rows": 3, "required": True},
        {"name": "partner_blockers", "label": "Where do partners most often get stuck?", "rows": 3, "required": True},
        {"name": "champion_shift", "label": "What would change if more people became accessibility champions?", "rows": 3, "required": True},
    ],
    "problem_statement": [
        {"name": "surface_problem", "label": "Surface problem", "rows": 2, "required": True},
        {"name": "capacity_problem", "label": "Deeper capacity-building problem", "rows": 2, "required": True},
        {"name": "who_learns", "label": "Who needs to learn or own part of this?", "rows": 2, "required": True},
        {"name": "repeatable_success", "label": "What does repeatable success look like?", "rows": 2, "required": True},
    ],
    "teach_vs_fix": [
        {"name": "partner_request", "label": "Partner request", "rows": 2, "required": True},
        {"name": "immediate_need", "label": "Immediate accessibility need", "rows": 2, "required": True},
        {"name": "partner_learning", "label": "What the partner needs to learn", "rows": 2, "required": True},
        {"name": "coaching_response", "label": "Supportive coaching response", "rows": 4, "required": True},
    ],
    "ai_boundary_map": [
        {"name": "tasks", "label": "Tasks to classify", "rows": 3, "required": True},
        {"name": "boundaries", "label": "Helpful for AI, risky, or human-required decisions", "rows": 3, "required": True},
        {"name": "safeguards", "label": "Safeguards and review checkpoints", "rows": 3, "required": True},
    ],
    "agent_formula": [
        {"name": "role", "label": "Role", "rows": 2, "required": True},
        {"name": "task", "label": "Task", "rows": 2, "required": True},
        {"name": "trusted_guidance", "label": "Trusted guidance", "rows": 3, "required": True},
        {"name": "output_format", "label": "Output format", "rows": 2, "required": True},
        {"name": "human_review", "label": "Human review safeguard", "rows": 2, "required": True},
    ],
    "lab_accessible_communication": [
        {"name": "communication_type", "label": "Communication type and audience", "rows": 2, "required": True},
        {"name": "top_issues", "label": "Top clarity or accessibility issues", "rows": 3, "required": True},
        {"name": "revised_content", "label": "Revised content draft", "rows": 5, "required": True},
        {"name": "teaching_note", "label": "Teaching note for the content owner", "rows": 3, "required": True},
        {"name": "review_checklist", "label": "Human-review checklist", "rows": 3, "required": True},
    ],
    "lab_alt_text_decision": [
        {"name": "image_context", "label": "Image context", "rows": 2, "required": True},
        {"name": "image_purpose", "label": "Purpose of image", "rows": 2, "required": True},
        {"name": "relevant_info", "label": "Relevant information to include", "rows": 2, "required": True},
        {"name": "omit_info", "label": "Information to omit", "rows": 2, "required": True},
        {"name": "draft_alt", "label": "Draft alt text or description guidance", "rows": 3, "required": True},
        {"name": "verification_questions", "label": "Human verification questions", "rows": 2, "required": True},
    ],
    "lab_remediation_plan": [
        {"name": "content_track", "label": "Content track and audience", "rows": 2, "required": True},
        {"name": "likely_barriers", "label": "Likely barriers", "rows": 3, "required": True},
        {"name": "priority_fixes", "label": "Highest-priority fixes", "rows": 3, "required": True},
        {"name": "owner_questions", "label": "Questions for content owner", "rows": 3, "required": True},
        {"name": "human_inspection", "label": "What requires human inspection", "rows": 2, "required": True},
        {"name": "coaching_message", "label": "Coaching message", "rows": 3, "required": True},
    ],
    "champion_studio": [
        {"name": "workflow_name", "label": "Workflow name", "rows": 2, "required": True},
        {"name": "partner_group", "label": "Who this workflow helps", "rows": 2, "required": True},
        {"name": "responsibility", "label": "Accessibility responsibility to teach", "rows": 3, "required": True},
        {"name": "ai_support", "label": "What GLOW or AI should support", "rows": 3, "required": True},
        {"name": "final_output", "label": "Final output artifact", "rows": 2, "required": True},
        {"name": "human_safeguard", "label": "Human-review safeguard", "rows": 2, "required": True},
    ],
    "capstone_shareout": [
        {"name": "workflow_summary", "label": "Workflow summary", "rows": 3, "required": True},
        {"name": "who_it_helps", "label": "Who it helps and what they learn", "rows": 3, "required": True},
        {"name": "reusability", "label": "How this will be reused", "rows": 2, "required": True},
        {"name": "safeguard", "label": "Final human-review safeguard", "rows": 2, "required": True},
    ],
    "action_plan_30_day": [
        {"name": "workflow_30", "label": "One workflow to try in the next 30 days", "rows": 2, "required": True},
        {"name": "partner_team_30", "label": "One partner or team to support", "rows": 2, "required": True},
        {"name": "safeguard_30", "label": "One safeguard to include every time", "rows": 2, "required": True},
        {"name": "first_step_30", "label": "First concrete next step", "rows": 2, "required": True},
    ],
}

EXERCISE_PACK = [
  {
    "name": "Accessibility Journey Check-In",
    "time": "20 minutes",
    "purpose": "Help participants locate themselves in the accessibility journey and identify partner support needs.",
    "output": "Accessibility journey notes and shared barriers list.",
  },
  {
    "name": "What Problem Are We Solving?",
    "time": "35 minutes",
    "purpose": "Train teams to start with the accessibility problem before selecting tools.",
    "output": "Problem statement with capacity-building focus.",
  },
  {
    "name": "Fix It for Me vs Teach Me to Improve It",
    "time": "40 minutes",
    "purpose": "Practice converting urgent fix requests into teachable coaching responses.",
    "output": "Coaching response patterns for partner ownership.",
  },
  {
    "name": "Helpful, Risky, or Human Required",
    "time": "40 minutes",
    "purpose": "Establish practical responsible-AI boundaries for accessibility tasks.",
    "output": "AI boundary map with review safeguards.",
  },
  {
    "name": "Accessibility Agent Formula",
    "time": "45 minutes",
    "purpose": "Build non-technical agent concepts using a repeatable formula.",
    "output": "Role + Task + Guidance + Output + Human Review draft.",
  },
  {
    "name": "GLOW Lab 1: Accessible Communications",
    "time": "60 minutes",
    "purpose": "Improve real communication artifacts while teaching reusable accessibility patterns.",
    "output": "Revised communication and human-review checklist.",
  },
  {
    "name": "GLOW Lab 2: Alt Text and Human Judgment",
    "time": "55 minutes",
    "purpose": "Use AI support without losing human control of image purpose and meaning.",
    "output": "Image purpose decision checklist with verification questions.",
  },
  {
    "name": "GLOW Lab 3: Remediation Planning",
    "time": "55 minutes",
    "purpose": "Turn large remediation requests into practical coaching workflows.",
    "output": "Prioritized remediation coaching template.",
  },
  {
    "name": "Accessibility Champion Studio",
    "time": "50 minutes",
    "purpose": "Design reusable partner-facing workflows for local institutional needs.",
    "output": "Draft champion workflow artifact.",
  },
]

RESOURCE_FILES = {
  "guide": "workshop-frontfacing-guide.md",
  "exercises": "workshop-frontfacing-exercises.md",
  "utilization": "workshop-frontfacing-utilization.md",
}

WORKSHOP_ACTION_TOKENS = {
    "GLOW:AUDIT": ("Audit Workspace", "audit.audit_form"),
    "GLOW:FIX": ("Fix Workspace", "fix.fix_form"),
    "GLOW:CONVERT": ("Convert Workspace", "convert.convert_form"),
    "GLOW:TEMPLATE": ("Template Builder", "template.template_form"),
    "GLOW:CHAT": ("Document Chat", "chat.chat_form"),
    "GLOW:ALT_TEXT": ("Alt-Text Helper", "alt_text.alt_text_form"),
    "GLOW:MAGIC": ("Magic Lab", "magic.magic_home"),
}

WORKSHOP_SAMPLE_FILES = {
    "board-agenda-docx": "04 - April 8 2026 BITS Board Meeting Agenda.docx",
    "board-agenda-md": "04 - April 8 2026 BITS Board Meeting Agenda.md",
    "board-agenda-html": "04 - April 8 2026 BITS Board Meeting Agenda.html",
    "glow-test-docx": "GLOW Test 2.docx",
}

MAGIC_SCENARIOS = [
    {
        "id": "communication-refresh",
        "title": "Accessible Communication Refresh",
        "goal": "Turn a dense announcement into a plain-language, well-structured communication.",
        "tokens": ["GLOW:AUDIT", "GLOW:FIX", "GLOW:TEMPLATE"],
        "sample_slug": "board-agenda-docx",
        "activity_key": "lab_accessible_communication",
        "workflow_text": "Run [[GLOW:AUDIT]] to identify barriers, draft improvements in [[GLOW:FIX]], then save a reusable coaching script in [[GLOW:TEMPLATE]].",
    },
    {
        "id": "alt-text-judgment",
        "title": "Alt Text and Human Judgment",
        "goal": "Practice purpose-first image decisions with explicit human verification.",
        "tokens": ["GLOW:ALT_TEXT", "GLOW:CHAT", "GLOW:TEMPLATE"],
        "sample_slug": "board-agenda-html",
        "activity_key": "lab_alt_text_decision",
        "workflow_text": "Use [[GLOW:ALT_TEXT]] for first-draft guidance, pressure-test language in [[GLOW:CHAT]], and package a checklist in [[GLOW:TEMPLATE]].",
    },
    {
        "id": "remediation-prioritization",
        "title": "Remediation Prioritization Sprint",
        "goal": "Convert a large remediation problem into a realistic, teachable plan.",
        "tokens": ["GLOW:AUDIT", "GLOW:CONVERT", "GLOW:MAGIC"],
        "sample_slug": "glow-test-docx",
        "activity_key": "lab_remediation_plan",
        "workflow_text": "Start with [[GLOW:AUDIT]] for evidence, summarize action tracks in [[GLOW:CONVERT]], and use [[GLOW:MAGIC]] for advanced advisory checks.",
    },
]


def _workshop_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_WORKSHOP_MODE", True))


def _lab_hub_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_WORKSHOP_LAB_HUB", True))


def _gallery_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_WORKSHOP_GALLERY", True))


def _peer_review_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_WORKSHOP_PEER_REVIEW", True))


def _activity_title(activity_key: str) -> str:
    return ACTIVITY_META.get(activity_key, {}).get("title", activity_key)


def _workshop_return_target(session_code: str, *, activity_key: str | None = None) -> str:
    key = (activity_key or "").strip()
    if key and key in ACTIVITY_PROMPTS:
        return url_for("workshop.workshop_activity", session_code=session_code, activity_key=key)
    return url_for("workshop.workshop_launchpad", session_code=session_code)


def _action_link_for_token(token: str, session_code: str, *, return_to: str) -> tuple[str, str]:
    label, endpoint = WORKSHOP_ACTION_TOKENS[token]
    href = url_for(
        endpoint,
        workshop_return=return_to,
        workshop_label=f"Return to Workshop ({session_code})",
    )
    return label, href


def _render_tokenized_workflow_text(text: str, session_code: str, *, return_to: str) -> Markup:
    rendered = escape(text or "")
    for token, (label, endpoint) in WORKSHOP_ACTION_TOKENS.items():
        pattern = f"[[{token}]]"
        if pattern in rendered:
            href = url_for(
                endpoint,
                workshop_return=return_to,
                workshop_label=f"Return to Workshop ({session_code})",
            )
            link = f'<a href="{escape(href)}">{escape(label)}</a>'
            rendered = rendered.replace(pattern, link)
    return Markup(rendered)


def _serialize_activity_submission(activity_key: str, fields: list[dict], values: dict[str, str], bonus_note: str) -> str:
    lines: list[str] = []
    lines.append(f"Activity: {_activity_title(activity_key)}")
    lines.append(f"Activity key: {activity_key}")
    lines.append("")
    for field in fields:
        label = field.get("label", field.get("name", "Field"))
        value = (values.get(field.get("name", "")) or "").strip()
        lines.append(f"{label}:")
        lines.append(value or "(not provided)")
        lines.append("")
    if bonus_note.strip():
        lines.append("Bonus reflection:")
        lines.append(bonus_note.strip())
        lines.append("")
    return "\n".join(lines).strip()


def _resolve_session_from_access_code(raw_code: str) -> tuple[str, str, str]:
    """
    Resolve user-entered access code to (session_code, session_title, event_name).
    Supports:
    - configured conference codes
    - direct existing session codes
    - ad-hoc session code creation
    """
    value = (raw_code or "").strip()
    if not value:
        raise ValueError("Please enter a workshop or conference code.")

    mapped = get_conference_code(value)
    if mapped:
        return (
            str(mapped.get("session_code", "")).strip(),
            str(mapped.get("session_title", "GLOW Workshop Session")).strip() or "GLOW Workshop Session",
            str(mapped.get("event_name", "")).strip(),
        )

    code = normalize_session_code(value)
    existing = get_session(code)
    if existing:
        return (
            code,
            str(existing.get("title", "GLOW Workshop Session")).strip() or "GLOW Workshop Session",
            str(existing.get("event_name", "")).strip(),
        )

    return (code, "GLOW Workshop Session", "")


def _active_login_email() -> str | None:
    user = getattr(g, "oidc_user_info", {}) if g is not None else {}
    if isinstance(user, dict):
        email = (user.get("email") or "").strip()
        if email:
            return email
    return None


@workshop_bp.route("/", methods=["GET", "POST"])
def workshop_home():
    if not _workshop_enabled():
        abort(404)

    # Best-effort code loading for conference events.
    try:
        load_conference_codes_from_env()
        load_conference_codes_from_file()
    except Exception:
        pass

    error = ""
    info = ""
    session_code = ""
    session_title = "GLOW Workshop Session"
    session_event = ""
    join_mode = False
    participant_display_name = "Participant"
    participant_key = (request.cookies.get(PARTICIPANT_COOKIE) or "").strip()
    participant = get_participant(participant_key) if participant_key else None

    query_code = (request.args.get("code") or "").strip()
    if query_code:
        try:
            session_code, session_title, session_event = _resolve_session_from_access_code(query_code)
            ensure_session(session_code, title=session_title, event_name=session_event)
            join_mode = True
        except ValueError as exc:
            error = str(exc)

    if participant and join_mode and str(participant.get("session_code", "")).strip() == session_code:
        participant_display_name = str(participant.get("display_name", "Participant")).strip() or "Participant"
        if _active_login_email():
            bind_participant_login(str(participant.get("participant_key", "")), _active_login_email() or "")
            info = "Welcome back. Your personal workshop content is ready."

    if request.method == "POST":
        action = (request.form.get("action") or "lookup").strip().lower()
        if action == "lookup":
            raw_code = (request.form.get("access_code") or "").strip()
            try:
                code, title, event_name = _resolve_session_from_access_code(raw_code)
                ensure_session(code, title=title, event_name=event_name)
                return redirect(url_for("workshop.workshop_home", code=code))
            except ValueError as exc:
                error = str(exc)
        elif action == "join":
            code = (request.form.get("session_code") or "").strip()
            display_name = (request.form.get("display_name") or "Participant").strip() or "Participant"
            try:
                normalized_code = normalize_session_code(code)
                session_meta = get_session(normalized_code)
                if session_meta is None:
                    abort(404)
                session_code = normalized_code
                session_title = str(session_meta.get("title", "GLOW Workshop Session")).strip() or "GLOW Workshop Session"
                session_event = str(session_meta.get("event_name", "")).strip()
                join_mode = True
                participant_row = create_or_update_participant(
                    normalized_code,
                    display_name,
                    participant_key=participant_key or None,
                    login_email=_active_login_email(),
                )
                resp = make_response(
                    redirect(
                        url_for(
                            "workshop.workshop_activity",
                            session_code=normalized_code,
                            activity_key=ACTIVITY_ORDER[0],
                            pulse=1,
                        )
                    )
                )
                resp.set_cookie(
                    PARTICIPANT_COOKIE,
                    str(participant_row.get("participant_key", "")),
                    max_age=60 * 60 * 24 * 90,
                    httponly=True,
                    samesite="Lax",
                )
                return resp
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

    <section aria-labelledby=\"frontfacing-docs\" class=\"join-box\">
      <h2 id=\"frontfacing-docs\">Front-Facing Workshop Documentation</h2>
      <p>Use these pages to run and scale the workshop in conference, onboarding, and institutional training environments.</p>
      <p>
        <a href=\"{{ url_for('workshop.workshop_guide') }}\">Workshop Guide</a> |
        <a href=\"{{ url_for('workshop.workshop_exercises') }}\">Exercises Pack</a> |
        <a href=\"{{ url_for('workshop.workshop_utilization') }}\">Utilization Guide</a> |
        {% if join_mode %}<a href=\"{{ url_for('workshop.workshop_follow_through', session_code=session_code) }}\">Follow-Through</a>{% endif %}
      </p>
    </section>

    <section aria-labelledby=\"join-heading\" class=\"join-box\">
      <h2 id=\"join-heading\">Join with a Conference or Workshop Code</h2>
      {% if error %}<p class=\"error\" role=\"alert\">{{ error }}</p>{% endif %}
      {% if info %}<p role="status"><strong>{{ info }}</strong></p>{% endif %}
      <form method=\"post\" action=\"{{ url_for('workshop.workshop_home') }}\">
        <input type=\"hidden\" name=\"csrf_token\" value=\"{{ csrf_token() }}\">
        <input type=\"hidden\" name=\"action\" value=\"lookup\">
        <label for=\"access_code\">Conference/workshop code</label>
        <input id=\"access_code\" name=\"access_code\" type=\"text\" required aria-describedby=\"session-help\" value="{{ session_code }}">
        <p id=\"session-help\">Enter your conference invite code. Existing session codes also work.</p>
        <p><button type=\"submit\">Look up workshop</button></p>
      </form>

      {% if join_mode %}
      <hr>
      <h3>Step 2: Confirm participant identity</h3>
      <p><strong>Workshop session:</strong> {{ session_code }} — {{ session_title }}{% if session_event %} ({{ session_event }}){% endif %}</p>
      <p>Use your name once and we will remember your personal content on this device without requiring login.</p>
      <form method="post" action="{{ url_for('workshop.workshop_home') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input type="hidden" name="action" value="join">
        <input type="hidden" name="session_code" value="{{ session_code }}">
        <label for="display_name">Your display name</label>
        <input id="display_name" name="display_name" type="text" value="{{ participant_display_name }}" required>
        <p><button type="submit">Enter workshop</button></p>
      </form>
      {% endif %}
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
        info=info,
        join_mode=join_mode,
        session_code=session_code,
        session_title=session_title,
        session_event=session_event,
        participant_display_name=participant_display_name,
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

    participant_key = (request.cookies.get(PARTICIPANT_COOKIE) or "").strip()
    participant = get_participant(participant_key) if participant_key else None
    participant_name = "Participant"
    if participant and str(participant.get("session_code", "")).strip() == code:
        participant_name = str(participant.get("display_name", "Participant")).strip() or "Participant"
        if _active_login_email():
            bind_participant_login(str(participant.get("participant_key", "")), _active_login_email() or "")

    activity_fields = ACTIVITY_FIELDS.get(
        activity_key,
        [{"name": "response", "label": "Response", "rows": 6, "required": True}],
    )
    field_values = {field.get("name", ""): "" for field in activity_fields}
    bonus_note = ""
    message = "Your previous activity was saved. Keep the momentum going."
    if not request.args.get("pulse"):
        message = ""
    if request.method == "POST":
        display_name = (request.form.get("display_name") or participant_name).strip() or participant_name
        anonymity_mode = bool(request.form.get("anonymity_mode"))
        submit_action = (request.form.get("submit_action") or "save").strip().lower()
        for field in activity_fields:
            key = field.get("name", "")
            field_values[key] = (request.form.get(key) or "").strip()
        bonus_note = (request.form.get("bonus_note") or "").strip()

        missing = [
            field.get("label", field.get("name", "field"))
            for field in activity_fields
            if field.get("required", True) and not field_values.get(field.get("name", ""), "").strip()
        ]
        if missing:
            message = "Please complete: " + ", ".join(missing[:3]) + ("..." if len(missing) > 3 else "")
        else:
            content_text = _serialize_activity_submission(activity_key, activity_fields, field_values, bonus_note)
            participant_row = create_or_update_participant(
                code,
                display_name,
                participant_key=(participant.get("participant_key") if participant else participant_key) or None,
                login_email=_active_login_email(),
            )
            participant = participant_row
            participant_name = str(participant_row.get("display_name", display_name)).strip() or display_name
            save_submission(
                code,
                activity_key,
                participant_name,
                content_text,
                participant_key=str(participant_row.get("participant_key", "")),
                anonymity_mode=anonymity_mode,
            )
            badge = ACTIVITY_META.get(activity_key, {}).get("badge", "Workshop Champion")
            if submit_action == "save_next":
                idx = ACTIVITY_ORDER.index(activity_key)
                next_key = ACTIVITY_ORDER[idx + 1] if idx < len(ACTIVITY_ORDER) - 1 else None
                if next_key:
                    resp = make_response(
                        redirect(
                            url_for(
                                "workshop.workshop_activity",
                                session_code=code,
                                activity_key=next_key,
                                pulse=1,
                            )
                        )
                    )
                    resp.set_cookie(
                        PARTICIPANT_COOKIE,
                        str(participant_row.get("participant_key", "")),
                        max_age=60 * 60 * 24 * 90,
                        httponly=True,
                        samesite="Lax",
                    )
                    return resp
            message = f"Saved. Badge unlocked: {badge}. Continue to the next activity or review the gallery."

    return_to = _workshop_return_target(code, activity_key=activity_key)

    idx = ACTIVITY_ORDER.index(activity_key)
    prev_key = ACTIVITY_ORDER[idx - 1] if idx > 0 else None
    next_key = ACTIVITY_ORDER[idx + 1] if idx < len(ACTIVITY_ORDER) - 1 else None
    count = len(list_submissions(code, activity_key=activity_key))
    all_submissions = list_submissions(code)
    by_activity = {key: 0 for key in ACTIVITY_ORDER}
    for submission in all_submissions:
        key = submission.get("activity_key", "")
        if key in by_activity:
            by_activity[key] += 1
    completed_activities = sum(1 for key in ACTIVITY_ORDER if by_activity.get(key, 0) > 0)
    progress_pct = round((completed_activities / len(ACTIVITY_ORDER)) * 100, 1)
    activity_meta = ACTIVITY_META.get(
        activity_key,
        {"title": activity_key, "time": "Varies", "badge": "Workshop Champion"},
    )

    rendered = render_template_string(
        """<!doctype html>
<html lang=\"en\"><head>
  <meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{{ activity_title }} | Workshop Session {{ session_code }}</title>
  <style>
    body { font-family: system-ui, sans-serif; line-height: 1.5; margin: 0; background: #f8fafc; }
    .page { max-width: 72rem; margin: 0 auto; padding: 1rem; }
    .skip-link { position: absolute; left: -9999px; top: auto; }
    .skip-link:focus { left: 1rem; top: 1rem; background: #fff; border: 2px solid #000; padding: .5rem; }
    .panel { background: #fff; border: 1px solid #ccd; border-radius: .5rem; padding: .9rem; margin: .85rem 0; }
    label { display: block; margin-top: .5rem; font-weight: 600; }
    textarea { width: min(68rem, 100%); min-height: 5rem; }
    input[type=text] { width: min(40rem, 100%); }
    .passport { display: flex; flex-wrap: wrap; gap: .4rem; list-style: none; padding: 0; }
    .passport li { border: 1px solid #6b7280; border-radius: 999px; padding: .2rem .6rem; background: #fff; }
    .passport li.complete { background: #e6ffed; border-color: #1f7a36; }
    progress { width: min(36rem, 100%); height: 1rem; }
    .msg { font-weight: 600; }
    nav a { margin-right: .75rem; }
  </style>
</head>
<body>
  <a class=\"skip-link\" href=\"#main\">Skip to main content</a>
  <main id=\"main\" class=\"page\">
    <h1>Workshop Activity: {{ activity_title }}</h1>
    <p><strong>Session:</strong> {{ session_code }}</p>
    {% if participant_name %}<p><strong>Participant:</strong> {{ participant_name }} (<a href="{{ url_for('workshop.workshop_my_content', session_code=session_code) }}">My content</a>)</p>{% endif %}
    <section class="panel" aria-labelledby="magic-progress">
      <h2 id="magic-progress">Workshop Progress Passport</h2>
      <p>Activity {{ idx + 1 }} of {{ total_activities }} | Time box: {{ activity_time }} | Badge: {{ activity_badge }}</p>
      <p><progress value="{{ completed_activities }}" max="{{ total_activities }}"></progress> {{ progress_pct }}% complete</p>
      <ul class="passport" aria-label="Activity completion status">
      {% for key in activity_order %}
        <li class="{% if by_activity.get(key, 0) > 0 %}complete{% endif %}">
          {{ activity_titles[key] }}{% if by_activity.get(key, 0) > 0 %} - complete{% endif %}
        </li>
      {% endfor %}
      </ul>
    </section>
    <section class="panel" aria-labelledby="challenge-brief">
      <h2 id="challenge-brief">Challenge Brief</h2>
      <p>{{ prompt_text }}</p>
    </section>
    {% if message %}<p class=\"msg\" role=\"status\">{{ message }}</p>{% endif %}

    <section class="panel" aria-labelledby="interactive-form">
      <h2 id="interactive-form">Interactive Activity Form</h2>
      <form method=\"post\" action=\"{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key=activity_key) }}\">
        <input type=\"hidden\" name=\"csrf_token\" value=\"{{ csrf_token() }}\">
        <label for=\"display_name\">Display name</label>
        <input id=\"display_name\" name=\"display_name\" type=\"text\" value="{{ participant_name }}">
        <p><label><input type=\"checkbox\" name=\"anonymity_mode\"> Share anonymously in gallery</label></p>
        {% for field in activity_fields %}
          <label for="{{ field.name }}">{{ field.label }}</label>
          <textarea
            id="{{ field.name }}"
            name="{{ field.name }}"
            rows="{{ field.rows or 3 }}"
            {% if field.required %}required{% endif %}
          >{{ field_values.get(field.name, "") }}</textarea>
        {% endfor %}
        <label for="bonus_note">Bonus reflection (optional)</label>
        <textarea id="bonus_note" name="bonus_note" rows="3">{{ bonus_note }}</textarea>
        <p>
          <button type="submit" name="submit_action" value="save">Save activity response</button>
          {% if next_key %}<button type="submit" name="submit_action" value="save_next">Save and continue</button>{% endif %}
        </p>
      </form>
    </section>

    <p>Total submissions for this activity: {{ count }}</p>
    <p><a href="{{ url_for('workshop.workshop_launchpad', session_code=session_code, activity=activity_key) }}">Open magical exercise launchpad</a></p>
    <nav aria-label=\"Activity navigation\">
      <a href=\"{{ url_for('workshop.workshop_home') }}\">Workshop home</a>
      {% if prev_key %}<a href=\"{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key=prev_key) }}\">Previous activity</a>{% endif %}
      {% if next_key %}<a href=\"{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key=next_key) }}\">Next activity</a>{% endif %}
      {% if gallery_enabled %}<a href=\"{{ url_for('workshop.workshop_gallery', session_code=session_code) }}\">Open gallery</a>{% endif %}
      <a href=\"{{ url_for('workshop.workshop_coach', session_code=session_code) }}\">Coach</a>
      <a href=\"{{ url_for('workshop.workshop_review', session_code=session_code) }}\">Review</a>
      <a href=\"{{ url_for('workshop.workshop_share', session_code=session_code) }}\">Share</a>
      <a href=\"{{ url_for('workshop.workshop_follow_through', session_code=session_code) }}\">Follow-Through</a>
    </nav>
  </main>
</body></html>""",
        session_code=code,
        activity_key=activity_key,
        activity_title=activity_meta.get("title", activity_key),
        activity_time=activity_meta.get("time", "Varies"),
        activity_badge=activity_meta.get("badge", "Workshop Champion"),
        activity_fields=activity_fields,
        field_values=field_values,
        bonus_note=bonus_note,
        prompt_text=ACTIVITY_PROMPTS[activity_key],
        message=message,
        idx=idx,
        total_activities=len(ACTIVITY_ORDER),
        completed_activities=completed_activities,
        progress_pct=progress_pct,
        by_activity=by_activity,
        activity_order=ACTIVITY_ORDER,
        activity_titles={key: _activity_title(key) for key in ACTIVITY_ORDER},
        prev_key=prev_key,
        next_key=next_key,
        count=count,
        gallery_enabled=_gallery_enabled(),
        participant_name=participant_name,
    )
    resp = make_response(rendered)
    if participant and participant.get("participant_key"):
        resp.set_cookie(
            PARTICIPANT_COOKIE,
            str(participant.get("participant_key", "")),
            max_age=60 * 60 * 24 * 90,
            httponly=True,
            samesite="Lax",
        )
    return resp


@workshop_bp.route("/session/<session_code>/launchpad", methods=["GET"])
def workshop_launchpad(session_code: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    session_meta = get_session(code)
    if session_meta is None:
        abort(404)

    activity_key = (request.args.get("activity") or "").strip()
    if activity_key and activity_key not in ACTIVITY_PROMPTS:
        activity_key = ""
    return_to = _workshop_return_target(code, activity_key=activity_key or ACTIVITY_ORDER[0])
    scenario_cards = []
    for scenario in MAGIC_SCENARIOS:
        action_links = []
        for token in scenario.get("tokens", []):
            if token in WORKSHOP_ACTION_TOKENS:
                label, href = _action_link_for_token(token, code, return_to=return_to)
                action_links.append({"token": token, "label": label, "href": href})
        scenario_cards.append(
            {
                "id": scenario["id"],
                "title": scenario["title"],
                "goal": scenario["goal"],
                "sample_slug": scenario["sample_slug"],
                "sample_name": WORKSHOP_SAMPLE_FILES.get(scenario["sample_slug"], ""),
                "activity_key": scenario["activity_key"],
                "activity_title": _activity_title(str(scenario["activity_key"])),
                "action_links": action_links,
                "workflow_html": _render_tokenized_workflow_text(str(scenario.get("workflow_text", "")), code, return_to=return_to),
            }
        )

    participant_key = (request.cookies.get(PARTICIPANT_COOKIE) or "").strip()
    participant = get_participant(participant_key) if participant_key else None
    participant_name = ""
    if participant and str(participant.get("session_code", "")).strip() == code:
        participant_name = str(participant.get("display_name", "")).strip()

    return render_template_string(
        """<!doctype html>
<html lang="en"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Workshop Launchpad | {{ session_code }}</title>
  <style>
    body { font-family: system-ui, sans-serif; line-height: 1.5; margin: 0; background: #f7fafc; }
    .page { max-width: 72rem; margin: 0 auto; padding: 1rem; }
    .card { background: #fff; border: 1px solid #ccd; border-radius: .5rem; padding: .9rem; margin: .85rem 0; }
    .token-list { display: flex; flex-wrap: wrap; list-style: none; padding: 0; gap: .4rem; }
    .token-list li { border: 1px solid #6b7280; border-radius: 999px; padding: .25rem .65rem; background: #fff; }
  </style>
</head><body><main class="page">
  <h1>Magical Exercise Launchpad</h1>
  <p><strong>Session:</strong> {{ session_code }} — {{ session_title }}</p>
  {% if participant_name %}<p><strong>Participant:</strong> {{ participant_name }} (<a href="{{ url_for('workshop.workshop_my_content', session_code=session_code) }}">My content</a>)</p>{% endif %}
  <p>Each scenario includes sample files, tokenized workflow guidance, and deep links into GLOW tools that preserve your way back.</p>

  {% for card in scenario_cards %}
  <section class="card" aria-labelledby="scenario-{{ card.id }}">
    <h2 id="scenario-{{ card.id }}">{{ card.title }}</h2>
    <p><strong>Goal:</strong> {{ card.goal }}</p>
    <p><strong>Suggested activity:</strong> <a href="{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key=card.activity_key) }}">{{ card.activity_title }}</a></p>
    <p><strong>Sample document:</strong> <a href="{{ url_for('workshop.workshop_sample_download', session_code=session_code, slug=card.sample_slug) }}">{{ card.sample_name }}</a></p>
    <p><strong>Tokenized workflow:</strong> {{ card.workflow_html }}</p>
    {% if card.action_links %}
    <ul class="token-list" aria-label="Scenario tool links">
      {% for action in card.action_links %}
        <li><a href="{{ action.href }}">{{ action.token }}</a></li>
      {% endfor %}
    </ul>
    {% endif %}
  </section>
  {% endfor %}

  <p>
    <a href="{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key=activity_key or 'journey_check_in') }}">Return to activity</a> |
    <a href="{{ url_for('workshop.workshop_gallery', session_code=session_code) }}">Open gallery</a> |
    <a href="{{ url_for('workshop.workshop_follow_through', session_code=session_code) }}">Follow-through</a>
  </p>
</main></body></html>""",
        session_code=code,
        session_title=session_meta.get("title", "GLOW Workshop Session"),
        participant_name=participant_name,
        scenario_cards=scenario_cards,
        activity_key=activity_key,
    )


@workshop_bp.route("/session/<session_code>/samples/<slug>", methods=["GET"])
def workshop_sample_download(session_code: str, slug: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    if get_session(code) is None:
        abort(404)

    filename = WORKSHOP_SAMPLE_FILES.get((slug or "").strip().lower())
    if not filename:
        abort(404)
    path = Path(current_app.root_path).parent.parent.parent / "samples" / filename
    if not path.exists():
        abort(404)
    return send_file(str(path), as_attachment=True, download_name=filename)


@workshop_bp.route("/session/<session_code>/me", methods=["GET"])
def workshop_my_content(session_code: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    if get_session(code) is None:
        abort(404)

    participant_key = (request.cookies.get(PARTICIPANT_COOKIE) or "").strip()
    participant = get_participant(participant_key) if participant_key else None
    if not participant or str(participant.get("session_code", "")).strip() != code:
        return render_template_string(
            """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>My Workshop Content | {{ session_code }}</title></head>
<body><main style="max-width:72rem;margin:0 auto;padding:1rem;font-family:system-ui,sans-serif;">
  <h1>My Workshop Content</h1>
  <p>We could not find your personal participant token for this session on this device.</p>
  <p><a href="{{ url_for('workshop.workshop_home', code=session_code) }}">Re-enter with session code</a></p>
</main></body></html>""",
            session_code=code,
        )

    if _active_login_email():
        bind_participant_login(str(participant.get("participant_key", "")), _active_login_email() or "")
    submissions = list_submissions_for_participant(code, str(participant.get("participant_key", "")))
    return render_template_string(
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>My Workshop Content | {{ session_code }}</title>
<style>
  body { font-family: system-ui, sans-serif; line-height: 1.5; margin: 0; background: #f8fafc; }
  main { max-width: 72rem; margin: 0 auto; padding: 1rem; }
  article { border: 1px solid #ccd; border-radius: .5rem; background: #fff; padding: .75rem; margin: .75rem 0; }
  pre { white-space: pre-wrap; }
</style>
</head>
<body><main>
  <h1>My Workshop Content</h1>
  <p><strong>Participant:</strong> {{ participant.display_name }} | <strong>Session:</strong> {{ session_code }}</p>
  {% if not submissions %}
    <p>No personal submissions yet.</p>
  {% else %}
    {% for item in submissions %}
      <article>
        <h2>{{ item.activity_key }}</h2>
        <p><strong>Updated:</strong> {{ item.updated_at_utc }}</p>
        <pre>{{ item.content_text }}</pre>
      </article>
    {% endfor %}
  {% endif %}
  <p>
    <a href="{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key='journey_check_in') }}">Continue workshop</a> |
    <a href="{{ url_for('workshop.workshop_gallery', session_code=session_code) }}">Open gallery</a>
  </p>
</main></body></html>""",
        session_code=code,
        participant=participant,
        submissions=submissions,
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
  <p>
    Export artifacts:
    <a href=\"{{ url_for('workshop.workshop_export_markdown', session_code=session_code) }}\">Markdown</a> |
    <a href=\"{{ url_for('workshop.workshop_export_json', session_code=session_code) }}\">JSON</a> |
    <a href=\"{{ url_for('workshop.workshop_export_html', session_code=session_code) }}\">HTML</a> |
    <a href=\"{{ url_for('workshop.workshop_export_docx', session_code=session_code) }}\">DOCX</a> |
    <a href=\"{{ url_for('workshop.workshop_follow_through', session_code=session_code) }}\">Follow-Through</a>
  </p>
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

        <h3>Promote to follow-through</h3>
        <form method=\"post\" action=\"{{ url_for('workshop.workshop_follow_through', session_code=session_code) }}\">
          <input type=\"hidden\" name=\"csrf_token\" value=\"{{ csrf_token() }}\">
          <input type=\"hidden\" name=\"source_submission_id\" value=\"{{ s.id }}\">
          <label>Kind
            <select name=\"item_kind\">
              <option value=\"template\">Reusable coaching template</option>
              <option value=\"checklist\">Checklist</option>
              <option value=\"action_commitment\">30-day action commitment</option>
            </select>
          </label>
          <label>Title <input type=\"text\" name=\"item_title\" value=\"{{ s.activity_key }} follow-through\"></label>
          <label>Owner <input type=\"text\" name=\"owner_name\" value=\"{% if s.anonymity_mode %}Workshop participant{% else %}{{ s.display_name }}{% endif %}\"></label>
          <label>Due date <input type=\"date\" name=\"due_date\"></label>
          <label>Details<textarea name=\"item_details\" required>{{ s.content_text }}</textarea></label>
          <p><button type=\"submit\">Save follow-through item</button></p>
        </form>
      </article>
    {% endfor %}
  {% endif %}
  <p>
    <a href=\"{{ url_for('workshop.workshop_home') }}\">Back to workshop home</a> |
    <a href=\"{{ url_for('workshop.workshop_facilitator', session_code=session_code) }}\">Facilitator dashboard</a> |
    <a href=\"{{ url_for('workshop.workshop_follow_through', session_code=session_code) }}\">Follow-through log</a>
  </p>
</main></body></html>
""",
        session_code=code,
        submissions=submissions,
        feedback=feedback,
        peer_review_enabled=_peer_review_enabled(),
    )


@workshop_bp.route("/session/<session_code>/follow-through", methods=["GET", "POST"])
def workshop_follow_through(session_code: str):
    if not _workshop_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    session_meta = get_session(code)
    if session_meta is None:
        abort(404)

    message = ""
    if request.method == "POST":
        kind = (request.form.get("item_kind") or "action_commitment").strip() or "action_commitment"
        title = (request.form.get("item_title") or "").strip()
        details = (request.form.get("item_details") or "").strip()
        owner_name = (request.form.get("owner_name") or "Participant").strip() or "Participant"
        due_date = (request.form.get("due_date") or "").strip() or None
        source_submission_id_raw = (request.form.get("source_submission_id") or "").strip()
        source_submission_id = int(source_submission_id_raw) if source_submission_id_raw.isdigit() else None

        if not title or not details:
            message = "Please add a title and details before saving."
        else:
            save_follow_through_item(
                code,
                kind,
                title,
                details,
                owner_name,
                due_date=due_date,
                source_submission_id=source_submission_id,
            )
            message = "Saved follow-through item."

    items = list_follow_through_items(code)
    templates = [item for item in items if item.get("kind") == "template"]
    checklists = [item for item in items if item.get("kind") == "checklist"]
    commitments = [item for item in items if item.get("kind") == "action_commitment"]

    return render_template_string(
        """<!doctype html>
<html lang="en"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Follow-Through | {{ session_code }}</title>
  <style>
    body { font-family: system-ui, sans-serif; line-height: 1.5; margin: 0; background: #f7fafc; }
    .page { max-width: 72rem; margin: 0 auto; padding: 1rem; }
    .panel { background: #fff; border: 1px solid #ccd; border-radius: .5rem; padding: .9rem; margin: .85rem 0; }
    label { display: block; margin-top: .5rem; }
    input[type=text], input[type=date], textarea, select { width: min(48rem, 100%); }
    textarea { min-height: 9rem; }
  </style>
</head><body><main class="page">
  <h1>Workshop Follow-Through</h1>
  <p><strong>Session:</strong> {{ session_code }} — {{ session_title }}</p>
  <p>This is where coaching outputs become reusable templates, checklists, and 30-day commitments.</p>
  {% if message %}<p role="status"><strong>{{ message }}</strong></p>{% endif %}

  <section class="panel" aria-labelledby="save-item">
    <h2 id="save-item">Save a follow-through item</h2>
    <form method="post" action="{{ url_for('workshop.workshop_follow_through', session_code=session_code) }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <label for="item_kind">Kind</label>
      <select id="item_kind" name="item_kind">
        <option value="action_commitment">30-day action commitment</option>
        <option value="template">Reusable coaching template</option>
        <option value="checklist">Checklist</option>
      </select>
      <label for="item_title">Title</label>
      <input id="item_title" name="item_title" type="text" required>
      <label for="owner_name">Owner</label>
      <input id="owner_name" name="owner_name" type="text" value="Participant">
      <label for="due_date">Due date</label>
      <input id="due_date" name="due_date" type="date">
      <label for="item_details">Details</label>
      <textarea id="item_details" name="item_details" required></textarea>
      <p><button type="submit">Save item</button></p>
    </form>
  </section>

  <section class="panel" aria-labelledby="commitments">
    <h2 id="commitments">30-day commitments</h2>
    {% if commitments %}
      <ul>
      {% for item in commitments %}
        <li>
          <strong>{{ item.title }}</strong> — {{ item.owner_name }}{% if item.due_date %} (due {{ item.due_date }}){% endif %}: {{ item.details }}
          <form method="post" action="{{ url_for('workshop.workshop_follow_through_status', session_code=session_code, item_id=item.id) }}" style="display:inline">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <input type="hidden" name="status" value="{% if item.status == 'done' %}open{% else %}done{% endif %}">
            <button type="submit">{% if item.status == 'done' %}Reopen{% else %}Mark complete{% endif %}</button>
          </form>
        </li>
      {% endfor %}
      </ul>
    {% else %}
      <p>No commitments saved yet.</p>
    {% endif %}
  </section>

  <section class="panel" aria-labelledby="templates">
    <h2 id="templates">Reusable coaching templates</h2>
    {% if templates %}
      <ul>
      {% for item in templates %}
        <li>
          <strong>{{ item.title }}</strong> — {{ item.owner_name }}: {{ item.details }}
          <form method="post" action="{{ url_for('workshop.workshop_follow_through_status', session_code=session_code, item_id=item.id) }}" style="display:inline">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <input type="hidden" name="status" value="{% if item.status == 'done' %}open{% else %}done{% endif %}">
            <button type="submit">{% if item.status == 'done' %}Reopen{% else %}Mark complete{% endif %}</button>
          </form>
        </li>
      {% endfor %}
      </ul>
    {% else %}
      <p>No templates saved yet.</p>
    {% endif %}
  </section>

  <section class="panel" aria-labelledby="checklists">
    <h2 id="checklists">Checklists</h2>
    {% if checklists %}
      <ul>
      {% for item in checklists %}
        <li>
          <strong>{{ item.title }}</strong> — {{ item.owner_name }}: {{ item.details }}
          <form method="post" action="{{ url_for('workshop.workshop_follow_through_status', session_code=session_code, item_id=item.id) }}" style="display:inline">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <input type="hidden" name="status" value="{% if item.status == 'done' %}open{% else %}done{% endif %}">
            <button type="submit">{% if item.status == 'done' %}Reopen{% else %}Mark complete{% endif %}</button>
          </form>
        </li>
      {% endfor %}
      </ul>
    {% else %}
      <p>No checklists saved yet.</p>
    {% endif %}
  </section>

  <p>
    <a href="{{ url_for('workshop.workshop_export_markdown', session_code=session_code) }}">Export workshop artifacts</a> |
    <a href="{{ url_for('workshop.workshop_follow_through_export', session_code=session_code) }}">Export follow-through markdown</a> |
    <a href="{{ url_for('workshop.workshop_home') }}">Back to workshop home</a>
  </p>
</main></body></html>""",
        session_code=code,
        session_title=session_meta.get("title", "GLOW Workshop Session"),
        message=message,
        commitments=commitments,
        templates=templates,
        checklists=checklists,
    )


@workshop_bp.route("/session/<session_code>/follow-through/export/markdown", methods=["GET"])
def workshop_follow_through_export(session_code: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    session_meta = get_session(code)
    if session_meta is None:
        abort(404)

    markdown = export_follow_through_markdown(code, session_title=session_meta.get("title", "GLOW Workshop Session"))
    return Response(
        markdown,
        mimetype="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{code}-follow-through.md"'},
    )


@workshop_bp.route("/session/<session_code>/follow-through/<int:item_id>/status", methods=["POST"])
def workshop_follow_through_status(session_code: str, item_id: int):
    if not _workshop_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    if get_session(code) is None:
        abort(404)

    status = (request.form.get("status") or "").strip().lower()
    if status not in {"open", "done", "paused"}:
        abort(400)

    update_follow_through_status(code, item_id, status)
    return redirect(url_for("workshop.workshop_follow_through", session_code=code))


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


@workshop_bp.route("/session/<session_code>/export/json", methods=["GET"])
def workshop_export_json(session_code: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    session_meta = get_session(code)
    if session_meta is None:
        abort(404)

    payload = export_session_json(code, session_title=session_meta.get("title", "GLOW Workshop Session"))
    return Response(
        payload,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{code}-workshop-artifacts.json"'},
    )


@workshop_bp.route("/session/<session_code>/export/html", methods=["GET"])
def workshop_export_html(session_code: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    session_meta = get_session(code)
    if session_meta is None:
        abort(404)

    html = export_session_html(code, session_title=session_meta.get("title", "GLOW Workshop Session"))
    return Response(
        html,
        mimetype="text/html",
        headers={"Content-Disposition": f'attachment; filename="{code}-workshop-artifacts.html"'},
    )


@workshop_bp.route("/session/<session_code>/export/docx", methods=["GET"])
def workshop_export_docx(session_code: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    session_meta = get_session(code)
    if session_meta is None:
        abort(404)

    try:
        content = export_session_docx_bytes(code, session_title=session_meta.get("title", "GLOW Workshop Session"))
    except ImportError:
        return Response("DOCX export unavailable: python-docx is not installed.", status=503, mimetype="text/plain")
    return Response(
        content,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{code}-workshop-artifacts.docx"'},
    )


@workshop_bp.route("/session/<session_code>/facilitator", methods=["GET"])
def workshop_facilitator(session_code: str):
    if not _workshop_enabled() or not _lab_hub_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    session_meta = get_session(code)
    if session_meta is None:
        abort(404)

    submissions = list_submissions(code)
    feedback = list_feedback_for_session(code)
    by_activity = {key: 0 for key in ACTIVITY_ORDER}
    anonymous_count = 0
    covered_feedback = 0
    for s in submissions:
        activity = s.get("activity_key", "")
        if activity in by_activity:
            by_activity[activity] += 1
        if int(s.get("anonymity_mode", 0)):
            anonymous_count += 1
        if feedback.get(int(s.get("id", 0))):
            covered_feedback += 1

    recent_submissions = submissions[:12]
    return render_template_string(
        """<!doctype html>
<html lang="en"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Facilitator Dashboard | {{ session_code }}</title>
  <style>
    body { font-family: system-ui, sans-serif; line-height: 1.5; margin: 0; background: #f7fafc; }
    .page { max-width: 72rem; margin: 0 auto; padding: 1rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: .75rem; }
    .card { background: #fff; border: 1px solid #ccd; border-radius: .5rem; padding: .8rem; }
    table { border-collapse: collapse; width: 100%; background: #fff; }
    th, td { border: 1px solid #ccd; padding: .45rem; text-align: left; }
    th { background: #eef3f9; }
  </style>
</head><body><main class="page">
  <h1>Facilitator Dashboard</h1>
  <p><strong>Session:</strong> {{ session_code }} — {{ session_title }}</p>

  <section class="grid" aria-label="Session metrics">
    <article class="card"><h2>Total submissions</h2><p>{{ total_submissions }}</p></article>
    <article class="card"><h2>Anonymous submissions</h2><p>{{ anonymous_count }}</p></article>
    <article class="card"><h2>Submissions with peer feedback</h2><p>{{ covered_feedback }}</p></article>
    <article class="card"><h2>Feedback coverage</h2><p>{{ feedback_coverage_pct }}%</p></article>
  </section>

  <h2>Activity completion snapshot</h2>
  <table>
    <thead><tr><th scope="col">Activity</th><th scope="col">Submission count</th></tr></thead>
    <tbody>
    {% for key, count in by_activity.items() %}
      <tr><th scope="row">{{ key }}</th><td>{{ count }}</td></tr>
    {% endfor %}
    </tbody>
  </table>

  <h2>Recent submissions</h2>
  {% if recent_submissions %}
  <table>
    <thead><tr><th scope="col">Updated (UTC)</th><th scope="col">Activity</th><th scope="col">Submitter</th><th scope="col">Peer feedback</th></tr></thead>
    <tbody>
    {% for s in recent_submissions %}
      <tr>
        <td>{{ s.updated_at_utc }}</td>
        <td>{{ s.activity_key }}</td>
        <td>{% if s.anonymity_mode %}Anonymous participant{% else %}{{ s.display_name }}{% endif %}</td>
        <td>{{ "Yes" if feedback.get(s.id) else "No" }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No submissions captured yet.</p>
  {% endif %}

  <p>
    <a href="{{ url_for('workshop.workshop_gallery', session_code=session_code) }}">Open gallery</a> |
    <a href="{{ url_for('workshop.workshop_export_markdown', session_code=session_code) }}">Export markdown</a> |
    <a href="{{ url_for('workshop.workshop_export_json', session_code=session_code) }}">Export json</a> |
    <a href="{{ url_for('workshop.workshop_export_html', session_code=session_code) }}">Export html</a> |
    <a href="{{ url_for('workshop.workshop_export_docx', session_code=session_code) }}">Export docx</a>
  </p>
</main></body></html>""",
        session_code=code,
        session_title=session_meta.get("title", "GLOW Workshop Session"),
        by_activity=by_activity,
        total_submissions=len(submissions),
        anonymous_count=anonymous_count,
        covered_feedback=covered_feedback,
        feedback_coverage_pct=(round((covered_feedback / len(submissions)) * 100, 1) if submissions else 0.0),
        recent_submissions=recent_submissions,
        feedback=feedback,
    )


@workshop_bp.route("/session/<session_code>/coach", methods=["GET"])
def workshop_coach(session_code: str):
    if not _workshop_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    if get_session(code) is None:
        abort(404)
    return render_template_string(
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Coach Mode | {{ session_code }}</title></head>
<body><main style="max-width:72rem;margin:0 auto;padding:1rem;font-family:system-ui,sans-serif;">
  <h1>Coach Mode</h1>
  <p>Use this surface to frame partner-centered coaching language that teaches ownership, not dependency.</p>
  <ul>
    <li>Start with the partner's real barrier and immediate need.</li>
    <li>Translate accessibility guidance into plain language the partner can reuse.</li>
    <li>Attach one human-review checkpoint before finalizing changes.</li>
  </ul>
  <p><a href="{{ url_for('workshop.workshop_activity', session_code=session_code, activity_key='teach_vs_fix') }}">Open Teach vs Fix activity</a></p>
  <p><a href="{{ url_for('workshop.workshop_home') }}">Back to workshop home</a></p>
</main></body></html>""",
        session_code=code,
    )


@workshop_bp.route("/session/<session_code>/review", methods=["GET"])
def workshop_review(session_code: str):
    if not _workshop_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    if get_session(code) is None:
        abort(404)
    return render_template_string(
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Review Mode | {{ session_code }}</title></head>
<body><main style="max-width:72rem;margin:0 auto;padding:1rem;font-family:system-ui,sans-serif;">
  <h1>Review Mode</h1>
  <p>Review keeps humans accountable for final context, policy fit, and disability-centered quality checks.</p>
  <ul>
    <li>Verify assumptions, audience context, and institutional requirements.</li>
    <li>Check whether proposed fixes are teachable and reusable by partners.</li>
    <li>Confirm each artifact has explicit safeguards and escalation points.</li>
  </ul>
  <p><a href="{{ url_for('workshop.workshop_gallery', session_code=session_code) }}">Open gallery for peer review</a></p>
  <p><a href="{{ url_for('workshop.workshop_home') }}">Back to workshop home</a></p>
</main></body></html>""",
        session_code=code,
    )


@workshop_bp.route("/session/<session_code>/share", methods=["GET"])
def workshop_share(session_code: str):
    if not _workshop_enabled():
        abort(404)
    try:
        code = normalize_session_code(session_code)
    except ValueError:
        abort(404)
    if get_session(code) is None:
        abort(404)
    return render_template_string(
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Share Mode | {{ session_code }}</title></head>
<body><main style="max-width:72rem;margin:0 auto;padding:1rem;font-family:system-ui,sans-serif;">
  <h1>Share Mode</h1>
  <p>Share mode packages workshop artifacts so teams can reuse strong workflows after the session.</p>
  <ul>
    <li>Publish anonymized gallery examples for team learning.</li>
    <li>Export artifacts as markdown, json, html, or docx for adoption and training.</li>
    <li>Promote proven workflows into templates and future GLOW skills.</li>
  </ul>
  <p>
    <a href="{{ url_for('workshop.workshop_export_markdown', session_code=session_code) }}">Export markdown</a> |
    <a href="{{ url_for('workshop.workshop_export_json', session_code=session_code) }}">Export json</a> |
    <a href="{{ url_for('workshop.workshop_export_html', session_code=session_code) }}">Export html</a> |
    <a href="{{ url_for('workshop.workshop_export_docx', session_code=session_code) }}">Export docx</a>
  </p>
  <p><a href="{{ url_for('workshop.workshop_home') }}">Back to workshop home</a></p>
</main></body></html>""",
        session_code=code,
    )


@workshop_bp.route("/guide", methods=["GET"])
def workshop_guide():
    if not _workshop_enabled():
        abort(404)

    return render_template_string(
        """<!doctype html>
<html lang=\"en\"><head>
  <meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Workshop Guide | GLOW</title>
  <style>
    :root { --ink:#112; --card:#ffffff; --line:#ccd; --hero1:#0a4b8f; --hero2:#0f766e; }
    body { margin:0; font-family: system-ui, sans-serif; color:var(--ink); line-height:1.55; background:#f7fafc; }
    .skip-link { position:absolute; left:-9999px; } .skip-link:focus { left:1rem; top:1rem; background:#fff; border:2px solid #000; padding:.5rem; }
    .hero { background: linear-gradient(120deg, var(--hero1), var(--hero2)); color:#fff; padding:2rem 1rem; }
    .wrap { max-width:72rem; margin:0 auto; }
    .hero h1 { margin:0 0 .5rem 0; }
    .hero p { margin:0; max-width:56rem; }
    .main { max-width:72rem; margin:0 auto; padding:1rem; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap:.75rem; }
    .card { background:var(--card); border:1px solid var(--line); border-radius:.5rem; padding:.875rem; }
    h2 { margin-top:1.25rem; }
    a.button { display:inline-block; background:#0a4b8f; color:#fff; padding:.55rem .85rem; border-radius:.35rem; text-decoration:none; }
    a.button:focus, a.button:hover { text-decoration:underline; }
  </style>
</head>
<body>
  <a class=\"skip-link\" href=\"#main\">Skip to main content</a>
  <header class=\"hero\"><div class=\"wrap\">
    <h1>Accessibility Agents in Action</h1>
    <p>A hands-on GLOW workshop design for conference and institutional training environments, centered on partner confidence, responsible AI use, and reusable accessibility workflows.</p>
  </div></header>
  <main id=\"main\" class=\"main\">
    <h2>Core Promise</h2>
    <p>Participants do not need to be AI scientists, developers, or programmers. They are guided through practical barriers and leave with artifacts that help others become accessibility champions.</p>
    <ul>
      <li><strong>G:</strong> Ground the work in a real accessibility problem.</li>
      <li><strong>L:</strong> Learn what people need to understand.</li>
      <li><strong>O:</strong> Organize a repeatable workflow.</li>
      <li><strong>W:</strong> Walk forward as accessibility champions.</li>
    </ul>

    <h2>Learning Outcomes</h2>
    <div class=\"grid\">
      <section class=\"card\"><h3>Problem-First Practice</h3><p>Teams start with user barriers and capacity goals before selecting tooling.</p></section>
      <section class=\"card\"><h3>Responsible AI Boundaries</h3><p>Every workflow defines what AI can draft and what humans must verify.</p></section>
      <section class=\"card\"><h3>Reusable Artifacts</h3><p>Participants leave with prompts, checklists, and action plans ready for immediate use.</p></section>
      <section class=\"card\"><h3>Champion Pathway</h3><p>Partners learn ownership patterns that scale accessibility beyond specialist bottlenecks.</p></section>
    </div>

    <h2>Use This Workshop Kit</h2>
    <p><a class=\"button\" href=\"{{ url_for('workshop.workshop_exercises') }}\">Open Exercises Pack</a> <a class=\"button\" href=\"{{ url_for('workshop.workshop_utilization') }}\">Open Utilization Guide</a></p>
    <p><a href=\"{{ url_for('workshop.workshop_home') }}\">Back to Workshop Mode home</a></p>
  </main>
</body></html>"""
    )


@workshop_bp.route("/exercises", methods=["GET"])
def workshop_exercises():
    if not _workshop_enabled():
        abort(404)

    return render_template_string(
        """<!doctype html>
<html lang=\"en\"><head>
  <meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Exercises Pack | GLOW Workshop Mode</title>
  <style>
    body { margin:0; font-family: system-ui, sans-serif; line-height:1.55; background:#f8fafc; }
    .page { max-width:72rem; margin:0 auto; padding:1rem; }
    .skip-link { position:absolute; left:-9999px; } .skip-link:focus { left:1rem; top:1rem; background:#fff; border:2px solid #000; padding:.5rem; }
    .exercise { background:#fff; border:1px solid #c9d2e3; border-radius:.5rem; padding:.875rem; margin:.75rem 0; }
    h1 { margin-bottom:.25rem; }
    h2 { margin-top:1.25rem; }
  </style>
</head><body>
  <a class=\"skip-link\" href=\"#main\">Skip to main content</a>
  <main id=\"main\" class=\"page\">
    <h1>Workshop Exercises Pack</h1>
    <p>These activities are conference-ready and aligned to the full-day schedule. Each activity is designed for practical output and human-review accountability.</p>
    {% for ex in exercises %}
      <section class=\"exercise\" aria-labelledby=\"ex-{{ loop.index }}\">
        <h2 id=\"ex-{{ loop.index }}\">{{ ex.name }}</h2>
        <p><strong>Time:</strong> {{ ex.time }}</p>
        <p><strong>Purpose:</strong> {{ ex.purpose }}</p>
        <p><strong>Participant Output:</strong> {{ ex.output }}</p>
      </section>
    {% endfor %}
    <p><a href=\"{{ url_for('workshop.workshop_guide') }}\">Back to Workshop Guide</a></p>
  </main>
</body></html>""",
        exercises=EXERCISE_PACK,
    )


@workshop_bp.route("/utilization", methods=["GET"])
def workshop_utilization():
    if not _workshop_enabled():
        abort(404)

    return render_template_string(
        """<!doctype html>
<html lang=\"en\"><head>
  <meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Utilization Guide | GLOW Workshop Mode</title>
  <style>
    body { margin:0; font-family: system-ui, sans-serif; line-height:1.55; background:#f8fafc; }
    .page { max-width:72rem; margin:0 auto; padding:1rem; }
    .skip-link { position:absolute; left:-9999px; } .skip-link:focus { left:1rem; top:1rem; background:#fff; border:2px solid #000; padding:.5rem; }
    .panel { background:#fff; border:1px solid #d1d5db; border-radius:.5rem; padding:.9rem; margin:.8rem 0; }
  </style>
</head><body>
  <a class=\"skip-link\" href=\"#main\">Skip to main content</a>
  <main id=\"main\" class=\"page\">
    <h1>Utilization Guide for Conference and Training</h1>
    <p>Use this guide to run Workshop Mode as a repeatable institutional experience with measurable learning outcomes.</p>

    <section class=\"panel\" aria-labelledby=\"preflight\">
      <h2 id=\"preflight\">Pre-Event Readiness</h2>
      <ul>
        <li>Enable workshop feature flags and validate route access.</li>
        <li>Run keyboard-only and screen-reader smoke tests.</li>
        <li>Prepare backup worksheets for offline fallback.</li>
        <li>Confirm facilitator script, timing, and support contacts.</li>
      </ul>
    </section>

    <section class=\"panel\" aria-labelledby=\"during\">
      <h2 id=\"during\">During Workshop Delivery</h2>
      <ul>
        <li>Keep framing on partner confidence and ownership.</li>
        <li>Require human-review checkpoints in every AI-assisted artifact.</li>
        <li>Use gallery + peer feedback to strengthen trust and reuse.</li>
        <li>Capture capstone artifacts and 30-day action commitments.</li>
      </ul>
    </section>

    <section class=\"panel\" aria-labelledby=\"after\">
      <h2 id=\"after\">Post-Event Follow Through</h2>
      <ul>
        <li>Export artifacts in Markdown for sharing and versioning.</li>
        <li>Package top workflows into prompts/checklists for local teams.</li>
        <li>Run a 30-day follow-up to measure adoption and confidence gains.</li>
        <li>Promote successful workflows into reusable GLOW skills.</li>
      </ul>
    </section>

    <section class=\"panel\" aria-labelledby=\"metrics\">
      <h2 id=\"metrics\">Utilization Metrics</h2>
      <ul>
        <li>Activity completion rates</li>
        <li>Capstone workflow quality and safeguard coverage</li>
        <li>Artifact reuse at 30 days</li>
        <li>Participant confidence delta (pre/post)</li>
      </ul>
    </section>

    <p>
      Download resources:
      <a href=\"{{ url_for('workshop.workshop_resource_download', slug='guide') }}\">Guide (.md)</a>,
      <a href=\"{{ url_for('workshop.workshop_resource_download', slug='exercises') }}\">Exercises (.md)</a>,
      <a href=\"{{ url_for('workshop.workshop_resource_download', slug='utilization') }}\">Utilization (.md)</a>
    </p>
    <p><a href=\"{{ url_for('workshop.workshop_guide') }}\">Back to Workshop Guide</a></p>
  </main>
</body></html>"""
    )


@workshop_bp.route("/resources/<slug>", methods=["GET"])
def workshop_resource_download(slug: str):
    if not _workshop_enabled():
        abort(404)
    filename = RESOURCE_FILES.get((slug or "").strip().lower())
    if not filename:
        abort(404)

    repo_root = Path(current_app.root_path).parent.parent.parent
    path = repo_root / "docs" / filename
    if not path.exists():
        abort(404)

    return send_file(
        str(path),
        mimetype="text/markdown",
        as_attachment=True,
        download_name=filename,
    )
