"""
auth.py
Week 23 — Pluggable Authentication Layer & Decorators.
"""

import hmac
import hashlib
import base64
import json
import datetime
from functools import wraps
from flask import request, jsonify
import config

class AuthProvider:
    """
    Pluggable Authentication Provider Interface (Refinement 1)
    """
    def issue_token(self, email, role):
        raise NotImplementedError()
        
    def verify_token(self, token):
        raise NotImplementedError()


class HMACTokenProvider(AuthProvider):
    """
    HMAC-SHA256 Token Provider implementation of AuthProvider
    """
    def __init__(self, secret_key):
        self.secret_key = secret_key.encode('utf-8')

    def issue_token(self, email, role):
        # Set token expiration to 24 hours from now
        exp = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)).isoformat()
        payload = {
            "email": email,
            "role": role,
            "exp": exp
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('utf-8')
        
        # Sign payload
        signature = hmac.new(self.secret_key, payload_bytes, hashlib.sha256).hexdigest()
        
        # Combine
        return f"{payload_b64}.{signature}"

    def verify_token(self, token):
        if not token:
            return None
            
        parts = token.split(".")
        if len(parts) != 2:
            return None
            
        payload_b64, signature = parts
        try:
            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode('utf-8'))
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            # Verify signature
            expected_sig = hmac.new(self.secret_key, payload_bytes, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_sig, signature):
                return None
                
            # Verify expiration
            exp_time = datetime.datetime.fromisoformat(payload["exp"])
            if datetime.datetime.now(datetime.timezone.utc) > exp_time:
                return None
                
            return payload
        except Exception:
            return None

# Global Pluggable Provider Instance
auth_provider = HMACTokenProvider(config.COGNIFY_SECRET_KEY)

def set_auth_provider(provider):
    """Allows hot-swapping the provider at runtime (e.g. to OIDC/JWT in future)."""
    global auth_provider
    auth_provider = provider

def get_token_from_header():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None

def require_auth(roles=None):
    """
    Decorator for route security using the pluggable AuthProvider.
    Supports COGNIFY_BYPASS_AUTH for backward compatibility in testing.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if config.COGNIFY_BYPASS_AUTH:
                # Bypass during regression/local testing if configured
                return f(*args, **kwargs)
                
            token = get_token_from_header()
            if not token:
                return jsonify({"success": False, "error_code": "UNAUTHORIZED", "message": "Missing authentication token"}), 401
                
            payload = auth_provider.verify_token(token)
            if not payload:
                return jsonify({"success": False, "error_code": "UNAUTHORIZED", "message": "Invalid or expired token"}), 401
                
            # Perform role-based check
            if roles and payload.get("role") not in roles:
                return jsonify({"success": False, "error_code": "FORBIDDEN", "message": "Permission denied"}), 403
                
            return f(*args, **kwargs)
        return decorated
    return decorator
