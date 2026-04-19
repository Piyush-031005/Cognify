import joblib
import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)

model = joblib.load(os.path.join(BASE_DIR, "model5.pkl"))

def predict_future(data):
    """
    data = {
        conceptual, memorized, fake,
        hesitant, confident
    }
    """

    df = pd.DataFrame([data])

    pred = model.predict(df)[0]

    return pred