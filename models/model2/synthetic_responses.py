import pandas as pd
import random

# load question bank
questions = pd.read_csv("final_question_bank.csv")

responses = []

num_students = 200
questions_per_student = 10

for student in range(1, num_students + 1):

    sample_questions = questions.sample(questions_per_student)

    for _, q in sample_questions.iterrows():

        correct = random.choice([0, 1])

        confidence = random.randint(1, 5)

        time_taken = random.randint(3, 15)

        responses.append({
            "user_id": f"S{student}",
            "question_id": q["id"],
            "subject": q["subject"],
            "topic": q["topic"],
            "answer_correct": correct,
            "confidence": confidence,
            "time_taken": time_taken,
            "expected_time": q["expected_time"]
        })

df = pd.DataFrame(responses)

df.to_csv("synthetic_responses.csv", index=False)

print("Generated responses:", len(df))
