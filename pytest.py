import sqlite3

conn = sqlite3.connect(":memory:")
c = conn.cursor()

c.execute("CREATE VIRTUAL TABLE test USING fts5(content);")
c.execute("INSERT INTO test(content) VALUES ('python developer mumbai');")
c.execute("INSERT INTO test(content) VALUES ('graphic designer pune');")

try:
    rows = c.execute("SELECT rowid, bm25(test) as score FROM test WHERE test MATCH 'python' ORDER BY score LIMIT 5;").fetchall()
    print("bm25() is supported ✅")
    print("Result:", rows)
except Exception as e:
    print("bm25() NOT supported ❌")
    print("Error:", e)

conn.close()