"""OIDC Authentication integration for GLOW (Keycloak)."""

from flask import Blueprint, current_app, g, redirect, session, url_for
from flask_oidc import OpenIDConnect
from functools import wraps

oidc_auth_bp = Blueprint('oidc_auth', __name__)

# Decorator for requiring login

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.oidc_id_token or not g.oidc_user_info:
            return redirect(url_for('oidc_auth.login', next=url_for(f.__name__)))
        return f(*args, **kwargs)
    return decorated

# Decorator for requiring a specific role

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_roles = g.oidc_user_info.get('roles', [])
            if role not in user_roles:
                return "Access denied: missing role", 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@oidc_auth_bp.route('/login')
def login():
    # OIDC login flow
    return redirect(url_for('oidc.login'))

@oidc_auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('oidc.logout'))

@oidc_auth_bp.before_app_request
def load_user():
    # Attach OIDC user info to flask.g for easy access
    oidc = current_app.extensions.get("oidc")
    if oidc and oidc.user_loggedin:
        g.oidc_id_token = oidc.get_access_token()
        g.oidc_user_info = oidc.user_getinfo(["email", "sub", "roles"])
    else:
        g.oidc_id_token = None
        g.oidc_user_info = {}
