import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# -----------------------
# Load dataset
# -----------------------

columns = [
    "time_taken",
    "idle_time",
    "rewrite_count",
    "backspace_count",
    "skipped",
    "question_id",
    "hesitation_score",
    "friction_level",
    "behavior_type"
]

df = pd.read_csv("cognitive_dataset.csv", names=columns)

# -----------------------
# Features & Target
# -----------------------

features = [
    "time_taken",
    "idle_time",
    "rewrite_count",
    "backspace_count",
    "skipped",
    "hesitation_score"
]

X = df[features]
y = df["behavior_type"]

# -----------------------
# Train Test Split
# -----------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------
# Model
# -----------------------

model = RandomForestClassifier(n_estimators=100)

model.fit(X_train, y_train)

# -----------------------
# Evaluation
# -----------------------

predictions = model.predict(X_test)

print("Model Evaluation:\n")
print(classification_report(y_test, predictions))

# -----------------------
# Save model
# -----------------------

joblib.dump(model, "cognitive_model.pkl")

print("\nCognitive ML model saved!")