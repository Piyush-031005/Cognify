import os
import sqlite3
import random
import json
import unittest
from datetime import datetime
import database
import app

class TestWorkspaceIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "test_workspace_cognify.db"
        
        # Override database name
        database.DB_NAME = cls.test_db
        app.get_conn = database.get_conn
        
        # Clean up any leftover db
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
            
        # Init database and tables
        database.init_db()
        database.upgrade_database_schema()
        database.seed_dynamic_concepts()
        
        # Seed a dummy question
        conn = database.get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO question_bank (
                subject, topic, subtopic, difficulty, cognitive_type, prompt,
                option_a, option_b, option_c, option_d, correct_index, explanation, status, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "dsa", "arrays", "basics", "medium", "conceptual",
            "Why is deletion in arrays O(n)?", "A", "B", "C", "D", 0,
            "Shifting elements takes linear time", "Draft", 1
        ))
        cls.qid = cur.lastrowid
        
        # Seed concept mapping
        cur.execute("SELECT id FROM concepts WHERE name = 'Array Indexing' OR name = 'Binary Search' LIMIT 1")
        crow = cur.fetchone()
        if crow:
            cur.execute("INSERT INTO question_concepts (question_id, concept_id, weight) VALUES (?, ?, ?)", (cls.qid, crow[0], 1.0))
            
        conn.commit()
        conn.close()
        
        # Configure app for testing
        app.app.config['TESTING'] = True
        cls.client = app.app.test_client()

    @classmethod
    def tearDownClass(cls):
        # Restore database setting
        database.DB_NAME = "cognify.db"
        if os.path.exists(cls.test_db):
            try:
                os.remove(cls.test_db)
            except Exception as e:
                print("Tear down warning:", e)

    def test_01_get_question_details(self):
        print("\n[TEST 01] Fetching question details...")
        res = self.client.get(f'/question/{self.qid}')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("question", data)
        self.assertIn("options", data)
        self.assertIn("concepts", data)
        self.assertIn("versions", data)
        self.assertIn("reviews", data)
        self.assertIn("qqi_history", data)
        self.assertIn("telemetry", data)
        self.assertIn("health", data)
        self.assertEqual(data["question"]["prompt"], "Why is deletion in arrays O(n)?")
        print("OK: Fetch question details passed.")

    def test_02_predict_impact(self):
        print("\n[TEST 02] Testing impact prediction before save...")
        payload = {
            "question_id": self.qid,
            "prompt": "Why does element deletion in static arrays require O(n) runtime complexity in average case?",
            "explanation": "All subsequent items must be shifted left to fill the deleted index space.",
            "concepts": ["Array Indexing", "Array Deletion"]
        }
        res = self.client.post('/question/predict-impact', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("current_qqi", data)
        self.assertIn("predicted_qqi", data)
        self.assertIn("reasons", data)
        self.assertTrue(len(data["reasons"]) > 0)
        print(f"OK: Impact prediction returned predicted QQI {data['predicted_qqi']}% with reasons.")

    def test_03_edit_question(self):
        print("\n[TEST 03] Submitting question edit/revision...")
        payload = {
            "question_id": self.qid,
            "prompt": "Why does deletion in arrays take O(n) time?",
            "options": ["Elements must be shifted", "B", "C", "D"],
            "correct_index": 0,
            "explanation": "Because we have to shift elements left",
            "difficulty": "hard",
            "cognitive_type": "reasoning",
            "concepts": ["Array Indexing", "Array Traversal"],
            "edited_by": "teacher_expert@cognify.com",
            "change_reason": "Corrected prompt wording and increased difficulty"
        }
        res = self.client.post('/question/edit', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["new_version"], 2)
        print("OK: Edit question successfully saved version 2.")

    def test_04_get_history_and_diff(self):
        print("\n[TEST 04] Testing version timeline history and field diffs...")
        # Get history
        res_hist = self.client.get(f'/question/history/{self.qid}')
        self.assertEqual(res_hist.status_code, 200)
        data_hist = json.loads(res_hist.data)
        self.assertEqual(len(data_hist["versions"]), 2) # Version 1 and 2
        
        # Get diff of version 2
        res_diff = self.client.get(f'/question/diff/{self.qid}/2')
        self.assertEqual(res_diff.status_code, 200)
        data_diff = json.loads(res_diff.data)
        self.assertEqual(data_diff["version"], 2)
        self.assertIn("diffs", data_diff)
        self.assertIn("prompt", data_diff["diffs"])
        self.assertIn("difficulty", data_diff["diffs"])
        self.assertEqual(data_diff["diffs"]["difficulty"]["old"], "medium")
        self.assertEqual(data_diff["diffs"]["difficulty"]["new"], "hard")
        print(f"OK: Diffs verified (Difficulty changed from medium to hard).")

    def test_05_telemetry_distribution(self):
        print("\n[TEST 05] Fetching question telemetry visualizations data...")
        res = self.client.get(f'/question/telemetry/{self.qid}')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("options_distribution", data)
        self.assertIn("time_buckets", data)
        self.assertEqual(len(data["options_distribution"]), 4) # A, B, C, D clicks
        print("OK: Telemetry distributions returned successfully.")

    def test_06_rollback_version(self):
        print("\n[TEST 06] Testing rollback of question to Version 1...")
        payload = {
            "question_id": self.qid,
            "target_version": 1,
            "edited_by": "teacher_rollback@cognify.com"
        }
        res = self.client.post('/question/rollback', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["new_version"], 3) # Rollback creates Version 3
        
        # Verify question details are restored to Version 1 (prompt: 'Why is deletion in arrays O(n)?')
        res_details = self.client.get(f'/question/{self.qid}')
        details = json.loads(res_details.data)
        self.assertEqual(details["question"]["prompt"], "Why is deletion in arrays O(n)?")
        self.assertEqual(details["question"]["difficulty"], "medium")
        print("OK: Rollback restored prompt and difficulty values successfully.")

if __name__ == '__main__':
    unittest.main()
