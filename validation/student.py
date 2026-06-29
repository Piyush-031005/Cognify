"""
validation/student.py
Week 23 — Student twin validations.
"""

from validation.common import validate_email, validate_required_fields

def validate_quiz_submission(data):
    """Validates the payload for quiz submission."""
    required = {
        "student_email": str,
        "question_id": (int, str),
        "correct": int
    }
    # Check fields present
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object"
        
    for field, allowed_types in required.items():
        if field not in data:
            return False, f"Missing required field: '{field}'"
        val = data[field]
        if isinstance(allowed_types, tuple):
            if not any(isinstance(val, t) for t in allowed_types):
                return False, f"Invalid type for field '{field}'"
        else:
            if not isinstance(val, allowed_types):
                return False, f"Invalid type for field '{field}'"
                
    if not validate_email(data["student_email"]):
        return False, "Invalid student email format"
        
    return True, None
