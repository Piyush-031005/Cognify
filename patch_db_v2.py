import re

file_path = r'f:\Cognify\database.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update kg_edges schema
old_kg_edges = """        stability_score REAL DEFAULT 1.0,"""
new_kg_edges = """        stability_score REAL DEFAULT 1.0,
        statistical_confidence REAL DEFAULT 0.0,
        teacher_confidence REAL DEFAULT 0.0,
        historical_stability REAL DEFAULT 1.0,
        overall_confidence REAL DEFAULT 0.0,"""
if 'statistical_confidence' not in content:
    content = content.replace(old_kg_edges, new_kg_edges)

# 2. Update kg_edges alterations list
old_alter = """        ("stability_score", "REAL DEFAULT 1.0")
    ]"""
new_alter = """        ("stability_score", "REAL DEFAULT 1.0"),
        ("statistical_confidence", "REAL DEFAULT 0.0"),
        ("teacher_confidence", "REAL DEFAULT 0.0"),
        ("historical_stability", "REAL DEFAULT 1.0"),
        ("overall_confidence", "REAL DEFAULT 0.0")
    ]"""
if '"statistical_confidence"' not in content:
    content = content.replace(old_alter, new_alter)

# 3. Update kg_edge_evidence schema
old_evidence = """        last_recomputed TEXT,"""
new_evidence = """        last_recomputed TEXT,
        conflict_detected BOOLEAN DEFAULT 0,
        conflict_details TEXT,"""
if 'conflict_detected' not in content:
    content = content.replace(old_evidence, new_evidence)

# 4. Update kg_evolution_log schema
old_log = """        actor TEXT,"""
new_log = """        actor TEXT,
        confidence_delta REAL,"""
if 'confidence_delta' not in content:
    content = content.replace(old_log, new_log)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Database schema patched for Phase 2 Step 2.")
