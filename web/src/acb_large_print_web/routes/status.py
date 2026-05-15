import requests
from flask import Blueprint, jsonify

from ..keycloak import get_keycloak_health_url

status_bp = Blueprint('status', __name__)

@status_bp.route('/health/keycloak')
def health_keycloak():
    url = get_keycloak_health_url()
    if not url:
        return jsonify({'keycloak': 'not-configured'}), 503
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            return jsonify({'keycloak': 'ok'}), 200
        return jsonify({'keycloak': 'unhealthy'}), 503
    except Exception:
        return jsonify({'keycloak': 'unreachable'}), 503

# ...existing status endpoints...
