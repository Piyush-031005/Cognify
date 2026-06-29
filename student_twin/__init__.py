"""
student_twin package initialization.
Delegates subscriber event routing and provides CQRS read APIs.
"""

import json
import hashlib
import datetime
from database import get_conn

# Import submodule handlers
import student_twin.profile as profile
import student_twin.progression as progression
import student_twin.recommendations as recommendations
import student_twin.timeline as timeline
import student_twin.reports as reports

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    profile.handle_memory_updated(event_data, is_replay, replay_mode)
    progression.handle_memory_updated(event_data, is_replay, replay_mode)
    timeline.handle_memory_updated(event_data, is_replay, replay_mode)

def handle_nbirt_updated(event_data, is_replay=False, replay_mode="SAFE"):
    profile.handle_nbirt_updated(event_data, is_replay, replay_mode)
    timeline.handle_nbirt_updated(event_data, is_replay, replay_mode)

def handle_attention_updated(event_data, is_replay=False, replay_mode="SAFE"):
    # Attention update changes focus state and triggers profile health score updates
    profile.handle_memory_updated(event_data, is_replay, replay_mode)
    timeline.handle_attention_updated(event_data, is_replay, replay_mode)

def handle_ccli_updated(event_data, is_replay=False, replay_mode="SAFE"):
    reports.handle_ccli_updated(event_data, is_replay, replay_mode)
    # Triggers health score updates
    profile.handle_memory_updated(event_data, is_replay, replay_mode)

def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    recommendations.handle_decision_generated(event_data, is_replay, replay_mode)

def handle_teacher_override_applied(event_data, is_replay=False, replay_mode="SAFE"):
    timeline.handle_teacher_override_applied(event_data, is_replay, replay_mode)

def handle_teacher_recommendation(event_data, is_replay=False, replay_mode="SAFE"):
    timeline.handle_teacher_recommendation(event_data, is_replay, replay_mode)

def rebuild_projections():
    """
    Clears all Student Twin projection tables, replays historical events sequentially,
    calculates projection state checksum, and updates metadata log (Lock 5).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM student_profile_projection")
        cur.execute("DELETE FROM student_progress_projection")
        cur.execute("DELETE FROM student_goal_projection")
        cur.execute("DELETE FROM student_daily_summary")
        cur.execute("DELETE FROM student_timeline_projection")
        cur.execute("DELETE FROM student_recommendation_history")
        cur.execute("DELETE FROM student_trend_projection")
        cur.execute("DELETE FROM student_achievements")
        conn.commit()
    finally:
        conn.close()

    # Chronologically replay
    import event_replay
    replay_res = event_replay.replay_all_events("student_twin", mode="SAFE")

    # Lock 5: Calculate validation checksum
    conn = get_conn()
    cur = conn.cursor()
    tables = [
        "student_profile_projection",
        "student_progress_projection",
        "student_goal_projection",
        "student_daily_summary",
        "student_timeline_projection",
        "student_recommendation_history",
        "student_trend_projection",
        "student_achievements"
    ]
    hasher = hashlib.md5()
    try:
        for t in tables:
            cur.execute(f"SELECT COUNT(*) as count FROM {t}")
            cnt = cur.fetchone()["count"] or 0
            hasher.update(str(cnt).encode('utf-8'))
        checksum = hasher.hexdigest()

        now_str = datetime.datetime.now().isoformat()
        cur.execute("""
            INSERT INTO student_projection_metadata (projection_version, checksum, rebuilt_at)
            VALUES ('v1.0', ?, ?)
            ON CONFLICT(projection_version) DO UPDATE SET
                checksum = excluded.checksum,
                rebuilt_at = excluded.rebuilt_at
        """, (checksum, now_str))
        conn.commit()
    finally:
        conn.close()

    return {
        "status": "success",
        "events_replayed": replay_res.get("events_processed", 0),
        "projection_checksum": checksum
    }

# --- CQRS Query Methods ---

def get_student_profile(email):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM student_profile_projection WHERE student_email = ?", (email,))
        row = cur.fetchone()
        if row:
            res = dict(row)
            res["strengths"] = json.loads(res["strengths_json"])
            res["weaknesses"] = json.loads(res["weaknesses_json"])
            res["memory_health"] = json.loads(res["memory_health_json"])
            return res
        return {}
    finally:
        conn.close()

def get_student_progress(email):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM student_progress_projection WHERE student_email = ?", (email,))
        prog = cur.fetchone()
        
        cur.execute("SELECT * FROM student_goal_projection WHERE student_email = ?", (email,))
        goals = [dict(r) for r in cur.fetchall()]
        
        cur.execute("SELECT * FROM student_achievements WHERE student_email = ?", (email,))
        ach = [dict(r) for r in cur.fetchall()]
        
        return {
            "progress": dict(prog) if prog else {},
            "goals": goals,
            "achievements": ach
        }
    finally:
        conn.close()

def get_student_timeline(email):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM student_timeline_projection 
            WHERE student_email = ? 
            ORDER BY timestamp DESC
        """, (email,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_student_recommendations(email):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM student_recommendation_history 
            WHERE student_email = ? AND status = 'PENDING'
            ORDER BY priority_score DESC
        """, (email,))
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            d["evidence_snapshot"] = json.loads(d["evidence_snapshot_json"])
            rows.append(d)
        return rows
    finally:
        conn.close()
