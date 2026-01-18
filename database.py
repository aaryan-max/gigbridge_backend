import sqlite3

DB_NAME = "gigbridge.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    db = get_db()
    cur = db.cursor()

    # CLIENT AUTH
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # CLIENT PROFILE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_profile (
        client_id INTEGER PRIMARY KEY,
        company_name TEXT,
        phone TEXT,
        location TEXT,
        bio TEXT,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)

    # FREELANCER AUTH
    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # FREELANCER PROFILE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_profile (
        freelancer_id INTEGER PRIMARY KEY,
        title TEXT,
        skills TEXT,
        experience INTEGER,
        min_budget REAL,
        max_budget REAL,
        rating REAL DEFAULT 0,
        total_projects INTEGER DEFAULT 0,
        bio TEXT,
        availability TEXT DEFAULT 'available',
        FOREIGN KEY (freelancer_id) REFERENCES freelancers(id)
    )
    """)

    db.commit()
    db.close()
