import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.errors
from postgres_config import get_postgres_connection, is_column_exists_error, is_table_exists_error, is_unique_violation_error, get_dict_cursor

def client_db():
    return get_postgres_connection()

def freelancer_db():
    return get_postgres_connection()

def _try_add_column(cur, table, col_def):
    """
    PostgreSQL version: Add column if it doesn't exist
    """
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_def}")
    except psycopg2.errors.Error:
        # Fallback for older PostgreSQL versions that don't support IF NOT EXISTS
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
        except is_column_exists_error:
            pass  # Column already exists, ignore
        except Exception:
            pass  # Other errors, ignore


def create_tables():
    # ==========================
    # CLIENT DB
    # ==========================
    db = client_db()
    cur = get_dict_cursor(db)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS client (
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # OAuth support (does NOT affect your existing login/signup/OTP logic)
    _try_add_column(cur, "client", "auth_provider TEXT DEFAULT 'local'")
    _try_add_column(cur, "client", "google_sub TEXT")

    # Profile photo support
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
    _try_add_column(cur, "client_profile", "latitude REAL")
    _try_add_column(cur, "client_profile", "longitude REAL")
    _try_add_column(cur, "client_profile", "dob TEXT")
    _try_add_column(cur, "client_profile", "name TEXT")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_otp (
        email TEXT PRIMARY KEY,
        otp TEXT,
        expires_at INTEGER
    )
    """)

    # Notifications (client side)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notification (
        id SERIAL PRIMARY KEY ,
        client_id INTEGER,
        message TEXT,
        created_at INTEGER
    )
    """)
    
    # Add enhanced notification columns if they don't exist
    _try_add_column(cur, "notification", "title TEXT")
    _try_add_column(cur, "notification", "related_entity_type TEXT")
    _try_add_column(cur, "notification", "related_entity_id INTEGER")
    _try_add_column(cur, "notification", "is_read BOOLEAN DEFAULT FALSE")

    # Call session (client.db copy)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS call_session (
        id SERIAL PRIMARY KEY ,
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

    # ==========================
    # MILESTONE TABLE
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS milestone (
        id SERIAL PRIMARY KEY,
        hire_request_id INTEGER,
        name TEXT,
        amount REAL,
        status TEXT DEFAULT 'CREATED',
        funded INTEGER DEFAULT 0,
        submitted INTEGER DEFAULT 0,
        approved INTEGER DEFAULT 0,
        created_at INTEGER
    )
    """)

    # ==========================
    # WORK LOG TABLE
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS work_log (
        id SERIAL PRIMARY KEY,
        hire_request_id INTEGER,
        freelancer_id INTEGER,
        work_date TEXT,
        hours REAL,
        calculated_regular REAL,
        calculated_overtime REAL,
        calculated_amount REAL,
        approved INTEGER DEFAULT 0,
        created_at INTEGER
    )
    """)

    # ==========================
    # INVOICE TABLE
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoice (
        id SERIAL PRIMARY KEY,
        hire_request_id INTEGER,
        total_amount REAL,
        week_start TEXT,
        week_end TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at INTEGER
    )
    """)

    # ==========================
    # CLIENT VERIFICATION
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_kyc (
        id SERIAL PRIMARY KEY,
        client_id INTEGER NOT NULL,
        government_id_path TEXT NOT NULL,
        pan_card_path TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TIMESTAMP,
        reviewed_by INTEGER
    )
    """)

    db.commit()
    db.close()

    # ==========================
    # FREELANCER DB
    # ==========================
    db = freelancer_db()
    cur = get_dict_cursor(db)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer (
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # OAuth support (does NOT affect your existing login/signup/OTP logic)
    _try_add_column(cur, "freelancer", "auth_provider TEXT DEFAULT 'local'")
    _try_add_column(cur, "freelancer", "google_sub TEXT")

    # Profile photo support
    _try_add_column(cur, "freelancer", "profile_image TEXT")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_profile (
        freelancer_id INTEGER PRIMARY KEY,
        title TEXT,
        skills TEXT,
        experience REAL,
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
    _try_add_column(cur, "freelancer_profile", "latitude REAL")
    _try_add_column(cur, "freelancer_profile", "longitude REAL")
    _try_add_column(cur, "freelancer_profile", "tags TEXT")
    _try_add_column(cur, "freelancer_profile", "current_plan TEXT DEFAULT 'FREE'")
    _try_add_column(cur, "freelancer_profile", "job_applies_used INTEGER DEFAULT 0")
    _try_add_column(cur, "freelancer_profile", "job_applies_reset_date INTEGER")
    _try_add_column(cur, "freelancer_profile", "dob TEXT")
    _try_add_column(cur, "freelancer_profile", "total_rating_sum REAL DEFAULT 0")
    _try_add_column(cur, "freelancer_profile", "availability_status TEXT DEFAULT 'AVAILABLE'")
    _try_add_column(cur, "freelancer_profile", "supports_fixed BOOLEAN DEFAULT TRUE")
    _try_add_column(cur, "freelancer_profile", "supports_hourly BOOLEAN DEFAULT TRUE")
    _try_add_column(cur, "freelancer_profile", "fixed_price REAL")
    _try_add_column(cur, "freelancer_profile", "hourly_rate REAL")
    _try_add_column(cur, "freelancer_profile", "overtime_rate_per_hour REAL")
    # New pricing-type aware fields
    _try_add_column(cur, "freelancer_profile", "pricing_type TEXT")
    _try_add_column(cur, "freelancer_profile", "per_person_rate REAL")
    _try_add_column(cur, "freelancer_profile", "starting_price REAL")
    _try_add_column(cur, "freelancer_profile", "searchable_price REAL")
    _try_add_column(cur, "freelancer_profile", "work_description TEXT")
    _try_add_column(cur, "freelancer_profile", "services_included TEXT")

    # Migrate experience from INTEGER to REAL for existing records
    try:
        # Check if experience column is still INTEGER type
        cur.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'freelancer_profile' 
            AND column_name = 'experience'
        """)
        result = cur.fetchone()
        
        if result and result[0] == 'integer':
            cur.execute("ALTER TABLE freelancer_profile ALTER COLUMN experience TYPE REAL")
    except Exception:
        # Column might already be REAL or migration already done
        pass

    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_otp (
        email TEXT PRIMARY KEY,
        otp TEXT,
        expires_at INTEGER
    )
    """)

    # Chat
    cur.execute("""
    CREATE TABLE IF NOT EXISTS message (
        id SERIAL PRIMARY KEY,
        sender_role TEXT,
        sender_id INTEGER,
        receiver_id INTEGER,
        text TEXT,
        timestamp INTEGER
    )
    """)

    # Hire / Job
    cur.execute("""
    CREATE TABLE IF NOT EXISTS hire_request (
        id SERIAL PRIMARY KEY,
        client_id INTEGER,
        freelancer_id INTEGER,
        job_title TEXT DEFAULT '',
        proposed_budget REAL,
        note TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at INTEGER
    )
    """)

    # Saved freelancers (client side)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_freelancer (
        client_id INTEGER,
        freelancer_id INTEGER,
        UNIQUE(client_id, freelancer_id)
    )
    """)

    # Saved clients (freelancer side)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_client (
        freelancer_id INTEGER,
        client_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(freelancer_id, client_id)
    )
    """)
    
    # Add created_at column to existing saved_client table if it doesn't exist
    _try_add_column(cur, "saved_client", "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    # Notifications (legacy copy kept in freelancer.db in your project)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notification (
        id SERIAL PRIMARY KEY ,
        client_id INTEGER,
        freelancer_id INTEGER,
        message TEXT,
        created_at INTEGER
    )
    """)
    
    # Add freelancer_id column if it doesn't exist
    _try_add_column(cur, "notification", "freelancer_id INTEGER")
    
    # Add enhanced notification columns if they don't exist
    _try_add_column(cur, "notification", "title TEXT")
    _try_add_column(cur, "notification", "related_entity_type TEXT")
    _try_add_column(cur, "notification", "related_entity_id INTEGER")
    _try_add_column(cur, "notification", "is_read BOOLEAN DEFAULT FALSE")

    # Portfolio
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id SERIAL PRIMARY KEY,
        freelancer_id INTEGER,
        title TEXT,
        description TEXT,
        image_path TEXT,
        created_at INTEGER
    )
    """)
    _try_add_column(cur, "portfolio", "image_data BYTEA")
    _try_add_column(cur, "portfolio", "media_type TEXT DEFAULT 'IMAGE'")
    _try_add_column(cur, "portfolio", "media_url TEXT")

    # Call session (freelancer.db copy)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS call_session (
        id SERIAL PRIMARY KEY,
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

    # Project posting tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_post (
        id SERIAL PRIMARY KEY,
        client_id INTEGER,
        category TEXT,
        description TEXT,
        location TEXT,
        pincode TEXT,
        status TEXT DEFAULT 'OPEN',
        created_at INTEGER
    )
    """)
    
    # Ensure location column exists (for existing databases)
    _try_add_column(cur, "project_post", "location TEXT")
    _try_add_column(cur, "project_post", "pincode TEXT")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_application (
        id SERIAL PRIMARY KEY,
        project_id INTEGER,
        freelancer_id INTEGER,
        proposal TEXT,
        bid_amount REAL,
        status TEXT DEFAULT 'PENDING',
        created_at INTEGER
    )
    """)
    
    # Ensure proposal column exists (for existing databases)
    _try_add_column(cur, "project_application", "proposal TEXT")
    _try_add_column(cur, "project_application", "bid_amount REAL")

    # ==========================
    # FTS5: Search index (PostgreSQL doesn't have FTS5, use full-text search)
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_search (
        freelancer_id INTEGER PRIMARY KEY,
        title TEXT,
        skills TEXT,
        bio TEXT,
        tags TEXT,
        portfolio_text TEXT
    )
    """)
    
    # Create GIN index for full-text search
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS freelancer_search_text_idx ON freelancer_search USING gin(to_tsvector('english', title || ' ' || skills || ' ' || bio || ' ' || tags || ' ' || portfolio_text))")
    except Exception:
        pass

    # ==========================
    # CLIENT VERIFICATION
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_verification (
        id SERIAL PRIMARY KEY,
        client_id INTEGER UNIQUE,
        government_id_path TEXT,
        pan_card_path TEXT,
        status TEXT DEFAULT 'PENDING',
        submitted_at INTEGER,
        reviewed_at INTEGER,
        rejection_reason TEXT
    )
    """)

    # ==========================
    # FREELANCER VERIFICATION
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_verification (
        id SERIAL PRIMARY KEY,
        freelancer_id INTEGER UNIQUE,
        government_id_path TEXT,
        pan_card_path TEXT,
        artist_proof_path TEXT,
        status TEXT DEFAULT 'PENDING',
        submitted_at INTEGER,
        reviewed_at INTEGER,
        rejection_reason TEXT
    )
    """)

    # ==========================
    # FREELANCER SUBSCRIPTION
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_subscription (
        id SERIAL PRIMARY KEY,
        freelancer_id INTEGER UNIQUE,
        plan_name TEXT DEFAULT 'FREE',
        start_date INTEGER,
        end_date INTEGER,
        status TEXT DEFAULT 'ACTIVE'
    )
    """)

    # ==========================
    # REVIEW TABLE
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS review (
        id SERIAL PRIMARY KEY,
        hire_request_id INTEGER UNIQUE,
        client_id INTEGER,
        freelancer_id INTEGER,
        rating REAL,
        review_text TEXT,
        created_at INTEGER
    )
    """)

    # Add contract type columns to hire_request
    _try_add_column(cur, "hire_request", "contract_type TEXT DEFAULT 'FIXED'")
    _try_add_column(cur, "hire_request", "contract_hourly_rate REAL")
    _try_add_column(cur, "hire_request", "contract_overtime_rate REAL")
    _try_add_column(cur, "hire_request", "weekly_limit REAL")
    _try_add_column(cur, "hire_request", "max_daily_hours REAL DEFAULT 8")
    _try_add_column(cur, "hire_request", "event_base_fee REAL")
    _try_add_column(cur, "hire_request", "event_included_hours REAL")
    _try_add_column(cur, "hire_request", "event_overtime_rate REAL")
    _try_add_column(cur, "hire_request", "advance_paid REAL DEFAULT 0")
    _try_add_column(cur, "hire_request", "event_date TEXT")
    _try_add_column(cur, "hire_request", "start_time TEXT")
    _try_add_column(cur, "hire_request", "end_time TEXT")
    # Payment & event lifecycle (Razorpay + dispute extension)
    _try_add_column(cur, "hire_request", "payment_status TEXT DEFAULT 'pending'")
    _try_add_column(cur, "hire_request", "payout_status TEXT DEFAULT 'on_hold'")
    _try_add_column(cur, "hire_request", "event_status TEXT DEFAULT 'scheduled'")
    _try_add_column(cur, "hire_request", "checkin_time INTEGER")
    _try_add_column(cur, "hire_request", "checkin_latitude REAL")
    _try_add_column(cur, "hire_request", "checkin_longitude REAL")
    _try_add_column(cur, "hire_request", "checkin_verified INTEGER DEFAULT 0")
    _try_add_column(cur, "hire_request", "completion_note TEXT")
    _try_add_column(cur, "hire_request", "completion_proof TEXT")
    _try_add_column(cur, "hire_request", "completed_at INTEGER")
    
    # Event venue fields for job-specific location
    _try_add_column(cur, "hire_request", "event_address TEXT")
    _try_add_column(cur, "hire_request", "event_city TEXT")
    _try_add_column(cur, "hire_request", "event_pincode TEXT")
    _try_add_column(cur, "hire_request", "event_landmark TEXT")
    _try_add_column(cur, "hire_request", "venue_source TEXT DEFAULT 'custom'")
    # Pricing-type and negotiation / hire-flow extensions (additive)
    _try_add_column(cur, "hire_request", "pricing_type TEXT")
    _try_add_column(cur, "hire_request", "selected_package_id INTEGER")
    _try_add_column(cur, "hire_request", "selected_package_name TEXT")
    _try_add_column(cur, "hire_request", "selected_package_price REAL")
    _try_add_column(cur, "hire_request", "selected_package_services TEXT")
    _try_add_column(cur, "hire_request", "client_budget REAL")
    _try_add_column(cur, "hire_request", "freelancer_quote REAL")
    _try_add_column(cur, "hire_request", "final_agreed_amount REAL")
    _try_add_column(cur, "hire_request", "counter_note TEXT")
    _try_add_column(cur, "hire_request", "negotiation_status TEXT DEFAULT 'REQUESTED'")
    _try_add_column(cur, "hire_request", "number_of_persons INTEGER")
    _try_add_column(cur, "hire_request", "guest_count INTEGER")
    _try_add_column(cur, "hire_request", "additional_requirements TEXT")

    # Package records for package-based pricing categories
    cur.execute("""
    CREATE TABLE IF NOT EXISTS freelancer_package (
        id SERIAL PRIMARY KEY,
        freelancer_id INTEGER NOT NULL,
        package_name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        created_at INTEGER
    )
    """)

    # ==========================
    # CALLS TABLE (Voice/Video Calls)
    # ==========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            call_id SERIAL PRIMARY KEY,
            caller_id INTEGER,
            receiver_id INTEGER,
            call_type VARCHAR(10),
            room_name TEXT,
            status VARCHAR(20) DEFAULT 'ringing',
            created_at INTEGER DEFAULT EXTRACT(EPOCH FROM NOW())::INTEGER
        )
    """)

    # ==========================
    # PAYMENT RECORDS (Razorpay hire & subscription)
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payment_records (
        payment_id SERIAL PRIMARY KEY,
        hire_id INTEGER,
        subscription_id INTEGER,
        record_type TEXT NOT NULL DEFAULT 'hire',
        razorpay_order_id TEXT,
        razorpay_payment_id TEXT,
        razorpay_signature TEXT,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'INR',
        status TEXT NOT NULL DEFAULT 'pending',
        created_at INTEGER
    )
    """)

    # ==========================
    # PAYOUT DETAILS (freelancer bank/UPI - separate from profile)
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payout_details (
        id SERIAL PRIMARY KEY,
        freelancer_id INTEGER NOT NULL,
        payout_method TEXT NOT NULL,
        account_holder_name TEXT,
        account_number TEXT,
        ifsc_code TEXT,
        upi_id TEXT,
        razorpay_contact_id TEXT,
        razorpay_fund_account_id TEXT,
        created_at INTEGER
    )
    """)

    # ==========================
    # DISPUTES
    # ==========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS disputes (
        dispute_id SERIAL PRIMARY KEY,
        hire_id INTEGER NOT NULL,
        raised_by TEXT NOT NULL,
        dispute_reason TEXT,
        proof TEXT,
        status TEXT DEFAULT 'OPEN',
        admin_decision TEXT,
        admin_note TEXT,
        resolution_type TEXT,
        resolved_at INTEGER
    )
    """)

    db.commit()

    # Bootstrap index once (only if empty) so existing profiles become searchable
    try:
        cur.execute("SELECT COUNT(*) FROM freelancer_search")
        cnt = int((cur.fetchone() or [0])[0] or 0)
        if cnt == 0:
            cur.execute("SELECT freelancer_id FROM freelancer_profile")
            ids = [r[0] for r in cur.fetchall()]
            db.commit()
            db.close()
            for fid in ids:
                rebuild_freelancer_search_index(fid)
            return
    except Exception:
        pass

    db.close()


# ============================================================
# FTS5 rebuild helper
# ============================================================

def rebuild_freelancer_search_index(freelancer_id: int):
    """
    Rebuild search row for one freelancer_id by pulling latest profile + portfolio.
    PostgreSQL version using regular table with GIN index.
    """
    try:
        fid = int(freelancer_id)
    except Exception:
        return

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)

        cur.execute("""
            SELECT COALESCE(title,''), COALESCE(skills,''), COALESCE(bio,''), COALESCE(tags,'')
            FROM freelancer_profile
            WHERE freelancer_id=%s
        """, (fid,))
        row = cur.fetchone()
        if not row:
            cur.execute("DELETE FROM freelancer_search WHERE freelancer_id=%s", (fid,))
            conn.commit()
            return

        title, skills, bio, tags = row

        cur.execute("""
            SELECT STRING_AGG(COALESCE(title,'') || ' ' || COALESCE(description,''), ' ')
            FROM portfolio
            WHERE freelancer_id=%s
        """, (fid,))
        prow = cur.fetchone()
        portfolio_text = (prow[0] if prow and prow[0] else "")

        # Replace row
        cur.execute("DELETE FROM freelancer_search WHERE freelancer_id=%s", (fid,))
        cur.execute("""
            INSERT INTO freelancer_search (freelancer_id, title, skills, bio, tags, portfolio_text)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (freelancer_id) DO UPDATE SET
                title=EXCLUDED.title,
                skills=EXCLUDED.skills,
                bio=EXCLUDED.bio,
                tags=EXCLUDED.tags,
                portfolio_text=EXCLUDED.portfolio_text
        """, (fid, title, skills, bio, tags, portfolio_text))

        conn.commit()
    except Exception:
        # Don't crash the app if indexing fails
        try:
            conn.commit()
        except Exception:
            pass
    finally:
        conn.close()


# ============================================================
# Existing helper getters used by llm_chatbot.py
# ============================================================

def get_latest_hire_requests_for_client(client_id: int, limit: int = 20):
    try:
        cid = int(client_id)
    except Exception:
        return []
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT h.id, h.client_id, h.freelancer_id, f.name, f.email, h.job_title, h.proposed_budget, h.note, h.status, h.created_at
            FROM hire_request h
            LEFT JOIN freelancer f ON f.id = h.freelancer_id
            WHERE h.client_id=%s
            ORDER BY h.created_at DESC
            LIMIT %s
        """, (cid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            if isinstance(r, dict):
                out.append({
                    "id": r.get("id"),
                    "client_id": r.get("client_id"),
                    "freelancer_id": r.get("freelancer_id"),
                    "freelancer_name": r.get("name"),
                    "freelancer_email": r.get("email"),
                    "job_title": r.get("job_title"),
                    "proposed_budget": r.get("proposed_budget"),
                    "note": r.get("note"),
                    "status": r.get("status"),
                    "created_at": r.get("created_at"),
                })
            else:
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
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, client_id, job_title, proposed_budget, note, status, created_at
            FROM hire_request
            WHERE freelancer_id=%s
            ORDER BY created_at DESC
            LIMIT %s
        """, (fid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            client_id = r.get("client_id") if isinstance(r, dict) else r[1]
            client_name = None
            client_email = None
            try:
                cconn = client_db()
                ccur = get_dict_cursor(cconn)
                ccur.execute("SELECT name, email FROM client WHERE id=%s", (client_id,))
                crow = ccur.fetchone()
                if crow:
                    if isinstance(crow, dict):
                        client_name = crow.get("name")
                        client_email = crow.get("email")
                    else:
                        client_name = crow[0]
                        client_email = crow[1]
            except Exception:
                pass
            finally:
                try:
                    cconn.close()
                except Exception:
                    pass
            
            if isinstance(r, dict):
                out.append({
                    "request_id": r.get("id"),
                    "client_id": client_id,
                    "client_name": client_name,
                    "client_email": client_email,
                    "job_title": r.get("job_title"),
                    "proposed_budget": r.get("proposed_budget"),
                    "note": r.get("note"),
                    "status": r.get("status"),
                    "created_at": r.get("created_at"),
                })
            else:
                out.append({
                    "request_id": r[0],
                    "client_id": client_id,
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
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT sender_role, sender_id, receiver_id, text, timestamp
            FROM message
            WHERE (sender_role='client' AND sender_id=%s)
               OR (sender_role='freelancer' AND receiver_id=%s)
            ORDER BY timestamp DESC
            LIMIT %s
        """, (cid, cid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            if isinstance(r, dict):
                out.append({
                    "sender_role": r.get("sender_role"),
                    "sender_id": r.get("sender_id"),
                    "receiver_id": r.get("receiver_id"),
                    "text": r.get("text"),
                    "timestamp": r.get("timestamp"),
                })
            else:
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
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT sender_role, sender_id, receiver_id, text, timestamp
            FROM message
            WHERE (sender_role='freelancer' AND sender_id=%s)
               OR (sender_role='client' AND receiver_id=%s)
            ORDER BY timestamp DESC
            LIMIT %s
        """, (fid, fid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            if isinstance(r, dict):
                out.append({
                    "sender_role": r.get("sender_role"),
                    "sender_id": r.get("sender_id"),
                    "receiver_id": r.get("receiver_id"),
                    "text": r.get("text"),
                    "timestamp": r.get("timestamp"),
                })
            else:
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
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT message, created_at
            FROM notification
            WHERE client_id=%s
            ORDER BY created_at DESC
            LIMIT %s
        """, (cid, int(limit)))
        rows = cur.fetchall()
        out = []
        for r in rows:
            if isinstance(r, dict):
                out.append({
                    "message": r.get("message"),
                    "created_at": r.get("created_at"),
                })
            else:
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
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT c.id, c.name, c.email, c.profile_image,
                   p.phone, p.location, p.bio, p.pincode, p.latitude, p.longitude
            FROM client c
            LEFT JOIN client_profile p ON p.client_id = c.id
            WHERE c.id=%s
        """, (cid,))
        r = cur.fetchone()
        if not r:
            return None
        if isinstance(r, dict):
            return {
                "id": r.get("id"),
                "name": r.get("name"),
                "email": r.get("email"),
                "profile_image": r.get("profile_image"),
                "phone": r.get("phone"),
                "location": r.get("location"),
                "bio": r.get("bio"),
                "pincode": r.get("pincode"),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
            }
        else:
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


def get_completed_project_count(freelancer_id: int):
    """Get the count of completed projects for a freelancer"""
    try:
        fid = int(freelancer_id)
    except Exception:
        return 0
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT COUNT(*)
            FROM hire_request
            WHERE freelancer_id = %s
            AND status = 'COMPLETED'
        """, (fid,))
        result = cur.fetchone()
        if result:
            return result.get("count", result[0] if not isinstance(result, dict) else 0)
        return 0
    except Exception:
        return 0
    finally:
        conn.close()


def get_freelancer_profile(freelancer_id: int):
    try:
        fid = int(freelancer_id)
    except Exception:
        return None
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT f.id, f.name, f.email, f.profile_image,
                   p.title, p.skills, p.experience, p.min_budget, p.max_budget,
                   p.rating, p.total_projects, p.bio, p.category, p.location, p.pincode, p.latitude, p.longitude, COALESCE(p.tags,''), COALESCE(p.availability_status,'AVAILABLE'),
                   COALESCE(p.supports_fixed, TRUE), COALESCE(p.supports_hourly, TRUE), p.fixed_price, p.hourly_rate, p.overtime_rate_per_hour
            FROM freelancer f
            LEFT JOIN freelancer_profile p ON p.freelancer_id = f.id
            WHERE f.id=%s
        """, (fid,))
        r = cur.fetchone()
        if not r:
            return None
        
        # Get completed projects count
        completed_projects = get_completed_project_count(fid)
        
        # Extract pricing fields with backward compatibility
        if isinstance(r, dict):
            supports_fixed = r.get("supports_fixed", True)
            supports_hourly = r.get("supports_hourly", True)
            fixed_price = r.get("fixed_price")
            hourly_rate = r.get("hourly_rate")
            overtime_rate = r.get("overtime_rate_per_hour")
        else:
            supports_fixed = r[19] if len(r) > 19 else True
            supports_hourly = r[20] if len(r) > 20 else True
            fixed_price = r[21] if len(r) > 21 else None
            hourly_rate = r[22] if len(r) > 22 else None
            overtime_rate = r[23] if len(r) > 23 else None
        
        # Backward compatibility: infer pricing models from existing data
        if supports_fixed is None and supports_hourly is None:
            # Old record - infer from pricing fields
            if fixed_price is not None and hourly_rate is not None:
                supports_fixed = True
                supports_hourly = True
            elif fixed_price is not None:
                supports_fixed = True
                supports_hourly = False
            elif hourly_rate is not None:
                supports_fixed = False
                supports_hourly = True
            else:
                # Default to both if no pricing data exists
                supports_fixed = True
                supports_hourly = True
        
        # Format experience from years (now stored as whole years)
        if isinstance(r, dict):
            experience_years = r.get("experience", 0) or 0
        else:
            experience_years = r[6] or 0
            
        # Since experience is now stored as whole years, display as years only
        experience_str = f"{int(experience_years)} years"
        
        if isinstance(r, dict):
            return {
                "id": r.get("id"),
                "name": r.get("name"),
                "email": r.get("email"),
                "profile_image": r.get("profile_image"),
                "title": r.get("title"),
                "skills": r.get("skills"),
                "experience": experience_years,
                "experience_formatted": experience_str,
                "min_budget": r.get("min_budget"),
                "max_budget": r.get("max_budget"),
                "rating": r.get("rating"),
                "total_projects": r.get("total_projects"),
                "projects_completed": completed_projects,
                "bio": r.get("bio"),
                "category": r.get("category"),
                "location": r.get("location"),
                "pincode": r.get("pincode"),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
                "tags": r.get("tags"),
                "availability_status": r.get("availability_status", "AVAILABLE"),
                "supports_fixed": supports_fixed,
                "supports_hourly": supports_hourly,
                "fixed_price": fixed_price,
                "hourly_rate": hourly_rate,
                "overtime_rate_per_hour": overtime_rate,
            }
        else:
            return {
                "id": r[0],
                "name": r[1],
                "email": r[2],
                "profile_image": r[3],
                "title": r[4],
                "skills": r[5],
                "experience": experience_years,
                "experience_formatted": experience_str,
                "min_budget": r[7],
                "max_budget": r[8],
                "rating": r[9],
                "total_projects": r[10],
                "projects_completed": completed_projects,
                "bio": r[11],
                "category": r[12],
                "location": r[13],
                "pincode": r[14],
                "latitude": r[15],
                "longitude": r[16],
                "tags": r[17],
                "availability_status": r[18],
                "supports_fixed": supports_fixed,
                "supports_hourly": supports_hourly,
                "fixed_price": fixed_price,
                "hourly_rate": hourly_rate,
                "overtime_rate_per_hour": overtime_rate,
            }
    except Exception:
        return None
    finally:
        conn.close()


# ============================================================
# FREELANCER VERIFICATION FUNCTIONS
# ============================================================

def get_freelancer_verification(freelancer_id: int):
    """Get verification status for a freelancer"""
    try:
        fid = int(freelancer_id)
    except Exception:
        return None
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, freelancer_id, government_id_path, pan_card_path, artist_proof_path,
                   status, submitted_at, reviewed_at, rejection_reason
            FROM freelancer_verification
            WHERE freelancer_id=%s
        """, (fid,))
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": r.get("id", r[0]) if isinstance(r, dict) else r[0],
            "freelancer_id": r.get("freelancer_id", r[1]) if isinstance(r, dict) else r[1],
            "government_id_path": r.get("government_id_path", r[2]) if isinstance(r, dict) else r[2],
            "pan_card_path": r.get("pan_card_path", r[3]) if isinstance(r, dict) else r[3],
            "artist_proof_path": r.get("artist_proof_path", r[4]) if isinstance(r, dict) else r[4],
            "status": r.get("status", r[5]) if isinstance(r, dict) else r[5],
            "submitted_at": r.get("submitted_at", r[6]) if isinstance(r, dict) else r[6],
            "reviewed_at": r.get("reviewed_at", r[7]) if isinstance(r, dict) else r[7],
            "rejection_reason": r.get("rejection_reason", r[8]) if isinstance(r, dict) else r[8],
        }
    except Exception:
        return None
    finally:
        conn.close()


def update_freelancer_verification(freelancer_id: int, government_id_path: str, pan_card_path: str, artist_proof_path: str = None):
    """Update or create verification record for freelancer"""
    try:
        fid = int(freelancer_id)
    except Exception:
        return False
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        import time
        current_time = int(time.time())
        
        # Check if record exists
        cur.execute("SELECT id FROM freelancer_verification WHERE freelancer_id=%s", (fid,))
        existing = cur.fetchone()
        
        if existing:
            # Update existing record
            cur.execute("""
                UPDATE freelancer_verification 
                SET government_id_path=%s, pan_card_path=%s, artist_proof_path=%s, 
                    status='PENDING', submitted_at=%s
                WHERE freelancer_id=%s
            """, (government_id_path, pan_card_path, artist_proof_path, current_time, fid))
        else:
            # Create new record
            cur.execute("""
                INSERT INTO freelancer_verification 
                (freelancer_id, government_id_path, pan_card_path, artist_proof_path, status, submitted_at)
                VALUES (%s, %s, %s, %s, 'PENDING', %s)
            """, (fid, government_id_path, pan_card_path, artist_proof_path, current_time))
        
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


# FREELANCER SUBSCRIPTION FUNCTIONS
# ============================================================

def get_freelancer_plan(freelancer_id: int):
    """Safely get freelancer plan, creating BASIC record if needed"""
    try:
        fid = int(freelancer_id)
    except Exception:
        return "BASIC"
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT plan_name
            FROM freelancer_subscription
            WHERE freelancer_id=%s
        """, (fid,))
        result = cur.fetchone()
        
        if result is None:
            # No subscription record exists, create BASIC
            import time
            current_time = int(time.time())
            cur.execute("""
                INSERT INTO freelancer_subscription 
                (freelancer_id, plan_name, status, start_date)
                VALUES (%s, 'BASIC', 'ACTIVE', %s)
            """, (fid, current_time))
            
            # Also update profile
            cur.execute("""
                UPDATE freelancer_profile 
                SET current_plan='BASIC'
                WHERE freelancer_id=%s
            """, (fid,))
            
            conn.commit()
            return "BASIC"
        
        # Record exists, get plan safely
        plan_name = result[0] if isinstance(result, (tuple, list)) else result['plan_name']
        
        # Handle NULL plan_name
        if not plan_name:
            cur.execute("""
                UPDATE freelancer_subscription 
                SET plan_name='BASIC'
                WHERE freelancer_id=%s
            """, (fid,))
            cur.execute("""
                UPDATE freelancer_profile 
                SET current_plan='BASIC'
                WHERE freelancer_id=%s
            """, (fid,))
            conn.commit()
            return "BASIC"
        
        # Migrate old plans
        if plan_name == "FREE":
            plan_name = "BASIC"
        elif plan_name == "PRO":
            plan_name = "PREMIUM"
        
        return plan_name
        
    except Exception:
        return "BASIC"
    finally:
        conn.close()


def get_freelancer_subscription(freelancer_id: int):
    """Get subscription details for freelancer"""
    try:
        fid = int(freelancer_id)
    except Exception:
        return None
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, freelancer_id, plan_name, start_date, end_date, status
            FROM freelancer_subscription
            WHERE freelancer_id=%s
        """, (fid,))
        r = cur.fetchone()
        if not r:
            # Return default BASIC subscription
            return {
                "id": None,
                "freelancer_id": fid,
                "plan_name": "BASIC",
                "start_date": None,
                "end_date": None,
                "status": "ACTIVE"
            }
        
        plan_name = r.get("plan_name", r[2]) if isinstance(r, dict) else r[2]
        # Migrate old plans
        if plan_name == "FREE":
            plan_name = "BASIC"
        elif plan_name == "PRO":
            plan_name = "PREMIUM"
        
        return {
            "id": r.get("id", r[0]) if isinstance(r, dict) else r[0],
            "freelancer_id": r.get("freelancer_id", r[1]) if isinstance(r, dict) else r[1],
            "plan_name": plan_name,
            "start_date": r.get("start_date", r[3]) if isinstance(r, dict) else r[3],
            "end_date": r.get("end_date", r[4]) if isinstance(r, dict) else r[4],
            "status": r.get("status", r[5]) if isinstance(r, dict) else r[5],
        }
    except Exception:
        return None
    finally:
        conn.close()


def update_client_kyc(client_id: int, government_id_path: str, pan_card_path: str):
    """Update or create KYC record for client"""
    try:
        cid = int(client_id)
    except Exception:
        return False
    
    conn = client_db()
    try:
        cur = get_dict_cursor(conn)
        import time
        current_time = int(time.time())
        
        # Check if record exists
        cur.execute("SELECT id FROM client_kyc WHERE client_id=%s", (cid,))
        existing = cur.fetchone()
        
        if existing:
            # Update existing record
            cur.execute("""
                UPDATE client_kyc 
                SET government_id_path=%s, pan_card_path=%s, status='PENDING', submitted_at=%s
                WHERE client_id=%s
            """, (government_id_path, pan_card_path, current_time, cid))
        else:
            # Create new record
            cur.execute("""
                INSERT INTO client_kyc 
                (client_id, government_id_path, pan_card_path, status, submitted_at)
                VALUES (%s, %s, %s, 'PENDING', %s)
            """, (cid, government_id_path, pan_card_path, current_time))
        
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_client_kyc(client_id: int):
    """Get KYC status for a client"""
    try:
        cid = int(client_id)
    except Exception:
        return None
    
    conn = client_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, client_id, government_id_path, pan_card_path,
                   status, submitted_at, reviewed_at, reviewed_by
            FROM client_kyc
            WHERE client_id=%s
        """, (cid,))
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": r.get("id", r[0]) if isinstance(r, dict) else r[0],
            "client_id": r.get("client_id", r[1]) if isinstance(r, dict) else r[1],
            "government_id_path": r.get("government_id_path", r[2]) if isinstance(r, dict) else r[2],
            "pan_card_path": r.get("pan_card_path", r[3]) if isinstance(r, dict) else r[3],
            "status": r.get("status", r[4]) if isinstance(r, dict) else r[4],
            "submitted_at": r.get("submitted_at", r[5]) if isinstance(r, dict) else r[5],
            "reviewed_at": r.get("reviewed_at", r[6]) if isinstance(r, dict) else r[6],
            "reviewed_by": r.get("reviewed_by", r[7]) if isinstance(r, dict) else r[7],
        }
    except Exception:
        return None
    finally:
        conn.close()


def update_client_kyc_review(client_id: int, status: str, reviewed_by: int):
    """Update client KYC review status"""
    try:
        cid = int(client_id)
        reviewer_id = int(reviewed_by)
    except Exception:
        return False
    
    if status not in ('APPROVED', 'REJECTED'):
        return False
    
    conn = client_db()
    try:
        cur = get_dict_cursor(conn)
        import time
        current_time = int(time.time())
        
        cur.execute("""
            UPDATE client_kyc 
            SET status=%s, reviewed_at=%s, reviewed_by=%s
            WHERE client_id=%s
        """, (status, current_time, reviewer_id, cid))
        
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_pending_client_kyc():
    """Get all pending client KYC submissions"""
    conn = client_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT ck.id, ck.client_id, ck.government_id_path, ck.pan_card_path,
                   ck.status, ck.submitted_at, c.name, c.email
            FROM client_kyc ck
            JOIN client c ON c.id = ck.client_id
            WHERE ck.status = 'PENDING'
            ORDER BY ck.submitted_at DESC
        """)
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "id": r[0],
                "client_id": r[1],
                "government_id_path": r[2],
                "pan_card_path": r[3],
                "status": r[4],
                "submitted_at": r[5],
                "client_name": r[6],
                "client_email": r[7],
            })
        return out
    except Exception:
        return []
    finally:
        conn.close()


def update_freelancer_subscription(freelancer_id: int, plan_name: str, days: int = 30):
    """Update or create subscription record for freelancer"""
    try:
        fid = int(freelancer_id)
    except Exception:
        return False
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        import time
        current_time = int(time.time())
        end_time = current_time + (days * 24 * 60 * 60)
        
        # Check if record exists
        cur.execute("SELECT id FROM freelancer_subscription WHERE freelancer_id=%s", (fid,))
        existing = cur.fetchone()
        
        if existing:
            # Update existing record
            cur.execute("""
                UPDATE freelancer_subscription 
                SET plan_name=%s, start_date=%s, end_date=%s, status='ACTIVE'
                WHERE freelancer_id=%s
            """, (plan_name, current_time, end_time, fid))
        else:
            # Create new record
            cur.execute("""
                INSERT INTO freelancer_subscription 
                (freelancer_id, plan_name, start_date, end_date, status)
                VALUES (%s, %s, %s, %s, 'ACTIVE')
            """, (fid, plan_name, current_time, end_time))
        
        # Update profile
        cur.execute("""
            UPDATE freelancer_profile 
            SET current_plan=%s
            WHERE freelancer_id=%s
        """, (plan_name, fid))
        
        # Reset job applies for paid plans
        if plan_name in ["PRO", "PREMIUM"]:
            cur.execute("""
                UPDATE freelancer_profile 
                SET job_applies_used=0
                WHERE freelancer_id=%s
            """, (fid,))
        
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_freelancer_job_applies(freelancer_id: int):
    """Get job applies count and limits for freelancer"""
    try:
        fid = int(freelancer_id)
    except Exception:
        return None
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT current_plan, job_applies_used, job_applies_reset_date
            FROM freelancer_profile
            WHERE freelancer_id=%s
        """, (fid,))
        r = cur.fetchone()
        if not r:
            return None
        
        current_plan = r[0] or "BASIC"
        applies_used = r[1] or 0
        reset_date = r[2]
        
        # Reset monthly counter if needed
        import time
        current_time = int(time.time())
        if reset_date and current_time > reset_date:
            applies_used = 0
            cur.execute("""
                UPDATE freelancer_profile 
                SET job_applies_used=0, job_applies_reset_date=%s
                WHERE freelancer_id=%s
            """, (current_time + (30 * 24 * 60 * 60), fid))
            conn.commit()
        
        # Get limits
        if current_plan == "BASIC":
            limit = 10
        else:
            limit = float('inf')  # Unlimited for PREMIUM
        
        return {
            "current_plan": current_plan,
            "applies_used": applies_used,
            "limit": limit,
            "remaining": max(0, limit - applies_used)
        }
    except Exception:
        return None
    finally:
        conn.close()


def increment_job_applies(freelancer_id: int):
    """Increment job applies count for freelancer"""
    try:
        fid = int(freelancer_id)
    except Exception:
        return False
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            UPDATE freelancer_profile 
            SET job_applies_used = job_applies_used + 1
            WHERE freelancer_id=%s
        """, (fid,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def check_subscription_expiry():
    """Check and update expired subscriptions"""
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        import time
        current_time = int(time.time())
        
        # Find expired subscriptions
        cur.execute("""
            SELECT freelancer_id 
            FROM freelancer_subscription 
            WHERE end_date < %s AND plan_name != 'BASIC'
        """, (current_time,))
        expired = cur.fetchall()
        
        for fid in expired:
            freelancer_id = fid[0]
            # Reset to BASIC
            cur.execute("""
                UPDATE freelancer_subscription 
                SET plan_name='BASIC', status='ACTIVE', start_date=NULL, end_date=NULL
                WHERE freelancer_id=%s
            """, (freelancer_id,))
            
            # Update profile
            cur.execute("""
                UPDATE freelancer_profile 
                SET current_plan='BASIC', job_applies_used=0
                WHERE freelancer_id=%s
            """, (freelancer_id,))
        
        conn.commit()
        return len(expired)
    except Exception:
        return 0
    finally:
        conn.close()
