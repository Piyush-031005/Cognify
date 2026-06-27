import hashlib
from database import get_conn


# =========================
# SEMANTIC ID GENERATOR
# =========================

def generate_semantic_id(concept, cognitive_type):

    raw = f"{concept.lower()}_{cognitive_type.lower()}"

    return hashlib.md5(
        raw.encode()
    ).hexdigest()


# =========================
# VARIANT ID GENERATOR
# =========================

def generate_variant_id(concept, cognitive_type, prompt):

    raw = f"""
    {concept.lower()}
    {cognitive_type.lower()}
    {prompt.lower()}
    """

    return hashlib.md5(
        raw.encode()
    ).hexdigest()


# =========================
# DUPLICATE CHECK
# =========================

def is_duplicate(cur, semantic_id):

    cur.execute("""
    SELECT id
    FROM question_bank
    WHERE semantic_id = ?
    """, (semantic_id,))

    return cur.fetchone() is not None


# =========================
# DB SCHEMA UPGRADE
# =========================

def upgrade_semantic_schema():

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
        ALTER TABLE question_bank
        ADD COLUMN semantic_id TEXT
        """)
    except:
        pass

    try:
        cur.execute("""
        ALTER TABLE question_bank
        ADD COLUMN variant_id TEXT
        """)
    except:
        pass

    conn.commit()
    conn.close()

    print("[OK] semantic schema upgraded")