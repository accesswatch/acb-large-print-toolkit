"""
OIDC Authentication integration for GLOW (Keycloak + Google login)
"""

from flask import Blueprint, redirect, url_for, session, g
from flask_oidc import OpenIDConnect
from functools import wraps

# OIDC config is expected in client_secrets.json (downloaded from Keycloak)
# Example Flask app config:
# OIDC_CLIENT_SECRETS = 'client_secrets.json'
# OIDC_RESOURCE_SERVER_ONLY = False
# OIDC_SCOPES = ['openid', 'email', 'profile']

# Initialize OIDC in your app factory:
#   oidc = OpenIDConnect(app)
#   app.register_blueprint(oidc_auth_bp)

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
    oidc = OpenIDConnect.current_app
    g.oidc_id_token = oidc.get_access_token() if oidc.user_loggedin else None
    g.oidc_user_info = oidc.user_getinfo(['email', 'sub', 'roles']) if oidc.user_loggedin else {}

# Example protected route usage:
#
# @app.route('/facilitator')
# @require_login
# @require_role('facilitator')
# def facilitator_dashboard():
#     ...

# To use:
# 1. Add Flask-OIDC to requirements.txt
# 2. Download client_secrets.json from Keycloak and place in web/src/acb_large_print_web/
# 3. Add OIDC config to Flask app config
# 4. Register oidc_auth_bp in your app factory
# 5. Use @require_login and @require_role decorators on protected routes
