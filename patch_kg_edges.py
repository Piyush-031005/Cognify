import os
file_path = r'f:\Cognify\database.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target1 = '        confidence REAL DEFAULT 0.95,'
replacement1 = '''        confidence REAL DEFAULT 0.95,
        discovery_method TEXT DEFAULT 'human',
        discovery_date TEXT,
        validation_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'production',
        stability_score REAL DEFAULT 1.0,'''

if target1 in content:
    content = content.replace(target1, replacement1)
    
target2 = '''    )
    \"\"\"

    # Create new student_concept_mastery'''

# In database.py it's:
#    )
#    """)
#
#    # Create new student_concept_mastery

target2 = '    )\n    """)\n\n    # Create new student_concept_mastery'

replacement2 = '''    )
    """)

    # Alter kg_edges table extensions for existing DBs
    alterations_kg_edges = [
        ("discovery_method", "TEXT DEFAULT 'human'"),
        ("discovery_date", "TEXT"),
        ("validation_count", "INTEGER DEFAULT 0"),
        ("status", "TEXT DEFAULT 'production'"),
        ("stability_score", "REAL DEFAULT 1.0")
    ]
    for col_name, col_type in alterations_kg_edges:
        try:
            cur.execute(f"ALTER TABLE kg_edges ADD COLUMN {col_name} {col_type}")
        except:
            pass

    # Create new student_concept_mastery'''

if target2 in content:
    content = content.replace(target2, replacement2)
    print("SUCCESS kg_edges updated")
else:
    print("Failed to find target2")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
