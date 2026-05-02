from flask import Flask, request, jsonify
from flask_cors import CORS
from models.model4.engine import get_weakness
from report import generate_report
from models.cognitive_master_engine import process_question

from database import (
    init_db,
    create_user,
    get_user,
    create_room,
    get_teacher_rooms,
    join_room,
    get_student_room,
    save_response,
    save_final_report,
    get_conn,

    get_all_subjects,
    get_topics_by_subject,
    get_subtopics,
    get_room_questions
)

from session_data import (
    add_question_session,
    get_all_sessions,
    reset_results,
    set_reflection,
    get_reflection
)

import os
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

init_db()


# =========================
# AUTH ROUTES
# =========================
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json

    existing = get_user(data["email"])
    if existing:
        return jsonify({"success": False, "message": "User already exists"})

    create_user(data)

    return jsonify({
        "success": True,
        "user": {
            "name": data["name"],
            "email": data["email"],
            "role": data["role"]
        }
    })


@app.route('/signin', methods=['POST'])
def signin():
    data = request.json

    user = get_user(data["email"])

    if not user or user["password"] != data["password"]:
        return jsonify({"success": False, "message": "Invalid credentials"})

    return jsonify({
        "success": True,
        "user": {
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    })


# =========================
# QUIZ SUBMIT
# =========================
@app.route('/submit', methods=['POST'])
def submit():
    data = request.json

    session_obj = process_question(data)
    print("MASTER SESSION:", session_obj)

    add_question_session(session_obj)
    set_reflection(data.get("reflection", ""))

    student_email = data.get("student_email", "anonymous")

    session_obj["room_code"] = data.get("room_code", "solo")
    session_obj["subject"] = data.get("subject", "")
    session_obj["topic"] = data.get("topic", "")
    session_obj["subtopic"] = data.get("subtopic", "")

    save_response(student_email, session_obj)

    return jsonify({
        "message": "Processed",
        "session": session_obj
    })


@app.route('/report', methods=['GET'])
def report():
    student_email = request.args.get("student_email", "anonymous")
    room_code = request.args.get("room_code", "solo")

    sessions = get_all_sessions()
    reflection = get_reflection()

    report_data = generate_report(sessions, reflection)
    report_data["perQuestion"] = sessions

    save_final_report(student_email, report_data, room_code)

    return jsonify(report_data)


@app.route('/weakness', methods=['GET'])
def weakness():
    return jsonify({
        "weakness": "Application"
    })


@app.route('/reset', methods=['POST'])
def reset():
    reset_results()
    return jsonify({"message": "Session reset"})


# =========================
# ROOM SYSTEM
# =========================
@app.route('/create-room', methods=['POST'])
def create_room_api():
    data = request.json
    code = create_room(data)

    return jsonify({
        "success": True,
        "room_code": code
    })


@app.route('/teacher-rooms/<email>', methods=['GET'])
def teacher_rooms(email):
    rooms = get_teacher_rooms(email)
    return jsonify(rooms)


@app.route('/join-room', methods=['POST'])
def join_room_api():
    data = request.json
    room = join_room(data)

    if not room:
        return jsonify({"success": False, "message": "Invalid room code"})

    return jsonify({
        "success": True,
        "room": room
    })


@app.route('/student-room/<email>', methods=['GET'])
def student_room(email):
    room = get_student_room(email)
    return jsonify(room if room else {})
 

# =========================
# TEACHER CUSTOM QUESTION ADD
# =========================
@app.route('/add-custom-question', methods=['POST'])
def add_custom_question():
    data = request.json

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO teacher_custom_questions (
            teacher_email, subject, topic, subtopic,
            prompt, options_json, correct_index,
            question_category, image_url, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        data["teacher_email"],
        data["subject"],
        data["topic"],
        data["subtopic"],
        data["prompt"],
        json.dumps(data["options"]),
        data["correct_index"],
        data["question_category"],
        data.get("image_url", "")
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

# =========================
# MISC
# =========================
@app.route('/')
def home():
    return {"message": "Cognify Backend Running Enterprise V2 🚀"}


@app.route('/favicon.ico')
def favicon():
    return '', 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


# =========================
# DYNAMIC SUBJECT/TOPIC/SUBTOPIC/QUESTION ROUTES
# =========================
@app.route('/subjects', methods=['GET'])
def subjects_api():
    return jsonify(get_all_subjects())


@app.route('/topics/<subject>', methods=['GET'])
def topics_api(subject):
    return jsonify(get_topics_by_subject(subject))


@app.route('/subtopics/<subject>/<topic>', methods=['GET'])
def subtopics_api(subject, topic):
    return jsonify(get_subtopics(subject, topic))


@app.route('/questions/<subject>/<topic>/<subtopic>/<difficulty>/<qtype>/<int:count>', methods=['GET'])
def room_questions_api(subject, topic, subtopic, difficulty, qtype, count):
    qs = get_room_questions(subject, topic, subtopic, difficulty, qtype, count)
    return jsonify(qs)