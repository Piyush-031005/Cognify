import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

BASE_DIR = os.path.dirname(__file__)

# dummy dataset
data = {
    "conceptual": [0.7, 0.2, 0.4, 0.6, 0.3],
    "memorized": [0.2, 0.5, 0.3, 0.2, 0.4],
    "fake": [0.1, 0.3, 0.3, 0.2, 0.3],
    "hesitant": [0.2, 0.8, 0.5, 0.3, 0.6],
    "confident": [0.8, 0.2, 0.5, 0.7, 0.4],
    "outcome": ["Improve", "Decline", "Stagnant", "Improve", "Decline"]
}

df = pd.DataFrame(data)

X = df.drop("outcome", axis=1)
y = df["outcome"]

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, os.path.join(BASE_DIR, "model5.pkl"))

print("Model5 trained & saved!")