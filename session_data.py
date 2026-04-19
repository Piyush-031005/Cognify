understanding_results = []
behavior_results = []
strategy_results = []
reflection_text = ""

def add_understanding(val):
    understanding_results.append(val)

def add_behavior(val):
    behavior_results.append(val)

def add_strategy(val):   
    strategy_results.append(val)

def set_reflection(text):
    global reflection_text
    reflection_text = text

def get_reflection():
    return reflection_text

def get_all_results():
    return {
        "understanding": understanding_results,
        "behavior": behavior_results,
        "strategy": strategy_results
    }

def reset_results():
    global understanding_results, behavior_results, reflection_text
    understanding_results = []
    behavior_results = []
    strategy_results = []
    reflection_text = ""


import joblib
import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)

def predict_strategy(data):
    """
    data = {
        "confidence": int,
        "time_taken": float,
        "correct": int
    }
    """

    # 🔥 Feature engineering (same as training)
    confidence_error = data["confidence"] * (1 - data["correct"])
    speed_score = 10 / data["time_taken"] if data["time_taken"] > 0 else 0
    fake_confidence = 1 if (data["confidence"] >= 4 and data["correct"] == 0) else 0
    guess_flag = 1 if (data["confidence"] <= 2 and data["correct"] == 1) else 0

    df = pd.DataFrame([{
        "confidence": data["confidence"],
        "time_taken": data["time_taken"],
        "confidence_error": confidence_error,
        "speed_score": speed_score,
        "fake_confidence": fake_confidence,
        "guess_flag": guess_flag
    }])

    pred = model.predict(df)[0]

    return str(pred)