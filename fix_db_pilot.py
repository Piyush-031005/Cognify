import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import database

conn = database.get_conn()
cur = conn.cursor()

# We need to add multiple columns. SQLite ALTER TABLE allows adding one column at a time.
new_columns = [
    ("executed_at", "TEXT"),
    ("outcome_window_days", "INTEGER"),
    ("success_category", "TEXT DEFAULT 'Pending'"),
    ("evidence_quality", "TEXT"),
    ("intervention_attribution", "TEXT")
]

for col_name, col_type in new_columns:
    try:
        cur.execute(f"ALTER TABLE teacher_recommendation_feedback ADD COLUMN {col_name} {col_type}")
        print(f"Added column {col_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column {col_name} already exists.")
        else:
            raise e

conn.commit()
conn.close()
print("Pilot analytics columns added successfully.")
