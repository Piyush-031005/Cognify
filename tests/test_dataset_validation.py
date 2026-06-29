import sqlite3
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Connect directly to the production database file
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cognify.db'))

import database
import app
import auth

# Force database and app to point to production cognify.db with Row factory
def get_test_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

database.get_conn = get_test_conn
app.get_conn = get_test_conn

from question_generator import MASTER_MAP

class TestDatasetValidation(unittest.TestCase):

    def setUp(self):
        self.client = app.app.test_client()

    def test_master_map_coverage(self):
        """Regression fails if ANY blueprint topic/subtopic returns zero questions."""
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        print("\n====================================================")
        print("VERIFYING EVERY BLUEPRINT COMBINATION")
        print("====================================================")
        
        failed = []
        for s, t, st in sorted(MASTER_MAP.keys()):
            cur.execute("""
                SELECT COUNT(*) FROM question_bank 
                WHERE subject = ? AND topic = ? AND subtopic = ? AND status = 'Approved'
            """, (s, t, st))
            count = cur.fetchone()[0]
            print(f"Blueprint Combo: {s} -> {t} -> {st} | Questions: {count}")
            if count == 0:
                failed.append(f"{s}/{t}/{st}")
                
        conn.close()
        
        self.assertEqual(len(failed), 0, f"FAIL: The following blueprint combinations returned zero questions: {failed}")
        print("[PASS] All blueprint combinations returned > 0 questions.")

    def test_e2e_all_subjects(self):
        """Simulates end-to-end quiz flow for every single supported subject."""
        print("\n====================================================")
        print("RUNNING END-TO-END VALIDATION FOR ALL 16 SUBJECTS")
        print("====================================================")
        
        # We need a unique topic/subtopic map for each subject to test
        subject_test_map = {}
        for s, t, st in MASTER_MAP.keys():
            if s not in subject_test_map:
                subject_test_map[s] = (t, st)
                
        for subject, (topic, subtopic) in sorted(subject_test_map.items()):
            print(f"\n--- Testing Subject: {subject.upper()} ({topic} -> {subtopic}) ---")
            
            # 1. Create Blueprint
            bp_payload = {
                "name": f"Validation Blueprint {subject}",
                "teacher_email": "teacher1@cognify.edu",
                "subject": subject,
                "topic": topic,
                "subtopic": subtopic,
                "purpose": "diagnostic",
                "difficulty": "medium",
                "question_count": 5,
                "duration": 10,
                "conceptual_pct": 25,
                "application_pct": 25,
                "reasoning_pct": 25,
                "memory_pct": 25
            }
            
            bp_res = self.client.post('/assessment-blueprints', json=bp_payload)
            self.assertEqual(bp_res.status_code, 200, f"Failed to create blueprint for {subject}: {bp_res.data}")
            bp_data = json.loads(bp_res.data)
            self.assertTrue(bp_data["success"])
            blueprint_id = bp_data["data"]["blueprint_id"]
            
            # 2. Create Room
            room_payload = {
                "teacher_email": "teacher1@cognify.edu",
                "blueprint_id": blueprint_id
            }
            room_res = self.client.post('/create-room', json=room_payload)
            self.assertEqual(room_res.status_code, 200, f"Failed to create room for {subject}: {room_res.data}")
            room_data = json.loads(room_res.data)
            self.assertTrue(room_data["success"])
            room_code = room_data["room_code"]
            
            # 3. Join Room (as Student)
            join_payload = {
                "room_code": room_code,
                "student_email": "student1@cognify.edu"
            }
            join_res = self.client.post('/join-room', json=join_payload)
            self.assertEqual(join_res.status_code, 200, f"Failed to join room for {subject}: {join_res.data}")
            join_data = json.loads(join_res.data)
            self.assertTrue(join_data["success"])
            
            # 4. Fetch Room Questions (Confirm count > 0)
            qs_res = self.client.get(f'/room-questions/{room_code}')
            self.assertEqual(qs_res.status_code, 200, f"Failed to fetch questions for room {room_code}: {qs_res.data}")
            qs = json.loads(qs_res.data)
            self.assertGreater(len(qs), 0, f"Zero questions loaded for {subject} quiz!")
            
            question_id = qs[0]["id"]
            
            # 5. Submit first question answer with Bearer auth token
            token = auth.auth_provider.issue_token("student1@cognify.edu", "student")
            headers = {"Authorization": f"Bearer {token}"}
            
            submit_payload = {
                "student_email": "student1@cognify.edu",
                "room_code": room_code,
                "question_id": question_id,
                "correct": 1,
                "subject": subject,
                "topic": topic,
                "subtopic": subtopic,
                "attempt_id": "validation_attempt",
                "response_time": 5.0,
                "confidence": 0.8
            }
            submit_res = self.client.post('/submit', json=submit_payload, headers=headers)
            self.assertEqual(submit_res.status_code, 200, f"Failed to submit answer for {subject}: {submit_res.data}")
            
            # 6. Fetch Room Report
            rep_res = self.client.get(f'/room-reports/{room_code}')
            self.assertEqual(rep_res.status_code, 200, f"Failed to fetch report for {subject}: {rep_res.data}")
            
            print(f"  [OK] {subject.upper()} integration checks passed successfully.")

if __name__ == "__main__":
    unittest.main()
