"""
school_admin_twin/curriculum.py
Curriculum Engine: computes school-wide concept coverage from teacher_classroom_retention projections (CQRS).
"""

import datetime
from database import get_conn

def recompute_curriculum_coverage():
    """
    Recalculates school_concept_coverage by aggregating teacher_classroom_retention.
    Uses projection-to-projection reads.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Aggregate mastered count and total students per subject & concept
        cur.execute("""
            SELECT r.subject, cr.concept_id, 
                   SUM(cr.mastered_count) as total_mastered, 
                   SUM(cr.total_students) as total_stu
            FROM teacher_classroom_retention cr
            JOIN rooms r ON cr.room_code = r.room_code
            GROUP BY r.subject, cr.concept_id
        """)
        rows = cur.fetchall()

        now_str = datetime.datetime.now().isoformat()
        for row in rows:
            sub = row["subject"]
            concept = row["concept_id"]
            tot_mastered = row["total_mastered"] or 0
            tot_students = row["total_stu"] or 0
            
            rate = round(tot_mastered / max(1, tot_students), 3)

            cur.execute("""
                INSERT INTO school_concept_coverage (
                    school_id, subject, concept_id, school_mastery_rate, total_students,
                    projection_version, updated_at
                ) VALUES ('default', ?, ?, ?, ?, 'v1.0', ?)
                ON CONFLICT(school_id, subject, concept_id) DO UPDATE SET
                    school_mastery_rate = excluded.school_mastery_rate,
                    total_students = excluded.total_students,
                    updated_at = excluded.updated_at
            """, (sub, concept, rate, tot_students, now_str))

        conn.commit()
    finally:
        conn.close()

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    recompute_curriculum_coverage()
