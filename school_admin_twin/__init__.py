"""
school_admin_twin package initialization.
Delegates event handlers and provides CQRS read APIs.
"""

import json
import hashlib
import datetime
from database import get_conn

# Import submodule handlers
import school_admin_twin.classroom as classroom
import school_admin_twin.teacher_summary as teacher_summary
import school_admin_twin.curriculum as curriculum
import school_admin_twin.risk_dashboard as risk_dashboard
import school_admin_twin.adoption as adoption
import school_admin_twin.snapshots as snapshots

# --- CEB Event Handlers ---

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    classroom.handle_memory_updated(event_data, is_replay, replay_mode)
    curriculum.handle_memory_updated(event_data, is_replay, replay_mode)
    if not is_replay:
        adoption.recompute_adoption_metrics()

def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    risk_dashboard.handle_decision_generated(event_data, is_replay, replay_mode)
    if not is_replay:
        adoption.recompute_adoption_metrics()

def handle_attention_updated(event_data, is_replay=False, replay_mode="SAFE"):
    classroom.handle_attention_updated(event_data, is_replay, replay_mode)
    if not is_replay:
        adoption.recompute_adoption_metrics()

def handle_teacher_override_applied(event_data, is_replay=False, replay_mode="SAFE"):
    teacher_summary.handle_teacher_override_applied(event_data, is_replay, replay_mode)
    if not is_replay:
        adoption.recompute_adoption_metrics()

# --- Rebuild Projections (Decision 5 Checksum) ---

def rebuild_projections():
    """
    Clears all school projection tables, chronologically replays historical events,
    re-aggregates all metrics, computes checksum, and writes metadata.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM school_org")
        cur.execute("DELETE FROM school_classroom_summary")
        cur.execute("DELETE FROM school_teacher_summary")
        cur.execute("DELETE FROM school_concept_coverage")
        cur.execute("DELETE FROM school_risk_dashboard")
        cur.execute("DELETE FROM school_adoption_metrics")
        cur.execute("DELETE FROM school_weekly_snapshot")
        conn.commit()
    finally:
        conn.close()

    # Seed default school
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT OR IGNORE INTO school_org (school_id, school_name, created_at)
            VALUES ('default', 'Default School', ?)
        """, (datetime.datetime.now().isoformat(),))
        conn.commit()
    finally:
        conn.close()

    # Replay events
    import event_replay
    replay_res = event_replay.replay_all_events("school_admin_twin", mode="SAFE")

    # Run full aggregation across all known rooms/teachers to ensure perfect parity
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT room_code FROM rooms")
        rooms = [row["room_code"] for row in cur.fetchall()]
        
        cur.execute("SELECT DISTINCT teacher_email FROM rooms")
        teachers = [row["teacher_email"] for row in cur.fetchall()]
    finally:
        conn.close()

    for r_code in rooms:
        classroom.recompute_classroom_summary(r_code)
        risk_dashboard.recompute_risk_dashboard(r_code)

    for t_email in teachers:
        teacher_summary.recompute_teacher_summary(t_email)

    curriculum.recompute_curriculum_coverage()
    adoption.recompute_adoption_metrics()
    snapshots.generate_weekly_snapshot()

    # Calculate checksum (Decision 5)
    conn = get_conn()
    cur = conn.cursor()
    tables = [
        "school_classroom_summary",
        "school_teacher_summary",
        "school_concept_coverage",
        "school_risk_dashboard",
        "school_adoption_metrics",
        "school_weekly_snapshot"
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
            INSERT INTO school_projection_metadata (projection_version, checksum, rebuilt_at)
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

# --- CQRS Read APIs (Decision 1) ---

def get_school_overview(school_id='default'):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM school_org WHERE school_id = ?", (school_id,))
        school_info = cur.fetchone()
        
        cur.execute("SELECT * FROM school_adoption_metrics WHERE school_id = ?", (school_id,))
        metrics = cur.fetchone()
        
        res = dict(school_info) if school_info else {"school_id": school_id, "school_name": "Default School"}
        res["metrics"] = dict(metrics) if metrics else {}
        return res
    finally:
        conn.close()

def get_classroom_summaries(school_id='default'):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM school_classroom_summary WHERE school_id = ? ORDER BY room_code", (school_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_classroom_detail(room_code):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM school_classroom_summary WHERE room_code = ?", (room_code,))
        row = cur.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()

def get_teacher_summaries(school_id='default'):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM school_teacher_summary WHERE school_id = ? ORDER BY teacher_email", (school_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_teacher_detail(teacher_email):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM school_teacher_summary WHERE teacher_email = ?", (teacher_email,))
        row = cur.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()

def get_curriculum_coverage(school_id='default'):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM school_concept_coverage WHERE school_id = ? ORDER BY subject, concept_id", (school_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_risk_dashboard(school_id='default'):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM school_risk_dashboard WHERE school_id = ? ORDER BY room_code", (school_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_weekly_snapshot(school_id='default'):
    return snapshots.get_latest_weekly_snapshot(school_id)
