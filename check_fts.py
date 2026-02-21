import sqlite3

conn = sqlite3.connect("freelancer.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='freelancer_search'")
result = cur.fetchone()

print("FTS table check result:", result)

conn.close()