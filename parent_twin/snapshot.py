"""
parent_twin/snapshot.py
CEB event handlers → updates parent_student_projection.
All raw signals are translated through digest.py before storage (Decision 2).
"""

import json
import datetime
from database import get_conn
import parent_twin.digest as digest


def _update_snapshot(email: str):
    """
    Reads ONLY from projection tables (CQRS — Decision 1).
    Reads student_profile_projection and student_progress_projection (projection-to-projection, Decision 3).
    Never touches raw engine tables.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Projection-to-projection read (Decision 3 locked)
        cur.execute(
            "SELECT cognitive_health_score, strengths_json, weaknesses_json FROM student_profile_projection WHERE student_email = ?",
            (email,)
        )
        profile_row = cur.fetchone()

        cur.execute(
            "SELECT streak_count, last_activity_date, total_attempts FROM student_progress_projection WHERE student_email = ?",
            (email,)
        )
        prog_row = cur.fetchone()

        cur.execute(
            "SELECT focus_state FROM student_attention_state WHERE student_email = ?",
            (email,)
        )
        att_row = cur.fetchone()

        # --- Digest translations (Decision 2) ---
        cog_score = profile_row["cognitive_health_score"] if profile_row else 0.75
        overall_digest = digest.translate_cognitive_health(cog_score)

        focus_state = att_row["focus_state"] if att_row else "optimal"
        att_label = digest.translate_attention(focus_state)

        # Memory trend from student_trend_projection (projection-to-projection)
        cur.execute(
            """
            SELECT metric_value FROM student_trend_projection
            WHERE student_email = ? AND metric_name = 'Health Score'
            ORDER BY recorded_at ASC LIMIT 10
            """,
            (email,)
        )
        trend_rows = cur.fetchall()
        recent_scores = [r["metric_value"] for r in trend_rows]
        memory_trend = digest.translate_memory_trend(recent_scores)

        # Strengths & weaknesses digests
        raw_strengths = json.loads(profile_row["strengths_json"]) if profile_row else []
        raw_weaknesses = json.loads(profile_row["weaknesses_json"]) if profile_row else []

        strengths_digest = [{"topic": s, "status": "Learning well"} for s in raw_strengths[:3]]
        weaknesses_digest = [
            {"topic": w, "status": digest.translate_memory_health(0.3)} for w in raw_weaknesses[:3]
        ]

        # Study habit summary (Decision 2 translations via digest)
        streak = prog_row["streak_count"] if prog_row else 0
        last_active = prog_row["last_activity_date"] if prog_row else None
        total_sessions = prog_row["total_attempts"] if prog_row else 0
        active_days = min(7, streak)
        habit_summary = digest.build_study_habit_summary(streak, active_days, total_sessions)

        now_str = datetime.datetime.now().isoformat()
        cur.execute(
            """
            INSERT INTO parent_student_projection (
                student_email, overall_digest, study_habit_summary_json,
                strengths_digest_json, weaknesses_digest_json, memory_trend,
                last_active_date, projection_version, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'v1.0', ?)
            ON CONFLICT(student_email) DO UPDATE SET
                overall_digest = excluded.overall_digest,
                study_habit_summary_json = excluded.study_habit_summary_json,
                strengths_digest_json = excluded.strengths_digest_json,
                weaknesses_digest_json = excluded.weaknesses_digest_json,
                memory_trend = excluded.memory_trend,
                last_active_date = excluded.last_active_date,
                updated_at = excluded.updated_at
            """,
            (
                email,
                overall_digest,
                json.dumps(habit_summary),
                json.dumps(strengths_digest),
                json.dumps(weaknesses_digest),
                memory_trend,
                last_active,
                now_str,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    if email:
        _update_snapshot(email)


def handle_attention_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    if email:
        _update_snapshot(email)


def handle_ccli_updated(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    if email:
        _update_snapshot(email)


def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
    email = event_data.get("entity_id")
    if email:
        _update_snapshot(email)
