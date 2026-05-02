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

# MATH
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