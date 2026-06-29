"""
validation/teacher.py
Week 23 — Teacher twin validations.
"""

from validation.common import validate_email, validate_required_fields

def validate_teacher_override(data):
    """Validates teacher override request payload (Refinement 5)."""
    required = {
        "student_email": str,
        "concept_id": str,
        "override_type": str
    }
    is_valid, err = validate_required_fields(data, required)
    if not is_valid:
        return False, err
        
    if not validate_email(data["student_email"]):
        return False, "Invalid student email format"
        
    if "reason" in data and not isinstance(data["reason"], str):
        return False, "Field 'reason' must be a string"
        
    if "actor" in data and not isinstance(data["actor"], str):
        return False, "Field 'actor' must be a string"
        
    return True, None
