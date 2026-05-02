from database import get_conn
import json

conn = get_conn()
cur = conn.cursor()

questions = [

# ========================= PHYSICS > MECHANICS > KINEMATICS =========================

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics","exam_level":"school",
"prompt":"A body moving with constant velocity has...",
"options":["Zero acceleration","Constant acceleration","Increasing velocity","Decreasing velocity"],
"correct_index":0,"question_type":"conceptual","difficulty":"easy",
"cognitive_skill":"principle_check","misconception_tag":"velocity_acceleration_confusion",
"bloom_level":"understand","estimated_time":12,"image_url":""
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics","exam_level":"school",
"prompt":"Acceleration is defined as?",
"options":["Rate of change of displacement","Rate of change of velocity","Distance covered per second","Mass into velocity"],
"correct_index":1,"question_type":"memory","difficulty":"easy",
"cognitive_skill":"definition_recall","misconception_tag":"formula_confusion",
"bloom_level":"remember","estimated_time":10,"image_url":""
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics","exam_level":"school",
"prompt":"If displacement is zero, what can we say?",
"options":["Distance must also be zero","Distance may or may not be zero","Velocity is zero","Acceleration is zero"],
"correct_index":1,"question_type":"tricky","difficulty":"medium",
"cognitive_skill":"misconception_probe","misconception_tag":"distance_displacement_confusion",
"bloom_level":"analyze","estimated_time":18,"image_url":""
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics","exam_level":"school",
"prompt":"Unit of velocity?",
"options":["m","m/s","m/s²","kgm/s"],
"correct_index":1,"question_type":"memory","difficulty":"easy",
"cognitive_skill":"unit_recall","misconception_tag":"unit_confusion",
"bloom_level":"remember","estimated_time":8,"image_url":""
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics","exam_level":"school",
"prompt":"If velocity is constant, displacement is?",
"options":["Zero","Uniformly changing","Directly proportional to time","Infinite"],
"correct_index":2,"question_type":"application","difficulty":"medium",
"cognitive_skill":"formula_application","misconception_tag":"motion_relation_confusion",
"bloom_level":"apply","estimated_time":16,"image_url":""
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics","exam_level":"school",
"prompt":"A freely falling object has approximately what acceleration near Earth?",
"options":["0","9.8 m/s²","1 m/s","Depends on mass"],
"correct_index":1,"question_type":"memory","difficulty":"easy",
"cognitive_skill":"constant_recall","misconception_tag":"gravity_confusion",
"bloom_level":"remember","estimated_time":9,"image_url":""
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics","exam_level":"school",
"prompt":"On a velocity-time graph, slope represents?",
"options":["Distance","Acceleration","Displacement","Speed"],
"correct_index":1,"question_type":"conceptual","difficulty":"medium",
"cognitive_skill":"graph_interpretation","misconception_tag":"graph_slope_confusion",
"bloom_level":"understand","estimated_time":15,"image_url":""
},

# ========================= MATH > ALGEBRA > QUADRATIC =========================

{
"subject":"math","topic":"algebra","subtopic":"quadratic","exam_level":"school",
"prompt":"Degree of quadratic equation is?",
"options":["1","2","3","4"],
"correct_index":1,"question_type":"memory","difficulty":"easy",
"cognitive_skill":"definition_recall","misconception_tag":"degree_confusion",
"bloom_level":"remember","estimated_time":8,"image_url":""
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic","exam_level":"school",
"prompt":"Number of roots of a quadratic equation can be?",
"options":["Only one","Only two","At most two","Infinite"],
"correct_index":2,"question_type":"conceptual","difficulty":"easy",
"cognitive_skill":"principle_check","misconception_tag":"root_count_confusion",
"bloom_level":"understand","estimated_time":12,"image_url":""
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic","exam_level":"school",
"prompt":"If discriminant is negative, roots are?",
"options":["Equal","Real and distinct","Imaginary","Zero"],
"correct_index":2,"question_type":"tricky","difficulty":"medium",
"cognitive_skill":"condition_analysis","misconception_tag":"discriminant_confusion",
"bloom_level":"analyze","estimated_time":16,"image_url":""
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic","exam_level":"school",
"prompt":"General form of quadratic equation?",
"options":["ax+b=0","ax²+bx+c=0","ax³+bx²+c=0","a+b=c"],
"correct_index":1,"question_type":"memory","difficulty":"easy",
"cognitive_skill":"formula_recall","misconception_tag":"equation_form_confusion",
"bloom_level":"remember","estimated_time":9,"image_url":""
},

# ========================= CS > PROGRAMMING > BASICS =========================

{
"subject":"cs","topic":"programming","subtopic":"basics","exam_level":"school",
"prompt":"Which of these is a loop structure?",
"options":["if","for","int","class"],
"correct_index":1,"question_type":"memory","difficulty":"easy",
"cognitive_skill":"syntax_recall","misconception_tag":"keyword_confusion",
"bloom_level":"remember","estimated_time":8,"image_url":""
},

{
"subject":"cs","topic":"programming","subtopic":"basics","exam_level":"school",
"prompt":"Variable is used to?",
"options":["Store data","Print code","Close compiler","Repeat hardware"],
"correct_index":0,"question_type":"conceptual","difficulty":"easy",
"cognitive_skill":"meaning_check","misconception_tag":"variable_purpose_confusion",
"bloom_level":"understand","estimated_time":10,"image_url":""
},

{
"subject":"cs","topic":"programming","subtopic":"basics","exam_level":"school",
"prompt":"Which data structure works on FIFO?",
"options":["Stack","Queue","Tree","Graph"],
"correct_index":1,"question_type":"tricky","difficulty":"medium",
"cognitive_skill":"logic_recall","misconception_tag":"fifo_lifo_confusion",
"bloom_level":"analyze","estimated_time":14,"image_url":""
}

]

for q in questions:
    cur.execute("""
    INSERT INTO questions_master (
        subject, topic, subtopic, exam_level,
        prompt, options_json, correct_index,
        question_type, difficulty, cognitive_skill,
        misconception_tag, bloom_level,
        estimated_time, image_url, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        q["subject"],
        q["topic"],
        q["subtopic"],
        q["exam_level"],
        q["prompt"],
        json.dumps(q["options"]),
        q["correct_index"],
        q["question_type"],
        q["difficulty"],
        q["cognitive_skill"],
        q["misconception_tag"],
        q["bloom_level"],
        q["estimated_time"],
        q["image_url"]
    ))

conn.commit()
conn.close()

print("QUESTIONS SEEDED SUCCESSFULLY")