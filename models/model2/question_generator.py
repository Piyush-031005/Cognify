import pandas as pd
import random

topics = {
    "Stack": [
        "LIFO principle",
        "push operation",
        "pop operation",
        "overflow",
        "underflow",
        "recursion usage",
        "expression evaluation",
        "undo operations"
    ],

    "Queue": [
        "FIFO principle",
        "enqueue operation",
        "dequeue operation",
        "circular queue",
        "priority queue",
        "BFS usage"
    ]
}

templates = [
    "Which concept is related to {}?",
    "{} is mainly associated with which structure?",
    "Which statement describes {}?",
    "{} is used in which situation?"
]

questions = []
qid = 1

for topic, concepts in topics.items():
    for concept in concepts:
        for i in range(20):

            question = random.choice(templates).format(concept)

            options = [
                "Stack",
                "Queue",
                "Tree",
                "Graph"
            ]

            answer = "A" if topic == "Stack" else "B"

            questions.append([
                qid,
                "DSA",
                topic,
                concept,
                "conceptual",
                "mcq",
                2,
                question,
                options[0],
                options[1],
                options[2],
                options[3],
                answer,
                8,
                concept
            ])

            qid += 1


df = pd.DataFrame(questions, columns=[
    "id","subject","topic","concept","type","format","difficulty",
    "question","optionA","optionB","optionC","optionD","answer",
    "expected_time","concept_group"
])

df.to_csv("generated_questions.csv", index=False)

print("Generated", len(df), "questions")
