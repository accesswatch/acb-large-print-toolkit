"""Authentication routes centered on Firebase sign-in and SQLAlchemy user RBAC.

URL prefix: /auth

Routes
──────
    GET/POST /auth/login
        POST     /auth/firebase-login
    GET/POST /auth/register
    GET      /auth/logout
    GET      /auth/verify-email/<token>
    GET/POST /auth/forgot-password
    GET/POST /auth/reset-password/<token>
    GET      /auth/oauth/<provider>           redirect to provider (legacy)
    GET      /auth/oauth/<provider>/callback  OAuth callback (legacy)

Supported login methods in the UI
─────────────────────────────────
    - Firebase Email Link (passwordless)
    - Firebase GitHub OAuth

The backend verifies Firebase ID tokens and creates/links SQLAlchemy users,
then establishes the server session via Flask-Login.
"""

from __future__ import annotations

import logging
import os
import re
import secrets
from datetime import UTC, datetime, timedelta

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

log = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)

# Minimum password length
_MIN_PASSWORD_LEN = 10
# Password reset token valid for
_RESET_EXPIRY_HOURS = 2
# Passwordless magic-link validity
_MAGIC_LINK_EXPIRY_MINUTES = 20
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_after_login():
    """Return the post-login destination (safe, same-origin)."""
    next_url = request.args.get("next") or session.pop("_login_next", None) or ""
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(url_for("account.dashboard"))


def _available_providers() -> list[dict]:
    """Return configured OAuth providers for the login UI.

    Currently restricted to GitHub only.  Add other providers here once
    their credentials are configured and tested.
    """
    providers = []
    if os.environ.get("GITHUB_CLIENT_ID"):
        providers.append({"id": "github", "label": "GitHub", "icon": "github"})
    return providers


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Registration is handled by Firebase email-link or GitHub on the login page.
    return redirect(url_for("auth.login"))


def _validate_registration(email: str, display_name: str, password: str, confirm: str) -> str | None:
    import re
    if not email or "@" not in email:
        return "A valid email address is required."
    if len(password) < _MIN_PASSWORD_LEN:
        return f"Password must be at least {_MIN_PASSWORD_LEN} characters."
    if password != confirm:
        return "Passwords do not match."
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return "Email address format is invalid."
    return None


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_after_login()

    if request.method == "POST":
        flash("Password sign-in is disabled. Use Email Link or GitHub.", "info")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/login.html",
        firebase_auth_enabled=(os.environ.get("FIREBASE_AUTH_ENABLED", "0") == "1"),
        firebase_web_api_key=(os.environ.get("FIREBASE_WEB_API_KEY") or ""),
        firebase_auth_domain=(os.environ.get("FIREBASE_AUTH_DOMAIN") or ""),
        firebase_project_id=(os.environ.get("FIREBASE_PROJECT_ID") or ""),
        firebase_app_id=(os.environ.get("FIREBASE_APP_ID") or ""),
        firebase_measurement_id=(os.environ.get("FIREBASE_MEASUREMENT_ID") or ""),
    )


@auth_bp.route("/firebase-login", methods=["POST"])
def firebase_login():
    """Sign in using a Firebase ID token posted by the browser/app client."""
    payload = request.get_json(silent=True) or {}
    id_token = str(payload.get("idToken") or "").strip()
    if not id_token:
        return jsonify({"ok": False, "error": "Missing Firebase ID token."}), 400

    from .. import firebase_auth

    if not firebase_auth.is_enabled():
        return jsonify({"ok": False, "error": "Firebase authentication is disabled."}), 403

    try:
        claims = firebase_auth.verify_id_token(id_token)
    except Exception as exc:
        log.warning("firebase_login: token verification failed: %s", exc)
        return jsonify({"ok": False, "error": "Invalid or expired Firebase token."}), 401

    email = str(claims.get("email") or "").strip().lower()
    if not email:
        return jsonify({"ok": False, "error": "Firebase token does not include an email address."}), 400

    provider_uid = str(claims.get("uid") or "")
    display_name = str(claims.get("name") or claims.get("email", "")).strip()
    email_verified = bool(claims.get("email_verified", False))
    sign_in_provider = str((claims.get("firebase") or {}).get("sign_in_provider") or "").strip()
    auth_provider = "github" if sign_in_provider == "github.com" else "passwordless"

    user = _find_or_create_firebase_user(
        email=email,
        uid=provider_uid,
        display_name=display_name,
        email_verified=email_verified,
        auth_provider=auth_provider,
    )
    _complete_login(user)
    return jsonify({"ok": True, "redirect": url_for("account.dashboard")})


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@auth_bp.route("/logout")
@login_required
def logout():
    from ..profile_sync import save_session_to_profile
    try:
        save_session_to_profile(current_user)
    except Exception:
        log.exception("logout: profile save failed for user %d", current_user.id)
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

@auth_bp.route("/verify-email/<token>")
def verify_email(token: str):
    from ..db import db
    from ..models import User
    user = db.session.execute(
        db.select(User).where(User.email_verify_token == token)
    ).scalar_one_or_none()
    if not user:
        flash("Verification link is invalid or has already been used.", "error")
        return redirect(url_for("auth.login"))
    user.is_email_verified = True
    user.email_verify_token = None
    db.session.commit()
    flash("Email verified. You can now sign in.", "success")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    sent = False
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        from ..db import db
        from ..models import User
        user = db.session.execute(
            db.select(User).where(User.email == email, User.auth_provider == "local")
        ).scalar_one_or_none()
        if user:
            user.password_reset_token = secrets.token_urlsafe(32)
            user.password_reset_expires = datetime.now(UTC) + timedelta(hours=_RESET_EXPIRY_HOURS)
            db.session.commit()
            _send_reset_email(user)
        # Always show same message to prevent email enumeration
        sent = True
    return render_template("auth/forgot_password.html", sent=sent)


@auth_bp.route("/magic-link", methods=["POST"])
def request_magic_link():
    flash("Use the login page Email Link button. Sign-in links are sent by Firebase.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/magic-link/<token>")
def magic_link_login(token: str):
    flash("This sign-in link is no longer supported. Use Firebase Email Link from the login page.", "error")
    return redirect(url_for("auth.login"))


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    from ..db import db
    from ..models import User
    user = db.session.execute(
        db.select(User).where(User.password_reset_token == token)
    ).scalar_one_or_none()

    if not user or not user.password_reset_expires:
        flash("Reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))
    if user.password_reset_expires < datetime.now(UTC):
        flash("Reset link has expired. Please request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    error = None
    if request.method == "POST":
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        if len(password) < _MIN_PASSWORD_LEN:
            error = f"Password must be at least {_MIN_PASSWORD_LEN} characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            user.set_password(password)
            user.password_reset_token = None
            user.password_reset_expires = None
            db.session.commit()
            flash("Password updated. You can now sign in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token, error=error)


# ---------------------------------------------------------------------------
# OAuth: redirect to provider
# ---------------------------------------------------------------------------

@auth_bp.route("/oauth/<provider>")
def oauth_redirect(provider: str):
    if provider not in _OAUTH_CONFIGS:
        abort_with_flash("OAuth provider not configured.", 404)

    cfg = _OAUTH_CONFIGS.get(provider, {})
    if not cfg.get("client_id"):
        abort_with_flash(f"{provider.title()} OAuth is not configured on this server.", 400)

    oauth = _get_oauth()
    client = getattr(oauth, provider, None)
    if not client:
        abort_with_flash("OAuth client not available.", 500)

    callback_url = url_for("auth.oauth_callback", provider=provider, _external=True)
    # Store provider in session to verify in callback
    session["_oauth_provider"] = provider
    return client.authorize_redirect(callback_url)


@auth_bp.route("/oauth/<provider>/callback")
def oauth_callback(provider: str):
    if provider not in _OAUTH_CONFIGS:
        abort_with_flash("OAuth provider not configured.", 404)

    oauth = _get_oauth()
    client = getattr(oauth, provider, None)
    if not client:
        abort_with_flash("OAuth client not available.", 500)

    try:
        token = client.authorize_access_token()
    except Exception as exc:
        log.warning("OAuth callback error for %s: %s", provider, exc)
        flash("Authentication failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    user_info = _extract_user_info(provider, token, client)
    if not user_info.get("email"):
        flash("Could not retrieve your email from the provider.", "error")
        return redirect(url_for("auth.login"))

    user = _find_or_create_oauth_user(provider, user_info)
    _complete_login(user)
    return _redirect_after_login()


# ---------------------------------------------------------------------------
# OAuth configuration registry
# ---------------------------------------------------------------------------

_OAUTH_CONFIGS: dict[str, dict] = {
    "google": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
        "client_kwargs": {"scope": "openid email profile"},
    },
    "github": {
        "client_id": os.environ.get("GITHUB_CLIENT_ID", ""),
        "client_secret": os.environ.get("GITHUB_CLIENT_SECRET", ""),
        "authorize_url": "https://github.com/login/oauth/authorize",
        "access_token_url": "https://github.com/login/oauth/access_token",
        "userinfo_endpoint": "https://api.github.com/user",
        "client_kwargs": {"scope": "read:user user:email"},
    },
    "microsoft": {
        "client_id": os.environ.get("MICROSOFT_CLIENT_ID", ""),
        "client_secret": os.environ.get("MICROSOFT_CLIENT_SECRET", ""),
        "server_metadata_url": (
            f"https://login.microsoftonline.com/"
            f"{os.environ.get('MICROSOFT_TENANT_ID', 'common')}"
            "/v2.0/.well-known/openid-configuration"
        ),
        "client_kwargs": {"scope": "openid email profile"},
    },
    "apple": {
        "client_id": os.environ.get("APPLE_CLIENT_ID", ""),
        "client_secret": os.environ.get("APPLE_CLIENT_SECRET", ""),
        "server_metadata_url": "https://appleid.apple.com/.well-known/openid-configuration",
        "client_kwargs": {"scope": "openid email name"},
    },
    "auth0": {
        "client_id": os.environ.get("AUTH0_CLIENT_ID", ""),
        "client_secret": os.environ.get("AUTH0_CLIENT_SECRET", ""),
        "server_metadata_url": (
            f"https://{os.environ.get('AUTH0_DOMAIN', '')}/.well-known/openid-configuration"
        ),
        "client_kwargs": {"scope": "openid email profile"},
    },
    "wordpress": {
        "client_id": os.environ.get("WORDPRESS_CLIENT_ID", ""),
        "client_secret": os.environ.get("WORDPRESS_CLIENT_SECRET", ""),
        # WordPress OAuth Server plugin endpoints (relative to base URL)
        "authorize_url": os.environ.get("WORDPRESS_BASE_URL", "").rstrip("/") + "/oauth/authorize",
        "access_token_url": os.environ.get("WORDPRESS_BASE_URL", "").rstrip("/") + "/oauth/token",
        "userinfo_endpoint": os.environ.get("WORDPRESS_BASE_URL", "").rstrip("/") + "/oauth/me",
        "client_kwargs": {"scope": "basic"},
    },
}

_oauth_instance = None


def _get_oauth():
    """Return the app-level Authlib OAuth registry (created once)."""
    global _oauth_instance
    if _oauth_instance is None:
        from authlib.integrations.flask_client import OAuth
        _oauth_instance = OAuth(current_app._get_current_object())  # type: ignore[attr-defined]
        for name, cfg in _OAUTH_CONFIGS.items():
            if not cfg.get("client_id"):
                continue
            register_kwargs = {
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "client_kwargs": cfg.get("client_kwargs", {}),
            }
            if "server_metadata_url" in cfg:
                register_kwargs["server_metadata_url"] = cfg["server_metadata_url"]
            else:
                register_kwargs["authorize_url"] = cfg.get("authorize_url", "")
                register_kwargs["access_token_url"] = cfg.get("access_token_url", "")
            # GitHub returns JSON by default; Authlib needs this hint
            if name == "github":
                register_kwargs["client_kwargs"]["token_endpoint_auth_method"] = "client_secret_post"
            _oauth_instance.register(name, **register_kwargs)
    return _oauth_instance


def _extract_user_info(provider: str, token: dict, client) -> dict:
    """Normalise user info from the provider's token/userinfo response."""
    if provider in ("google", "microsoft", "auth0", "apple"):
        userinfo = token.get("userinfo")
        if not userinfo:
            try:
                userinfo = client.userinfo()
            except Exception:
                userinfo = token.get("id_token_claims") or {}
        return {
            "sub": str(userinfo.get("sub") or userinfo.get("oid") or ""),
            "email": str(userinfo.get("email") or "").strip().lower(),
            "name": str(userinfo.get("name") or ""),
        }
    if provider == "github":
        # Fetch user profile
        resp = client.get("https://api.github.com/user", token=token)
        data = resp.json()
        email = str(data.get("email") or "").strip().lower()
        if not email:
            # GitHub may hide the primary email; fetch from /user/emails
            try:
                emails_resp = client.get("https://api.github.com/user/emails", token=token)
                for entry in emails_resp.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = str(entry["email"]).strip().lower()
                        break
                if not email:
                    # Fall back to any verified address
                    for entry in emails_resp.json():
                        if entry.get("verified"):
                            email = str(entry["email"]).strip().lower()
                            break
            except Exception:
                pass
        return {
            "sub": str(data.get("id") or ""),
            "email": email,
            "name": str(data.get("name") or data.get("login") or ""),
        }
    if provider == "wordpress":
        # WordPress OAuth Me endpoint
        wp_base = os.environ.get("WORDPRESS_BASE_URL", "").rstrip("/")
        resp = client.get(wp_base + "/oauth/me", token=token)
        data = resp.json()
        return {
            "sub": str(data.get("ID") or data.get("id") or ""),
            "email": str(data.get("user_email") or data.get("email") or "").strip().lower(),
            "name": str(data.get("display_name") or data.get("name") or ""),
        }
    return {}


# ---------------------------------------------------------------------------
# User creation / linking helpers
# ---------------------------------------------------------------------------

def _find_or_create_oauth_user(provider: str, user_info: dict):
    """Return (or create) a User for the given OAuth identity."""
    from ..db import db
    from ..models import User, UserOAuthIdentity

    email = user_info["email"]
    external_id = user_info["sub"]

    # 1. Exact OAuth identity match
    identity = db.session.execute(
        db.select(UserOAuthIdentity).where(
            UserOAuthIdentity.provider == provider,
            UserOAuthIdentity.external_id == external_id,
        )
    ).scalar_one_or_none()
    if identity:
        identity.last_used_at = datetime.now(UTC)
        db.session.commit()
        return identity.user

    # 2. Email match → link new identity to existing account
    user = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user:
        # 3. Create new account
        user = User(
            email=email,
            display_name=user_info.get("name") or email.split("@")[0],
            auth_provider=provider,
            is_email_verified=True,  # Provider has verified the email
        )
        db.session.add(user)
        db.session.flush()

    identity = UserOAuthIdentity(
        user_id=user.id,
        provider=provider,
        external_id=external_id,
        last_used_at=datetime.now(UTC),
    )
    db.session.add(identity)
    db.session.commit()
    return user


def _find_or_create_firebase_user(
    *,
    email: str,
    uid: str,
    display_name: str,
    email_verified: bool,
    auth_provider: str,
):
    """Find or create a local account from Firebase claims."""
    from ..db import db
    from ..models import User, UserOAuthIdentity

    identity = db.session.execute(
        db.select(UserOAuthIdentity).where(
            UserOAuthIdentity.provider == "firebase",
            UserOAuthIdentity.external_id == uid,
        )
    ).scalar_one_or_none()
    if identity:
        identity.last_used_at = datetime.now(UTC)
        identity.user.auth_provider = auth_provider
        if email_verified:
            identity.user.is_email_verified = True
        db.session.commit()
        return identity.user

    user = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            display_name=display_name or email.split("@")[0],
            auth_provider=auth_provider,
            is_email_verified=email_verified,
        )
        db.session.add(user)
        db.session.flush()
    else:
        if display_name and (not user.display_name or user.display_name == user.email.split("@")[0]):
            user.display_name = display_name
        user.auth_provider = auth_provider
        if email_verified:
            user.is_email_verified = True

    identity = UserOAuthIdentity(
        user_id=user.id,
        provider="firebase",
        external_id=uid,
        last_used_at=datetime.now(UTC),
    )
    db.session.add(identity)
    db.session.commit()
    return user


def _complete_login(user) -> None:
    """Finish a successful login: update DB, load profile, set Flask-Login state."""
    from ..db import db
    from ..profile_sync import load_profile_to_session
    user.touch_login()
    db.session.commit()
    login_user(user, remember=bool(request.form.get("remember_me")))
    load_profile_to_session(user)
    log.info("login: user %d (%s) via %s", user.id, user.email, user.auth_provider)


# ---------------------------------------------------------------------------
# Email helpers (graceful no-op when Flask-Mail is not configured)
# ---------------------------------------------------------------------------

def _send_verification_email(user) -> None:
    link = url_for("auth.verify_email", token=user.email_verify_token, _external=True)
    _send_auth_email(
        to=user.email,
        subject="Verify your GLOW account",
        body=(
            f"Hello {user.display_name},\n\n"
            f"Click the link below to verify your email address:\n{link}\n\n"
            f"If you did not create a GLOW account, you can ignore this email.\n"
        ),
    )


def _send_reset_email(user) -> None:
    link = url_for("auth.reset_password", token=user.password_reset_token, _external=True)
    _send_auth_email(
        to=user.email,
        subject="Reset your GLOW password",
        body=(
            f"Hello {user.display_name},\n\n"
            f"Click the link below to reset your password (valid for {_RESET_EXPIRY_HOURS} hours):\n"
            f"{link}\n\n"
            f"If you did not request a password reset, you can ignore this email.\n"
        ),
    )


def _send_magic_link_email(user, token: str) -> None:
    link = url_for("auth.magic_link_login", token=token, _external=True)
    _send_auth_email(
        to=user.email,
        subject="Your GLOW sign-in link",
        body=(
            f"Hello {user.display_name},\n\n"
            f"Use the link below to sign in (valid for {_MAGIC_LINK_EXPIRY_MINUTES} minutes):\n"
            f"{link}\n\n"
            "If you did not request this, you can ignore this email.\n"
        ),
    )


def _magic_link_serializer() -> URLSafeTimedSerializer:
    secret = current_app.config.get("SECRET_KEY") or os.environ.get("SECRET_KEY", "")
    return URLSafeTimedSerializer(str(secret))


def _make_magic_link_token(email: str) -> str:
    return _magic_link_serializer().dumps({"email": email}, salt="auth-magic-link")


def _verify_magic_link_token(token: str) -> str | None:
    try:
        payload = _magic_link_serializer().loads(
            token,
            salt="auth-magic-link",
            max_age=_MAGIC_LINK_EXPIRY_MINUTES * 60,
        )
        email = str(payload.get("email") or "").strip().lower()
        if not email or not _EMAIL_RE.match(email):
            return None
        return email
    except (BadSignature, SignatureExpired):
        return None


def _send_auth_email(to: str, subject: str, body: str) -> None:
    try:
        from flask_mail import Message
        from ..email import mail
        msg = Message(subject=subject, recipients=[to], body=body)
        mail.send(msg)
    except Exception:
        log.exception("auth: failed to send email to %s (subject: %s)", to, subject)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def abort_with_flash(message: str, code: int):
    flash(message, "error")
    return redirect(url_for("auth.login"))
