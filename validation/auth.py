"""
validation/auth.py
Week 23 — Authentication route validations.
"""

from validation.common import validate_email, validate_required_fields

def validate_signup(data):
    """Validates the payload for signing up a new user."""
    required = {
        "name": str,
        "email": str,
        "role": str,
        "password": str
    }
    is_valid, err = validate_required_fields(data, required)
    if not is_valid:
        return False, err
        
    if not validate_email(data["email"]):
        return False, "Invalid email format"
        
    allowed_roles = ("super_admin", "school_admin", "teacher", "parent", "student", "research_viewer")
    if data["role"] not in allowed_roles:
        return False, f"Invalid role: must be one of {allowed_roles}"
        
    if len(data["password"]) < 6:
        return False, "Password must be at least 6 characters long"
        
    return True, None

def validate_signin(data):
    """Validates the payload for signing in."""
    required = {
        "email": str,
        "password": str
    }
    is_valid, err = validate_required_fields(data, required)
    if not is_valid:
        return False, err
        
    if not validate_email(data["email"]):
        return False, "Invalid email format"
        
    return True, None
