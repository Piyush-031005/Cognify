from pynput import keyboard
import time
from realtime.session_manager import SessionManager
import pandas as pd
import os
import joblib

# Start session
session = SessionManager(question_id="Q_LIVE_1")
tracker = session.tracker

print("\n--- REAL KEYBOARD TRACKING STARTED ---")
print("Type something... Press ESC to stop.\n")

# Keyboard press handler
def on_press(key):
    try:
        tracker.key_press(str(key.char))
    except AttributeError:
        if key == keyboard.Key.backspace:
            tracker.key_press("BACKSPACE")

# Stop on ESC
def on_release(key):
    if key == keyboard.Key.esc:
        return False

# Start listening
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

# Get features
features = session.get_features()

# ----------------------
# LOAD ML MODEL
# ----------------------
ml_model = joblib.load("model/cognitive_model.pkl")

# ----------------------
# PREPARE INPUT
# ----------------------
input_data = pd.DataFrame([{
    "time_taken": features["time_taken"],
    "idle_time": features["idle_time"],
    "rewrite_count": features["rewrite_count"],
    "backspace_count": features["backspace_count"],
    "skipped": features["skipped"],
    "hesitation_score": (
        features["idle_time"] / max(features["time_taken"], 1)
    )
}])

# ----------------------
# PREDICTION
# ----------------------
prediction = ml_model.predict(input_data)[0]

print("\n🧠 ML Prediction:")
print("Behavior Type:", prediction)

# ----------------------
# PRINT INPUT
# ----------------------
print("\n--- INPUT DATA ---")
for k, v in features.items():
    print(f"{k}: {v}")

# ----------------------
# SAVE DATASET
# ----------------------
data = {
    **features,
    "behavior_type": prediction
}

df = pd.DataFrame([data])

file_exists = os.path.isfile("cognitive_dataset.csv")

df.to_csv(
    "cognitive_dataset.csv",
    mode="a",
    header=not file_exists,
    index=False
)

print("\nData saved for ML training!")