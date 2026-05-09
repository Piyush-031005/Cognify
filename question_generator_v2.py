from database import get_conn
from datetime import datetime
import random

# =========================
# SMART VARIATION ENGINE
# =========================
def vary(prompt_list):
    return random.choice(prompt_list)

# =========================
# DIFFICULTY ENGINE (REAL)
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
# DUPLICATE CHECK (STRONG)
# =========================
def is_duplicate(cur, prompt):
    cur.execute("""
    SELECT id FROM question_bank
    WHERE LOWER(prompt) = ?
    """, (prompt.lower(),))
    return cur.fetchone() is not None

# =========================
# INSERT ENGINE
# =========================
def insert_questions(subject, topic, subtopic, qlist):
    conn = get_conn()
    cur = conn.cursor()

    inserted = 0

    for q in qlist:
        prompt = q["prompt"].strip().lower()

        if is_duplicate(cur, prompt):
            continue

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
            get_difficulty(q["type"]),
            q["type"],
            prompt,
            q["options"][0],
            q["options"][1],
            q["options"][2],
            q["options"][3],
            q["correct"],
            datetime.now().isoformat()
        ))

        inserted += 1

    conn.commit()
    conn.close()

    return inserted

# =========================
# AUTO EXPAND ENGINE 🔥
# =========================
def ensure_minimum(subject, topic, subtopic, generator, target=25):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*) as c FROM question_bank
    WHERE subject=? AND topic=? AND subtopic=?
    """, (subject, topic, subtopic))

    count = cur.fetchone()["c"]

    rounds = 0

    while count < target and rounds < 10:
        inserted = insert_questions(subject, topic, subtopic, generator())

        count += inserted
        rounds += 1

        if inserted == 0:
            break  # no new variation possible

    conn.close()

# =========================
# GENERATORS (UPGRADED)
# =========================

def cn_network_layer():
    return [
        {
            "type": "memory",
            "prompt": vary([
                "IP full form?",
                "What does IP stand for?",
                "IP abbreviation means?"
            ]),
            "options": ["Internet Protocol","Internal Process","Input Protocol","Internet Process"],
            "correct": 0
        },
        {
            "type": "conceptual",
            "prompt": vary([
                "Why IP is unreliable?",
                "Why IP is connectionless?",
                "Why IP does not guarantee delivery?"
            ]),
            "options": ["No acknowledgment","Too slow","Uses TCP","Encrypted"],
            "correct": 0
        },
        {
            "type": "tricky",
            "prompt": vary([
                "IP guarantees what?",
                "What does IP ensure?",
                "Which guarantee IP provides?"
            ]),
            "options": ["Delivery","Order","Nothing","Speed"],
            "correct": 2
        },
        {
            "type": "application",
            "prompt": vary([
                "If packet lost in IP?",
                "Packet drop in IP leads to?",
                "Lost packet in IP results in?"
            ]),
            "options": ["Retransmission","Drop","Reordering","Crash"],
            "correct": 1
        },
        {
            "type": "reasoning",
            "prompt": vary([
                "Why TCP needed over IP?",
                "Why IP needs TCP layer?",
                "Why IP alone insufficient?"
            ]),
            "options": ["Reliability","Speed","Security","Routing"],
            "correct": 0
        }
    ]

def dsa_arrays():
    return [
        {
            "type": "memory",
            "prompt": vary([
                "Array stores elements in?",
                "Where array elements stored?",
                "Memory layout of array?"
            ]),
            "options": ["Contiguous memory","Random memory","Heap scattered","Stack"],
            "correct": 0
        },
        {
            "type": "conceptual",
            "prompt": vary([
                "Why array access O(1)?",
                "Why indexing fast in array?",
                "How array gives constant access?"
            ]),
            "options": ["Direct indexing","Traversal","Hashing","Pointer chain"],
            "correct": 0
        },
        {
            "type": "tricky",
            "prompt": vary([
                "Worst case insertion in array?",
                "Insertion complexity array?",
                "Insert at beginning array cost?"
            ]),
            "options": ["O(n)","O(1)","O(log n)","O(n log n)"],
            "correct": 0
        },
        {
            "type": "application",
            "prompt": vary([
                "Where arrays better than linked list?",
                "Why array used over linked list?",
                "Real use of array advantage?"
            ]),
            "options": ["Cache efficiency","Dynamic insert","Flexibility","Pointers"],
            "correct": 0
        },
        {
            "type": "reasoning",
            "prompt": vary([
                "Why binary search needs sorted array?",
                "Why sorting required for binary search?",
                "Binary search works only when?"
            ]),
            "options": ["Divide search","Reduce memory","Speed","Avoid loops"],
            "correct": 0
        }
    ]

# =========================
# MASTER MAP
# =========================

GEN_MAP = {
    ("cn","network_layer","ip"): cn_network_layer,
    ("dsa","arrays","basics"): dsa_arrays,
}

# =========================
# RUN V5
# =========================

if __name__ == "__main__":
    for (subj, topic, subtopic), func in GEN_MAP.items():
        ensure_minimum(subj, topic, subtopic, func, target=25)

    print("🔥 V5 COMPLETE (AUTO EXPAND + NO REPEAT + SMART DIFFICULTY)")