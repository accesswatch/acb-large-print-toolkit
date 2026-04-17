"""Consent gate -- first-visit privacy agreement.

Every first-time visitor is redirected here before accessing any tool.
Agreement is stored in a long-lived cookie (glow_consent_v1).

Routes:
  GET  /consent          -- show the agreement page
  POST /consent          -- record agreement, set cookie, redirect to ?next=
"""

from __future__ import annotations

from datetime import timedelta

from flask import (
    Blueprint,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

consent_bp = Blueprint("consent", __name__)

#: Cookie name.  Increment the suffix if the agreement text changes materially
#: so that returning users are asked to re-agree.
CONSENT_COOKIE_NAME = "glow_consent_v1"
CONSENT_COOKIE_MAX_AGE = int(timedelta(days=365).total_seconds())

#: Routes the consent gate never intercepts.  Keep this list minimal.
CONSENT_EXEMPT_PREFIXES = (
    "/consent",
    "/static",
    "/health",
    "/privacy",
    "/favicon",
)


def has_consent(req) -> bool:
    """Return True if the visitor has already agreed."""
    return req.cookies.get(CONSENT_COOKIE_NAME) == "1"


def consent_required(req) -> bool:
    """Return True if this request should trigger the consent redirect."""
    path = req.path.rstrip("/") or "/"
    if any(path.startswith(prefix) for prefix in CONSENT_EXEMPT_PREFIXES):
        return False
    return not has_consent(req)


@consent_bp.route("/", methods=["GET"])
def consent_form():
    next_url = request.args.get("next") or url_for("main.index")
    # Reject open-redirect: only accept relative paths
    if next_url.startswith(("http://", "https://", "//")):
        next_url = url_for("main.index")
    return render_template("consent.html", next_url=next_url)


@consent_bp.route("/", methods=["POST"])
def consent_submit():
    agreed = request.form.get("agreed") == "yes"
    next_url = request.form.get("next_url") or url_for("main.index")

    # Reject open-redirect
    if next_url.startswith(("http://", "https://", "//")):
        next_url = url_for("main.index")

    if not agreed:
        return render_template(
            "consent.html",
            next_url=next_url,
            error="You must agree to the terms before continuing.",
        ), 400

    resp = make_response(redirect(next_url))
    resp.set_cookie(
        CONSENT_COOKIE_NAME,
        "1",
        max_age=CONSENT_COOKIE_MAX_AGE,
        httponly=True,
        samesite="Strict",
        secure=request.is_secure,
    )
    return resp


@consent_bp.route("/withdraw", methods=["POST"])
def consent_withdraw():
    """Clear the consent cookie so the user is asked to agree again next visit."""
    resp = make_response(redirect(url_for("consent.consent_form")))
    resp.delete_cookie(CONSENT_COOKIE_NAME, samesite="Strict")
    return resp
