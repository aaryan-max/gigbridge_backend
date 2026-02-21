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
    _try_add_column(cur, "client_profile", "pincode TEXT")
    # Add geolocation columns (safe, idempotent)
    _try_add_column(cur, "client_profile", "latitude REAL")
    _try_add_column(cur, "client_profile", "longitude REAL")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_otp (
        email TEXT PRIMARY KEY,
        otp TEXT,
        expires_at INTEGER
    )
    """)

    # ---------- NOTIFICATIONS (client side) ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notification (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        message TEXT,
        created_at INTEGER
    )
    """)

    # ---------- CALL SESSION ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS call_session (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller_role TEXT,
        caller_id INTEGER,
        receiver_role TEXT,
        receiver_id INTEGER,
        call_type TEXT,
        room_name TEXT,
        status TEXT,
        created_at INTEGER
    )
    """)

    db.commit()
    db.close()

def get_latest_hire_requests_for_client(client_id: int, limit: int = 20):
    try:
        cid = int(client_id)
    except Exception:
        return []
    conn = freelancer_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT h.id, h.client_id, h.freelancer_id, f.name, f.email, h.job_title, h.proposed_budget, h.note, h.status, h.created_at
            FROM hire_request h
            LEFT JOIN freelancer f ON f.id = h.freelancer_id
            WHERE h.client_id=?
            ORDER BY h.created_at DESC
            LIMIT ?
        """, (cid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "request_id": r[0],
                "client_id": r[1],
                "freelancer_id": r[2],
                "freelancer_name": r[3],
                "freelancer_email": r[4],
                "job_title": r[5],
                "proposed_budget": r[6],
                "note": r[7],
                "status": r[8],
                "created_at": r[9],
            })
        return out
    except Exception:
        return []
    finally:
        conn.close()

def get_latest_hire_requests_for_freelancer(freelancer_id: int, limit: int = 20):
    try:
        fid = int(freelancer_id)
    except Exception:
        return []
    conn = freelancer_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, client_id, job_title, proposed_budget, note, status, created_at
            FROM hire_request
            WHERE freelancer_id=?
            ORDER BY created_at DESC
            LIMIT ?
        """, (fid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            client_name = None
            client_email = None
            try:
                cconn = client_db()
                ccur = cconn.cursor()
                ccur.execute("SELECT name, email FROM client WHERE id=?", (r[1],))
                crow = ccur.fetchone()
                if crow:
                    client_name, client_email = crow[0], crow[1]
            except Exception:
                pass
            finally:
                try:
                    cconn.close()
                except Exception:
                    pass
            out.append({
                "request_id": r[0],
                "client_id": r[1],
                "client_name": client_name,
                "client_email": client_email,
                "job_title": r[2],
                "proposed_budget": r[3],
                "note": r[4],
                "status": r[5],
                "created_at": r[6],
            })
        return out
    except Exception:
        return []
    finally:
        conn.close()

def get_latest_messages_for_client(client_id: int, limit: int = 50):
    try:
        cid = int(client_id)
    except Exception:
        return []
    conn = freelancer_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT sender_role, sender_id, receiver_id, text, timestamp
            FROM message
            WHERE (sender_role='client' AND sender_id=?)
               OR (sender_role='freelancer' AND receiver_id=?)
            ORDER BY timestamp DESC
            LIMIT ?
        """, (cid, cid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "sender_role": r[0],
                "sender_id": r[1],
                "receiver_id": r[2],
                "text": r[3],
                "timestamp": r[4],
            })
        return out
    except Exception:
        return []
    finally:
        conn.close()

def get_latest_messages_for_freelancer(freelancer_id: int, limit: int = 50):
    try:
        fid = int(freelancer_id)
    except Exception:
        return []
    conn = freelancer_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT sender_role, sender_id, receiver_id, text, timestamp
            FROM message
            WHERE (sender_role='freelancer' AND sender_id=?)
               OR (sender_role='client' AND receiver_id=?)
            ORDER BY timestamp DESC
            LIMIT ?
        """, (fid, fid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "sender_role": r[0],
                "sender_id": r[1],
                "receiver_id": r[2],
                "text": r[3],
                "timestamp": r[4],
            })
        return out
    except Exception:
        return []
    finally:
        conn.close()

def get_latest_notifications_for_client(client_id: int, limit: int = 50):
    try:
        cid = int(client_id)
    except Exception:
        return []
    conn = client_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT message, created_at
            FROM notification
            WHERE client_id=?
            ORDER BY created_at DESC
            LIMIT ?
        """, (cid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "message": r[0],
                "created_at": r[1],
            })
        return out
    except Exception:
        return []
    finally:
        conn.close()

def get_client_profile(client_id: int):
    try:
        cid = int(client_id)
    except Exception:
        return None
    conn = client_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id, c.name, c.email, c.profile_image,
                   p.phone, p.location, p.bio, p.pincode, p.latitude, p.longitude
            FROM client c
            LEFT JOIN client_profile p ON p.client_id = c.id
            WHERE c.id=?
        """, (cid,))
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "profile_image": r[3],
            "phone": r[4],
            "location": r[5],
            "bio": r[6],
            "pincode": r[7],
            "latitude": r[8],
            "longitude": r[9],
        }
    except Exception:
        return None
    finally:
        conn.close()

def get_freelancer_profile(freelancer_id: int):
    try:
        fid = int(freelancer_id)
    except Exception:
        return None
    conn = freelancer_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT f.id, f.name, f.email, f.profile_image,
                   p.title, p.skills, p.experience, p.min_budget, p.max_budget,
                   p.rating, p.total_projects, p.bio, p.category, p.location, p.pincode, p.latitude, p.longitude
            FROM freelancer f
            LEFT JOIN freelancer_profile p ON p.freelancer_id = f.id
            WHERE f.id=?
        """, (fid,))
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "profile_image": r[3],
            "title": r[4],
            "skills": r[5],
            "experience": r[6],
            "min_budget": r[7],
            "max_budget": r[8],
            "rating": r[9],
            "total_projects": r[10],
            "bio": r[11],
            "category": r[12],
            "location": r[13],
            "pincode": r[14],
            "latitude": r[15],
            "longitude": r[16],
        }
    except Exception:
        return None
    finally:
        conn.close()
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
    _try_add_column(cur, "freelancer_profile", "location TEXT")
    _try_add_column(cur, "freelancer_profile", "pincode TEXT")
    # Add geolocation columns (safe, idempotent)
    _try_add_column(cur, "freelancer_profile", "latitude REAL")
    _try_add_column(cur, "freelancer_profile", "longitude REAL")

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
    
    # ===== UPDATED: STORE PORTFOLIO IMAGE AS BLOB =====
    # Add image_data column for BLOB storage while keeping image_path for backward compatibility
    _try_add_column(cur, "portfolio", "image_data BLOB")

    # ---------- CALL SESSION ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS call_session (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller_role TEXT,
        caller_id INTEGER,
        receiver_role TEXT,
        receiver_id INTEGER,
        call_type TEXT,
        room_name TEXT,
        status TEXT,
        created_at INTEGER
    )
    """)

    db.commit()
    db.close()
