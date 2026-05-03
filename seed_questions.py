from database import get_conn

conn = get_conn()
cur = conn.cursor()

questions = [

# PHYSICS
{
"subject":"physics","topic":"mechanics","subtopic":"kinematics",
"difficulty":"easy","qtype":"conceptual",
"prompt":"A body moving with constant velocity has...",
"options":["Zero acceleration","Constant acceleration","Increasing velocity","Decreasing velocity"],
"correct_index":0
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics",
"difficulty":"easy","qtype":"memory",
"prompt":"Acceleration is defined as?",
"options":["Rate of change of displacement","Rate of change of velocity","Distance covered per second","Mass into velocity"],
"correct_index":1
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics",
"difficulty":"medium","qtype":"tricky",
"prompt":"If displacement is zero, what can we say?",
"options":["Distance must also be zero","Distance may or may not be zero","Velocity is zero","Acceleration is zero"],
"correct_index":1
},

{
"subject":"physics","topic":"mechanics","subtopic":"kinematics",
"difficulty":"medium","qtype":"application",
"prompt":"On velocity-time graph slope represents?",
"options":["Distance","Acceleration","Displacement","Speed"],
"correct_index":1
},


# ================= MATH MEGA PACK =================

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"application",
"prompt":"If roots of equation are equal, discriminant is?",
"options":["Positive","Negative","Zero","Infinity"],
"correct_index":2
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"hard","qtype":"conceptual",
"prompt":"If sum of roots is zero, equation must be?",
"options":["bx = 0","ax² + c = 0","ax² + bx = 0","ax² + bx + c = 0"],
"correct_index":1
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"tricky",
"prompt":"If roots are 2 and -2, equation is?",
"options":["x² - 4 = 0","x² + 4 = 0","x² - 2x = 0","x² + 2x = 0"],
"correct_index":0
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"easy","qtype":"memory",
"prompt":"Discriminant formula is?",
"options":["b² - 4ac","a² - 4bc","b² + 4ac","a² + b²"],
"correct_index":0
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"conceptual",
"prompt":"Nature of roots depends on?",
"options":["a","b","c","discriminant"],
"correct_index":3
},

# -------- TRIGONOMETRY --------

{
"subject":"math","topic":"trigonometry","subtopic":"identities",
"difficulty":"easy","qtype":"memory",
"prompt":"sin²x + cos²x = ?",
"options":["0","1","2","sin x"],
"correct_index":1
},

{
"subject":"math","topic":"trigonometry","subtopic":"identities",
"difficulty":"medium","qtype":"tricky",
"prompt":"tan x = ?",
"options":["sin x / cos x","cos x / sin x","sin x * cos x","1/sin x"],
"correct_index":0
},

{
"subject":"math","topic":"trigonometry","subtopic":"heights",
"difficulty":"medium","qtype":"application",
"prompt":"Height of object can be found using?",
"options":["sin only","cos only","tan","log"],
"correct_index":2
},

# -------- CALCULUS --------

{
"subject":"math","topic":"calculus","subtopic":"derivatives",
"difficulty":"easy","qtype":"memory",
"prompt":"Derivative of x² is?",
"options":["x","2x","x²","2"],
"correct_index":1
},

{
"subject":"math","topic":"calculus","subtopic":"derivatives",
"difficulty":"medium","qtype":"conceptual",
"prompt":"Derivative represents?",
"options":["Area","Slope","Volume","Distance"],
"correct_index":1
},

{
"subject":"math","topic":"calculus","subtopic":"limits",
"difficulty":"medium","qtype":"tricky",
"prompt":"Limit of constant is?",
"options":["0","constant","infinity","undefined"],
"correct_index":1
},

# -------- PROBABILITY --------

{
"subject":"math","topic":"probability","subtopic":"basic",
"difficulty":"easy","qtype":"memory",
"prompt":"Probability lies between?",
"options":["0 and 1","1 and 2","-1 and 1","0 and 10"],
"correct_index":0
},

{
"subject":"math","topic":"probability","subtopic":"basic",
"difficulty":"medium","qtype":"conceptual",
"prompt":"Probability of sure event is?",
"options":["0","1","0.5","2"],
"correct_index":1
},

{
"subject":"math","topic":"probability","subtopic":"basic",
"difficulty":"medium","qtype":"tricky",
"prompt":"Probability of impossible event is?",
"options":["1","0","-1","infinite"],
"correct_index":1
},
{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"easy","qtype":"memory",
"prompt":"General form of quadratic equation?",
"options":["ax+b=0","ax²+bx+c=0","ax³+bx²+c=0","a+b=c"],
"correct_index":1
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"easy","qtype":"conceptual",
"prompt":"Number of roots of quadratic equation can be?",
"options":["Only one","Only two","At most two","Infinite"],
"correct_index":2
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"tricky",
"prompt":"If discriminant is negative, roots are?",
"options":["Equal","Real distinct","Imaginary","Zero"],
"correct_index":2
},

# CS
{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"easy","qtype":"memory",
"prompt":"Which of these is a loop structure?",
"options":["if","for","int","class"],
"correct_index":1
},

{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"easy","qtype":"conceptual",
"prompt":"Variable is used to?",
"options":["Store data","Print code","Close compiler","Repeat hardware"],
"correct_index":0
},

{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"medium","qtype":"tricky",
"prompt":"Which data structure works on FIFO?",
"options":["Stack","Queue","Tree","Graph"],
"correct_index":1
}

]

for q in questions:
    cur.execute("""
    INSERT INTO question_bank (
        subject, topic, subtopic, difficulty, qtype,
        prompt, option_a, option_b, option_c, option_d, correct_index
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        q["subject"],
        q["topic"],
        q["subtopic"],
        q["difficulty"],
        q["qtype"],
        q["prompt"],
        q["options"][0],
        q["options"][1],
        q["options"][2],
        q["options"][3],
        q["correct_index"]
    ))

conn.commit()
conn.close()

print("QUESTION BANK SEEDED SUCCESSFULLY")