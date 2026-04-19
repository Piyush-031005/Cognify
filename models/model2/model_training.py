import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# load processed dataset
data = pd.read_csv("processed_responses.csv")

# -----------------------
# Create Learning Labels
# -----------------------

def classify_learning(row):

    if row["answer_correct"] == 1 and row["confidence"] >= 4:
        return "conceptual"

    elif row["answer_correct"] == 0 and row["confidence"] >= 4:
        return "fake_understanding"

    elif row["answer_correct"] == 1 and row["confidence"] <= 2:
        return "guessing"

    else:
        return "memorized"

data["learning_type"] = data.apply(classify_learning, axis=1)

# -----------------------
# Features for Model
# -----------------------

features = [
    "confidence",
    "time_taken",
    "confidence_error",
    "speed_score",
    "fake_confidence",
    "guess_flag"
]

X = data[features]
y = data["learning_type"]

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

# Predictions

predictions = model.predict(X_test)

print("Model Evaluation:")
print(classification_report(y_test, predictions))


joblib.dump(model, "fake_understanding_model.pkl")

print("Model saved successfully!")
