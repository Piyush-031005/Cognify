from database import get_conn

conn = get_conn()
cur = conn.cursor()

questions = [

# ================= PHYSICS =================
{
"subject":"physics","topic":"mechanics","subtopic":"kinematics",
"difficulty":"easy","qtype":"conceptual",
"cognitive_type":"conceptual",
"tags":"velocity,acceleration",
"estimated_time":20,
"explanation":"Constant velocity means no change in velocity hence acceleration is zero.",
"prompt":"A body moving with constant velocity has...",
"options":["Zero acceleration","Constant acceleration","Increasing velocity","Decreasing velocity"],
"correct_index":0
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics",
"difficulty":"easy","qtype":"memory",
"cognitive_type":"memory",
"tags":"definition,acceleration",
"estimated_time":15,
"explanation":"Acceleration is rate of change of velocity.",
"prompt":"Acceleration is defined as?",
"options":["Rate of change of displacement","Rate of change of velocity","Distance covered per second","Mass into velocity"],
"correct_index":1
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics",
"difficulty":"medium","qtype":"tricky",
"cognitive_type":"tricky",
"tags":"displacement,distance",
"estimated_time":25,
"explanation":"Displacement can be zero even if distance is not.",
"prompt":"If displacement is zero, what can we say?",
"options":["Distance must also be zero","Distance may or may not be zero","Velocity is zero","Acceleration is zero"],
"correct_index":1
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics",
"difficulty":"medium","qtype":"application",
"cognitive_type":"application",
"tags":"graph,velocity",
"estimated_time":25,
"explanation":"Slope of velocity-time graph gives acceleration.",
"prompt":"On velocity-time graph slope represents?",
"options":["Distance","Acceleration","Displacement","Speed"],
"correct_index":1
},

# ================= MATH =================

# QUADRATIC
{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"application",
"cognitive_type":"application",
"tags":"discriminant",
"estimated_time":20,
"explanation":"Equal roots occur when discriminant = 0.",
"prompt":"If roots of equation are equal, discriminant is?",
"options":["Positive","Negative","Zero","Infinity"],
"correct_index":2
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"hard","qtype":"conceptual",
"cognitive_type":"conceptual",
"tags":"roots",
"estimated_time":30,
"explanation":"If sum of roots = 0 → b = 0 → ax² + c = 0.",
"prompt":"If sum of roots is zero, equation must be?",
"options":["bx = 0","ax² + c = 0","ax² + bx = 0","ax² + bx + c = 0"],
"correct_index":1
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"tricky",
"cognitive_type":"tricky",
"tags":"roots",
"estimated_time":25,
"explanation":"Roots 2 and -2 → (x-2)(x+2) = x² - 4.",
"prompt":"If roots are 2 and -2, equation is?",
"options":["x² - 4 = 0","x² + 4 = 0","x² - 2x = 0","x² + 2x = 0"],
"correct_index":0
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"easy","qtype":"memory",
"cognitive_type":"memory",
"tags":"formula",
"estimated_time":15,
"explanation":"Discriminant = b² - 4ac.",
"prompt":"Discriminant formula is?",
"options":["b² - 4ac","a² - 4bc","b² + 4ac","a² + b²"],
"correct_index":0
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"conceptual",
"cognitive_type":"conceptual",
"tags":"roots",
"estimated_time":20,
"explanation":"Nature of roots depends on discriminant.",
"prompt":"Nature of roots depends on?",
"options":["a","b","c","discriminant"],
"correct_index":3
},

# TRIGONOMETRY
{
"subject":"math","topic":"trigonometry","subtopic":"identities",
"difficulty":"easy","qtype":"memory",
"cognitive_type":"memory",
"tags":"identity",
"estimated_time":10,
"explanation":"sin²x + cos²x = 1",
"prompt":"sin²x + cos²x = ?",
"options":["0","1","2","sin x"],
"correct_index":1
},

# CALCULUS
{
"subject":"math","topic":"calculus","subtopic":"derivatives",
"difficulty":"easy","qtype":"memory",
"cognitive_type":"memory",
"tags":"derivative",
"estimated_time":10,
"explanation":"Derivative of x² is 2x.",
"prompt":"Derivative of x² is?",
"options":["x","2x","x²","2"],
"correct_index":1
},

# PROBABILITY
{
"subject":"math","topic":"probability","subtopic":"basic",
"difficulty":"easy","qtype":"memory",
"cognitive_type":"memory",
"tags":"range",
"estimated_time":10,
"explanation":"Probability lies between 0 and 1.",
"prompt":"Probability lies between?",
"options":["0 and 1","1 and 2","-1 and 1","0 and 10"],
"correct_index":0
},

# ================= CS =================
{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"easy","qtype":"memory",
"cognitive_type":"memory",
"tags":"loop",
"estimated_time":10,
"explanation":"for loop is a looping structure.",
"prompt":"Which of these is a loop structure?",
"options":["if","for","int","class"],
"correct_index":1
},

{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"easy","qtype":"conceptual",
"cognitive_type":"conceptual",
"tags":"variable",
"estimated_time":10,
"explanation":"Variable stores data values.",
"prompt":"Variable is used to?",
"options":["Store data","Print code","Close compiler","Repeat hardware"],
"correct_index":0
},

{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"medium","qtype":"tricky",
"cognitive_type":"tricky",
"tags":"data-structure",
"estimated_time":15,
"explanation":"Queue follows FIFO.",
"prompt":"Which data structure works on FIFO?",
"options":["Stack","Queue","Tree","Graph"],
"correct_index":1
}

]

# ================= INSERT =================
for q in questions:
    cur.execute("""
    INSERT INTO question_bank (
        subject, topic, subtopic,
        difficulty, qtype,
        cognitive_type,
        prompt,
        option_a, option_b, option_c, option_d,
        correct_index,
        explanation,
        tags,
        estimated_time
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        q["subject"],
        q["topic"],
        q["subtopic"],
        q["difficulty"],
        q["qtype"],
        q["cognitive_type"],
        q["prompt"],
        q["options"][0],
        q["options"][1],
        q["options"][2],
        q["options"][3],
        q["correct_index"],
        q["explanation"],
        q["tags"],
        q["estimated_time"]
    ))

conn.commit()
conn.close()

print("🔥 COGNIFY QUESTION BANK SEEDED SUCCESSFULLY")