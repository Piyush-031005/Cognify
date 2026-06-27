# model3_engine.py

import joblib
import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)

model = joblib.load(os.path.join(BASE_DIR, "cognitive_model.pkl"))

def predict_behavior(data):
    """
    data = {
        "time_taken": float,
        "idle_time": float,
        "rewrite_count": int,
        "backspace_count": int,
        "skipped": int
    }
    returns (str_pred, float_confidence)
    """
    # Feature engineering (IMPORTANT)
    hesitation_score = data["idle_time"] / max(data["time_taken"], 1)

    df = pd.DataFrame([{
        "time_taken": data["time_taken"],
        "idle_time": data["idle_time"],
        "rewrite_count": data["rewrite_count"],
        "backspace_count": data["backspace_count"],
        "skipped": data["skipped"],
        "hesitation_score": hesitation_score
    }])

    pred = model.predict(df)[0]
    
    # Calculate probability/confidence of the predicted class
    probs = model.predict_proba(df)[0]
    classes = list(model.classes_)
    pred_idx = classes.index(pred)
    conf = float(probs[pred_idx])

    return str(pred), round(conf, 3)