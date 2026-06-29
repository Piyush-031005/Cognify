"""
seed_pilot_data.py
Week 24 — Seeding realistic pilot dataset for demonstration & testing.
"""

import sqlite3
import datetime
import json
import config
from database import get_conn, init_db, upgrade_database_schema

def seed_data():
    """Seeds realistic school, teacher, student, parent, and telemetry logs."""
    print("[PILOT SEED] Initializing database...")
    init_db()
    upgrade_database_schema()

    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        # Clear transactional and question tables for clean seeding
        for t in ["rooms", "room_students", "parent_student_mapping", "responses", "cognitive_load_events", "memory_state_transitions", "student_recommendation_history", "student_profile_projection", "student_trend_projection", "misconception_clusters", "misconception_evidence", "question_bank", "question_concepts", "room_questions_map"]:
            cur.execute(f"DELETE FROM {t}")
            
        print("[PILOT SEED] Seeding users...")
        users = [
            ("superadmin@cognify.edu", "Super Admin", "super_admin", "admin123"),
            ("schooladmin@cognify.edu", "Principal Skinner", "school_admin", "school123"),
            ("teacher1@cognify.edu", "Mrs. Krabappel", "teacher", "teacher123"),
            ("teacher2@cognify.edu", "Mr. Dewhurst", "teacher", "teacher123"),
            ("student1@cognify.edu", "Bart Simpson", "student", "student123"),
            ("student2@cognify.edu", "Lisa Simpson", "student", "student123"),
            ("student3@cognify.edu", "Milhouse Van Houten", "student", "student123"),
            ("parent1@cognify.edu", "Homer Simpson", "parent", "parent123"),
            ("parent2@cognify.edu", "Marge Simpson", "parent", "parent123"),
            ("researcher@cognify.edu", "Dr. Frink", "research_viewer", "research123")
        ]
        
        for email, name, role, password in users:
            cur.execute("""
                INSERT INTO users (email, name, role, password)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    role = excluded.role,
                    password = excluded.password
            """, (email, name, role, password))

        print("[PILOT SEED] Seeding classrooms...")
        rooms = [
            ("R101", "teacher1@cognify.edu", "Math Grade 4", "2026-06-29"),
            ("R102", "teacher2@cognify.edu", "Science Grade 5", "2026-06-29")
        ]
        for room_code, teacher_email, subject, created_at in rooms:
            cur.execute("""
                INSERT INTO rooms (room_code, teacher_email, subject, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(room_code) DO UPDATE SET
                    teacher_email = excluded.teacher_email,
                    subject = excluded.subject
            """, (room_code, teacher_email, subject, created_at))

        print("[PILOT SEED] Mapping students to classrooms...")
        room_mappings = [
            ("R101", "student1@cognify.edu"),
            ("R101", "student2@cognify.edu"),
            ("R102", "student2@cognify.edu"),
            ("R102", "student3@cognify.edu")
        ]
        for room_code, student_email in room_mappings:
            cur.execute("""
                INSERT INTO room_students (room_code, student_email, joined_at)
                VALUES (?, ?, ?)
            """, (room_code, student_email, "2026-06-29"))

        print("[PILOT SEED] Seeding Parent-Student Mapping (Decision 4)...")
        parent_mappings = [
            ("parent1@cognify.edu", "student1@cognify.edu", "father", 1),
            ("parent1@cognify.edu", "student2@cognify.edu", "father", 0),
            ("parent2@cognify.edu", "student1@cognify.edu", "mother", 0),
            ("parent2@cognify.edu", "student2@cognify.edu", "mother", 1)
        ]
        for parent_email, student_email, rel, is_primary in parent_mappings:
            cur.execute("""
                INSERT INTO parent_student_mapping (parent_email, student_email, relationship_type, is_primary, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (parent_email, student_email, rel, is_primary, "2026-06-29"))

        print("[PILOT SEED] Seeding authoritative question bank...")
        from seed_questions import run_seed_questions
        run_seed_questions(conn)

        # Commit and close connection to release SQLite lock before running generator
        conn.commit()
        conn.close()

        print("[PILOT SEED] Seeding generated concept variants...")
        from question_generator import run_generator
        run_generator(count_per_concept=2)

        # Reopen connection for subsequent inserts
        conn = get_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        print("[PILOT SEED] Mapping questions to classrooms...")
        cur.execute("SELECT id FROM question_bank WHERE subject = 'math'")
        math_ids = [r["id"] for r in cur.fetchall()]
        for qid in math_ids[:15]:
            cur.execute("""
                INSERT INTO room_questions_map (room_code, question_id, source_type, created_at)
                VALUES ('R101', ?, 'question_bank', datetime('now'))
            """, (qid,))

        cur.execute("SELECT id FROM question_bank WHERE subject = 'physics'")
        physics_ids = [r["id"] for r in cur.fetchall()]
        for qid in physics_ids[:15]:
            cur.execute("""
                INSERT INTO room_questions_map (room_code, question_id, source_type, created_at)
                VALUES ('R102', ?, 'question_bank', datetime('now'))
            """, (qid,))

        # Query seeded questions to generate realistic responses
        cur.execute("SELECT id, subject, topic, subtopic, prompt FROM question_bank")
        seeded_qs = cur.fetchall()

        print("[PILOT SEED] Seeding responses & telemetry...")
        t0 = datetime.datetime.now()
        for i, q_row in enumerate(seeded_qs[:19]):
            q_id = q_row["id"]
            subject = q_row["subject"]
            topic = q_row["topic"]
            subtopic = q_row["subtopic"]
            q_text = q_row["prompt"]
            
            # Lisa (student2) answers correctly, Bart (student1) hesitates & misses some
            resp_data = [
                ("student2@cognify.edu", 1, 3.2, 0.9, 1.2),
                ("student1@cognify.edu", 0, 8.5, 0.4, 4.8)
            ]
            for student, correct, response_time, confidence, idle in resp_data:
                # We determine room code matching student/subject
                r_code = "R101" if subject.lower() == "math" else "R102"
                cur.execute("""
                    INSERT INTO responses (
                        room_code, student_email, attempt_id, subject, topic, subtopic,
                        question_id, question_text, correct, response_time, idle_time, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r_code, student, f"attempt_{i}", subject, topic, subtopic,
                    q_id, q_text, correct, response_time, idle, (t0 - datetime.timedelta(days=i)).isoformat()
                ))

                cur.execute("""
                    INSERT INTO cognitive_load_events (event_id, student_email, composite_load, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (f"ev_load_{student}_{q_id}", student, 0.35 if correct else 0.72, (t0 - datetime.timedelta(days=i)).isoformat()))

        print("[PILOT SEED] Seeding memory state transitions...")
        transitions = [
            ("student1@cognify.edu", "fractions", "Learning", "Stable", (t0 - datetime.timedelta(days=5)).isoformat()),
            ("student1@cognify.edu", "fractions", "Stable", "Forgetting", (t0 - datetime.timedelta(days=1)).isoformat()),
            ("student2@cognify.edu", "fractions", "Learning", "Stable", (t0 - datetime.timedelta(days=5)).isoformat()),
            ("student2@cognify.edu", "fractions", "Stable", "mastered", (t0 - datetime.timedelta(days=1)).isoformat())
        ]
        for student, concept, old_st, new_st, ts in transitions:
            cur.execute("""
                INSERT INTO memory_state_transitions (student_email, concept_id, old_state, new_state, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (student, concept, old_st, new_st, ts))

        print("[PILOT SEED] Seeding student recommendations...")
        recs = [
            ("student1@cognify.edu", "Practice exercises on fraction additions to arrest decay", 0.85, 0.90, "{}", "COMPLETED", (t0 - datetime.timedelta(days=2)).isoformat()),
            ("student2@cognify.edu", "Prerequisite Review: algebraic ratios", 0.72, 0.95, "{}", "COMPLETED", (t0 - datetime.timedelta(days=2)).isoformat())
        ]
        for student, text, priority_score, confidence, evidence_snapshot_json, status, ts in recs:
            cur.execute("""
                INSERT INTO student_recommendation_history (id, student_email, recommendation, priority_score, confidence, evidence_snapshot_json, status, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"rec_{student}_{abs(hash(text))}", student, text, priority_score, confidence, evidence_snapshot_json, status, ts))

        print("[PILOT SEED] Seeding other twin projections...")
        cur.execute("""
            INSERT INTO student_profile_projection (student_email, strengths_json, weaknesses_json, memory_health_json, cognitive_health_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("student1@cognify.edu", "[]", "[]", "{}", 0.52, t0.isoformat()))
        cur.execute("""
            INSERT INTO student_profile_projection (student_email, strengths_json, weaknesses_json, memory_health_json, cognitive_health_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("student2@cognify.edu", "[]", "[]", "{}", 0.95, t0.isoformat()))

        cur.execute("""
            INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at)
            VALUES (?, ?, ?, ?)
        """, ("student1@cognify.edu", "Health Score", 0.50, (t0 - datetime.timedelta(days=2)).isoformat()))
        cur.execute("""
            INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at)
            VALUES (?, ?, ?, ?)
        """, ("student1@cognify.edu", "Health Score", 0.52, t0.isoformat()))

        cur.execute("""
            INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at)
            VALUES (?, ?, ?, ?)
        """, ("student2@cognify.edu", "Health Score", 0.90, (t0 - datetime.timedelta(days=2)).isoformat()))
        cur.execute("""
            INSERT INTO student_trend_projection (student_email, metric_name, metric_value, recorded_at)
            VALUES (?, ?, ?, ?)
        """, ("student2@cognify.edu", "Health Score", 0.95, t0.isoformat()))

        cur.execute("""
            INSERT INTO misconception_clusters (cluster_id, misconception_name, concept_id)
            VALUES ('m1', 'FractionsOverlap', 'fractions')
        """)
        cur.execute("""
            INSERT INTO misconception_evidence (id, cluster_id, wrong_answer_count, student_count)
            VALUES ('e1', 'm1', 8, 2)
        """)

        conn.commit()
        print("[PILOT SEED] Seed completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"[PILOT SEED ERROR] Seeding aborted: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    seed_data()
