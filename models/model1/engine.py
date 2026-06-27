import joblib
import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)

model = joblib.load(os.path.join(BASE_DIR, "model1.pkl"))
scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))

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
    df = pd.DataFrame([data])
    df_scaled = scaler.transform(df)

    pred = model.predict(df_scaled)[0]
    
    # Calculate probability/confidence of the predicted class
    probs = model.predict_proba(df_scaled)[0]
    classes = list(model.classes_)
    pred_idx = classes.index(pred)
    conf = float(probs[pred_idx])

    return int(pred), round(conf, 3)