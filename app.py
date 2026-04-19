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


if __name__ == "__main__":
    app.run(debug=True)