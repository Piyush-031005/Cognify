from flask import Flask, request, jsonify
from flask_cors import CORS
from models.model1.engine import predict_understanding
from models.model3.engine import predict_behavior
from models.model2.engine import predict_strategy
from models.model4.engine import get_weakness
from session_data import (
    add_understanding, add_behavior, add_strategy,
    get_all_results, reset_results,
    set_reflection, get_reflection
)
from report import generate_report

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# 🔥 MAIN SUBMIT ROUTE (MISSING THA)
@app.route('/submit', methods=['POST'])
def submit():
    data = request.json

    # Model 1
    u_pred = predict_understanding({
        "response_time": data["response_time"],
        "attempts": data["attempts"],
        "confidence": data["confidence"],
        "is_application": data["is_application"],
        "correct": data["correct"]
    })

    # Model 3
    b_pred = predict_behavior({
        "time_taken": data["time_taken"],
        "idle_time": data["idle_time"],
        "rewrite_count": data["rewrite_count"],
        "backspace_count": data["backspace_count"],
        "skipped": data["skipped"]
    })

    # Model 2
    m2_pred = predict_strategy({
        "confidence": data["confidence"],
        "time_taken": data["response_time"],
        "correct": data["correct"]
    })

    # 🔥 DEBUG PRINTS
    print("Model1:", u_pred)
    print("Model2:", m2_pred)
    print("Model3:", b_pred)

    # store
    add_understanding(u_pred)
    add_behavior(b_pred)
    add_strategy(m2_pred)
    set_reflection(data.get("reflection", ""))

    return jsonify({
        "message": "Processed",
        "understanding": u_pred,
        "behavior": b_pred,
        "strategy": m2_pred
    })


@app.route('/report', methods=['GET'])
def report():
    data = get_all_results()
    data["reflection"] = get_reflection()

    return jsonify(generate_report(data))


@app.route('/weakness', methods=['GET'])
def weakness():
    data = get_all_results()

    result = get_weakness(data)

    print("Model4:", result)

    return jsonify({
        "weakness": result
    })


@app.route('/reset', methods=['POST'])
def reset():
    reset_results()
    return jsonify({"message": "Session reset"})


@app.route('/')
def home():
    return {"message": "Cognify Backend Running 🚀"}


@app.route('/favicon.ico')
def favicon():
    return '', 204

import json
import os

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

@app.route('/debug')
def debug():
    return "DEBUG WORKING"

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))