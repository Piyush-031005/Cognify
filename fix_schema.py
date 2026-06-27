import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import database

file_path = r'f:\Cognify\database.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure we add student_memory_events
if 'student_memory_events' not in content:
    schema_sql = """
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
"""
    # Just append it to init_db before conn.commit()
    target = "conn.commit()\n    conn.close()"
    if target in content:
        content = content.replace(target, schema_sql + "    " + target, 1)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Patched database.py with student_memory_events")
        
        # Now run init_db to actually create it
        database.init_db()
        print("init_db ran.")
    else:
        print("Target string not found in database.py")
else:
    print("student_memory_events already in database.py")
