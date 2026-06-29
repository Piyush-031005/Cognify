"""
validation/common.py
Week 23 — Common validations.
"""

import re

def validate_email(email):
    """Simple email validation check."""
    if not email or not isinstance(email, str):
        return False
    # Simple email regex
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

def validate_required_fields(data, required_fields):
    """Checks if all required fields are present and not empty."""
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object"
    for field, field_type in required_fields.items():
        if field not in data:
            return False, f"Missing required field: '{field}'"
        if not isinstance(data[field], field_type):
            return False, f"Invalid type for field '{field}': expected {field_type.__name__}, got {type(data[field]).__name__}"
        if field_type == str and not data[field].strip():
            return False, f"Field '{field}' cannot be empty or whitespace"
    return True, None
