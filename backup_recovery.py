"""
backup_recovery.py
Week 23 — SQLite Online Non-blocking Backup & Recovery (Refinement 6).
"""

import os
import json
import sqlite3
import hashlib
import datetime
import config

def get_projection_row_checksum(conn):
    """
    Calculates an MD5 checksum over the row counts of all primary twin projections
    to ensure restoration integrity.
    """
    tables = [
        "teacher_classroom_retention",
        "teacher_engagement_summary",
        "teacher_intervention_queue",
        "student_profile_projection",
        "student_progress_projection",
        "parent_student_projection",
        "school_classroom_summary",
        "school_teacher_summary",
        "research_concept_decay"
    ]
    cur = conn.cursor()
    hasher = hashlib.md5()
    try:
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) as count FROM {t}")
                cnt = cur.fetchone()["count"] or 0
                hasher.update(str(cnt).encode('utf-8'))
            except sqlite3.OperationalError:
                # Table might not exist in early schema
                hasher.update(b"0")
        return hasher.hexdigest()
    except Exception:
        return "unknown_checksum"

def backup_database(target_path):
    """
    Safely makes an online copy of the database without locking other connections.
    Saves metadata sidecar next to the backup file.
    """
    src_conn = sqlite3.connect(config.DATABASE_URL)
    dest_conn = sqlite3.connect(target_path)
    try:
        # Perform non-blocking online backup (Decision 6)
        src_conn.backup(dest_conn)
        
        # Calculate checksum on active db
        checksum = get_projection_row_checksum(src_conn)
        
        # Write metadata sidecar
        meta = {
            "database_version": config.DATABASE_VERSION,
            "schema_version": config.SCHEMA_VERSION,
            "git_commit": config.GIT_COMMIT,
            "release_tag": config.RELEASE_TAG,
            "created_at": datetime.datetime.now().isoformat(),
            "checksum": checksum
        }
        meta_path = f"{target_path}.meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4)
            
        return {
            "status": "success",
            "backup_file": target_path,
            "metadata_file": meta_path,
            "metadata": meta
        }
    finally:
        dest_conn.close()
        src_conn.close()

def restore_database(source_path):
    """
    Restores the database from backup and verifies metadata/checksums.
    """
    meta_path = f"{source_path}.meta.json"
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Backup file not found: {source_path}")
        
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Backup metadata sidecar not found: {meta_path}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Perform online restore
    src_conn = sqlite3.connect(source_path)
    dest_conn = sqlite3.connect(config.DATABASE_URL)
    try:
        # Verify version compatibility before writing
        if meta.get("schema_version") != config.SCHEMA_VERSION:
            raise ValueError(f"Schema mismatch: Backup is {meta.get('schema_version')}, system is {config.SCHEMA_VERSION}")
            
        # Copy backup database into live connection
        src_conn.backup(dest_conn)
        
        # Verify checksum post-restoration
        post_checksum = get_projection_row_checksum(dest_conn)
        if post_checksum != meta.get("checksum"):
            raise ValueError("Restoration checksum validation failed: Data corruption detected")
            
        return {
            "status": "success",
            "metadata": meta,
            "verified_checksum": post_checksum
        }
    finally:
        dest_conn.close()
        src_conn.close()
