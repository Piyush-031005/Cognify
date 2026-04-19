import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# load dataset
import os

BASE_DIR = os.path.dirname(__file__)
df = pd.read_csv(os.path.join(BASE_DIR, "processed_responses_with_strategy.csv"))

# features
features = [
    "confidence",
    "time_taken",
    "confidence_error",
    "speed_score",
    "fake_confidence",
    "guess_flag"
]

X = df[features]
y = df["strategy_type"]

# split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# model
model = RandomForestClassifier(n_estimators=100)

# train
model.fit(X_train, y_train)

# test
predictions = model.predict(X_test)

print("Model Evaluation:\n")
print(classification_report(y_test, predictions))

# save model
joblib.dump(model, "strategy_model.pkl")

print("\nStrategy model saved!")