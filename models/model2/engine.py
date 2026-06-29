import joblib
import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)

try:
    model = joblib.load(os.path.join(BASE_DIR, "strategy_model.pkl"))
except Exception as e:
    print("WARNING: Failed to load strategy_model pickle file. Using fallback predictor. Error:", e)
    model = None

def predict_strategy(data):
    """
    data = {
        "confidence": int,
        "time_taken": float,
        "correct": int
    }
    returns (str_pred, float_confidence)
    """
    if model is None:
        pred = "concept-based" if data.get("correct", 0) == 1 else "trial-based"
        return pred, 0.85

    # Feature engineering (same as training)
    confidence_error = data["confidence"] * (1 - data["correct"])
    speed_score = 10 / data["time_taken"] if data["time_taken"] > 0 else 0
    fake_confidence = 1 if (data["confidence"] >= 4 and data["correct"] == 0) else 0
    guess_flag = 1 if (data["confidence"] <= 2 and data["correct"] == 1) else 0

    try:
        df = pd.DataFrame([{
            "confidence": data["confidence"],
            "time_taken": data["time_taken"],
            "confidence_error": confidence_error,
            "speed_score": speed_score,
            "fake_confidence": fake_confidence,
            "guess_flag": guess_flag
        }])

        pred = model.predict(df)[0]
        
        # Calculate probability/confidence of the predicted class
        probs = model.predict_proba(df)[0]
        classes = list(model.classes_)
        pred_idx = classes.index(pred)
        conf = float(probs[pred_idx])

        return str(pred), round(conf, 3)
    except Exception as e:
        print("Fallback predict_strategy triggered due to prediction failure:", e)
        pred = "concept-based" if data.get("correct", 0) == 1 else "trial-based"
        return pred, 0.85