import pandas as pd
import random

subjects = {
    "DSA": ["Stack", "Queue", "Tree", "Graph"],
    "AI": ["Machine Learning", "Neural Networks"],
    "DAA": ["Dynamic Programming", "Greedy"],
    "Fullstack": ["React", "Database"]
}

types = ["basic", "conceptual", "application", "tricky"]

data = []

for subject, topics in subjects.items():
    for topic in topics:
        for q_type in types:
            for i in range(3):   # 3 questions per type

                question = f"{topic} {q_type} question {i+1}"

                options = ["Option A", "Option B", "Option C", "Option D"]
                answer = random.choice(["A", "B", "C", "D"])

                data.append([
                    subject, topic, q_type,
                    question,
                    options[0], options[1], options[2], options[3],
                    answer
                ])

df = pd.DataFrame(data, columns=[
    "subject","topic","type","question","A","B","C","D","answer"
])

df.to_csv("questions_big.csv", index=False)

print("🔥 Big dataset created!")