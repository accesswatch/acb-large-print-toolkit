import requests
from flask import Blueprint, jsonify

status_bp = Blueprint('status', __name__)

@status_bp.route('/health/keycloak')
def health_keycloak():
    try:
        resp = requests.get('http://keycloak:8080/realms/master', timeout=3)
        if resp.status_code == 200:
            return jsonify({'keycloak': 'ok'}), 200
        return jsonify({'keycloak': 'unhealthy'}), 503
    except Exception:
        return jsonify({'keycloak': 'unreachable'}), 503

# ...existing status endpoints...
