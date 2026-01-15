import sqlite3

def client_db():
    return sqlite3.connect("client.db")

def freelancer_db():
    return sqlite3.connect("freelancer.db")

def create_tables():
    # Client table
    cdb = client_db()
    c = cdb.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS client (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    cdb.commit()
    cdb.close()

    # Freelancer table
    fdb = freelancer_db()
    f = fdb.cursor()
    f.execute("""
        CREATE TABLE IF NOT EXISTS freelancer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    fdb.commit()
    fdb.close()
