import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import database

conn = database.get_conn()
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS intervention_history (
    intervention_id TEXT PRIMARY KEY,
    recommendation_id TEXT,
    student_email TEXT,
    teacher_email TEXT,
    question_id TEXT,
    concept_id TEXT,
    kg_version TEXT,
    qqi_version TEXT,
    model_version TEXT,
    pre_mastery REAL,
    post_mastery REAL,
    mastery_gain REAL,
    teacher_action TEXT,
    timestamp TEXT
)
''')

# Also update teacher_recommendation_feedback schema to support "Viewed" and "Verified"
# Since SQLite ALTER TABLE is limited, we just trust the app level logic to use these strings in `action_taken` or `success_category`.

conn.commit()
conn.close()
print("intervention_history table created successfully.")
