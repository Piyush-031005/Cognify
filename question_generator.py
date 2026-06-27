from database import get_conn
from datetime import datetime
import random
from semantic_engine import (
    generate_semantic_id,
    generate_variant_id
)

# ==========================================
# MASTER MAP (EXPANDED TO ALL 6 PILOT DOMAINS)
# ==========================================

MASTER_MAP = {
    ("dsa", "arrays", "array_operations"): [
        "array indexing",
        "contiguous memory layout",
        "insertion complexity",
        "searching algorithms",
        "array deletion"
    ],
    ("math", "quadratic_equations", "roots_of_quadratic"): [
        "discriminant",
        "roots of quadratic",
        "nature of roots",
        "quadratic formula",
        "graph behavior"
    ],
    ("physics", "classical_mechanics", "laws_of_motion"): [
        "inertia and mass",
        "rotational mass",
        "rotational inertia calculation",
        "angular momentum"
    ],
    ("chemistry", "organic_chemistry", "functional_groups"): [
        "isomerism",
        "stereoisomerism",
        "chiral centers",
        "stereocenters"
    ],
    ("biology", "genetics", "mendelian_inheritance"): [
        "mendelian laws",
        "punnett squares",
        "dihybrid crosses",
        "genotypic ratios"
    ],
    ("english", "grammar", "sentence_structure"): [
        "modifiers placement",
        "dangling modifiers",
        "subject implied",
        "corrections"
    ]
}

# ==========================================
# OPTION BANK (HIGH QUALITY PEDAGOGICAL CHOICES)
# ==========================================

OPTION_BANK = {
    "array indexing": ["Direct index offsets", "Sequential memory scan", "Pointer search", "Hash indexing"],
    "contiguous memory layout": ["Contiguous block allocation", "Linked pointers list", "Indexed segmented nodes", "Stack memory frames"],
    "insertion complexity": ["O(n) linear shift time", "O(1) constant time", "O(log n) logarithmic time", "O(n log n)"],
    "searching algorithms": ["Binary search on sorted lists", "Linear scan on unsorted lists", "Depth-first traversal", "Breadth-first expansion"],
    "array deletion": ["Requires elements shifting", "Immediate memory release", "Pointer relocation", "Null index fill"],

    "discriminant": ["b²-4ac expression", "a²-4bc expression", "b²+4ac expression", "a²+b²-c²"],
    "roots of quadratic": ["Solutions making function zero", "Extreme vertex coordinates", "Derivatives values", "Function integration bounds"],
    "nature of roots": ["Real or imaginary domain", "Positive or negative signs", "Ascending or descending direction", "Stable or unstable behavior"],
    "quadratic formula": ["(-b±√D)/2a solutions", "(b±√D)/2a solutions", "(-b±D)/2a solutions", "(b±D)/2a solutions"],
    "graph behavior": ["Parabolic symmetry shape", "Linear direction path", "Circular radius loop", "Hyperbolic curve segments"],

    "inertia and mass": ["Resistance to motion changes", "Force of gravity pull", "Velocity change rate", "Work energy ratio"],
    "rotational mass": ["Moment of inertia resistance", "Angular velocity speed", "Linear state state weight", "Centripetal force pull"],
    "rotational inertia calculation": ["Integral mass distribution sum", "Pure total mass sum", "Angular momentum ratio", "Linear weight acceleration"],
    "angular momentum": ["Momentum in rotational system", "Linear velocity momentum", "Torque balance force", "Centripetal state pull"],

    "isomerism": ["Same formula unique structure", "Unique formula same structure", "Identical spatial shapes", "Mirror spatial shapes"],
    "stereoisomerism": ["Spatial dimensional arrangement configurations", "Functional group structural variations", "Atom alignment bonds", "Stereocenter splits"],
    "chiral centers": ["Four distinct bonded groups carbons", "Three bonded groups carbons", "Double bonded carbons", "Symmetric side groups"],
    "stereocenters": ["Asymmetric carbon configuration centers", "Functional group core centers", "Double bond cores", "Aromatic rings"],

    "mendelian laws": ["Segregation and independent assortment laws", "Linked genes chromosome crossing", "Natural traits selection", "Phenotypic dilution ratios"],
    "punnett squares": ["Genotypic crossing prediction grids", "Pedigree history logs", "Chromosome division charts", "Linked traits list"],
    "dihybrid crosses": ["Double traits inheritance checking", "Single trait inheritance checking", "Sex-linked trait analysis", "Gene mutation tracking"],
    "genotypic ratios": ["Offspring genetic traits ratios", "Visual trait percentage", "Survival fitness rate", "Mutation frequency"],

    "modifiers placement": ["Ambiguous target modification", "Clear subject modification", "Verb clause coordination", "Sentence splicing"],
    "dangling modifiers": ["Missing target modifier subject", "Clear target modifier subject", "Improper adjective split", "Pronoun coordinate"],
    "subject implied": ["Incorrectly assuming implied actors", "Specifying clear active actors", "Passive voice sentences", "Coordinate verb joins"],
    "corrections": ["Inserting active actors subjects", "Removing description clauses", "Joining coordinate sentences", "Truncating descriptive words"]
}

# ==========================================
# DIFFICULTY RULES
# ==========================================

def get_diff(qtype):
    return {
        "memory": "easy",
        "conceptual": "medium",
        "tricky": "medium",
        "application": "hard",
        "reasoning": "hard"
    }[qtype]

# ==========================================
# QUESTION BUILDER ENGINE
# ==========================================

def generate_question(concept):
    base_options = OPTION_BANK.get(concept, ["Correct Option", "Trap Option 1", "Trap Option 2", "Trap Option 3"])
    correct_answer = base_options[0]

    options = base_options.copy()
    random.shuffle(options)

    correct_index = options.index(correct_answer)
    wrong_index = random.choice([i for i in range(4) if i != correct_index])

    return [
        {
            "type": "memory",
            "prompt": f"Which option best defines {concept}?",
            "options": options,
            "correct": correct_index
        },
        {
            "type": "conceptual",
            "prompt": f"Why is {concept} key to structural analysis?",
            "options": options,
            "correct": correct_index
        },
        {
            "type": "tricky",
            "prompt": f"Which statement is FALSE regarding {concept}?",
            "options": options,
            "correct": wrong_index
        },
        {
            "type": "application",
            "prompt": f"How is {concept} utilized in real-world scenarios?",
            "options": options,
            "correct": correct_index
        },
        {
            "type": "reasoning",
            "prompt": f"What structural problem does {concept} solve?",
            "options": options,
            "correct": correct_index
        }
    ]

# ==========================================
# INSERT LOGIC
# ==========================================

def insert_to_db(cur, s, t, st, q):
    # Duplicate check
    cur.execute("""
        SELECT id FROM question_bank 
        WHERE prompt = ? AND option_a = ? AND option_b = ?
    """, (q["prompt"], q["options"][0], q["options"][1]))
    
    if cur.fetchone():
        return False

    # Generate semantic and variant IDs
    semantic_id = generate_semantic_id(st, q["type"])
    variant_id = generate_variant_id(st, q["type"], q["prompt"])

    cur.execute("""
        INSERT INTO question_bank (
            subject, topic, subtopic, difficulty, cognitive_type,
            prompt, option_a, option_b, option_c, option_d,
            correct_index, semantic_id, variant_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        s, t, st, get_diff(q["type"]), q["type"],
        q["prompt"], q["options"][0], q["options"][1], q["options"][2], q["options"][3],
        q["correct"], semantic_id, variant_id, datetime.now().isoformat()
    ))
    return True

# ==========================================
# RUN SEED GENERATOR
# ==========================================

def run_generator(count_per_concept=2):
    conn = get_conn()
    cur = conn.cursor()
    
    total = 0
    for (s, t, st), concepts in MASTER_MAP.items():
        for concept in concepts:
            # Generate variants
            for _ in range(count_per_concept):
                qlist = generate_question(concept)
                for q in qlist:
                    if insert_to_db(cur, s, t, st, q):
                        total += 1
                        
    conn.commit()
    conn.close()
    print(f"Unified Question Generator Completed. Added {total} questions to Database.")

if __name__ == "__main__":
    print("Running Production-grade Question Generator...")
    run_generator()