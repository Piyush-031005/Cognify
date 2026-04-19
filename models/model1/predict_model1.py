import joblib
import numpy as np

model = joblib.load("model1.pkl")
scaler = joblib.load("scaler.pkl")

# example user input
# [response_time, attempts, confidence, is_application, correct]
user = np.array([[12, 1, 0.9, 0, 0]])

user = scaler.transform(user)

pred = model.predict(user)[0]

labels = {
    0: "Memorized",
    1: "Conceptual Understanding",
    2: "Fake Understanding"
}

print("Prediction:", labels[pred])