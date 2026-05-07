from database import get_conn
from datetime import datetime
import random

# =========================
# CN GENERATOR
# =========================

def cn_error_detection():
    return [
        {
            "type": "conceptual",
            "prompt": "Why is CRC more reliable than parity check?",
            "options": [
                "It detects multiple bit errors",
                "It uses encryption",
                "It is faster",
                "It compresses data"
            ],
            "correct": 0
        },
        {
            "type": "tricky",
            "prompt": "Parity bit can detect?",
            "options": [
                "Only single bit errors",
                "All errors",
                "No errors",
                "Burst errors always"
            ],
            "correct": 0
        },
        {
            "type": "application",
            "prompt": "CRC is mainly used in?",
            "options": [
                "Data transmission",
                "CPU scheduling",
                "Memory allocation",
                "Encryption"
            ],
            "correct": 0
        },
        {
            "type": "memory",
            "prompt": "CRC stands for?",
            "options": [
                "Cyclic Redundancy Check",
                "Control Redundancy Code",
                "Coded Random Check",
                "Cyclic Random Code"
            ],
            "correct": 0
        },
        {
            "type": "reasoning",
            "prompt": "Why parity fails in even number of bit errors?",
            "options": [
                "Parity remains same",
                "Parity flips twice",
                "Parity resets",
                "Parity becomes random"
            ],
            "correct": 0
        }
    ]

# =========================
# DSA GENERATOR
# =========================

def dsa_arrays():
    return [
        {
            "type": "conceptual",
            "prompt": "Why is array access O(1)?",
            "options": [
                "Direct indexing",
                "Sequential access",
                "Pointer traversal",
                "Hashing"
            ],
            "correct": 0
        },
        {
            "type": "tricky",
            "prompt": "Worst case insertion in array?",
            "options": [
                "O(n)",
                "O(1)",
                "O(log n)",
                "O(n log n)"
            ],
            "correct": 0
        },
        {
            "type": "application",
            "prompt": "Where arrays are preferred over linked list?",
            "options": [
                "Cache efficiency",
                "Dynamic insertion",
                "Memory saving",
                "Tree traversal"
            ],
            "correct": 0
        },
        {
            "type": "memory",
            "prompt": "Array stores elements in?",
            "options": [
                "Contiguous memory",
                "Random memory",
                "Stack memory",
                "Heap scattered"
            ],
            "correct": 0
        },
        {
            "type": "reasoning",
            "prompt": "Why binary search needs sorted array?",
            "options": [
                "To divide search space",
                "To reduce memory",
                "To increase speed",
                "To avoid loops"
            ],
            "correct": 0
        }
    ]

# =========================
# MATH GENERATOR
# =========================

def math_quadratic():
    return [
        {
            "type": "memory",
            "prompt": "Discriminant formula?",
            "options": ["b²-4ac", "a²-4bc", "b²+4ac", "a²+b²"],
            "correct": 0
        },
        {
            "type": "conceptual",
            "prompt": "Discriminant decides?",
            "options": ["Nature of roots", "Sum of roots", "Product", "Graph"],
            "correct": 0
        },
        {
            "type": "tricky",
            "prompt": "If D < 0 roots are?",
            "options": ["Imaginary", "Equal", "Real", "Zero"],
            "correct": 0
        },
        {
            "type": "application",
            "prompt": "If roots equal then D?",
            "options": ["0", "1", "-1", "∞"],
            "correct": 0
        },
        {
            "type": "reasoning",
            "prompt": "Why quadratic has max 2 roots?",
            "options": ["Degree 2", "Two variables", "Graph linear", "No reason"],
            "correct": 0
        }
    ]

# =========================
# MASTER MAP
# =========================

GEN_MAP = {
    ("cn","data_link","error_detection"): cn_error_detection,
    ("dsa","arrays","basics"): dsa_arrays,
    ("math","algebra","quadratic"): math_quadratic
}

# =========================
# INSERT
# =========================

def insert_questions(subject, topic, subtopic, qlist):
    conn = get_conn()
    cur = conn.cursor()

    for q in qlist:
        cur.execute("""
            INSERT INTO question_bank (
                subject, topic, subtopic, difficulty, cognitive_type,
                prompt, option_a, option_b, option_c, option_d,
                correct_index, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            subject,
            topic,
            subtopic,
            random.choice(["easy","medium","hard"]),
            q["type"],
            q["prompt"],
            q["options"][0],
            q["options"][1],
            q["options"][2],
            q["options"][3],
            q["correct"],
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()

# =========================
# RUN
# =========================

def run():
    total = 0

    for (subject, topic, subtopic), func in GEN_MAP.items():
        qlist = func()

        insert_questions(subject, topic, subtopic, qlist)

        print(f"✔ {subject}/{topic}/{subtopic} → {len(qlist)}")
        total += len(qlist)

    print(f"\n🔥 TOTAL GENERATED: {total}")


if __name__ == "__main__":
    run()