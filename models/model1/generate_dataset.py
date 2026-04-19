import pandas as pd
import random

data = []

for _ in range(3000):
    response_time = random.uniform(1, 20)
    attempts = random.randint(1, 3)
    confidence = random.uniform(0, 1)
    is_application = random.randint(0, 1)
    correct = random.randint(0, 1)

    if correct == 1 and response_time < 5 and is_application == 1:
        label = 1
    elif correct == 1 and response_time > 12:
        label = 0
    elif correct == 0 and confidence > 0.8:
        label = 2
    elif correct == 0 and attempts > 2:
        label = 2
    else:
        label = random.choice([0, 1])

    data.append([
        response_time,
        attempts,
        confidence,
        is_application,
        correct,
        label
    ])

df = pd.DataFrame(data, columns=[
    "response_time",
    "attempts",
    "confidence",
    "is_application",
    "correct",
    "label"
])

df.to_csv("model1_dataset.csv", index=False)

print("Fresh dataset created!")