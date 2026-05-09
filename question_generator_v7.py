from database import get_conn
from datetime import datetime
import random

# =========================
# MASTER CONCEPT MAP
# =========================

MASTER_MAP = {
    ("dsa","arrays","basics"): [
        "indexing",
        "memory layout",
        "time complexity",
        "insertion",
        "searching"
    ],

    ("cn","network_layer","ip"): [
        "addressing",
        "packet delivery",
        "connectionless nature",
        "routing",
        "packet loss"
    ],

    ("math","algebra","quadratic"): [
        "discriminant",
        "nature of roots",
        "graph behavior",
        "root formulas",
        "applications"
    ]
}

# =========================
# QUESTION ENGINE
# =========================

def generate_by_concept(concept):

    return [
        {
            "type":"memory",
            "prompt": f"What is {concept}?",
            "options":["Definition A","Definition B","Definition C","Definition D"],
            "correct":0
        },
        {
            "type":"conceptual",
            "prompt": f"Why is {concept} important?",
            "options":["Reason A","Reason B","Reason C","Reason D"],
            "correct":0
        },
        {
            "type":"tricky",
            "prompt": f"Which statement is FALSE about {concept}?",
            "options":["False A","False B","False C","False D"],
            "correct":0
        },
        {
            "type":"application",
            "prompt": f"Where is {concept} used in real scenarios?",
            "options":["Use A","Use B","Use C","Use D"],
            "correct":0
        },
        {
            "type":"reasoning",
            "prompt": f"What problem does {concept} solve?",
            "options":["Solve A","Solve B","Solve C","Solve D"],
            "correct":0
        }
    ]

# =========================
# DIFFICULTY MAP
# =========================

def get_difficulty(qtype):
    return {
        "memory":"easy",
        "conceptual":"medium",
        "tricky":"medium",
        "application":"hard",
        "reasoning":"hard"
    }[qtype]

# =========================
# INSERT ENGINE
# =========================

def insert_question(cur, subject, topic, subtopic, q):

    cur.execute("""
    SELECT id FROM question_bank WHERE prompt=?
    """, (q["prompt"],))

    if cur.fetchone():
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
# MAIN ENGINE
# =========================

def run_engine():

    conn = get_conn()
    cur = conn.cursor()

    total = 0

    for (subject, topic, subtopic), concepts in MASTER_MAP.items():

        for concept in concepts:

            qlist = generate_by_concept(concept)

            for q in qlist:

                if insert_question(cur, subject, topic, subtopic, q):
                    total += 1

    conn.commit()
    conn.close()

    print(f"🔥 V7 GENERATED → {total} questions")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    print("🚀 V7 MASTER ENGINE RUNNING...")
    run_engine()