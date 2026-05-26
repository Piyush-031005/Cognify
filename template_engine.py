import random

# =========================
# TEMPLATE ENGINE
# =========================

TEMPLATES = {

    "memory": [

        "What is {}?",
        "Define {}.",
        "{} refers to?",
        "Which statement best defines {}?",
        "Identify the correct statement about {}."

    ],

    "conceptual": [

        "Why is {} important?",
        "What is the purpose of {}?",
        "Why do we use {}?",
        "What makes {} significant?",
        "Why is {} necessary?"

    ],

    "tricky": [

        "Which option is incorrect about {}?",
        "Identify the false statement regarding {}.",
        "What is NOT true about {}?",
        "Which statement is logically wrong about {}?",
        "Select the incorrect explanation of {}."

    ],

    "application": [

        "Where is {} applied?",
        "In which real scenario is {} used?",
        "How is {} used in real systems?",
        "Where would you use {}?",
        "{} is most useful in which situation?"

    ],

    "reasoning": [

        "What problem does {} solve?",
        "Why was {} introduced?",
        "What issue does {} address?",
        "How does {} improve system behavior?",
        "Why is {} needed in practical systems?"

    ]
}


# =========================
# GENERATE PROMPT
# =========================

def generate_prompt(concept, cognitive_type):

    template = random.choice(
        TEMPLATES[cognitive_type]
    )

    return template.format(concept)