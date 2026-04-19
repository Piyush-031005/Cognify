import pandas as pd
import time
import joblib

# load question bank
questions = pd.read_csv("final_question_bank.csv")

# load models
model = joblib.load("fake_understanding_model.pkl")
strategy_model = joblib.load("strategy_model.pkl")

# shuffle questions
questions = questions.sample(frac=1).reset_index(drop=True)

# number of questions per quiz
NUM_QUESTIONS = 10
questions = questions.head(NUM_QUESTIONS)

# topic score storage
topic_scores = {}

# 🔥 NEW: Failure tracking
error_tracking = {}

for index, q in questions.iterrows():

    print("\nQuestion:", q["question"])

    if q["format"] == "mcq":
        print("A:", q["optionA"])
        print("B:", q["optionB"])
        print("C:", q["optionC"])
        print("D:", q["optionD"])

    start = time.time()

    while True:
        answer = input("Your answer (A/B/C/D): ").strip().upper()

        if answer in ["A", "B", "C", "D"]:
            break
        else:
            print("Please enter a valid option: A, B, C, or D")

    end = time.time()

    # confidence input
    while True:
        try:
            confidence = int(input("Confidence (1-5): "))
            if 1 <= confidence <= 5:
                break
            else:
                print("Enter number between 1 and 5")
        except:
            print("Please enter a number")

    time_taken = round(end - start, 2)

    # correctness
    correct = 1 if answer == str(q["answer"]).upper() else 0

    # ----------------------
    # Feature Engineering
    # ----------------------

    confidence_error = confidence * (1 - correct)
    speed_score = q["expected_time"] / time_taken if time_taken > 0 else 0
    fake_confidence = 1 if (confidence >= 4 and correct == 0) else 0
    guess_flag = 1 if (confidence <= 2 and correct == 1) else 0

    features = pd.DataFrame([{
        "confidence": confidence,
        "time_taken": time_taken,
        "confidence_error": confidence_error,
        "speed_score": speed_score,
        "fake_confidence": fake_confidence,
        "guess_flag": guess_flag
    }])

    # ----------------------
    # Model Predictions
    # ----------------------

    learning = model.predict(features)[0]
    strategy = strategy_model.predict(features)[0]

    print("Learning behaviour:", learning)
    print("Strategy type:", strategy)

    # ----------------------
    # 🔥 Failure Loop Detection
    # ----------------------

    topic = q["topic"]

    if topic not in error_tracking:
        error_tracking[topic] = 0

    if correct == 0:
        error_tracking[topic] += 1
    else:
        error_tracking[topic] = 0

    if error_tracking[topic] >= 2:
        print("⚠️ Failure Loop Detected in topic:", topic)

    # ----------------------
    # Understanding Score
    # ----------------------

    score = 50

    if correct == 1:
        score += 20
    else:
        score -= 20

    if confidence >= 4 and correct == 1:
        score += 10

    if confidence >= 4 and correct == 0:
        score -= 15

    if confidence <= 2 and correct == 1:
        score -= 5

    score = max(0, min(score, 100))

    print("Understanding Score:", score)

    # ----------------------
    # Topic Tracking
    # ----------------------

    if topic not in topic_scores:
        topic_scores[topic] = []

    topic_scores[topic].append(score)

    # ----------------------
    # Save response
    # ----------------------

    response = {
        "user_id": "U1",
        "question_id": q["id"],
        "subject": q["subject"],
        "topic": q["topic"],
        "answer_correct": correct,
        "confidence": confidence,
        "time_taken": time_taken,
        "expected_time": q["expected_time"],
        "understanding_score": score,
        "learning_type": learning,
        "strategy_type": strategy
    }

    df = pd.DataFrame([response])
    df.to_csv("responses.csv", mode="a", header=False, index=False)

# ----------------------
# Final Cognitive Profile
# ----------------------

print("\n--- Cognitive Profile ---")

for topic, scores in topic_scores.items():
    avg_score = sum(scores) / len(scores)
    print(topic, "Understanding:", round(avg_score, 2))

print("\nQuiz Completed!")