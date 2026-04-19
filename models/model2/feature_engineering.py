import pandas as pd

# load responses
data = pd.read_csv("synthetic_responses.csv")

# -------- Feature 1: Confidence Error --------
# high confidence but wrong answer
data["confidence_error"] = data["confidence"] * (1 - data["answer_correct"])

# -------- Feature 2: Speed Score --------
# faster answers may indicate guessing
avg_time = data["time_taken"].mean()

data["speed_score"] = avg_time / data["time_taken"]

# -------- Feature 3: Fake Confidence Flag --------
data["fake_confidence"] = ((data["confidence"] >= 4) & (data["answer_correct"] == 0)).astype(int)

# -------- Feature 4: Guessing Flag --------
data["guess_flag"] = ((data["confidence"] <= 2) & (data["answer_correct"] == 1)).astype(int)

# save new dataset
data.to_csv("processed_responses.csv", index=False)

print("Feature engineering complete!")
print(data.head())
