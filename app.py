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
    save_final_report
)

from session_data import (
    add_question_session,
    get_all_sessions,
    reset_results,
    set_reflection,
    get_reflection
)

import json
import os

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
# QUIZ / COGNITIVE PROCESSING
# =========================
@app.route('/submit', methods=['POST'])
def submit():
    data = request.json

    session_obj = process_question(data)

    print("MASTER SESSION:", session_obj)

    add_question_session(session_obj)
    set_reflection(data.get("reflection", ""))

    student_email = data.get("student_email", "anonymous")
    save_response(student_email, session_obj)

    return jsonify({
        "message": "Processed",
        "session": session_obj
    })


@app.route('/report', methods=['GET'])
def report():
    student_email = request.args.get("student_email", "anonymous")

    sessions = get_all_sessions()
    reflection = get_reflection()

    report_data = generate_report(sessions, reflection)
    report_data["perQuestion"] = sessions

    save_final_report(student_email, report_data)
    
    reset_results()

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
# TEACHER ROOM SYSTEM
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
# QUESTION BANK ROUTES
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "models", "data", "questions.json")

with open(file_path) as f:
    QUESTIONS_DB = json.load(f)


@app.route('/questions/<subject>/<topic>/<subtopic>', methods=['GET'])
def get_questions_subtopic(subject, topic, subtopic):
    qs = QUESTIONS_DB.get(subject, {}).get(topic, {}).get(subtopic, [])
    return jsonify(qs)


@app.route('/topics/<subject>', methods=['GET'])
def get_topics(subject):
    topics = list(QUESTIONS_DB.get(subject, {}).keys())
    return jsonify(topics)


@app.route('/questions/<subject>/<topic>', methods=['GET'])
def get_questions(subject, topic):
    subtopics = QUESTIONS_DB.get(subject, {}).get(topic, {})
    return jsonify(list(subtopics.keys()))


# =========================
# MISC
# =========================
@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/debug')
def debug():
    return "DEBUG WORKING"


@app.route('/')
def home():
    return {"message": "Cognify Backend Running 🚀"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))