import sqlite3
from database import get_conn
from question_generator import MASTER_MAP
import json

def run_verification():
    print("====================================================")
    print("COGNIFY DATASET VERIFICATION & HEALTH RUNNER")
    print("====================================================")
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Total & Approved
    cur.execute("SELECT COUNT(*) FROM question_bank")
    total_questions = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM question_bank WHERE status = 'Approved'")
    approved_questions = cur.fetchone()[0]
    
    # Subject breakdown
    cur.execute("""
        SELECT subject, topic, subtopic, COUNT(*) as cnt 
        FROM question_bank 
        GROUP BY subject, topic, subtopic
    """)
    rows = [dict(r) for r in cur.fetchall()]
    
    subjects_stats = {}
    for r in rows:
        subj = r["subject"]
        top = r["topic"]
        subt = r["subtopic"]
        cnt = r["cnt"]
        
        if subj not in subjects_stats:
            subjects_stats[subj] = {}
        if top not in subjects_stats[subj]:
            subjects_stats[subj][top] = {}
        subjects_stats[subj][top][subt] = cnt
        
    print(f"Total Questions in Bank: {total_questions}")
    print(f"Approved Questions:      {approved_questions}")
    print("\n--- Detailed Subject Breakdown ---")
    
    for subj, topics in sorted(subjects_stats.items()):
        total_subj_questions = sum(sum(subt.values()) for subt in topics.values())
        print(f"\nSubject: {subj.upper()} (Total: {total_subj_questions} questions)")
        for top, subtopics in sorted(topics.items()):
            print(f"  Topic: {top}")
            for subt, count in sorted(subtopics.items()):
                print(f"    Subtopic: {subt} -> {count} questions")
                
    # Missing combinations from master map
    missing = []
    for s, t, st in MASTER_MAP.keys():
        cur.execute("""
            SELECT COUNT(*) FROM question_bank 
            WHERE subject = ? AND topic = ? AND subtopic = ? AND status = 'Approved'
        """, (s, t, st))
        count = cur.fetchone()[0]
        if count == 0:
            missing.append(f"{s}/{t}/{st}")
            
    # Orphan check
    cur.execute("""
        SELECT id FROM question_bank 
        WHERE subject IS NULL OR subject = '' 
           OR topic IS NULL OR topic = '' 
           OR subtopic IS NULL OR subtopic = ''
           OR prompt IS NULL OR prompt = ''
    """)
    orphans = [r[0] for r in cur.fetchall()]
    
    # Unmapped check
    cur.execute("SELECT id FROM question_bank WHERE id NOT IN (SELECT DISTINCT question_id FROM room_questions_map)")
    unmapped = [r[0] for r in cur.fetchall()]
    
    print("\n====================================================")
    print("HEALTH SUMMARY")
    print("====================================================")
    print(f"Missing Master Map combinations: {len(missing)}")
    if missing:
        for m in missing:
            print(f"  [MISSING] {m}")
    print(f"Orphan questions count:           {len(orphans)}")
    print(f"Unmapped questions count:         {len(unmapped)}")
    
    health = "PASS" if not missing else "FAIL"
    print(f"Overall Dataset Health Status:    [{health}]")
    print("====================================================")
    
    conn.close()
    return health == "PASS"

if __name__ == "__main__":
    run_verification()
