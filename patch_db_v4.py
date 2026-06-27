import os

file_path = r'f:\Cognify\database.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update kg_nodes schema in init_db
old_nodes_schema = """        overall_confidence REAL DEFAULT 0.0,
        canonical_id TEXT
    )"""

new_nodes_schema = """        overall_confidence REAL DEFAULT 0.0,
        canonical_id TEXT,
        severity TEXT DEFAULT 'moderate',
        recommended_intervention TEXT
    )"""

if 'recommended_intervention' not in content:
    content = content.replace(old_nodes_schema, new_nodes_schema)

# 2. Add student_memory_events table creation to init_db
memory_events_schema = """
    # Append-only Cognitive Memory Events
    cur.execute('''
    CREATE TABLE IF NOT EXISTS student_memory_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        node_id TEXT,
        memory_type TEXT, -- 'concept', 'misconception', 'intervention'
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

if 'student_memory_events' not in content:
    # Inject it before conn.commit() in init_db
    search_str = "    conn.commit()\n    conn.close()"
    content = content.replace(search_str, memory_events_schema + "\n" + search_str, 1)

# 3. Add alterations and table creation to upgrade_database_schema
alter_block = """    # Alter kg_nodes table for Phase 3
    alterations_kg_nodes_p3 = [
        ("severity", "TEXT DEFAULT 'moderate'"),
        ("recommended_intervention", "TEXT")
    ]
    for col, ctype in alterations_kg_nodes_p3:
        try:
            cur.execute(f"ALTER TABLE kg_nodes ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass

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

# Inject into upgrade_database_schema
upgrade_search_str = "    conn.commit()\n    print(\"DATABASE SCHEMA UPGRADED SUCCESSFULLY.\")"
if "alterations_kg_nodes_p3 =" not in content:
    content = content.replace(upgrade_search_str, alter_block + "\n" + upgrade_search_str)


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Database schema patched for Phase 3 (Educational Memory).")
