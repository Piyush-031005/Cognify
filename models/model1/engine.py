import joblib
import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)

try:
    model = joblib.load(os.path.join(BASE_DIR, "model1.pkl"))
    scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))
except Exception as e:
    print("WARNING: Failed to load model1/scaler pickle files. Using fallback predictor. Error:", e)
    model = None
    scaler = None

def predict_understanding(data):
    """
    data = {
        "response_time": float,
        "attempts": int,
        "confidence": float,
        "is_application": int,
        "correct": int
    }
    returns (int_pred, float_confidence)
    """
    if model is None or scaler is None:
        # Fallback to rule-based logic
        pred = 1 if data.get("correct", 0) == 1 else 2
        return pred, 0.85
        
    try:
        df = pd.DataFrame([data])
        df_scaled = scaler.transform(df)

        pred = model.predict(df_scaled)[0]
        
        # Calculate probability/confidence of the predicted class
        probs = model.predict_proba(df_scaled)[0]
        classes = list(model.classes_)
        pred_idx = classes.index(pred)
        conf = float(probs[pred_idx])

        return int(pred), round(conf, 3)
    except Exception as e:
        print("Fallback predict_understanding triggered due to prediction failure:", e)
        pred = 1 if data.get("correct", 0) == 1 else 2
        return pred, 0.85