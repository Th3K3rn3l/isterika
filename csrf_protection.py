"""
Simple CSRF protection for Flask API endpoints
"""
from functools import wraps
from flask import session, request, jsonify
import secrets

def generate_csrf_token():
    """Generate a new CSRF token and store it in session"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']

def get_csrf_token():
    """Get the current CSRF token from session"""
    return session.get('csrf_token')

def csrf_protect(f):
    """Decorator to protect API endpoints from CSRF attacks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only check CSRF for state-changing methods
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = None

            # Check for token in headers first (most common for API calls)
            token = request.headers.get('X-CSRF-Token')

            # If not in headers, check JSON body
            if not token and request.is_json:
                token = request.json.get('csrf_token')

            # If not in JSON, check form data
            if not token and request.form:
                token = request.form.get('csrf_token')

            session_token = session.get('csrf_token')

            if not token or not session_token or token != session_token:
                return jsonify({'error': 'CSRF token missing or invalid'}), 403

        return f(*args, **kwargs)

    return decorated_function
