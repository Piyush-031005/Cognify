"""
parent_twin/__init__.py
CQRS facade, event routing, and rebuild_projections() with MD5 checksum (Decision 5).
"""

import json
import hashlib
import datetime
from database import get_conn

import parent_twin.snapshot as snapshot
import parent_twin.weekly_report as weekly_report
import parent_twin.notifications as notifications
import parent_twin.digest as digest


# ─── CEB Event Handlers ──────────────────────────────────────────────────────

def handle_memory_updated(event_data, is_replay=False, replay_mode="SAFE"):
    snapshot.handle_memory_updated(event_data, is_replay, replay_mode)


def handle_attention_updated(event_data, is_replay=False, replay_mode="SAFE"):
    snapshot.handle_attention_updated(event_data, is_replay, replay_mode)


def handle_ccli_updated(event_data, is_replay=False, replay_mode="SAFE"):
    snapshot.handle_ccli_updated(event_data, is_replay, replay_mode)


def handle_decision_generated(event_data, is_replay=False, replay_mode="SAFE"):
    snapshot.handle_decision_generated(event_data, is_replay, replay_mode)


# ─── Projection Rebuild (Decision 5 — Checksum) ──────────────────────────────

def rebuild_projections():
    """
    Clears Parent Twin projection tables, replays events in SAFE mode,
    then computes and stores a projection checksum.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM parent_student_projection")
        cur.execute("DELETE FROM parent_weekly_report")
        cur.execute("DELETE FROM parent_notification_log")
        conn.commit()
    finally:
        conn.close()

    import event_replay
    replay_res = event_replay.replay_all_events("parent_twin", mode="SAFE")

    # Checksum over row counts of all parent projection tables
    conn = get_conn()
    cur = conn.cursor()
    tables = [
        "parent_student_projection",
        "parent_weekly_report",
        "parent_notification_log",
    ]
    hasher = hashlib.md5()
    try:
        for t in tables:
            cur.execute(f"SELECT COUNT(*) as count FROM {t}")
            cnt = cur.fetchone()["count"] or 0
            hasher.update(str(cnt).encode("utf-8"))
        checksum = hasher.hexdigest()

        now_str = datetime.datetime.now().isoformat()
        cur.execute(
            """
            INSERT INTO parent_projection_metadata (projection_version, checksum, rebuilt_at)
            VALUES ('v1.0', ?, ?)
            ON CONFLICT(projection_version) DO UPDATE SET
                checksum = excluded.checksum,
                rebuilt_at = excluded.rebuilt_at
            """,
            (checksum, now_str),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "status": "success",
        "events_replayed": replay_res.get("events_processed", 0),
        "projection_checksum": checksum,
    }


# ─── CQRS Query Methods (Decision 1 — Read-only from parent_* tables) ────────

def get_children(parent_email: str) -> list:
    """Returns all students linked to a parent via parent_student_mapping."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT m.student_email, m.relationship_type, m.is_primary,
                   p.overall_digest, p.memory_trend, p.last_active_date
            FROM parent_student_mapping m
            LEFT JOIN parent_student_projection p ON m.student_email = p.student_email
            WHERE m.parent_email = ?
            ORDER BY m.is_primary DESC, m.student_email
            """,
            (parent_email,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_snapshot(parent_email: str, student_email: str) -> dict:
    """
    Returns the parent-facing snapshot for a specific child.
    Verifies the parent-child mapping before returning data (security).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT 1 FROM parent_student_mapping WHERE parent_email = ? AND student_email = ?",
            (parent_email, student_email),
        )
        if not cur.fetchone():
            return {"error": "Access denied or child not linked to this parent."}

        cur.execute(
            "SELECT * FROM parent_student_projection WHERE student_email = ?",
            (student_email,)
        )
        row = cur.fetchone()
        if not row:
            return {"message": "No projection data yet. Check back after the first study session."}

        return {
            "student_email": student_email,
            "overall_digest": row["overall_digest"],
            "memory_trend": row["memory_trend"],
            "last_active_date": row["last_active_date"],
            "study_habits": json.loads(row["study_habit_summary_json"]),
            "strengths": json.loads(row["strengths_digest_json"]),
            "weaknesses": json.loads(row["weaknesses_digest_json"]),
            "projection_version": row["projection_version"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def link_child(parent_email: str, student_email: str,
               relationship_type: str = "guardian", is_primary: int = 1) -> dict:
    """
    Creates or updates a parent-student mapping entry.
    """
    valid_types = ("mother", "father", "guardian", "mentor")
    if relationship_type not in valid_types:
        raise ValueError(f"Invalid relationship_type: {relationship_type}. Must be one of {valid_types}")

    conn = get_conn()
    cur = conn.cursor()
    now_str = datetime.datetime.now().isoformat()
    try:
        cur.execute(
            """
            INSERT INTO parent_student_mapping
                (parent_email, student_email, relationship_type, is_primary, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(parent_email, student_email) DO UPDATE SET
                relationship_type = excluded.relationship_type,
                is_primary = excluded.is_primary
            """,
            (parent_email, student_email, relationship_type, is_primary, now_str),
        )
        conn.commit()
        return {"status": "success", "linked": student_email}
    finally:
        conn.close()
