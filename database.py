import sqlite3

# ---------- CONNECTIONS ----------
def client_db():
    return sqlite3.connect("client.db")

def freelancer_db():
    return sqlite3.connect("freelancer.db")


# ---------- TABLE CREATION ----------
def create_tables():
    cdb = client_db()
    fdb = freelancer_db()

    ccur = cdb.cursor()
    fcur = fdb.cursor()

    # CLIENT TABLE
    ccur.execute("""
    CREATE TABLE IF NOT EXISTS client (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    ccur.execute("""
    CREATE TABLE IF NOT EXISTS client_profile (
        client_id INTEGER PRIMARY KEY,
        phone TEXT,
        location TEXT,
        bio TEXT
    )
    """)

    # FREELANCER TABLE
    fcur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    fcur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_profile (
        freelancer_id INTEGER PRIMARY KEY,
        title TEXT,
        skills TEXT,
        experience INTEGER,
        min_budget REAL,
        max_budget REAL,
        bio TEXT,
        rating REAL DEFAULT 0
    )
    """)

    cdb.commit()
    fdb.commit()
    cdb.close()
    fdb.close()
