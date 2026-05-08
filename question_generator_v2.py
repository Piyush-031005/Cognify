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




def cn_network_layer():
    return [
        {"type":"memory","prompt":"IP works on which layer?","options":["Network","Transport","Data link","Application"],"correct":0},
        {"type":"conceptual","prompt":"Why IP is connectionless?","options":["No session tracking","Uses TCP","Encrypts data","Stores packets"],"correct":0},
        {"type":"tricky","prompt":"IP guarantees?","options":["None","Delivery","Order","Reliability"],"correct":0},
        {"type":"application","prompt":"Which device uses IP?","options":["Router","Switch","Hub","Bridge"],"correct":0},
        {"type":"reasoning","prompt":"Why packet loss occurs in IP?","options":["No reliability","Encryption","Compression","Caching"],"correct":0}
    ]

def dsa_stack():
    return [
        {"type":"memory","prompt":"Stack follows?","options":["LIFO","FIFO","Random","Priority"],"correct":0},
        {"type":"conceptual","prompt":"Why stack used in recursion?","options":["Function calls","Sorting","Searching","Traversal"],"correct":0},
        {"type":"tricky","prompt":"Overflow occurs when?","options":["Stack full","Stack empty","Queue full","Memory free"],"correct":0},
        {"type":"application","prompt":"Stack used in?","options":["Undo operation","Database","Networking","Routing"],"correct":0},
        {"type":"reasoning","prompt":"Why stack is fast?","options":["Top access O(1)","Sorted data","Dynamic size","Tree based"],"correct":0}
    ]

def dsa_queue():
    return [
        {"type":"memory","prompt":"Queue follows?","options":["FIFO","LIFO","Random","Stack"],"correct":0},
        {"type":"conceptual","prompt":"Queue used in?","options":["Scheduling","Sorting","Recursion","Stack"],"correct":0},
        {"type":"tricky","prompt":"Deque allows?","options":["Both ends","Front only","Rear only","None"],"correct":0},
        {"type":"application","prompt":"Queue used in BFS?","options":["Yes","No","Sometimes","Never"],"correct":0},
        {"type":"reasoning","prompt":"Why queue for scheduling?","options":["Fairness","Speed","Memory","Sorting"],"correct":0}
    ]

def dbms_sql():
    return [
        {"type":"memory","prompt":"SELECT used for?","options":["Fetch data","Insert","Delete","Update"],"correct":0},
        {"type":"conceptual","prompt":"Primary key ensures?","options":["Uniqueness","Sorting","Deletion","Indexing"],"correct":0},
        {"type":"tricky","prompt":"NULL means?","options":["Unknown","Zero","Empty","False"],"correct":0},
        {"type":"application","prompt":"JOIN used for?","options":["Combine tables","Delete","Insert","Sort"],"correct":0},
        {"type":"reasoning","prompt":"Why indexing used?","options":["Faster search","Security","Deletion","Backup"],"correct":0}
    ]

def os_scheduling():
    return [
        {"type":"memory","prompt":"FCFS stands for?","options":["First Come First Serve","Fast CPU First Serve","First CPU First Serve","None"],"correct":0},
        {"type":"conceptual","prompt":"Scheduling improves?","options":["CPU utilization","Memory","Disk","Network"],"correct":0},
        {"type":"tricky","prompt":"Starvation occurs in?","options":["Priority scheduling","FCFS","Round robin","FIFO"],"correct":0},
        {"type":"application","prompt":"Round robin uses?","options":["Time slice","Priority","Stack","Queue"],"correct":0},
        {"type":"reasoning","prompt":"Why scheduling needed?","options":["Efficiency","Security","Storage","Compression"],"correct":0}
    ]

def logical_reasoning():
    return [
        {"type":"memory","prompt":"Series follows pattern of?","options":["Logic","Memory","Data","Code"],"correct":0},
        {"type":"conceptual","prompt":"Syllogism checks?","options":["Logical validity","Memory","Speed","Data"],"correct":0},
        {"type":"tricky","prompt":"All A are B, some B are C → ?","options":["Uncertain","True","False","Always true"],"correct":0},
        {"type":"application","prompt":"Coding decoding used in?","options":["Pattern recognition","Sorting","Searching","Memory"],"correct":0},
        {"type":"reasoning","prompt":"Why reasoning tests matter?","options":["Thinking ability","Memory","Speed","Typing"],"correct":0}
    ]


# =========================
# MASTER MAP
# =========================

GEN_MAP = {
    ("cn","data_link","error_detection"): cn_error_detection,
    ("cn","network_layer","ip"): cn_network_layer,

    ("dsa","arrays","basics"): dsa_arrays,
    ("dsa","stack","basics"): dsa_stack,
    ("dsa","queue","basics"): dsa_queue,

    ("dbms","sql","queries"): dbms_sql,
    ("os","scheduling","process"): os_scheduling,

    ("math","algebra","quadratic"): math_quadratic,

    ("logic","reasoning","basic"): logical_reasoning
}

# =========================
# INSERT
# =========================

def insert_questions(subject, topic, subtopic, qlist):
    conn = get_conn()
    cur = conn.cursor()

    for q in qlist:

        # 🔍 duplicate check
        cur.execute("""
        SELECT id FROM question_bank
        WHERE subject=? AND topic=? AND subtopic=? AND prompt=?
        """, (subject, topic, subtopic, q["prompt"]))

        if cur.fetchone():
            continue

        # ✅ insert
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
            {
                "memory": "easy",
                "conceptual": "medium",
                "tricky": "medium",
                "application": "hard",
                "reasoning": "hard"
            }[q["type"]],
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



