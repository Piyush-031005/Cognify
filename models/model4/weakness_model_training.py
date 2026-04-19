import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# ---------------------------
# LOAD DATA
# ---------------------------
df = pd.read_csv("balanced_dataset.csv")
print("📊 Dataset Shape:", df.shape)

# ---------------------------
# FEATURES & LABEL
# ---------------------------
X = df[["application_acc","basic_acc","conceptual_acc","tricky_acc"]]
y = df["weak_area"]

# ---------------------------
# ADD NOISE (REALISTIC 🔥)
# ---------------------------
X = X + np.random.normal(0, 0.02, X.shape)

# ---------------------------
# TRAIN TEST SPLIT
# ---------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# ---------------------------
# MODEL
# ---------------------------
model = RandomForestClassifier(max_depth=3)
model.fit(X_train, y_train)

# ---------------------------
# EVALUATION
# ---------------------------
accuracy = model.score(X_test, y_test)
print("\n🎯 Test Accuracy:", accuracy)

# ---------------------------
# SAVE MODEL
# ---------------------------
joblib.dump(model, "weakness_model.pkl")

print("\n🔥 Model trained and saved successfully!")