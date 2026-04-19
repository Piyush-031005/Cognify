import joblib
import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)

model = joblib.load(os.path.join(BASE_DIR, "strategy_model.pkl"))

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