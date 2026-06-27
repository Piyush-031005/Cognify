import os
import re

file_path = r'f:\Cognify\database.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update kg_nodes schema
old_nodes_schema = """        created_at TEXT,
        updated_at TEXT,
        metadata TEXT
    )"""

new_nodes_schema = """        created_at TEXT,
        updated_at TEXT,
        metadata TEXT,
        status TEXT DEFAULT 'production',
        discovery_method TEXT DEFAULT 'expert',
        validation_count INTEGER DEFAULT 0,
        statistical_confidence REAL DEFAULT 0.0,
        teacher_confidence REAL DEFAULT 0.0,
        historical_stability REAL DEFAULT 1.0,
        overall_confidence REAL DEFAULT 0.0,
        canonical_id TEXT
    )"""

if 'canonical_id' not in content:
    content = content.replace(old_nodes_schema, new_nodes_schema)

# 2. Add alterations for kg_nodes to upgrade_database_schema
# We will just append the alterations at the end of upgrade_database_schema
alter_block = """    # Alter kg_nodes table for existing DBs
    alterations_kg_nodes = [
        ("status", "TEXT DEFAULT 'production'"),
        ("discovery_method", "TEXT DEFAULT 'expert'"),
        ("validation_count", "INTEGER DEFAULT 0"),
        ("statistical_confidence", "REAL DEFAULT 0.0"),
        ("teacher_confidence", "REAL DEFAULT 0.0"),
        ("historical_stability", "REAL DEFAULT 1.0"),
        ("overall_confidence", "REAL DEFAULT 0.0"),
        ("canonical_id", "TEXT")
    ]
    for col, ctype in alterations_kg_nodes:
        try:
            cur.execute(f"ALTER TABLE kg_nodes ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass
"""

# Inject before conn.commit() in upgrade_database_schema
search_str = "    conn.commit()\n    print(\"DATABASE SCHEMA UPGRADED SUCCESSFULLY.\")"
if "alterations_kg_nodes =" not in content:
    content = content.replace(search_str, alter_block + "\n" + search_str)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Database schema patched for Step 3.")
