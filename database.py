import sqlite3
from datetime import datetime
import random
import string

DB_NAME = "cognify.db"


def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    print("DATABASE INIT RUNNING...")
    conn = get_conn()
    cur = conn.cursor()

       # RESPONSES TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        question_id INTEGER,
        question_text TEXT,
        response_time REAL,
        idle_time REAL,
        rewrite_count INTEGER,
        backspace_count INTEGER,
        attempts INTEGER,
        confidence REAL,
        correct INTEGER,
        hesitation_score REAL,
        engagement_score REAL,
        understanding_pred INTEGER,
        behavior_pred TEXT,
        strategy_pred TEXT,
        cognitive_flag TEXT,
        created_at TEXT
    )
    """)

    # ROOMS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT UNIQUE,
        teacher_email TEXT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        created_at TEXT
    )
    """)

    # ROOM STUDENTS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS room_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        student_email TEXT,
        joined_at TEXT
    )
    """)

    # REPORTS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        room_code TEXT,
        report_json TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def create_user(data):
    conn = sqlite3.connect("cognify.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users
        (name, age, email, password, education, learning_style, subjects, confidence, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["age"],
        data["email"],
        data["password"],
        data["education"],
        data["learningStyle"],
        ", ".join(data["subjects"]),
        data["confidence"],
        data["role"],
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_user(email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()

    conn.close()
    return dict(row) if row else None


def save_response(student_email, obj):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO responses (
            student_email,
            question_id,
            question_text,
            response_time,
            idle_time,
            rewrite_count,
            backspace_count,
            attempts,
            confidence,
            correct,
            hesitation_score,
            engagement_score,
            understanding_pred,
            behavior_pred,
            strategy_pred,
            cognitive_flag,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_email,
        obj.get("question_id"),
        obj.get("question_text"),
        obj.get("response_time"),
        obj.get("idle_time"),
        obj.get("rewrite_count"),
        obj.get("backspace_count"),
        obj.get("attempts"),
        obj.get("confidence"),
        obj.get("correct"),
        obj.get("hesitation_score"),
        obj.get("engagement_score"),
        obj.get("understanding_pred"),
        obj.get("behavior_pred"),
        obj.get("strategy_pred"),
        obj.get("cognitive_flag"),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


import json

def save_final_report(student_email, report_obj, room_code="solo"):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO reports (student_email, room_code, report_json, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        student_email,
        room_code,
        json.dumps(report_obj),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_room(data):
    conn = get_conn()
    cur = conn.cursor()

    room_code = generate_room_code()

    cur.execute("""
        INSERT INTO rooms (room_code, teacher_email, subject, topic, subtopic, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        room_code,
        data["teacher_email"],
        data["subject"],
        data["topic"],
        data["subtopic"],
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return room_code


def get_teacher_rooms(email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rooms WHERE teacher_email = ? ORDER BY id DESC", (email,))
    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]



def join_room(data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rooms WHERE room_code = ?", (data["room_code"],))
    room = cur.fetchone()

    if not room:
        conn.close()
        return None

    cur.execute("""
        INSERT INTO room_students (room_code, student_email, joined_at)
        VALUES (?, ?, ?)
    """, (
        data["room_code"],
        data["student_email"],
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return dict(room)


def get_student_room(email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT rooms.* FROM rooms
        JOIN room_students ON rooms.room_code = room_students.room_code
        WHERE room_students.student_email = ?
        ORDER BY room_students.id DESC
        LIMIT 1
    """, (email,))

    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None