import sqlite3
import time
import os
from database import freelancer_db, client_db, _try_add_column

def ensure_admin_tables():
    conn = freelancer_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        is_enabled INTEGER DEFAULT 1,
        created_at INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_session (
        token TEXT PRIMARY KEY,
        admin_id INTEGER,
        expires_at INTEGER,
        created_at INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        payload_json TEXT,
        created_at INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kyc_document (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        freelancer_id INTEGER NOT NULL,
        doc_type TEXT NOT NULL,
        file_path TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        uploaded_at INTEGER,
        verified_by_admin_id INTEGER,
        verified_at INTEGER,
        reject_reason TEXT
    )
    """)
    _try_add_column(cur, "freelancer_profile", "verification_status TEXT DEFAULT 'NOT_SUBMITTED'")
    _try_add_column(cur, "freelancer_profile", "is_verified INTEGER DEFAULT 0")
    _try_add_column(cur, "freelancer_profile", "verification_note TEXT DEFAULT ''")
    conn.commit()
    conn.close()
    c = client_db()
    ccur = c.cursor()
    _try_add_column(ccur, "client", "is_enabled INTEGER DEFAULT 1")
    c.commit()
    c.close()
    f = freelancer_db()
    fcur = f.cursor()
    _try_add_column(fcur, "freelancer", "is_enabled INTEGER DEFAULT 1")
    f.commit()
    f.close()
