from database import get_conn
from datetime import datetime
import random
import hashlib

# =========================
# UNIQUE CHECK (SMART)
# =========================
def is_similar(p1, p2):
    p1 = p1.lower().strip()
    p2 = p2.lower().strip()

    # allow variation — only reject if almost identical
    return p1 == p2


def already_exists(cur, prompt):
    cur.execute("SELECT prompt FROM question_bank")
    rows = cur.fetchall()

    for r in rows:
        if is_similar(prompt, r["prompt"]):
            return True
    return False


# =========================
# DIFFICULTY ENGINE
# =========================
def get_difficulty(qtype):
    return {
        "memory": "easy",
        "conceptual": "medium",
        "tricky": "medium",
        "application": "hard",
        "reasoning": "hard"
    }[qtype]


# =========================
# AI GENERATOR CORE
# =========================
def generate_question(subtopic):
    
    base_templates = [
    ("memory", f"What is {subtopic}?"),
    ("memory", f"{subtopic} refers to?"),

    ("conceptual", f"Which statement best describes {subtopic}?"),
    ("conceptual", f"Why is {subtopic} important?"),

    ("tricky", f"Which of the following is NOT true about {subtopic}?"),
    ("tricky", f"What is a common misconception about {subtopic}?"),

    ("application", f"Where is {subtopic} used in real-world systems?"),
    ("application", f"In which scenario is {subtopic} applied?"),

    ("reasoning", f"Why is {subtopic} preferred over alternatives?"),
    ("reasoning", f"What problem does {subtopic} solve?")
]

    qtype, prompt = random.choice(base_templates)

    return {
        "type": qtype,
        "prompt": prompt,
        "options": [
            "Option A",
            "Option B",
            "Option C",
            "Option D"
        ],
        "correct": 0
    }


# =========================
# INSERT ENGINE
# =========================
def insert_question(cur, subject, topic, subtopic, q):

    if already_exists(cur, q["prompt"]):
        return False

    cur.execute("""
    INSERT INTO question_bank (
        subject, topic, subtopic,
        difficulty, cognitive_type,
        prompt,
        option_a, option_b, option_c, option_d,
        correct_index, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        subject,
        topic,
        subtopic,
        get_difficulty(q["type"]),
        q["type"],
        q["prompt"],
        q["options"][0],
        q["options"][1],
        q["options"][2],
        q["options"][3],
        q["correct"],
        datetime.now().isoformat()
    ))

    return True


# =========================
# AUTO EXPAND ENGINE
# =========================
def expand_dataset():

    conn = get_conn()
    cur = conn.cursor()

    TARGET = 20

    cur.execute("""
    SELECT DISTINCT subject, topic, subtopic FROM question_bank
    """)
    combos = cur.fetchall()

    total_added = 0

    for c in combos:

        subject = c["subject"]
        topic = c["topic"]
        subtopic = c["subtopic"]

        cur.execute("""
        SELECT COUNT(*) as cnt FROM question_bank
        WHERE subject=? AND topic=? AND subtopic=?
        """, (subject, topic, subtopic))

        current = cur.fetchone()["cnt"]

        for _ in range(25):  # force generate

            q = generate_question(subtopic)

            if insert_question(cur, subject, topic, subtopic, q):
                current += 1
                total_added += 1

    conn.commit()
    conn.close()

    print(f"🔥 V6.5 COMPLETE → {total_added} new questions added")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    print("🚀 V6.5 AI GENERATION STARTED...")
    expand_dataset()