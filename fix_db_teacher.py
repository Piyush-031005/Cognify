import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import database

conn = database.get_conn()
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS teacher_recommendation_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id TEXT,
    action_taken TEXT,
    outcome_notes TEXT,
    timestamp TEXT
)
''')
conn.commit()
conn.close()
print("Directly executed CREATE TABLE for teacher_recommendation_feedback on DB.")
