import json
from database import get_conn
import memory_engine

SCHEMA_VERSION = "1.0"
MEMORY_MODEL_VERSION = "v1.1"
QQI_VERSION = "v1.1"
KG_VERSION = "v1.0"

def get_unified_cognitive_state(student_email):
    """
    Acts as the canonical, READ-ONLY interface for a student's cognitive state.
    Pulls data from Educational Memory, Knowledge Graph, QQI history, and Telemetry.
    Does not write to any database.
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # 1. Fetch Memory States
    try:
        memory = memory_engine.get_full_student_memory(student_email)
    except Exception:
        memory = {"mastered": [], "at_risk": [], "forgetting": [], "active_misconceptions": []}

    # 2. Fetch Recent Telemetry Flags (e.g., struggling on a specific question)
    cur.execute('''
        SELECT question_id, correct, timestamp 
        FROM responses 
        WHERE student_email = ? 
        ORDER BY timestamp DESC LIMIT 20
    ''', (student_email,))
    recent_responses = [dict(r) for r in cur.fetchall()]
    
    # Calculate recent accuracy
    if recent_responses:
        recent_accuracy = sum(1 for r in recent_responses if r["correct"]) / len(recent_responses)
    else:
        recent_accuracy = None

    conn.close()

    return {
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "memory_model_version": MEMORY_MODEL_VERSION,
            "qqi_version": QQI_VERSION,
            "kg_version": KG_VERSION,
            "student_email": student_email
        },
        "memory": memory,
        "telemetry": {
            "recent_accuracy": recent_accuracy,
            "recent_attempts_count": len(recent_responses)
        }
    }
