"""
student_twin/progression.py
Progression Engine: manages learning streaks, goals progress, and student achievements.
"""

import json
import uuid
import datetime
from database import get_conn

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    """
    Consumes MemoryUpdated event. Updates streaks, goals, and checks achievements.
    """
    if not isinstance(event_data, dict):
        event_data = dict(event_data)
        
    email = event_data.get("entity_id")
    payload = event_data.get("payload_json", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
        
    concept_id = payload.get("concept_id")
    if not email:
        return

    conn = get_conn()
    cur = conn.cursor()
    try:
        # 1. Update Attempts & Streaks
        today_str = datetime.date.today().isoformat()
        cur.execute("SELECT streak_count, last_activity_date, total_attempts FROM student_progress_projection WHERE student_email = ?", (email,))
        prog_row = cur.fetchone()
        
        if prog_row:
            streak = prog_row["streak_count"] or 0
            last_date = prog_row["last_activity_date"]
            total_att = (prog_row["total_attempts"] or 0) + 1
            
            if last_date:
                try:
                    last_parsed = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
                    delta = (datetime.date.today() - last_parsed).days
                    if delta == 1:
                        streak += 1
                    elif delta > 1:
                        streak = 1
                except Exception:
                    streak = 1
            else:
                streak = 1
        else:
            streak = 1
            total_att = 1
            
        cur.execute("""
            INSERT INTO student_progress_projection (
                student_email, streak_count, last_activity_date, completed_concepts_count, total_attempts, projection_version, updated_at
            ) VALUES (?, ?, ?, 0, ?, 'v1.0', ?)
            ON CONFLICT(student_email) DO UPDATE SET
                streak_count = excluded.streak_count,
                last_activity_date = excluded.last_activity_date,
                total_attempts = excluded.total_attempts,
                updated_at = excluded.updated_at
        """, (email, streak, today_str, total_att, today_str))

        # Check completed concepts count
        cur.execute("SELECT COUNT(*) as count FROM concept_memory WHERE student_email = ? AND memory_state IN ('Stable', 'mastered')", (email,))
        comp_count = cur.fetchone()["count"] or 0
        cur.execute("UPDATE student_progress_projection SET completed_concepts_count = ? WHERE student_email = ?", (comp_count, email))

        # 2. Update Goals completion progress
        if concept_id:
            cur.execute("SELECT memory_strength FROM concept_memory WHERE student_email = ? AND concept_id = ?", (email, concept_id))
            mem_row = cur.fetchone()
            curr_mastery = mem_row["memory_strength"] if mem_row else 0.5
            
            cur.execute("""
                SELECT goal_id, target_mastery FROM student_goal_projection 
                WHERE student_email = ? AND target_concept = ? AND status = 'IN_PROGRESS'
            """, (email, concept_id))
            goals = cur.fetchall()
            for g in goals:
                gid = g["goal_id"]
                target = g["target_mastery"]
                status = "COMPLETED" if curr_mastery >= target else "IN_PROGRESS"
                
                cur.execute("""
                    UPDATE student_goal_projection
                    SET current_mastery = ?, status = ?, updated_at = ?
                    WHERE goal_id = ?
                """, (curr_mastery, status, today_str, gid))
                
                if status == "COMPLETED":
                    unlock_achievement(email, "Goal completed", today_str)

        # 3. Check Achievements (Lock 4)
        if streak >= 7:
            unlock_achievement(email, "7-day streak", today_str)
        if comp_count >= 5:
            unlock_achievement(email, "Concept mastered", today_str)
        if total_att >= 100:
            unlock_achievement(email, "100 questions solved", today_str)

        conn.commit()
    finally:
        conn.close()

def unlock_achievement(student_email, ach_type, unlocked_date):
    """
    Helper to check and unlock achievements.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id FROM student_achievements 
            WHERE student_email = ? AND achievement_type = ?
        """, (student_email, ach_type))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO student_achievements (id, student_email, achievement_type, unlocked_at, projection_version)
                VALUES (?, ?, ?, ?, 'v1.0')
            """, (str(uuid.uuid4()), student_email, ach_type, unlocked_date))
            
            # Log to timeline
            cur.execute("""
                INSERT INTO student_timeline_projection (
                    student_email, event_id, event_type, event_description, importance, timestamp, projection_version
                ) VALUES (?, ?, 'AchievementUnlocked', ?, 'high', ?, 'v1.0')
            """, (student_email, str(uuid.uuid4()), f"Achievement unlocked: {ach_type}!", unlocked_date))
        conn.commit()
    finally:
        conn.close()

def add_student_goal(student_email, target_concept, target_mastery):
    """
    UI API method to manually set goals.
    """
    conn = get_conn()
    cur = conn.cursor()
    goal_id = str(uuid.uuid4())
    now_str = datetime.datetime.now().isoformat()
    try:
        # Fetch current mastery
        cur.execute("SELECT memory_strength FROM concept_memory WHERE student_email = ? AND concept_id = ?", (student_email, target_concept))
        mem_row = cur.fetchone()
        curr_mastery = mem_row["memory_strength"] if mem_row else 0.0
        
        cur.execute("""
            INSERT INTO student_goal_projection (
                goal_id, student_email, target_concept, target_mastery, current_mastery, status, projection_version, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'IN_PROGRESS', 'v1.0', ?)
        """, (goal_id, student_email, target_concept, target_mastery, curr_mastery, now_str))
        conn.commit()
        return {"status": "success", "goal_id": goal_id}
    finally:
        conn.close()
