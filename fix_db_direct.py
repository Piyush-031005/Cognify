import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import database

conn = database.get_conn()
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS student_memory_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_email TEXT,
    node_id TEXT,
    memory_type TEXT,
    retrieval_strength REAL,
    storage_strength REAL,
    confidence REAL,
    update_reason TEXT,
    evidence_count INTEGER,
    effectiveness_delta REAL,
    memory_model_version TEXT DEFAULT 'v1.0',
    timestamp TEXT
)
''')
conn.commit()
conn.close()
print("Directly executed CREATE TABLE for student_memory_events on DB.")
