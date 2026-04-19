# generate_model5_dataset.py

import pandas as pd
import random

data = []

for _ in range(2000):
    conceptual = random.uniform(0, 1)
    memorized = random.uniform(0, 1)
    fake = random.uniform(0, 1)

    hesitant = random.uniform(0, 1)
    confident = random.uniform(0, 1)

    # normalize
    total1 = conceptual + memorized + fake
    conceptual /= total1
    memorized /= total1
    fake /= total1

    total2 = hesitant + confident
    hesitant /= total2
    confident /= total2

    # label logic
    if conceptual > 0.6 and confident > 0.6:
        outcome = "Improve"
    elif fake > 0.4 or hesitant > 0.6:
        outcome = "Decline"
    else:
        outcome = "Stagnant"

    data.append([conceptual, memorized, fake, hesitant, confident, outcome])

df = pd.DataFrame(data, columns=[
    "conceptual", "memorized", "fake",
    "hesitant", "confident", "outcome"
])

df.to_csv("model5_dataset.csv", index=False)

print("Dataset ready!")