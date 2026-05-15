"""Workshop mode routes for training and conference delivery (7.3.0).

These routes provide an accessible, non-technical entry point for
facilitator-led workshops based on the GLOW framework.
"""

from __future__ import annotations

from flask import Blueprint, abort, render_template_string

from ..feature_flags import get_flag

workshop_bp = Blueprint("workshop", __name__)


def _workshop_enabled() -> bool:
    return bool(get_flag("GLOW_ENABLE_WORKSHOP_MODE", True))


@workshop_bp.route("/", methods=["GET"])
def workshop_home():
    if not _workshop_enabled():
        abort(404)

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

        <section aria-labelledby=\"promise-heading\">
            <h2 id=\"promise-heading\">Workshop Promise</h2>
            <ol>
                <li><strong>G</strong>round the work in a real accessibility problem.</li>
                <li><strong>L</strong>earn what people need to understand.</li>
                <li><strong>O</strong>rganize a repeatable workflow.</li>
                <li><strong>W</strong>alk forward as accessibility champions.</li>
            </ol>
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
                    <tr>
                        <th scope=\"col\">Time</th>
                        <th scope=\"col\">Session</th>
                        <th scope=\"col\">Primary Mode</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in schedule %}
                    <tr>
                        <th scope=\"row\">{{ item.time }}</th>
                        <td>{{ item.title }}</td>
                        <td>{{ item.mode }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>

        <section aria-labelledby=\"labhub-heading\">
            <h2 id=\"labhub-heading\">Lab Hub Feature Status</h2>
            <ul>
                <li>Guided forms: {% if workshop_lab_hub_enabled %}Enabled{% else %}Disabled{% endif %}</li>
                <li>Shared gallery: {% if workshop_gallery_enabled %}Enabled{% else %}Disabled{% endif %}</li>
                <li>Peer review workflow: {% if workshop_peer_review_enabled %}Enabled{% else %}Disabled{% endif %}</li>
            </ul>
        </section>
    </main>
</body>
</html>""",
        schedule=schedule,
        outcomes=outcomes,
        workshop_lab_hub_enabled=bool(get_flag("GLOW_ENABLE_WORKSHOP_LAB_HUB", True)),
        workshop_gallery_enabled=bool(get_flag("GLOW_ENABLE_WORKSHOP_GALLERY", True)),
        workshop_peer_review_enabled=bool(get_flag("GLOW_ENABLE_WORKSHOP_PEER_REVIEW", True)),
    )
