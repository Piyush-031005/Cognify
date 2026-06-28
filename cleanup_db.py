import re

file_path = r'f:\Cognify\database.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the duplicate column definitions in kg_edges
content = re.sub(r'        discovery_method TEXT DEFAULT \'human\',\n        discovery_date TEXT,\n        validation_count INTEGER DEFAULT 0,\n        status TEXT DEFAULT \'production\',\n        stability_score REAL DEFAULT 1\.0,\n        discovery_method TEXT DEFAULT \'human\',\n        discovery_date TEXT,\n        validation_count INTEGER DEFAULT 0,\n        status TEXT DEFAULT \'production\',\n        stability_score REAL DEFAULT 1\.0,',
r'''        discovery_method TEXT DEFAULT 'human',
        discovery_date TEXT,
        validation_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'production',
        stability_score REAL DEFAULT 1.0,''', content)

# Check if kg_edge_evidence was created correctly
if 'kg_edge_evidence' not in content:
    print("kg_edge_evidence missing, adding...")
    target = '        created_at TEXT\n    )\n    """)\n\n    # --- Week 5'
    new_tables = '''        created_at TEXT
    )
    """)

    # Create kg_edge_evidence table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kg_edge_evidence (
        id TEXT PRIMARY KEY,
        source_id TEXT,
        target_id TEXT,
        relation_type TEXT,
        teacher_support INTEGER DEFAULT 0,
        teacher_rejections INTEGER DEFAULT 0,
        student_sample_size INTEGER DEFAULT 0,
        p_struggle_given_mastered REAL,
        p_struggle_given_not_mastered REAL,
        kl_divergence REAL,
        confidence_score REAL,
        explanation TEXT,
        last_recomputed TEXT,
        FOREIGN KEY (source_id, target_id, relation_type) REFERENCES kg_edges(source_id, target_id, relation_type)
    )
    """)

    # Create apd_batch_runs table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS apd_batch_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date TEXT,
        subject TEXT,
        student_sample INTEGER,
        concepts_analyzed INTEGER,
        edges_tested INTEGER,
        candidates_generated INTEGER,
        execution_time_ms INTEGER
    )
    """)

    # Create kg_evolution_log table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kg_evolution_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation TEXT,
        entity_id TEXT,
        old_state TEXT,
        new_state TEXT,
        actor TEXT,
        timestamp TEXT
    )
    """)

    # --- Week 5'''
    content = content.replace(target, new_tables)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Cleanup complete.")
