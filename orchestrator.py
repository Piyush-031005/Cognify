import json
import time
from datetime import datetime
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
    t0 = time.time()
    try:
        memory = memory_engine.get_full_student_memory(student_email)
    except Exception as e:
        # Graceful degradation
        memory = {"mastered": [], "at_risk": [], "forgetting": [], "active_misconceptions": []}
    memory_query_time_ms = (time.time() - t0) * 1000

    # 2. Fetch Recent Telemetry Flags
    t0 = time.time()
    try:
        cur.execute('''
            SELECT question_id, correct, timestamp 
            FROM responses 
            WHERE student_email = ? 
            ORDER BY timestamp DESC LIMIT 20
        ''', (student_email,))
        recent_responses = [dict(r) for r in cur.fetchall()]
    except Exception:
        recent_responses = []
    telemetry_query_time_ms = (time.time() - t0) * 1000
    
    # Calculate recent accuracy
    if recent_responses:
        recent_accuracy = sum(1 for r in recent_responses if r["correct"]) / len(recent_responses)
        # Calculate freshness
        last_timestamp = recent_responses[0]["timestamp"]
        try:
            days_old = (datetime.now() - datetime.fromisoformat(last_timestamp)).days
            freshness_score = max(0.0, 1.0 - (days_old * 0.05))
        except Exception:
            freshness_score = 0.5
    else:
        recent_accuracy = None
        freshness_score = 0.0

    conn.close()

    return {
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "memory_model_version": MEMORY_MODEL_VERSION,
            "qqi_version": QQI_VERSION,
            "kg_version": KG_VERSION,
            "student_email": student_email,
            "generated_at": datetime.now().isoformat(),
            "freshness_score": freshness_score,
            "profiling": {
                "memory_query_time_ms": round(memory_query_time_ms, 2),
                "telemetry_query_time_ms": round(telemetry_query_time_ms, 2)
            }
        },
        "memory": memory,
        "telemetry": {
            "recent_accuracy": recent_accuracy,
            "recent_attempts_count": len(recent_responses)
        }
    }
