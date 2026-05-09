from database import get_conn
from datetime import datetime
import random

# =========================
# MASTER MAP (EXPANDED)
# =========================

MASTER_MAP = {
    ("dsa","arrays","basics"): [
        "indexing",
        "memory",
        "insertion",
        "searching",
        "complexity"
    ],

    ("cn","network_layer","ip"): [
        "ip addressing",
        "packet delivery",
        "connectionless",
        "routing",
        "packet loss"
    ],

    ("math","algebra","quadratic"): [
        "discriminant",
        "roots",
        "nature",
        "formula",
        "graph"
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

    options = OPTION_BANK.get(concept, ["A","B","C","D"])
    random.shuffle(options)

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
            "correct": 0
        },
        {
            "type":"conceptual",
            "prompt": random.choice([
                f"Why is {concept} important?",
                f"Explain the significance of {concept}.",
                f"What makes {concept} unique?",
                f"How does {concept} impact related concepts?"
            ]),
            "options": options,
            "correct": 0
        },
        {
            "type":"tricky",
            "prompt": random.choice([
                f"Which option is incorrect about {concept}?",
                f"Identify the false statement regarding {concept}.",
                f"Select the incorrect description of {concept}.",
                f"Which of the following is NOT true about {concept}?"
            ]),
            "options": options,
            "correct": 1
        },
        {
            "type":"application",
            "prompt": random.choice([
                f"Where is {concept} applied?",
                f"In what scenarios is {concept} used?",
                f"Give an example of {concept} in action.",
                f"How is {concept} utilized in real-world applications?"
            ]),
            "options": options,
            "correct": 0
        },
        {
            "type":"reasoning",
            "prompt": random.choice([
                f"What problem does {concept} solve?",
                f"How would you approach solving a problem related to {concept}?",
                f"Explain the logical steps to address {concept}.",
                f"Provide a reasoned argument about {concept}."
            ]),
            "options": options,
            "correct": 0
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
    cur.execute("SELECT id FROM question_bank WHERE prompt=?", (q["prompt"],))
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

            for _ in range(5):  # 🔥 variants

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