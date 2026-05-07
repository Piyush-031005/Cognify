from database import get_conn
from datetime import datetime
import random

# =========================
# CONFIG
# =========================

COGNITIVE_TYPES = ["memory", "conceptual", "tricky", "application", "reasoning"]

# =========================
# TEMPLATE ENGINE
# =========================

def generate_memory(subtopic):
    return {
        "prompt": f"What is the basic definition of {subtopic}?",
        "options": ["Correct concept", "Wrong concept 1", "Wrong concept 2", "Wrong concept 3"],
        "correct": 0
    }

def generate_conceptual(subtopic):
    return {
        "prompt": f"Which statement best explains {subtopic}?",
        "options": ["Correct explanation", "Misconception", "Partial truth", "Irrelevant"],
        "correct": 0
    }

def generate_tricky(subtopic):
    return {
        "prompt": f"Which of the following is FALSE about {subtopic}?",
        "options": ["Trap option", "Correct statement", "Correct statement", "Correct statement"],
        "correct": 0
    }

def generate_application(subtopic):
    return {
        "prompt": f"Where would {subtopic} be used in real systems?",
        "options": ["Correct scenario", "Wrong scenario", "Wrong scenario", "Wrong scenario"],
        "correct": 0
    }

def generate_reasoning(subtopic):
    return {
        "prompt": f"Why is {subtopic} preferred over alternatives?",
        "options": ["Correct reasoning", "Wrong reasoning", "Random logic", "Incorrect assumption"],
        "correct": 0
    }

GENERATOR_MAP = {
    "memory": generate_memory,
    "conceptual": generate_conceptual,
    "tricky": generate_tricky,
    "application": generate_application,
    "reasoning": generate_reasoning
}

# =========================
# MAIN GENERATOR
# =========================

def generate_questions(subject, topic, subtopic, count_per_type=2):
    questions = []

    for qtype in COGNITIVE_TYPES:
        for _ in range(count_per_type):
            q = GENERATOR_MAP[qtype](subtopic)

            questions.append({
                "subject": subject,
                "topic": topic,
                "subtopic": subtopic,
                "difficulty": random.choice(["easy", "medium", "hard"]),
                "cognitive_type": qtype,
                "prompt": q["prompt"],
                "options": q["options"],
                "correct_index": q["correct"],
                "created_at": datetime.now().isoformat()
            })

    return questions

# =========================
# DB INSERT
# =========================

def insert_questions(questions):
    conn = get_conn()
    cur = conn.cursor()

    for q in questions:
        cur.execute("""
            INSERT INTO question_bank (
                subject, topic, subtopic, difficulty, cognitive_type,
                prompt, option_a, option_b, option_c, option_d,
                correct_index, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q["subject"],
            q["topic"],
            q["subtopic"],
            q["difficulty"],
            q["cognitive_type"],
            q["prompt"],
            q["options"][0],
            q["options"][1],
            q["options"][2],
            q["options"][3],
            q["correct_index"],
            q["created_at"]
        ))

    conn.commit()
    conn.close()

# =========================
# MASTER CONTROL
# =========================

def run_generation():
    MASTER_MAP = [
        ("cn", "data_link", "error_detection"),
        ("cn", "network_layer", "ip"),
        ("dsa", "arrays", "basics"),
        ("math", "algebra", "quadratic"),
    ]

    total = 0

    for subject, topic, subtopic in MASTER_MAP:
        qs = generate_questions(subject, topic, subtopic, count_per_type=2)
        insert_questions(qs)

        print(f"Generated {len(qs)} questions for {subject}/{topic}/{subtopic}")
        total += len(qs)

    print(f"\n🔥 TOTAL GENERATED: {total} questions")


# =========================
# RUN
# =========================

if __name__ == "__main__":
    run_generation()