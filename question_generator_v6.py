from database import get_conn
from datetime import datetime
import random

# =========================
# WORD BANKS (AI STYLE)
# =========================

objects = ["array", "stack", "queue"]
properties = ["access", "insertion", "deletion"]
complexities = ["O(1)", "O(n)", "O(log n)"]

ip_terms = ["packet", "routing", "delivery", "transmission"]

# =========================
# PROMPT GENERATOR ENGINE
# =========================

def generate_prompt(template, variables):
    return template.format(**variables)

# =========================
# TEMPLATES (POWER SOURCE)
# =========================

ARRAY_TEMPLATES = [
    ("memory", "What is the time complexity of {property} in {object}?"),
    ("conceptual", "Why is {object} {property} efficient?"),
    ("tricky", "Which operation in {object} is NOT {complexity}?"),
    ("application", "In real systems, where is {object} used for {property}?"),
    ("reasoning", "Why does {object} perform {property} in {complexity}?")
]

IP_TEMPLATES = [
    ("memory", "IP is responsible for {term}?"),
    ("conceptual", "Why does IP not guarantee {term}?"),
    ("tricky", "Which of these is NOT handled by IP: {term}?"),
    ("application", "If {term} fails in IP, what happens?"),
    ("reasoning", "Why is IP considered unreliable for {term}?")
]

# =========================
# OPTION GENERATOR
# =========================

def generate_options(correct):
    options = [correct]

    distractors = [
        "Faster execution",
        "Memory optimization",
        "Security enhancement",
        "Random behavior"
    ]

    while len(options) < 4:
        d = random.choice(distractors)
        if d not in options:
            options.append(d)

    random.shuffle(options)
    return options, options.index(correct)

# =========================
# DUPLICATE CHECK
# =========================

def exists(cur, prompt):
    cur.execute("SELECT id FROM question_bank WHERE prompt=?", (prompt,))
    return cur.fetchone() is not None

# =========================
# INSERT ENGINE
# =========================

def insert(subject, topic, subtopic, qtype, prompt, options, correct_index):
    conn = get_conn()
    cur = conn.cursor()

    if exists(cur, prompt):
        conn.close()
        return 0

    difficulty_map = {
        "memory": "easy",
        "conceptual": "medium",
        "tricky": "medium",
        "application": "hard",
        "reasoning": "hard"
    }

    cur.execute("""
    INSERT INTO question_bank (
        subject, topic, subtopic, difficulty, cognitive_type,
        prompt, option_a, option_b, option_c, option_d,
        correct_index, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        subject, topic, subtopic,
        difficulty_map[qtype],
        qtype,
        prompt,
        options[0], options[1], options[2], options[3],
        correct_index,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    return 1

# =========================
# GENERATE BULK QUESTIONS
# =========================

def generate_array_questions(n=50):
    total = 0

    for _ in range(n):
        template_type, template = random.choice(ARRAY_TEMPLATES)

        vars = {
            "object": random.choice(objects),
            "property": random.choice(properties),
            "complexity": random.choice(complexities)
        }

        prompt = generate_prompt(template, vars)

        correct = "Direct indexing" if template_type == "conceptual" else random.choice(complexities)

        options, idx = generate_options(correct)

        total += insert("dsa", "arrays", "basics", template_type, prompt, options, idx)

    return total

def generate_ip_questions(n=50):
    total = 0

    for _ in range(n):
        template_type, template = random.choice(IP_TEMPLATES)

        vars = {
            "term": random.choice(ip_terms)
        }

        prompt = generate_prompt(template, vars)

        correct = "No guarantee"

        options, idx = generate_options(correct)

        total += insert("cn", "network_layer", "ip", template_type, prompt, options, idx)

    return total

# =========================
# MAIN RUN
# =========================

if __name__ == "__main__":
    print("🚀 GENERATING AI-LEVEL QUESTIONS...")

    total = 0
    total += generate_array_questions(80)
    total += generate_ip_questions(80)

    print(f"🔥 DONE: {total} questions inserted")