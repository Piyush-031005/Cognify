from database import get_conn
from datetime import datetime
import random

# =========================
# MASTER MAP (EXPANDED)
# =========================

MASTER_MAP = {
    ("dsa","arrays","basics"): [
        "array indexing",
        "array memory allocation",
        "array insertion complexity",
        "searching in arrays",
        "time complexity of arrays"
    ],

    ("cn","network_layer","ip"): [
        "IP addressing",
        "packet delivery in IP",
        "connectionless communication in IP",
        "routing in network layer",
        "packet loss in networking"
    ],

    ("math","algebra","quadratic"): [
        "discriminant of quadratic equation",
        "roots of quadratic equation",
        "nature of roots in quadratic equation",
        "quadratic formula",
        "graph of quadratic equation"
    ]
}

# =========================
# OPTION BANK (REAL)
# =========================

OPTION_BANK = {
    "indexing": ["Direct access", "Sequential access", "Hash lookup", "Binary traversal"],
    "memory": ["Contiguous memory", "Random memory", "Fragmented blocks", "Stack memory"],
    "insertion": ["O(n)", "O(1)", "O(log n)", "O(n log n)"],
    "searching": ["Linear search", "Binary search", "DFS", "BFS"],
    "complexity": ["O(1)", "O(n)", "O(log n)", "O(n²)"],

    "ip addressing": ["Logical addressing", "Physical addressing", "Port addressing", "MAC addressing"],
    "packet delivery": ["Best effort", "Guaranteed", "Encrypted", "Compressed"],
    "connectionless": ["No handshake", "Handshake required", "Secure channel", "Session based"],
    "routing": ["Path selection", "Encryption", "Compression", "Storage"],
    "packet loss": ["Drop", "Retry", "Cache", "Encrypt"],

    "discriminant": ["b²-4ac", "a²-4bc", "b²+4ac", "a²+b²"],
    "roots": ["Solutions of equation", "Graph points", "Derivatives", "Limits"],
    "nature": ["Real/imaginary", "Positive/negative", "Increasing/decreasing", "Stable/unstable"],
    "formula": ["(-b±√D)/2a", "(b±√D)/2a", "(-b±D)/2a", "(b±D)/2a"],
    "graph": ["Parabola", "Line", "Circle", "Hyperbola"]
}

# =========================
# QUESTION ENGINE
# =========================

def generate_question(concept):

    base_options = OPTION_BANK.get(concept, ["A","B","C","D"])
    correct_answer = base_options[0]

    options = base_options.copy()
    random.shuffle(options)

    correct_index = options.index(correct_answer)

    # tricky ke liye wrong index
    wrong_index = random.choice([i for i in range(4) if i != correct_index])

    return [
        {
            "type":"memory",
            "prompt": random.choice([
                f"What is {concept}?",
                f"Which statement best defines {concept}?",
                f"{concept} refers to?",
                f"Identify correct statement about {concept}"
            ]),
            "options": options,
            "correct": correct_index
        },

        {
            "type":"conceptual",
            "prompt": random.choice([
                f"Why is {concept} important?",
                f"What is the purpose of {concept}?",
                f"Why do we use {concept}?",
                f"What makes {concept} important?"
            ]),
            "options": options,
            "correct": correct_index
        },

        {
            "type":"tricky",
            "prompt": random.choice([
                f"Which option is incorrect about {concept}?",
                f"Which statement is false regarding {concept}?",
                f"Identify the wrong statement about {concept}",
                f"What is NOT true about {concept}?"
            ]),
            "options": options,
            "correct": wrong_index
        },

        {
            "type":"application",
            "prompt": random.choice([
                f"Where is {concept} applied?",
                f"In which scenario is {concept} used?",
                f"Where would you use {concept}?",
                f"{concept} is used in which situation?"
            ]),
            "options": options,
            "correct": correct_index
        },

        {
            "type":"reasoning",
            "prompt": random.choice([
                f"What problem does {concept} solve?",
                f"Why is {concept} needed?",
                f"What issue does {concept} address?",
                f"Why was {concept} introduced?"
            ]),
            "options": options,
            "correct": correct_index
        }
    ]

# =========================
# DIFFICULTY
# =========================

def get_diff(t):
    return {
        "memory":"easy",
        "conceptual":"medium",
        "tricky":"medium",
        "application":"hard",
        "reasoning":"hard"
    }[t]

# =========================
# INSERT
# =========================

def insert(cur, s, t, st, q):

    cur.execute("""
    SELECT id FROM question_bank
    WHERE prompt=?
    AND option_a=?
    AND option_b=?
    AND option_c=?
    AND option_d=?
    """, (
        q["prompt"],
        q["options"][0],
        q["options"][1],
        q["options"][2],
        q["options"][3]
    ))

    # duplicate found
    if cur.fetchone():
        return False

    # insert new question
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
        s, t, st,
        get_diff(q["type"]),
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
# ENGINE
# =========================

def run():
    conn = get_conn()
    cur = conn.cursor()

    total = 0

    for (s,t,st), concepts in MASTER_MAP.items():

        for concept in concepts:

            for _ in range(10):  # 🔥 variants

                qlist = generate_question(concept)

                for q in qlist:
                    if insert(cur, s, t, st, q):
                        total += 1

    conn.commit()
    conn.close()

    print(f"🔥 V8 GENERATED → {total} questions")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    print("🚀 V8 RUNNING...")
    run()