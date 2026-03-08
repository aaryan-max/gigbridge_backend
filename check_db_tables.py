import sqlite3

# Check client.db tables
conn = sqlite3.connect('client.db')
cur = conn.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
client_tables = cur.fetchall()
print('Tables in client.db:', client_tables)
conn.close()

# Check freelancer.db tables
conn = sqlite3.connect('freelancer.db')
cur = conn.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
freelancer_tables = cur.fetchall()
print('Tables in freelancer.db:', freelancer_tables)
conn.close()
