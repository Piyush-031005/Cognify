import os

file_path = r'f:\Cognify\database.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update question_bank schema in init_db
old_qb_schema = """        qqi_score REAL DEFAULT 80.0,
        qqi_confidence REAL DEFAULT 0.1,"""

new_qb_schema = """        qqi_score REAL DEFAULT 80.0,
        qqi_confidence REAL DEFAULT 0.1,
        calibrated_qqi_score REAL,
        calibrated_difficulty TEXT,"""

if 'calibrated_qqi_score' not in content:
    content = content.replace(old_qb_schema, new_qb_schema)

# 2. Update question_versions schema
old_qv_schema = """        change_reason TEXT,
        edited_at TEXT,"""
        
new_qv_schema = """        change_reason TEXT,
        calibration_reason TEXT,
        edited_at TEXT,"""

if 'calibration_reason' not in content:
    content = content.replace(old_qv_schema, new_qv_schema)

# 3. Add to upgrade_database_schema
alter_block = """    # Alter question_bank for QQI Calibration
    alterations_qb_calib = [
        ("calibrated_qqi_score", "REAL"),
        ("calibrated_difficulty", "TEXT")
    ]
    for col, ctype in alterations_qb_calib:
        try:
            cur.execute(f"ALTER TABLE question_bank ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass

    # Alter question_versions
    try:
        cur.execute("ALTER TABLE question_versions ADD COLUMN calibration_reason TEXT")
    except sqlite3.OperationalError:
        pass
"""

upgrade_search_str = "    conn.commit()\n    print(\"DATABASE SCHEMA UPGRADED SUCCESSFULLY.\")"
if "alterations_qb_calib =" not in content:
    content = content.replace(upgrade_search_str, alter_block + "\n" + upgrade_search_str)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Database patched for QQI Calibration.")
