"""
tests/test_pilot_dataset.py
Week 24 — Integration test verifying the pilot seeding dataset.
"""

import os
import sys
import unittest
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from database import get_conn
import seed_pilot_data

class TestPilotDataset(unittest.TestCase):
    def test_pilot_seed_execution(self):
        # Run seeder
        seed_pilot_data.seed_data()

        # Connect and verify
        conn = get_conn()
        cur = conn.cursor()
        try:
            # 1. Verify users seeded
            cur.execute("SELECT COUNT(*) FROM users")
            user_cnt = cur.fetchone()[0]
            self.assertTrue(user_cnt >= 10, f"Expected at least 10 users, found {user_cnt}")

            # 2. Verify classrooms seeded
            cur.execute("SELECT COUNT(*) FROM rooms")
            room_cnt = cur.fetchone()[0]
            self.assertEqual(room_cnt, 2)

            # 3. Verify mappings
            cur.execute("SELECT COUNT(*) FROM parent_student_mapping")
            parent_maps = cur.fetchone()[0]
            self.assertEqual(parent_maps, 4)

            # 4. Verify telemetry responses
            cur.execute("SELECT COUNT(*) FROM responses")
            resp_cnt = cur.fetchone()[0]
            self.assertTrue(resp_cnt > 0)
            
            # 5. Verify student profiles exist
            cur.execute("SELECT COUNT(*) FROM student_profile_projection")
            prof_cnt = cur.fetchone()[0]
            self.assertEqual(prof_cnt, 2)

        finally:
            conn.close()

if __name__ == '__main__':
    unittest.main()
