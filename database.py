import sqlite3

def client_db():
    return sqlite3.connect("client.db")

def freelancer_db():
    return sqlite3.connect("freelancer.db")

def _try_add_column(cur, table, col_def):
    """
    SQLite doesn't support: ADD COLUMN IF NOT EXISTS
    So we try, and ignore if column already exists.
    """
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
    except sqlite3.OperationalError:
        pass

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

    # OAuth support (does NOT affect your existing login/signup/OTP logic)
    _try_add_column(cur, "client", "auth_provider TEXT DEFAULT 'local'")
    _try_add_column(cur, "client", "google_sub TEXT")

    # NEW CODE: Profile photo support
    _try_add_column(cur, "client", "profile_image TEXT")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_profile (
        client_id INTEGER PRIMARY KEY,
        phone TEXT,
        location TEXT,
        bio TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_otp (
        email TEXT PRIMARY KEY,
        otp TEXT,
        expires_at INTEGER
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

    # OAuth support (does NOT affect your existing login/signup/OTP logic)
    _try_add_column(cur, "freelancer", "auth_provider TEXT DEFAULT 'local'")
    _try_add_column(cur, "freelancer", "google_sub TEXT")

    # NEW CODE: Profile photo support
    _try_add_column(cur, "freelancer", "profile_image TEXT")

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
        category TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_otp (
        email TEXT PRIMARY KEY,
        otp TEXT,
        expires_at INTEGER
    )
    """)

    # ---------- CHAT ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS message (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_role TEXT,
        sender_id INTEGER,
        receiver_id INTEGER,
        text TEXT,
        timestamp INTEGER
    )
    """)

    # ---------- HIRE / JOB ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS hire_request (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        freelancer_id INTEGER,
        job_title TEXT DEFAULT '',
        proposed_budget REAL,
        note TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at INTEGER
    )
    """)

    # ---------- SAVED FREELANCERS (client side) ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_freelancer (
        client_id INTEGER,
        freelancer_id INTEGER,
        UNIQUE(client_id, freelancer_id)
    )
    """)

    # ---------- SAVED CLIENTS (freelancer side) ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_client (
        freelancer_id INTEGER,
        client_id INTEGER,
        UNIQUE(freelancer_id, client_id)
    )
    """)

    # ---------- NOTIFICATIONS ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notification (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        message TEXT,
        created_at INTEGER
    )
    """)

    # ---------- PORTFOLIO ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        freelancer_id INTEGER,
        title TEXT,
        description TEXT,
        image_path TEXT,
        created_at INTEGER
    )
    """)

    db.commit()
    db.close()