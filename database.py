import sqlite3
from datetime import datetime
import random
import string
import json

DB_NAME = "cognify.db"


# =========================
# CONNECTION
# =========================
def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# INIT DATABASE
# =========================
def init_db():
    print("DATABASE INIT RUNNING...")
    conn = get_conn()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        email TEXT UNIQUE,
        password TEXT,
        education TEXT,
        learning_style TEXT,
        subjects TEXT,
        confidence REAL,
        role TEXT,
        created_at TEXT
    )
    """)

    # QUESTIONS MASTER (SYSTEM GENERATED)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        exam_level TEXT,
        prompt TEXT,
        options_json TEXT,
        correct_index INTEGER,
        question_type TEXT,
        difficulty TEXT,
        cognitive_skill TEXT,
        misconception_tag TEXT,
        bloom_level TEXT,
        estimated_time INTEGER,
        image_url TEXT,
        created_at TEXT
    )
    """)

    # QUESTION BANK META TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        difficulty TEXT,
        qtype TEXT,
        prompt TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_index INTEGER
)
""")

    # TEACHER CUSTOM QUESTIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_custom_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_email TEXT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT,
        prompt TEXT,
        options_json TEXT,
        correct_index INTEGER,
        question_category TEXT,
        image_url TEXT,
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
    difficulty TEXT,
    question_mix TEXT,
    question_count INTEGER,
    created_at TEXT
)
""")

    # ROOM QUESTION MAP
    cur.execute("""
    CREATE TABLE IF NOT EXISTS room_questions_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        question_id INTEGER,
        source_type TEXT,
        created_at TEXT
    )
    """)

    # ROOM STUDENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS room_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        student_email TEXT,
        joined_at TEXT
    )
    """)

    # RESPONSES EXPANDED
    cur.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        student_email TEXT,
        subject TEXT,
        attempt_id TEXT,
        topic TEXT,
        subtopic TEXT,
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
        confidence_error REAL,
        engagement_score REAL,
        understanding_pred INTEGER,
        behavior_pred TEXT,
        strategy_pred TEXT,
        cognitive_flag TEXT,
        hover_count INTEGER,
        same_option_clicks INTEGER,
        reflection_length INTEGER,
        created_at TEXT
    )
    """)

    # REPORTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        room_code TEXT,
        report_json TEXT,
        created_at TEXT
    )
    """)

    # LONG TERM STUDENT PROFILE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT UNIQUE,
        avg_conceptual REAL,
        avg_hesitation REAL,
        avg_confidence REAL,
        dominant_pattern TEXT,
        weak_subjects TEXT,
        tests_taken INTEGER,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================
# USER FUNCTIONS
# =========================
def create_user(data):
    conn = get_conn()
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


# =========================
# ROOM FUNCTIONS
# =========================
def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_room(data):
    conn = get_conn()
    cur = conn.cursor()

    room_code = generate_room_code()

    cur.execute("""
        INSERT INTO rooms (
            room_code,
            teacher_email,
            subject,
            topic,
            subtopic,
            difficulty,
            question_mix,
            question_count,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        room_code,
        data["teacher_email"],
        data["subject"],
        data["topic"],
        data["subtopic"],
        data.get("difficulty", "mixed"),
        data.get("question_mix", "mixed"),
        data.get("question_count", 5),
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


# =========================
# RESPONSE + REPORT SAVE
# =========================
def save_response(student_email, obj):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO responses (
            room_code, student_email, attempt_id, subject, topic, subtopic,
            question_id, question_text,
            response_time, idle_time, rewrite_count, backspace_count,
            attempts, confidence, correct,
            hesitation_score, confidence_error, engagement_score,
            understanding_pred, behavior_pred, strategy_pred,
            cognitive_flag, hover_count, same_option_clicks, reflection_length,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        obj.get("room_code", "solo"),
student_email,
obj.get("attempt_id", "default_attempt"),
obj.get("subject", ""),
        obj.get("topic", ""),
        obj.get("subtopic", ""),
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
        obj.get("confidence_error"),
        obj.get("engagement_score"),
        obj.get("understanding_pred"),
        obj.get("behavior_pred"),
        obj.get("strategy_pred"),
        obj.get("cognitive_flag"),
        obj.get("hover_count"),
        obj.get("same_option_clicks"),
        obj.get("reflection_length"),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


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


def get_all_subjects():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT subject FROM question_bank ORDER BY subject")
    rows = cur.fetchall()
    conn.close()
    return [r["subject"] for r in rows]


def get_topics_by_subject(subject):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT topic FROM question_bank WHERE subject=? ORDER BY topic", (subject,))
    rows = cur.fetchall()
    conn.close()
    return [r["topic"] for r in rows]


def get_subtopics(subject, topic):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT subtopic FROM question_bank
        WHERE subject=? AND topic=?
        ORDER BY subtopic
    """, (subject, topic))
    rows = cur.fetchall()
    conn.close()
    return [r["subtopic"] for r in rows]


def get_room_questions(subject, topic, subtopic, difficulty="mixed", qtype="mixed", limit_count=5):
    conn = get_conn()
    cur = conn.cursor()

    query = """
    SELECT * FROM question_bank
    WHERE subject=? AND topic=? AND subtopic=?
    """
    params = [subject, topic, subtopic]

    if difficulty != "mixed":
        query += " AND difficulty=?"
        params.append(difficulty)

    if qtype != "mixed":
        query += " AND qtype=?"
        params.append(qtype)

    query += " ORDER BY RANDOM() LIMIT ?"
    params.append(limit_count)

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()

    final = []

    for r in rows:
        final.append({
            "id": r["id"],
            "prompt": r["prompt"],
            "options": [
                r["option_a"],
                r["option_b"],
                r["option_c"],
                r["option_d"]
            ],
            "correctIndex": r["correct_index"]
        })

    return final

# =========================
# FETCH STUDENT RESPONSES
# =========================
def get_student_responses(student_email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM responses
        WHERE student_email = ?
        ORDER BY id ASC
    """, (student_email,))

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# =========================
# CLEAR STUDENT RESPONSES AFTER REPORT
# =========================
def clear_student_responses(student_email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM responses
        WHERE student_email = ?
    """, (student_email,))

    conn.commit()
    conn.close()


def get_student_responses(student_email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM responses
        WHERE student_email = ?
        ORDER BY id ASC
    """, (student_email,))

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_attempt_responses(student_email, attempt_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM responses
        WHERE student_email = ? AND attempt_id = ?
        ORDER BY id ASC
    """, (student_email, attempt_id))

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]