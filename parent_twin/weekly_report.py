"""
parent_twin/weekly_report.py
Decision 6 — Append-only weekly report generator.
Reports are NEVER overwritten. Each generation creates a new row.
Previous rows are marked is_latest = 0 before inserting the new one.
"""

import json
import uuid
import datetime
from database import get_conn
import parent_twin.digest as digest


def _get_week_bounds():
    """Returns ISO start/end strings for the current calendar week (Mon–Sun)."""
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


def generate_weekly_report(parent_email: str, student_email: str) -> dict:
    """
    Generates a new weekly report by reading from parent_student_projection and
    student_trend_projection (projection-to-projection reads — Decision 3).
    Old reports for the same week are marked is_latest=0 (Decision 6 — append-only).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        week_start, week_end = _get_week_bounds()

        # Mark previous reports for this week as not-latest (Decision 6)
        cur.execute(
            """
            UPDATE parent_weekly_report
            SET is_latest = 0
            WHERE parent_email = ? AND student_email = ? AND week_start_date = ?
            """,
            (parent_email, student_email, week_start),
        )

        # Read from parent_student_projection (CQRS — Decision 1)
        cur.execute(
            "SELECT * FROM parent_student_projection WHERE student_email = ?",
            (student_email,)
        )
        snap = cur.fetchone()

        if snap:
            overall_digest = snap["overall_digest"]
            strengths = json.loads(snap["strengths_digest_json"])
            weaknesses = json.loads(snap["weaknesses_digest_json"])
            memory_trend = snap["memory_trend"]
            habit_summary = json.loads(snap["study_habit_summary_json"])
        else:
            overall_digest = "No data yet"
            strengths = []
            weaknesses = []
            memory_trend = "stable"
            habit_summary = {"habit_summary": "No study activity recorded yet."}

        # Build recommendations using pure digest functions
        att_label = "Focused"  # default if no attention data in snapshot
        recommendations = digest.build_recommendations(overall_digest, memory_trend, att_label)

        report_id = str(uuid.uuid4())
        now_str = datetime.datetime.now().isoformat()

        cur.execute(
            """
            INSERT INTO parent_weekly_report (
                report_id, parent_email, student_email,
                week_start_date, week_end_date,
                overall_digest, strengths_json, weaknesses_json,
                study_habits_json, memory_trend, recommendations_json,
                is_latest, generated_at, projection_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 'v1.0')
            """,
            (
                report_id, parent_email, student_email,
                week_start, week_end,
                overall_digest,
                json.dumps(strengths),
                json.dumps(weaknesses),
                json.dumps(habit_summary),
                memory_trend,
                json.dumps(recommendations),
                now_str,
            ),
        )
        conn.commit()

        return {
            "report_id": report_id,
            "week_start_date": week_start,
            "week_end_date": week_end,
            "overall_digest": overall_digest,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "study_habits": habit_summary,
            "memory_trend": memory_trend,
            "recommendations": recommendations,
            "generated_at": now_str,
            "is_latest": True,
        }
    finally:
        conn.close()


def get_latest_weekly_report(parent_email: str, student_email: str) -> dict:
    """
    Returns the latest weekly report. Generates one if none exists for this week.
    """
    conn = get_conn()
    cur = conn.cursor()
    week_start, _ = _get_week_bounds()
    try:
        cur.execute(
            """
            SELECT * FROM parent_weekly_report
            WHERE parent_email = ? AND student_email = ? AND week_start_date = ? AND is_latest = 1
            ORDER BY generated_at DESC LIMIT 1
            """,
            (parent_email, student_email, week_start),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return generate_weekly_report(parent_email, student_email)

    return {
        "report_id": row["report_id"],
        "week_start_date": row["week_start_date"],
        "week_end_date": row["week_end_date"],
        "overall_digest": row["overall_digest"],
        "strengths": json.loads(row["strengths_json"]),
        "weaknesses": json.loads(row["weaknesses_json"]),
        "study_habits": json.loads(row["study_habits_json"]),
        "memory_trend": row["memory_trend"],
        "recommendations": json.loads(row["recommendations_json"]),
        "generated_at": row["generated_at"],
        "is_latest": bool(row["is_latest"]),
    }
