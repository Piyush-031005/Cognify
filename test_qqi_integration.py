import os
import shutil
import math
import sqlite3
import random
import uuid
from datetime import datetime, timezone
import database
from qqi_engine import update_question_qqi, record_teacher_review, get_concept_quality_index

def run_integration_test():
    print("====================================================")
    print("RUNNING AUTOMATED QQI ENGINE INTEGRATION TEST SUITE")
    print("====================================================")

    # Use a temporary database file
    test_db = "test_cognify.db"
    
    # Clean up any leftover test db
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except Exception as e:
            print("Cleanup warning:", e)
        
    # Override database name in database module
    database.DB_NAME = test_db

    # Initialize the test database schemas
    database.init_db()
    database.upgrade_database_schema()
    database.seed_dynamic_concepts() # Seed concepts in test db
    
    conn = database.get_conn()
    cur = conn.cursor()
    
    try:
        # Copy one question from production database to test database
        prod_conn = sqlite3.connect("cognify.db")
        prod_cur = prod_conn.cursor()
        try:
            prod_cur.execute("SELECT * FROM question_bank LIMIT 1")
            q_row = prod_cur.fetchone()
        except Exception:
            q_row = None
        
        if not q_row:
            # Fallback seed if no questions in prod db
            cur.execute("""
                INSERT INTO question_bank (
                    subject, topic, subtopic, difficulty, cognitive_type, prompt,
                    option_a, option_b, option_c, option_d, correct_index, estimated_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("dsa", "arrays", "basics", "medium", "conceptual", "Why does array perform deletion in O(n)?", "A", "B", "C", "D", 0, 30, "Draft"))
            qid = cur.lastrowid
            prompt = "Why does array perform deletion in O(n)?"
            subject, topic, subtopic = "dsa", "arrays", "basics"
        else:
            q_dict = dict(zip([col[0] for col in prod_cur.description], q_row))
            # Get columns in test database question_bank
            cur.execute("PRAGMA table_info(question_bank)")
            test_cols = {col[1] for col in cur.fetchall()}
            
            # Copy only matching columns
            common_cols = [k for k in q_dict.keys() if k in test_cols]
            cols_str = ", ".join(common_cols)
            placeholders = ", ".join(["?"] * len(common_cols))
            vals = [q_dict[k] for k in common_cols]
            
            cur.execute(f"INSERT INTO question_bank ({cols_str}) VALUES ({placeholders})", vals)
            
            # Retrieve values
            qid = q_dict["id"]
            prompt = q_dict["prompt"]
            subject = q_dict["subject"]
            topic = q_dict["topic"]
            subtopic = q_dict["subtopic"]
            
        prod_conn.close()
        
        # Explicitly set status to Draft for testing transitions
        cur.execute("UPDATE question_bank SET status = 'Draft', qqi_score = 80.0, qqi_confidence = 0.10 WHERE id = ?", (qid,))
        conn.commit()
        
        # Link question to concept in test database
        cur.execute("SELECT id FROM concepts WHERE name = 'Array Indexing'")
        c_row = cur.fetchone()
        if c_row:
            cur.execute("INSERT OR IGNORE INTO question_concepts (question_id, concept_id, weight) VALUES (?, ?, ?)", (qid, c_row[0], 1.0))
            conn.commit()
            
        # Simulate 12 responses (Confidence should equal 0.34)
        print("\n[STEP 1] Simulating 12 student responses...")
        for i in range(12):
            student_email = f"student_{uuid.uuid4().hex[:6]}@school.edu"
            correct = 1 if i % 2 == 0 else 0
            cur.execute("""
                INSERT INTO responses (
                    room_code, student_email, attempt_id, subject, topic, subtopic,
                    question_id, question_text, response_time, idle_time, rewrite_count,
                    backspace_count, attempts, confidence, correct, hesitation_score,
                    confidence_error, engagement_score, hover_count, same_option_clicks, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "pilot_room", student_email, "attempt_1", subject, topic, subtopic,
                qid, prompt, 15.0 + random.uniform(-2, 2), 2.0, 0, 0, 1, 0.8, correct, 0.2, 0.1, 0.9, 4, 1,
                datetime.utcnow().isoformat()
            ))
            
        conn.commit() # commit response insertions so they can be read by qqi_engine
        
        # Recalculate QQI and check values
        res = update_question_qqi(qid)
        print(f"[RESULT] Recalculated QQI: {res['qqi_score']}, Confidence: {res['qqi_confidence']}, Status: {res['new_status']}")
        
        # Assertions
        assert res["responses_count"] == 12, f"Expected 12 responses, got {res['responses_count']}"
        assert res["qqi_confidence"] == 0.34, f"Expected QQI confidence to be 0.34, got {res['qqi_confidence']}"
        
        # Assert QQI Status remains 'Pilot' because Confidence (0.34) <= 0.70 (requires > 0.70 for Approved)
        assert res["new_status"] == "Pilot", f"Expected lifecycle status 'Pilot' (confidence is too low), got '{res['new_status']}'"
        print("OK: Step 1 Assertions Passed: QQI confidence is 0.34 and status remained 'Pilot' as required.")

        # 4. Record teacher reviews with estimated solve time
        print("\n[STEP 2] Recording teacher review feedback...")
        feedback = {
            "difficulty": 3,
            "concept_correct": True,
            "language_rating": 5,
            "useful": True,
            "recommended": True,
            "estimated_solve_time": 15
        }
        res_review = record_teacher_review(qid, "teacher_expert@school.edu", feedback)
        
        # Assertions on rating update
        cur.execute("SELECT teacher_rating_score FROM question_bank WHERE id = ?", (qid,))
        teacher_score = cur.fetchone()["teacher_rating_score"]
        assert teacher_score == 100.0, f"Expected teacher rating score to be 100.0, got {teacher_score}"
        print("OK: Step 2 Assertions Passed: Teacher review successfully recorded and QQI recalculated.")

        # 5. Simulate 100 responses to push Confidence above 0.70 (N=112 responses -> Confidence should be ~0.75)
        print("\n[STEP 3] Simulating additional 100 student responses to increase confidence...")
        for i in range(100):
            student_email = f"student_{uuid.uuid4().hex[:6]}@school.edu"
            correct = 1 if i % 4 != 0 else 0  # 75% accuracy
            cur.execute("""
                INSERT INTO responses (
                    room_code, student_email, attempt_id, subject, topic, subtopic,
                    question_id, question_text, response_time, idle_time, rewrite_count,
                    backspace_count, attempts, confidence, correct, hesitation_score,
                    confidence_error, engagement_score, hover_count, same_option_clicks, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "pilot_room", student_email, "attempt_2", subject, topic, subtopic,
                qid, prompt, 14.5 + random.uniform(-1, 1), 1.0, 0, 0, 1, 0.85, correct, 0.1, 0.05, 0.95, 2, 1,
                datetime.utcnow().isoformat()
            ))
            
        conn.commit()
        
        res_final = update_question_qqi(qid)
        print(f"[RESULT] Recalculated QQI: {res_final['qqi_score']}, Confidence: {res_final['qqi_confidence']}, Status: {res_final['new_status']}")
        
        # Assertions
        assert res_final["responses_count"] == 112, f"Expected 112 responses, got {res_final['responses_count']}"
        assert res_final["qqi_confidence"] > 0.70, f"Expected QQI confidence > 0.70, got {res_final['qqi_confidence']}"
        
        # Since QQI is high and Confidence is > 0.70, it should transition to Approved!
        assert res_final["new_status"] == "Approved", f"Expected lifecycle status 'Approved', got '{res_final['new_status']}'"
        print("OK: Step 3 Assertions Passed: QQI confidence exceeded 0.70 and status transitioned to 'Approved'.")

        # 6. Fetch CQI concept quality index summary checks
        print("\n[STEP 4] Testing Concept Quality Index (CQI) dashboard summaries...")
        cqi_data = get_concept_quality_index(subject, topic)
        
        assert "concepts" in cqi_data, "CQI reports missing concepts list key."
        assert "summary" in cqi_data, "CQI reports missing summary key."
        summary = cqi_data["summary"]
        assert "top_healthy" in summary, "CQI summary missing top_healthy."
        assert "top_weak" in summary, "CQI summary missing top_weak."
        assert "dead_nodes" in summary, "CQI summary missing dead_nodes."
        assert "overloaded" in summary, "CQI summary missing overloaded."
        print(f"[CQI SUMMARY] Dead Nodes: {summary['dead_nodes']}")
        print(f"[CQI SUMMARY] Top Healthy: {summary['top_healthy']}")
        print("OK: Step 4 Assertions Passed: CQI structural dashboard metrics validated successfully.")

        print("\n====================================================")
        print("ALL AUTOMATED QQI ENGINE INTEGRATION TESTS PASSED")
        print("====================================================")
        
    except Exception as e:
        print(f"\n[TEST FAILURE ERROR]: {e}")
        raise e
    finally:
        conn.close()
        # Restore production database name
        database.DB_NAME = "cognify.db"
        # Clean up database file
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
                print("[TEST CLEANUP] Test database deleted successfully.")
            except Exception as e:
                print("Cleanup error on test db deletion:", e)

if __name__ == "__main__":
    run_integration_test()
