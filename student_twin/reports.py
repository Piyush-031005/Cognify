"""
student_twin/reports.py
Reports Generator: compiles daily summaries and appends trend projections.
"""

import json
import datetime
from database import get_conn

def handle_ccli_updated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes CCLIUpdated event. Updates daily summaries and metrics history.
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
        
    email = event_data.get("entity_id")
    if not email:
        return

    conn = get_conn()
    cur = conn.cursor()
    try:
        # Fetch cognitive load value
        cur.execute("SELECT rolling_ccli, alert_status FROM student_cognitive_load_state WHERE student_email = ?", (email,))
        ccli_row = cur.fetchone()
        ccli_val = ccli_row["rolling_ccli"] if ccli_row else 0.5

        # Fetch focus states
        cur.execute("SELECT focus_state FROM student_attention_state WHERE student_email = ?", (email,))
        att_row = cur.fetchone()
        focus = att_row["focus_state"] if att_row else "optimal"

        today_str = datetime.date.today().isoformat()

        # Update student_daily_summary
        cur.execute("""
            SELECT avg_ccli, focus_state_counts_json, response_count 
            FROM student_daily_summary 
            WHERE student_email = ? AND summary_date = ?
        """, (email, today_str))
        summary_row = cur.fetchone()

        if summary_row:
            resp_count = (summary_row["response_count"] or 0) + 1
            avg_ccli = round(((summary_row["avg_ccli"] or 0.5) * (resp_count - 1) + ccli_val) / resp_count, 3)
            
            counts = json.loads(summary_row["focus_state_counts_json"])
            counts[focus] = counts.get(focus, 0) + 1
        else:
            resp_count = 1
            avg_ccli = round(ccli_val, 3)
            counts = {"optimal": 0, "decay": 0, "fatigued": 0}
            counts[focus] = 1

        cur.execute("""
            INSERT INTO student_daily_summary (
                student_email, summary_date, avg_ccli, focus_state_counts_json, response_count, projection_version, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'v1.0', ?)
            ON CONFLICT(student_email, summary_date) DO UPDATE SET
                avg_ccli = excluded.avg_ccli,
                focus_state_counts_json = excluded.focus_state_counts_json,
                response_count = excluded.response_count,
                updated_at = excluded.updated_at
        """, (email, today_str, avg_ccli, json.dumps(counts), resp_count, today_str))

        # Lock 2: Record in trend projection
        cur.execute("""
            INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at)
            VALUES (?, 'CCLI', ?, ?)
        """, (email, ccli_val, today_str))

        conn.commit()
    finally:
        conn.close()
