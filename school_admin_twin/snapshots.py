"""
school_admin_twin/snapshots.py
snapshots.py: Append-only weekly snapshot generator for the school/admin metrics (Decision 4).
"""

import json
import uuid
import datetime
from database import get_conn

def _get_week_bounds():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()

def generate_weekly_snapshot(school_id='default'):
    """
    Generates a new weekly snapshot. Marks older ones for this week as is_latest = 0 (Decision 4).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        week_start, week_end = _get_week_bounds()

        # Mark older snapshots for this week as not-latest
        cur.execute("""
            UPDATE school_weekly_snapshot
            SET is_latest = 0
            WHERE school_id = ? AND week_start_date = ?
        """, (school_id, week_start))

        # Get adoption metrics
        cur.execute("SELECT * FROM school_adoption_metrics WHERE school_id = ?", (school_id,))
        adopt_row = cur.fetchone()
        adoption = dict(adopt_row) if adopt_row else {}

        # Get classroom summaries for distribution details
        cur.execute("SELECT room_code, avg_cognitive_health, at_risk_count, mastery_rate FROM school_classroom_summary WHERE school_id = ?", (school_id,))
        classrooms = [dict(r) for r in cur.fetchall()]

        summary_data = {
            "adoption": adoption,
            "classroom_distribution": classrooms,
            "total_classrooms_count": len(classrooms)
        }

        snapshot_id = str(uuid.uuid4())
        now_str = datetime.datetime.now().isoformat()

        cur.execute("""
            INSERT INTO school_weekly_snapshot (
                snapshot_id, school_id, week_start_date, week_end_date,
                summary_json, is_latest, generated_at, projection_version
            ) VALUES (?, ?, ?, ?, ?, 1, ?, 'v1.0')
        """, (snapshot_id, school_id, week_start, week_end, json.dumps(summary_data), now_str))

        conn.commit()

        return {
            "snapshot_id": snapshot_id,
            "school_id": school_id,
            "week_start_date": week_start,
            "week_end_date": week_end,
            "summary": summary_data,
            "generated_at": now_str,
            "is_latest": True
        }
    finally:
        conn.close()

def get_latest_weekly_snapshot(school_id='default'):
    """
    Returns the latest snapshot or generates one on-demand if missing.
    """
    conn = get_conn()
    cur = conn.cursor()
    week_start, _ = _get_week_bounds()
    try:
        cur.execute("""
            SELECT * FROM school_weekly_snapshot
            WHERE school_id = ? AND week_start_date = ? AND is_latest = 1
            ORDER BY generated_at DESC LIMIT 1
        """, (school_id, week_start))
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return generate_weekly_snapshot(school_id)

    return {
        "snapshot_id": row["snapshot_id"],
        "school_id": row["school_id"],
        "week_start_date": row["week_start_date"],
        "week_end_date": row["week_end_date"],
        "summary": json.loads(row["summary_json"]),
        "generated_at": row["generated_at"],
        "is_latest": bool(row["is_latest"])
    }
