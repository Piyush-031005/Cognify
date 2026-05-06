from database import get_conn

conn = get_conn()
cur = conn.cursor()

questions = [

# ================= PHYSICS =================
{
"subject":"physics","topic":"mechanics","subtopic":"laws_of_motion",
"difficulty":"easy","qtype":"memory","cognitive_type":"memory",
"tags":"newton","estimated_time":15,
"explanation":"Newton's first law defines inertia.",
"prompt":"Which law explains inertia?",
"options":["First law","Second law","Third law","Gravitation"],
"correct_index":0
},

{
"subject":"physics","topic":"mechanics","subtopic":"laws_of_motion",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"force","estimated_time":20,
"explanation":"Force changes state of motion.",
"prompt":"Force is required to?",
"options":["Maintain motion","Change motion","Stop time","Increase mass"],
"correct_index":1
},

{
"subject":"physics","topic":"mechanics","subtopic":"laws_of_motion",
"difficulty":"medium","qtype":"tricky","cognitive_type":"tricky",
"tags":"trap","estimated_time":25,
"explanation":"Zero net force → constant velocity, not zero motion.",
"prompt":"If net force is zero, object must be?",
"options":["At rest","Moving with constant velocity","Accelerating","Disappearing"],
"correct_index":1
},

{
"subject":"physics","topic":"mechanics","subtopic":"laws_of_motion",
"difficulty":"medium","qtype":"application","cognitive_type":"application",
"tags":"f=ma","estimated_time":25,
"explanation":"Acceleration depends on force and mass.",
"prompt":"If force doubles and mass same, acceleration?",
"options":["Same","Half","Double","Zero"],
"correct_index":2
},

{
"subject":"physics","topic":"mechanics","subtopic":"laws_of_motion",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"analysis","estimated_time":30,
"explanation":"Action-reaction pairs act on different bodies.",
"prompt":"Why action-reaction forces don't cancel?",
"options":["Same direction","Different bodies","Different magnitude","No reason"],
"correct_index":1
},

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
"difficulty":"easy","qtype":"memory","cognitive_type":"memory",
"tags":"formula","estimated_time":15,
"explanation":"Standard quadratic form is ax²+bx+c=0.",
"prompt":"General form of quadratic equation is?",
"options":["ax+b=0","ax²+bx+c=0","ax³+bx²","a+b=c"],
"correct_index":1
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"roots","estimated_time":20,
"explanation":"Discriminant determines nature of roots.",
"prompt":"What determines nature of roots?",
"options":["a","b","c","discriminant"],
"correct_index":3
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"tricky","cognitive_type":"tricky",
"tags":"trap","estimated_time":25,
"explanation":"Negative discriminant → imaginary roots.",
"prompt":"If D < 0, roots are?",
"options":["Real","Equal","Imaginary","Zero"],
"correct_index":2
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"medium","qtype":"application","cognitive_type":"application",
"tags":"solve","estimated_time":25,
"explanation":"Roots can be calculated via formula.",
"prompt":"Formula to find roots is?",
"options":["b²-4ac","(-b±√D)/2a","a²+b²","none"],
"correct_index":1
},

{
"subject":"math","topic":"algebra","subtopic":"quadratic",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"logic","estimated_time":30,
"explanation":"Equal roots when discriminant = 0.",
"prompt":"If roots are equal, D = ?",
"options":["1","0","-1","infinite"],
"correct_index":1
},

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
"difficulty":"easy","qtype":"memory","cognitive_type":"memory",
"tags":"syntax,loop","estimated_time":15,
"explanation":"for loop is a standard iteration structure.",
"prompt":"Which keyword is used for iteration?",
"options":["if","for","break","return"],
"correct_index":1
},

{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"variable,storage","estimated_time":20,
"explanation":"Variables store values and allow manipulation.",
"prompt":"Why do we use variables in programming?",
"options":["To store values","To stop execution","To print output","To exit program"],
"correct_index":0
},

{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"medium","qtype":"tricky","cognitive_type":"tricky",
"tags":"logic,error","estimated_time":25,
"explanation":"Assignment (=) is often confused with equality (==).",
"prompt":"Which operator is used for comparison?",
"options":["=","==","!=","+="],
"correct_index":1
},

{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"medium","qtype":"application","cognitive_type":"application",
"tags":"loop,logic","estimated_time":25,
"explanation":"Loop runs block multiple times.",
"prompt":"Which structure is best for repeating code 10 times?",
"options":["if","switch","for","break"],
"correct_index":2
},

{
"subject":"cs","topic":"programming","subtopic":"basics",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"flow,logic","estimated_time":30,
"explanation":"Nested loops increase execution layers.",
"prompt":"If a loop runs inside another loop, what increases?",
"options":["Memory only","Execution depth","Syntax errors","Compilation time"],
"correct_index":1
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
},

{
"subject":"cs","topic":"data_structures","subtopic":"queue_stack",
"difficulty":"easy","qtype":"memory","cognitive_type":"memory",
"tags":"queue,fifo","estimated_time":15,
"explanation":"Queue follows FIFO.",
"prompt":"Queue follows which principle?",
"options":["LIFO","FIFO","Random","None"],
"correct_index":1
},

{
"subject":"cs","topic":"data_structures","subtopic":"queue_stack",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"stack,lifo","estimated_time":20,
"explanation":"Stack follows Last In First Out.",
"prompt":"Why is stack called LIFO?",
"options":["Last added removed first","First removed last","Random removal","No order"],
"correct_index":0
},

{
"subject":"cs","topic":"data_structures","subtopic":"queue_stack",
"difficulty":"medium","qtype":"tricky","cognitive_type":"tricky",
"tags":"confusion,stack_queue","estimated_time":25,
"explanation":"Students confuse FIFO & LIFO.",
"prompt":"Which structure removes element first inserted?",
"options":["Stack","Queue","Tree","Graph"],
"correct_index":1
},

{
"subject":"cs","topic":"data_structures","subtopic":"queue_stack",
"difficulty":"medium","qtype":"application","cognitive_type":"application",
"tags":"real-life","estimated_time":25,
"explanation":"Queue models real-life waiting lines.",
"prompt":"Which structure models a ticket counter line?",
"options":["Stack","Queue","Tree","Array"],
"correct_index":1
},

{
"subject":"cs","topic":"data_structures","subtopic":"queue_stack",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"operation,analysis","estimated_time":30,
"explanation":"Stack reverses order naturally.",
"prompt":"Which structure helps reverse data order easily?",
"options":["Queue","Stack","Graph","Tree"],
"correct_index":1
},

# arrays
{
"subject":"dsa","topic":"arrays","subtopic":"basics",
"difficulty":"easy","qtype":"memory","cognitive_type":"memory",
"tags":"array","estimated_time":15,
"explanation":"Array stores elements in contiguous memory.",
"prompt":"Array stores elements in?",
"options":["Random memory","Contiguous memory","Stack","Queue"],
"correct_index":1
},

{
"subject":"dsa","topic":"arrays","subtopic":"basics",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"access","estimated_time":20,
"explanation":"Indexing gives direct access.",
"prompt":"Why array access is fast?",
"options":["Sorted","Indexed","Linked","Dynamic"],
"correct_index":1
},

{
"subject":"dsa","topic":"arrays","subtopic":"basics",
"difficulty":"medium","qtype":"tricky","cognitive_type":"tricky",
"tags":"trap","estimated_time":25,
"explanation":"Insertion in middle is costly.",
"prompt":"Worst case insertion in array is?",
"options":["O(1)","O(log n)","O(n)","O(n²)"],
"correct_index":2
},

{
"subject":"dsa","topic":"arrays","subtopic":"basics",
"difficulty":"medium","qtype":"application","cognitive_type":"application",
"tags":"search","estimated_time":25,
"explanation":"Binary search requires sorted array.",
"prompt":"Binary search works on?",
"options":["Any array","Sorted array","Stack","Graph"],
"correct_index":1
},

{
"subject":"dsa","topic":"arrays","subtopic":"basics",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"complexity","estimated_time":30,
"explanation":"Tradeoff between memory & speed.",
"prompt":"Why arrays are preferred over linked list sometimes?",
"options":["Less memory","Faster access","Dynamic size","No pointers"],
"correct_index":1
},

# jee physics (rotation+thinking traps)

{
"subject":"jee_physics","topic":"rotation","subtopic":"torque",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"torque,concept","estimated_time":25,
"explanation":"Torque depends on force and perpendicular distance.",
"prompt":"Torque is maximum when angle between force and lever arm is?",
"options":["0°","30°","90°","180°"],
"correct_index":2
},

{
"subject":"jee_physics","topic":"rotation","subtopic":"torque",
"difficulty":"hard","qtype":"tricky","cognitive_type":"tricky",
"tags":"trap,torque","estimated_time":30,
"explanation":"Parallel force → zero torque.",
"prompt":"Force applied along rod produces torque?",
"options":["Maximum","Minimum","Zero","Infinite"],
"correct_index":2
},

{
"subject":"jee_physics","topic":"rotation","subtopic":"angular_motion",
"difficulty":"medium","qtype":"application","cognitive_type":"application",
"tags":"angular","estimated_time":30,
"explanation":"α = τ / I",
"prompt":"If torque doubles and inertia same, angular acceleration?",
"options":["Half","Double","Same","Zero"],
"correct_index":1
},

{
"subject":"jee_physics","topic":"rotation","subtopic":"angular_motion",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"deep reasoning","estimated_time":40,
"explanation":"Distribution of mass affects inertia.",
"prompt":"Why hollow cylinder rotates faster than solid one?",
"options":["Less mass","Lower inertia","Higher torque","No friction"],
"correct_index":1
},

{
"subject":"jee_math","topic":"calculus","subtopic":"limits",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"limits","estimated_time":25,
"explanation":"Limit represents approaching value.",
"prompt":"Limit x→0 (sin x / x) equals?",
"options":["0","1","∞","-1"],
"correct_index":1
},

{
"subject":"jee_math","topic":"calculus","subtopic":"derivatives",
"difficulty":"hard","qtype":"tricky","cognitive_type":"tricky",
"tags":"trap","estimated_time":30,
"explanation":"Derivative of constant is zero.",
"prompt":"Derivative of 5 is?",
"options":["1","0","5","Undefined"],
"correct_index":1
},

{
"subject":"jee_math","topic":"calculus","subtopic":"derivatives",
"difficulty":"medium","qtype":"application","cognitive_type":"application",
"tags":"slope","estimated_time":30,
"explanation":"Derivative = slope of tangent.",
"prompt":"Slope of tangent at x=2 for x² is?",
"options":["2","4","6","8"],
"correct_index":1
},

{
"subject":"jee_math","topic":"calculus","subtopic":"derivatives",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"multi-step","estimated_time":40,
"explanation":"Chain rule concept.",
"prompt":"Derivative of (x² + 1)² involves?",
"options":["Product rule","Chain rule","Quotient rule","None"],
"correct_index":1
},

{
"subject":"logic","topic":"cognition","subtopic":"decision",
"difficulty":"medium","qtype":"tricky","cognitive_type":"tricky",
"tags":"elimination","estimated_time":30,
"explanation":"Close options trigger confusion.",
"prompt":"Which option seems correct but isn't logically complete?",
"options":["Almost correct","Fully correct","Irrelevant","Random"],
"correct_index":0
},

{
"subject":"logic","topic":"cognition","subtopic":"decision",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"meta-thinking","estimated_time":40,
"explanation":"Thinking about thinking.",
"prompt":"Choosing answer based on familiarity indicates?",
"options":["Conceptual clarity","Memory bias","Logical reasoning","Deep analysis"],
"correct_index":1
},

{
"subject":"logic","topic":"cognition","subtopic":"attention",
"difficulty":"medium","qtype":"application","cognitive_type":"application",
"tags":"attention","estimated_time":30,
"explanation":"Focus impacts decision quality.",
"prompt":"Frequent option hovering indicates?",
"options":["Confidence","Scanning behavior","Random guessing","Strong memory"],
"correct_index":1
},

# dbms
{
"subject":"dbms","topic":"sql","subtopic":"queries",
"difficulty":"easy","qtype":"memory","cognitive_type":"memory",
"tags":"sql,select","estimated_time":20,
"explanation":"SELECT is used to fetch data.",
"prompt":"Which SQL command is used to retrieve data?",
"options":["INSERT","UPDATE","SELECT","DELETE"],
"correct_index":2
},

{
"subject":"dbms","topic":"sql","subtopic":"joins",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"joins","estimated_time":25,
"explanation":"INNER JOIN returns matching rows.",
"prompt":"Which join returns only matching records?",
"options":["LEFT JOIN","RIGHT JOIN","INNER JOIN","FULL JOIN"],
"correct_index":2
},

{
"subject":"dbms","topic":"normalization","subtopic":"nf",
"difficulty":"medium","qtype":"tricky","cognitive_type":"tricky",
"tags":"normalization","estimated_time":30,
"explanation":"2NF removes partial dependency.",
"prompt":"2NF removes?",
"options":["Transitive dependency","Partial dependency","Redundancy","Primary key"],
"correct_index":1
},

{
"subject":"dbms","topic":"transactions","subtopic":"acid",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"acid","estimated_time":40,
"explanation":"Atomicity ensures all or nothing execution.",
"prompt":"If a transaction fails midway, which property ensures rollback?",
"options":["Consistency","Isolation","Atomicity","Durability"],
"correct_index":2
},

# cn
{
"subject":"cn","topic":"network_layer","subtopic":"ip",
"difficulty":"easy","qtype":"memory","cognitive_type":"memory",
"tags":"ip","estimated_time":20,
"explanation":"IP identifies devices on network.",
"prompt":"IP address is used for?",
"options":["Port mapping","Device identification","Encryption","Compression"],
"correct_index":1
},

{
"subject":"cn","topic":"transport_layer","subtopic":"tcp_udp",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"tcp","estimated_time":25,
"explanation":"TCP is reliable.",
"prompt":"Which protocol ensures reliable delivery?",
"options":["UDP","TCP","IP","ARP"],
"correct_index":1
},

{
"subject":"cn","topic":"data_link","subtopic":"error_detection",
"difficulty":"medium","qtype":"tricky","cognitive_type":"tricky",
"tags":"crc","estimated_time":30,
"explanation":"CRC detects errors, not corrects.",
"prompt":"CRC is used for?",
"options":["Error correction","Error detection","Encryption","Routing"],
"correct_index":1
},

{
"subject":"cn","topic":"network_layer","subtopic":"routing",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"routing","estimated_time":40,
"explanation":"Routing finds best path.",
"prompt":"Routing algorithm primarily optimizes?",
"options":["Bandwidth","Latency/path","Security","Memory"],
"correct_index":1
},

# os
{
"subject":"os","topic":"process","subtopic":"scheduling",
"difficulty":"easy","qtype":"memory","cognitive_type":"memory",
"tags":"fcfs","estimated_time":20,
"explanation":"FCFS executes in arrival order.",
"prompt":"FCFS scheduling executes processes based on?",
"options":["Priority","Arrival time","Burst time","Random"],
"correct_index":1
},

{
"subject":"os","topic":"process","subtopic":"deadlock",
"difficulty":"medium","qtype":"conceptual","cognitive_type":"conceptual",
"tags":"deadlock","estimated_time":25,
"explanation":"Deadlock needs 4 conditions.",
"prompt":"Deadlock occurs when?",
"options":["CPU idle","Mutual exclusion exists","Memory free","Single process"],
"correct_index":1
},

{
"subject":"os","topic":"memory","subtopic":"paging",
"difficulty":"medium","qtype":"tricky","cognitive_type":"tricky",
"tags":"paging","estimated_time":30,
"explanation":"Paging avoids fragmentation but adds overhead.",
"prompt":"Paging removes?",
"options":["External fragmentation","Internal fragmentation","Deadlock","Scheduling"],
"correct_index":0
},

{
"subject":"os","topic":"memory","subtopic":"virtual_memory",
"difficulty":"hard","qtype":"reasoning","cognitive_type":"reasoning",
"tags":"vm","estimated_time":40,
"explanation":"Virtual memory extends RAM using disk.",
"prompt":"Virtual memory primarily helps in?",
"options":["Speed increase","Memory expansion","Security","CPU optimization"],
"correct_index":1
}

]

# ================= INSERT =================
for q in questions:
    options = q["options"] + [""] * 4  # safety: ensure at least 4 options
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
        options[0],
        options[1],
        options[2],
        options[3],
        q["correct_index"],
        q["explanation"],
        q["tags"],
        q["estimated_time"]
    ))

conn.commit()
conn.close()

print("🔥 COGNIFY QUESTION BANK SEEDED SUCCESSFULLY")
