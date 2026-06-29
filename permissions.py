"""
permissions.py
Week 23 — Central Permission Engine (Refinement 2).
"""

from database import get_conn

def can_view_student(actor_email, actor_role, student_email):
    """Checks if the actor is permitted to view student cognitive details."""
    if actor_role == "super_admin":
        return True
        
    if actor_role == "student" and actor_email == student_email:
        return True
        
    if actor_role == "teacher":
        # Check if student is enrolled in any of the teacher's rooms
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT 1 FROM room_students s
                JOIN rooms r ON s.room_code = r.room_code
                WHERE r.teacher_email = ? AND s.student_email = ?
                LIMIT 1
            """, (actor_email, student_email))
            return cur.fetchone() is not None
        finally:
            conn.close()

    if actor_role == "parent":
        # Check if parent is mapped to child
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT 1 FROM parent_student_mapping
                WHERE parent_email = ? AND student_email = ?
                LIMIT 1
            """, (actor_email, student_email))
            return cur.fetchone() is not None
        finally:
            conn.close()
            
    return False

def can_override(actor_email, actor_role, student_email=None):
    """Checks if actor can apply a teacher override."""
    if actor_role == "super_admin":
        return True
    if actor_role == "teacher":
        if not student_email:
            return True
        # Verify student is in teacher's room
        return can_view_student(actor_email, actor_role, student_email)
    return False

def can_view_parent(actor_email, actor_role, parent_email):
    """Checks if actor can access parent/household information."""
    if actor_role == "super_admin":
        return True
    if actor_role == "parent" and actor_email == parent_email:
        return True
    return False

def can_rebuild(actor_email, actor_role):
    """Checks if actor can trigger rebuilds (Decision 5 / Replay)."""
    return actor_role in ("super_admin", "school_admin")

def can_view_school(actor_email, actor_role, school_id='default'):
    """Checks if actor can access school dashboard and adoption statistics."""
    return actor_role in ("super_admin", "school_admin")

def can_view_research(actor_email, actor_role):
    """Checks if actor can access learning science analytics."""
    return actor_role in ("super_admin", "research_viewer")
