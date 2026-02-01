import sqlite3

def client_db():
    return sqlite3.connect("client.db")

def freelancer_db():
    return sqlite3.connect("freelancer.db")

def create_tables():
    # ---------- CLIENT ----------
    db = client_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS client (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_profile (
        client_id INTEGER PRIMARY KEY,
        phone TEXT,
        location TEXT,
        bio TEXT
    )
    """)

    db.commit()
    db.close()

    # ---------- FREELANCER ----------
    db = freelancer_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_profile (
        freelancer_id INTEGER PRIMARY KEY,
        title TEXT,
        skills TEXT,
        experience INTEGER,
        min_budget REAL,
        max_budget REAL,
        rating REAL DEFAULT 0,
        bio TEXT,
        category TEXT
    )
    """)

    db.commit()
    db.close()
