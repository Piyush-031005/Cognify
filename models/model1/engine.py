import joblib
import pandas as pd

import os
import joblib

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
    """

    df = pd.DataFrame([data])
    df_scaled = scaler.transform(df)

    pred = model.predict(df_scaled)[0]

    return int(pred)