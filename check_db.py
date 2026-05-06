import sqlite3

conn = sqlite3.connect("cognify.db")
cur = conn.cursor()

cur.execute("PRAGMA table_info(question_bank)")
columns = cur.fetchall()

for col in columns:
    print(col)

conn.close()