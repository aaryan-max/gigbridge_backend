import psycopg2
import psycopg2.errors
from flask import Flask, request, jsonify
from database import client_db, freelancer_db
from psycopg2.extras import RealDictCursor
from postgres_config import get_postgres_connection, get_dict_cursor
from booking_service import validate_hire_request_slot, format_time_slot_display
import random
import time
import smtplib
import os
import requests
import secrets
from rapidfuzz import fuzz
import urllib.parse
import shutil
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from admin_db import ensure_admin_tables
from admin_routes import admin_bp
from kyc_routes import kyc_bp
from client_kyc_routes import client_kyc_bp
from payment_routes import payment_bp
from ai_chat import register_chat_routes
from ai_chat_routes import register_ai_chat_routes

from database import create_tables, rebuild_freelancer_search_index
from venue_helper import prepare_venue_data, validate_venue_data, check_venue_freelancer_compatibility
from settings import (
    FEATURE_HIDE_UNVERIFIED_FROM_SEARCH,
    FEATURE_BLOCK_DISABLED_USERS,
    FEATURE_ENFORCE_VERIFIED_FOR_HIRE_MESSAGE,
)
from categories import is_valid_category
from call_service import start_call, update_call_status, get_incoming_calls


# ============================================================
# AGE VALIDATION UTILITIES
# ============================================================

def calculate_age(dob_str):
    """Calculate age from DOB string in YYYY-MM-DD format"""
    from datetime import datetime
    try:
        dob_date = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        return age
    except ValueError:
        return None


def validate_age(age):
    """Validate age is between 18 and 60 years inclusive"""
    if age < 18:
        return False, "User must be at least 18 years old."
    if age > 60:
        return False, "Maximum allowed age is 60 years."
    return True, None


# ============================================================
# Semantic (RAG-style) search helpers
from semantic_search import load_or_build, semantic_search, upsert_freelancer
from filters_service import fetch_filtered_freelancers
from database import create_tables, rebuild_freelancer_search_index, get_freelancer_verification, update_freelancer_verification, get_freelancer_subscription, update_freelancer_subscription, get_freelancer_job_applies, increment_job_applies, check_subscription_expiry, get_freelancer_plan
from categories import is_valid_category


# ============================================================
# APP INIT
# ============================================================

app = Flask(__name__)

# ============================================================
# GLOBAL ERROR HANDLERS - ENSURE JSON RESPONSES
# ============================================================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "msg": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "msg": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"success": False, "msg": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "msg": "Internal server error"}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    # Log the full error for debugging
    import traceback
    print("="*50)
    print("🚨 UNHANDLED EXCEPTION CAUGHT:")
    print(f"Error Type: {type(error).__name__}")
    print(f"Error Message: {str(error)}")
    print("Full Traceback:")
    traceback.print_exc()
    print("="*50)
    
    # Return user-friendly error but include actual error message in dev mode
    error_msg = str(error) if app.debug else "Server error occurred"
    return jsonify({"success": False, "msg": error_msg}), 500

create_tables()
ensure_admin_tables()

# ============================================================
# STARTUP VALIDATION
# ============================================================

def validate_startup():
    """Validate database connectivity and required tables"""
    try:
        print("Validating database connectivity...")
        
        # Test client database
        client_conn = client_db()
        client_cur = get_dict_cursor(client_conn)
        client_cur.execute("SELECT 1")
        client_conn.close()
        print("[OK] Client database connection")
        
        # Test freelancer database
        freelancer_conn = freelancer_db()
        freelancer_cur = get_dict_cursor(freelancer_conn)
        freelancer_cur.execute("SELECT 1")
        freelancer_conn.close()
        print("[OK] Freelancer database connection")
        
        # Check required tables exist
        conn = client_db()
        cur = get_dict_cursor(conn)
        
        tables_to_check = ['client', 'client_otp', 'freelancer', 'freelancer_otp']
        for table in tables_to_check:
            try:
                cur.execute(f"SELECT 1 FROM {table} LIMIT 1")
                print(f"[OK] Table '{table}'")
            except Exception as e:
                print(f"[ERROR] Table '{table}': {str(e)}")
        
        conn.close()
        print("Startup validation completed successfully!")
        
    except Exception as e:
        print(f"Startup validation failed: {str(e)}")
        import traceback
        traceback.print_exc()

# Run startup validation
validate_startup()

app.register_blueprint(admin_bp)
app.register_blueprint(kyc_bp)
app.register_blueprint(client_kyc_bp)
app.register_blueprint(payment_bp)

# Register database chat routes
register_chat_routes(app)

# Register AI chat routes
register_ai_chat_routes(app)

# Try to load semantic index (optional; app still works without it)
try:
    load_or_build()
except Exception as _e:
    print("Semantic index not loaded:", _e)

# ============================================================
# AGENT: PENDING ACTION MEMORY
# ============================================================

# ============================================================
# EMAIL CONFIG
# ============================================================

SENDER_EMAIL = os.getenv("GIGBRIDGE_SENDER_EMAIL", "gigbridgee@gmail.com")
APP_PASSWORD = os.getenv("GIGBRIDGE_APP_PASSWORD", "tvtplklbvcnrwmzt")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# ============================================================
# OTP CONFIG
# ============================================================

OTP_TTL_SECONDS = 5 * 60  # 5 minutes

# ============================================================
# GOOGLE OAUTH CONFIG (ADDED - DOES NOT CHANGE EXISTING LOGIC)
# ============================================================

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/auth/google/callback")

# state -> { role, created_at, done, result }
GOOGLE_OAUTH_STATES = {}

def _google_state_cleanup():
    now = now_ts()
    expired = []
    for k, v in GOOGLE_OAUTH_STATES.items():
        if now - int(v.get("created_at", now)) > 10 * 60:  # 10 minutes
            expired.append(k)
    for k in expired:
        GOOGLE_OAUTH_STATES.pop(k, None)

def fuzzy_score(query: str, text: str) -> int:
    # token_set_ratio is very good for search-like matching
    return fuzz.token_set_ratio(query or "", text or "")        


# ============================================================
# HELPERS
# ============================================================

def now_ts():
    return int(time.time())

def get_json():
    return request.get_json(silent=True) or {}

def require_fields(data, fields):
    return [f for f in fields if f not in data or str(data[f]).strip() == ""]

def valid_email(email):
    email = (email or "").strip()
    return ("@" in email) and ("." in email)

# ============================================================
# GEO HELPERS
# ============================================================

def geocode_address(address: str):
    address = (address or "").strip()
    if not address:
        return None, None
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "GigBridge/1.0 (contact: support@gigbridge.local)"},
            timeout=8,
        )
        if resp.status_code != 200:
            return None, None
        data = resp.json()
        if not data:
            return None, None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
    except Exception:
        return None, None

def geocode_pincode(pincode: str, location_hint: str = None):
    pincode = (pincode or "").strip()
    if not pincode:
        return None, None
    try:
        hint = (location_hint or "").strip()
        if hint:
            q = f"{pincode}, {hint}, India"
        else:
            q = f"{pincode}, Mumbai, India"
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1},
            headers={"User-Agent": "GigBridge/1.0 (contact: support@gigbridge.local)"},
            timeout=8,
        )
        if resp.status_code != 200:
            print(f"[geo] Nominatim HTTP {resp.status_code} for pincode={pincode} hint={hint}")
            return None, None
        data = resp.json()
        if not data:
            print(f"[geo] No results from Nominatim for pincode={pincode} hint={hint}")
            return None, None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
    except Exception as e:
        print(f"[geo] Exception geocoding pincode={pincode}: {e}")
        return None, None

def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        import math
        R = 6371.0
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        d_phi = math.radians(float(lat2) - float(lat1))
        d_lambda = math.radians(float(lon2) - float(lon1))
        a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    except Exception:
        return 999999.0

# ============================================================
# EMAIL HELPERS
# ============================================================

def send_email(to_email, subject, body):
    if not SENDER_EMAIL or not APP_PASSWORD:
        raise RuntimeError("Email credentials missing. Set env vars or configure in code.")

    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.send_message(msg)
    server.quit()

def send_login_email(to_email, name, role, action):
    send_email(
        to_email,
        "🎉 GigBridge Login Successful",
        f"""
Hi {name},

Your {action} as a {role} on GigBridge was successful ✅

Welcome to GigBridge 🚀
"""
    )

def send_otp_email(to_email, otp):
    send_email(
        to_email,
        "🔐 GigBridge OTP Verification",
        f"""
Your OTP for GigBridge signup is:

🔢 OTP: {otp}

⏱ Valid for 5 minutes.
❌ Do NOT share this OTP with anyone.
"""
    )

# ============================================================
# OTP TABLES
# ============================================================

def create_otp_tables():
    conn = client_db()
    cur = get_dict_cursor(conn)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS client_otp (
            email TEXT PRIMARY KEY,
            otp TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS freelancer_otp (
            email TEXT PRIMARY KEY,
            otp TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

create_otp_tables()

# ============================================================
# OTP – CLIENT
# ============================================================

@app.route("/client/send-otp", methods=["POST"])
def client_send_otp():
    d = get_json()
    missing = require_fields(d, ["email"])
    if missing:
        return jsonify({"success": False, "msg": "Email required"}), 400

    email = str(d["email"]).strip().lower()
    if not valid_email(email):
        return jsonify({"success": False, "msg": "Invalid email"}), 400

    otp = str(random.randint(100000, 999999))
    expires_at = now_ts() + OTP_TTL_SECONDS

    conn = client_db()
    cur = get_dict_cursor(conn)
    cur.execute(
        "INSERT INTO client_otp (email, otp, expires_at) VALUES (%s, %s, %s) ON CONFLICT (email) DO UPDATE SET otp=EXCLUDED.otp, expires_at=EXCLUDED.expires_at",
        (email, otp, expires_at)
    )
    conn.commit()
    conn.close()

    try:
        send_otp_email(email, otp)
    except:
        pass

    return jsonify({"success": True, "msg": "OTP sent"})

@app.route("/client/verify-otp", methods=["POST"])
def client_verify_otp():
    print("=== CLIENT VERIFY OTP DEBUG ===")
    
    d = get_json()
    print(f"Received data: {d}")
    
    missing = require_fields(d, ["name", "email", "password", "otp"])
    if missing:
        print("Missing fields error")
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    name = str(d["name"]).strip()
    email = str(d["email"]).strip().lower()
    password = str(d["password"])
    otp_in = str(d["otp"]).strip()
    
    print(f"Processed: name={name}, email={email}, otp={otp_in}")

    conn = None
    try:
        conn = client_db()
        cur = get_dict_cursor(conn)
        print("Database connection established")
        
        # Verify OTP
        cur.execute("SELECT otp, expires_at FROM client_otp WHERE email=%s", (email,))    
        row = cur.fetchone()
        print(f"OTP query result: {row}")

        if not row:
            print("OTP not found")
            return jsonify({"success": False, "msg": "OTP not found"}), 400

        db_otp = row["otp"]
        expires_at = int(row["expires_at"])
        if now_ts() > expires_at:
            print("OTP expired")
            cur.execute("DELETE FROM client_otp WHERE email=%s", (email,))
            conn.commit()
            return jsonify({"success": False, "msg": "OTP expired"}), 400

        if str(db_otp) != otp_in:
            print("Invalid OTP")
            return jsonify({"success": False, "msg": "Invalid OTP"}), 400

        print("OTP verified, inserting client")
        # Insert client with RETURNING id
        cur.execute(
            "INSERT INTO client (name, email, password) VALUES (%s, %s, %s) RETURNING id",
            (name, email, generate_password_hash(password))
        )
        row = cur.fetchone()
        client_id = row["id"] if isinstance(row, dict) else row[0]
        print(f"Client inserted with ID: {client_id}")

        # Clean up OTP
        cur.execute("DELETE FROM client_otp WHERE email=%s", (email,))
        conn.commit()
        print("Transaction committed")

        try:
            send_login_email(email, name, "Client", "signup")
        except Exception as e:
            print(f"Email sending failed: {e}")

        print("Returning success response")
        return jsonify({"success": True, "client_id": client_id})

    except psycopg2.IntegrityError as e:
        print(f"IntegrityError (duplicate email): {e}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": "Client already exists"}), 409
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": "Server error"}), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed")
        print("=== END CLIENT VERIFY OTP DEBUG ===")

# ============================================================
# OTP – FREELANCER
# ============================================================

@app.route("/freelancer/send-otp", methods=["POST"])
def freelancer_send_otp():
    print("=== FREELANCER SEND OTP DEBUG ===")
    
    d = get_json()
    print(f"Received data: {d}")
    
    missing = require_fields(d, ["email"])
    if missing:
        print("Missing email field")
        return jsonify({"success": False, "msg": "Email required"}), 400

    email = str(d["email"]).strip().lower()
    if not valid_email(email):
        print("Invalid email format")
        return jsonify({"success": False, "msg": "Invalid email"}), 400

    otp = str(random.randint(100000, 999999))
    expires_at = now_ts() + OTP_TTL_SECONDS
    
    print(f"Generated OTP for {email}: {otp}")

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        print("Database connection established")
        
        # PostgreSQL UPSERT syntax
        cur.execute(
            "INSERT INTO freelancer_otp (email, otp, expires_at) VALUES (%s, %s, %s) "
            "ON CONFLICT (email) DO UPDATE SET otp = EXCLUDED.otp, expires_at = EXCLUDED.expires_at",
            (email, otp, expires_at)
        )
        conn.commit()
        print("OTP saved to database")

    except psycopg2.errors.UniqueViolation as e:
        print(f"UniqueViolation error: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": "Email already has OTP pending"}), 409
    except psycopg2.IntegrityError as e:
        print(f"IntegrityError: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": "Database integrity error"}), 409
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed")

    try:
        send_otp_email(email, otp)
        print("OTP email sent successfully")
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        # Continue even if email fails

    print("=== END FREELANCER SEND OTP DEBUG ===")
    return jsonify({"success": True, "msg": "OTP sent"})

@app.route("/freelancer/verify-otp", methods=["POST"])
def freelancer_verify_otp():
    print("=== FREELANCER VERIFY OTP DEBUG ===")
    
    d = get_json()
    print(f"Received data: {d}")
    
    missing = require_fields(d, ["name", "email", "password", "otp"])
    if missing:
        print("Missing fields error")
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    name = str(d["name"]).strip()
    email = str(d["email"]).strip().lower()
    password = str(d["password"])
    otp_in = str(d["otp"]).strip()
    
    print(f"Processed: name={name}, email={email}, otp={otp_in}")

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        print("Database connection established")
        
        # Verify OTP
        cur.execute("SELECT otp, expires_at FROM freelancer_otp WHERE email=%s", (email,))    
        row = cur.fetchone()
        print(f"OTP query result: {row}")

        if not row:
            print("OTP not found")
            return jsonify({"success": False, "msg": "OTP not found"}), 400

        db_otp = row["otp"]
        expires_at = int(row["expires_at"])
        if now_ts() > expires_at:
            print("OTP expired")
            cur.execute("DELETE FROM freelancer_otp WHERE email=%s", (email,))
            conn.commit()
            return jsonify({"success": False, "msg": "OTP expired"}), 400

        if str(db_otp) != otp_in:
            print("Invalid OTP")
            return jsonify({"success": False, "msg": "Invalid OTP"}), 400

        print("OTP verified, inserting freelancer")
        # Insert freelancer with RETURNING id
        cur.execute(
            "INSERT INTO freelancer (name, email, password) VALUES (%s, %s, %s) RETURNING id",
            (name, email, generate_password_hash(password))
        )
        row = cur.fetchone()
        freelancer_id = row["id"] if isinstance(row, dict) else row[0]
        print(f"Freelancer inserted with ID: {freelancer_id}")

        # Clean up OTP
        cur.execute("DELETE FROM freelancer_otp WHERE email=%s", (email,))
        conn.commit()
        print("Transaction committed")

        try:
            send_login_email(email, name, "Freelancer", "signup")
        except Exception as e:
            print(f"Email sending failed: {e}")

        print("Returning success response")
        return jsonify({"success": True, "freelancer_id": freelancer_id})

    except psycopg2.errors.UniqueViolation as e:
        print(f"UniqueViolation (duplicate email): {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": "Freelancer already exists"}), 409
    except psycopg2.IntegrityError as e:
        print(f"IntegrityError: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": "Database integrity error"}), 409
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed")
        print("=== END FREELANCER VERIFY OTP DEBUG ===")

# ============================================================
# PASSWORD RESET – CLIENT
# ============================================================

@app.route("/client/verify-otp-for-reset", methods=["POST"])
def client_verify_otp_for_reset():
    """Verify OTP for password reset"""
    print("=== CLIENT VERIFY OTP FOR RESET DEBUG ===")
    
    d = get_json()
    print(f"Received data: {d}")
    
    missing = require_fields(d, ["email", "otp"])
    if missing:
        print("Missing fields error")
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    email = str(d["email"]).strip().lower()
    otp_in = str(d["otp"]).strip()
    
    print(f"Processed: email={email}, otp_entered={otp_in}")

    conn = None
    try:
        conn = client_db()
        cur = get_dict_cursor(conn)
        print("Database connection established")
        
        # PostgreSQL placeholder syntax
        cur.execute("SELECT otp, expires_at FROM client_otp WHERE email=%s", (email,))
        row = cur.fetchone()
        print(f"OTP query result: {row}")
        
        if not row:
            print("OTP not found for email:", email)
            return jsonify({"success": False, "msg": "OTP not found"}), 400
        
        stored_otp = row["otp"]
        expires_at = int(row["expires_at"])
        print(f"Stored OTP: {stored_otp}, Entered OTP: {otp_in}")
        print(f"Current time: {now_ts()}, Expires at: {expires_at}")
        
        if now_ts() > expires_at:
            print("OTP expired")
            # Clean up expired OTP
            cur.execute("DELETE FROM client_otp WHERE email=%s", (email,))
            conn.commit()
            return jsonify({"success": False, "msg": "OTP expired"}), 400
        
        if str(stored_otp) != otp_in:
            print(f"OTP mismatch: stored='{stored_otp}' vs entered='{otp_in}'")
            return jsonify({"success": False, "msg": "Invalid OTP or OTP expired"}), 400
        
        print("OTP verified successfully")
        # OTP verified, allow password reset
        return jsonify({"success": True, "msg": "OTP verified"})
        
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed")
        print("=== END CLIENT VERIFY OTP FOR RESET DEBUG ===")

@app.route("/client/reset-password", methods=["POST"])
def client_reset_password():
    """Reset client password"""
    print("=== CLIENT RESET PASSWORD DEBUG ===")
    
    d = get_json()
    print(f"Received data: {d}")
    
    missing = require_fields(d, ["email", "new_password"])
    if missing:
        print("Missing fields error")
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    email = str(d["email"]).strip().lower()
    new_password = str(d["new_password"])
    
    print(f"Processed: email={email}, password_length={len(new_password)}")
    
    if len(new_password) < 6:
        print("Password too short")
        return jsonify({"success": False, "msg": "Password must be at least 6 characters"}), 400

    conn = None
    try:
        conn = client_db()
        cur = get_dict_cursor(conn)
        print("Database connection established")
        
        # PostgreSQL placeholder syntax
        cur.execute("UPDATE client SET password=%s WHERE email=%s", 
                   (generate_password_hash(new_password), email))
        
        if cur.rowcount == 0:
            print("No client found with email:", email)
            return jsonify({"success": False, "msg": "Email not found"}), 404
        
        print(f"Password updated for {cur.rowcount} client(s)")
        
        # Clean up OTP after successful password reset
        cur.execute("DELETE FROM client_otp WHERE email=%s", (email,))
        conn.commit()
        print("OTP cleaned up, transaction committed")
        
        return jsonify({"success": True, "msg": "Password reset successful"})
        
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed")
        print("=== END CLIENT RESET PASSWORD DEBUG ===")

# ============================================================
# PASSWORD RESET – FREELANCER
# ============================================================

@app.route("/freelancer/verify-otp-for-reset", methods=["POST"])
def freelancer_verify_otp_for_reset():
    """Verify OTP for password reset"""
    print("=== FREELANCER VERIFY OTP FOR RESET DEBUG ===")
    
    d = get_json()
    print(f"Received data: {d}")
    
    missing = require_fields(d, ["email", "otp"])
    if missing:
        print("Missing fields error")
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    email = str(d["email"]).strip().lower()
    otp_in = str(d["otp"]).strip()
    
    print(f"Processed: email={email}, otp_entered={otp_in}")

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        print("Database connection established")
        
        # PostgreSQL placeholder syntax
        cur.execute("SELECT otp, expires_at FROM freelancer_otp WHERE email=%s", (email,))
        row = cur.fetchone()
        print(f"OTP query result: {row}")
        
        if not row:
            print("OTP not found for email:", email)
            return jsonify({"success": False, "msg": "OTP not found"}), 400
        
        stored_otp = row["otp"]
        expires_at = int(row["expires_at"])
        print(f"Stored OTP: {stored_otp}, Entered OTP: {otp_in}")
        print(f"Current time: {now_ts()}, Expires at: {expires_at}")
        
        if now_ts() > expires_at:
            print("OTP expired")
            # Clean up expired OTP
            cur.execute("DELETE FROM freelancer_otp WHERE email=%s", (email,))
            conn.commit()
            return jsonify({"success": False, "msg": "OTP expired"}), 400
        
        if str(stored_otp) != otp_in:
            print(f"OTP mismatch: stored='{stored_otp}' vs entered='{otp_in}'")
            return jsonify({"success": False, "msg": "Invalid OTP or OTP expired"}), 400
        
        print("OTP verified successfully")
        # OTP verified, allow password reset
        return jsonify({"success": True, "msg": "OTP verified"})
        
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed")
        print("=== END FREELANCER VERIFY OTP FOR RESET DEBUG ===")

@app.route("/freelancer/reset-password", methods=["POST"])
def freelancer_reset_password():
    """Reset freelancer password"""
    print("=== FREELANCER RESET PASSWORD DEBUG ===")
    
    d = get_json()
    print(f"Received data: {d}")
    
    missing = require_fields(d, ["email", "new_password"])
    if missing:
        print("Missing fields error")
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    email = str(d["email"]).strip().lower()
    new_password = str(d["new_password"])
    
    print(f"Processed: email={email}, password_length={len(new_password)}")
    
    if len(new_password) < 6:
        print("Password too short")
        return jsonify({"success": False, "msg": "Password must be at least 6 characters"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        print("Database connection established")
        
        # PostgreSQL placeholder syntax
        cur.execute("UPDATE freelancer SET password=%s WHERE email=%s", 
                   (generate_password_hash(new_password), email))
        
        if cur.rowcount == 0:
            print("No freelancer found with email:", email)
            return jsonify({"success": False, "msg": "Email not found"}), 404
        
        print(f"Password updated for {cur.rowcount} freelancer(s)")
        
        # Clean up OTP after successful password reset
        cur.execute("DELETE FROM freelancer_otp WHERE email=%s", (email,))
        conn.commit()
        print("OTP cleaned up, transaction committed")
        
        return jsonify({"success": True, "msg": "Password reset successful"})
        
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed")
        print("=== END FREELANCER RESET PASSWORD DEBUG ===")

@app.route("/client/signup", methods=["POST"])
def client_signup():
    """Direct signup endpoint for clients"""
    d = get_json()
    missing = require_fields(d, ["name", "email", "password"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    name = str(d["name"]).strip()
    email = str(d["email"]).strip().lower()
    password = str(d["password"])
    
    if not valid_email(email):
        return jsonify({"success": False, "msg": "Invalid email format"}), 400
    
    conn = client_db()
    cur = get_dict_cursor(conn)
    
    # Check if email already exists
    cur.execute("SELECT id FROM client WHERE email=%s", (email,))
    if cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Email already exists"}), 400
    
    # Insert new client
    cur.execute("INSERT INTO client (name, email, password) VALUES (%s, %s, %s)", 
               (name, email, generate_password_hash(password)))
    client_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "client_id": client_id})

@app.route("/freelancer/signup", methods=["POST"])
def freelancer_signup():
    """Direct signup endpoint for freelancers"""
    d = get_json()
    missing = require_fields(d, ["name", "email", "password"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    name = str(d["name"]).strip()
    email = str(d["email"]).strip().lower()
    password = str(d["password"])
    
    if not valid_email(email):
        return jsonify({"success": False, "msg": "Invalid email format"}), 400
    
    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    
    # Check if email already exists
    cur.execute("SELECT id FROM freelancer WHERE email=%s", (email,))
    if cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Email already exists"}), 400
    
    # Insert new freelancer
    cur.execute("INSERT INTO freelancer (name, email, password) VALUES (%s, %s, %s)", 
               (name, email, generate_password_hash(password)))
    freelancer_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "freelancer_id": freelancer_id})

# ============================================================
# LOGIN APIs (CORE LOGIC SAME)
# ============================================================

@app.route("/client/login", methods=["POST"])
def client_login():
    d = get_json()
    missing = require_fields(d, ["email", "password"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    email = str(d["email"]).strip().lower()
    password = str(d["password"])

    conn = client_db()
    cur = get_dict_cursor(conn)
    cur.execute("SELECT id,password,name FROM client WHERE email=%s", (email,))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row["password"], password):
        if FEATURE_BLOCK_DISABLED_USERS:
            try:
                c2 = client_db()
                cur2 = get_dict_cursor(c2)
                cur2.execute("SELECT COALESCE(is_enabled,1) as is_enabled FROM client WHERE id=%s", (row["id"],))
                en = cur2.fetchone()
                c2.close()
                if en and int(en.get("is_enabled", 1)) != 1:
                    return jsonify({"success": False, "msg": "Account disabled"}), 403
            except Exception:
                pass
        try:
            send_login_email(email, row["name"], "Client", "login")
        except:
            pass
        return jsonify({"success": True, "client_id": row["id"]})

    return jsonify({"success": False, "msg": "Invalid credentials"})

@app.route("/freelancer/login", methods=["POST"])
def freelancer_login():
    d = get_json()
    missing = require_fields(d, ["email", "password"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    email = str(d["email"]).strip().lower()
    password = str(d["password"])

    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("SELECT id,password,name FROM freelancer WHERE email=%s", (email,))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row["password"], password):
        if FEATURE_BLOCK_DISABLED_USERS:
            try:
                f2 = freelancer_db()
                cur2 = get_dict_cursor(f2)
                cur2.execute("SELECT COALESCE(is_enabled,1) as is_enabled FROM freelancer WHERE id=%s", (row["id"],))
                en = cur2.fetchone()
                f2.close()
                if en and int(en.get("is_enabled", 1)) != 1:
                    return jsonify({"success": False, "msg": "Account disabled"}), 403
            except Exception:
                pass
        try:
            send_login_email(email, row["name"], "Freelancer", "login")
        except:
            pass
        return jsonify({"success": True, "freelancer_id": row["id"]})

    return jsonify({"success": False, "msg": "Invalid credentials"})

# ============================================================
# PROFILES
# ============================================================

@app.route("/client/profile", methods=["POST"])
def client_profile():
    d = get_json()
    missing = require_fields(d, ["client_id", "name", "phone", "location", "bio", "dob"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    # Validate DOB format and calculate age
    age = calculate_age(d["dob"])
    if age is None:
        return jsonify({"success": False, "msg": "Invalid DOB format. Use YYYY-MM-DD"}), 400
    
    # Apply age restriction (18-60 years)
    is_valid_age, age_error_msg = validate_age(age)
    if not is_valid_age:
        return jsonify({"success": False, "msg": age_error_msg}), 400
    pincode = str(d.get("pincode", "") or "").strip()
    lat = lon = None
    if pincode:
        if (len(pincode) != 6) or (not pincode.isdigit()):
            return jsonify({"success": False, "msg": "Invalid pincode"}), 400
        lat, lon = geocode_pincode(pincode, d.get("location"))

        if lat is None or lon is None:
            return jsonify({"success": False, "msg": "Enter valid pincode"}), 400

    if (lat is None or lon is None) and d.get("location"):
        lat, lon = geocode_address(d["location"])
        
    conn = client_db()
    cur = get_dict_cursor(conn)
    cur.execute("""
        INSERT INTO client_profile (client_id, name, phone, location, bio, pincode, latitude, longitude, dob)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(client_id) DO UPDATE SET
        phone=excluded.phone,
        location=excluded.location,
        bio=excluded.bio,
        pincode=excluded.pincode,
        latitude=excluded.latitude,
        longitude=excluded.longitude,
        dob=excluded.dob,
        name=excluded.name
    """, (d["client_id"], d["name"], d["phone"], d["location"], d["bio"], pincode, lat, lon, d["dob"]))
    conn.commit()
    conn.close()

    # Add notification (store in PostgreSQL)
    c2 = client_db()
    cur2 = get_dict_cursor(c2)
    cur2.execute("""
        INSERT INTO notification (client_id, message, created_at)
        VALUES (%s, %s, %s)
    """, (d["client_id"], "Profile updated successfully", now_ts()))
    c2.commit()
    c2.close()

    return jsonify({"success": True})

@app.route("/freelancer/profile", methods=["POST"])
def freelancer_profile():
    d = get_json()
    missing = require_fields(d, ["freelancer_id", "title", "skills", "years", "months", "min_budget", "max_budget", "bio", "category", "location", "dob"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    # Validate years and months
    try:
        years = int(d["years"])
        months = int(d["months"])
    except (ValueError, TypeError):
        return jsonify({"success": False, "msg": "Years and months must be integers"}), 400
    
    if years < 0 or years > 40:
        return jsonify({"success": False, "msg": "Years must be between 0 and 40"}), 400
    if months < 0 or months > 11:
        return jsonify({"success": False, "msg": "Months must be between 0 and 11"}), 400

    # Validate DOB format and calculate age
    age = calculate_age(d["dob"])
    if age is None:
        return jsonify({"success": False, "msg": "Invalid DOB format. Use YYYY-MM-DD"}), 400
    
    # Apply age restriction (18-60 years)
    is_valid_age, age_error_msg = validate_age(age)
    if not is_valid_age:
        return jsonify({"success": False, "msg": age_error_msg}), 400
    
    # Calculate total experience in years
    total_experience = years + (months / 12)
    
    # Validate experience against age (minimum working age is 18)
    max_experience = age - 18
    if total_experience > max_experience:
        return jsonify({"success": False, "msg": "Experience exceeds logical age limit"}), 400

    if not is_valid_category(d["category"]):
        return jsonify({"success": False, "msg": "Invalid category"}), 400

    # Validate availability_status if provided
    availability_status = d.get("availability_status", "AVAILABLE")
    allowed_statuses = ["AVAILABLE", "BUSY", "ON_LEAVE"]
    if availability_status not in allowed_statuses:
        return jsonify({"success": False, "msg": "Invalid availability status"}), 400

    # Optional location support for geocoding
    lat, lon = (None, None)
    pincode = str(d.get("pincode", "") or "").strip()
    if pincode:
        if (len(pincode) != 6) or (not pincode.isdigit()):
            return jsonify({"success": False, "msg": "Invalid pincode"}), 400
        lat, lon = geocode_pincode(pincode, d.get("location"))

        if lat is None or lon is None:
            return jsonify({"success": False, "msg": "Enter valid pincode"}), 400

    loc_str = d.get("location")
    if loc_str and (lat is None or lon is None):
        lat, lon = geocode_address(str(loc_str))

    freelancer_id = int(d["freelancer_id"])

    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute(
        """
        INSERT INTO freelancer_profile
        (freelancer_id, title, skills, experience, min_budget, max_budget, bio, category, location, pincode, latitude, longitude, dob, availability_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(freelancer_id) DO UPDATE SET
            title=excluded.title,
            skills=excluded.skills,
            experience=excluded.experience,
            min_budget=excluded.min_budget,
            max_budget=excluded.max_budget,
            bio=excluded.bio,
            category=excluded.category,
            location=excluded.location,
            pincode=excluded.pincode,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            dob=excluded.dob,
            availability_status=excluded.availability_status
        """,
        (
            freelancer_id,
            d["title"],
            d["skills"],
            total_experience,  # Store as decimal
            float(d["min_budget"]),
            float(d["max_budget"]),
            d["bio"],
            d["category"],
            d["location"],
            pincode,
            lat,
            lon,
            d["dob"],
            availability_status,
        ),
    )
    conn.commit()
    conn.close()

    # Rebuild FTS index for better keyword search
    rebuild_freelancer_search_index(freelancer_id)

    # Update semantic index (optional)
    try:
        upsert_freelancer(freelancer_id)
    except Exception:
        pass

    return jsonify({"success": True})

@app.route("/freelancer/update-availability", methods=["POST"])
def update_freelancer_availability():
    """Update freelancer availability status"""
    d = get_json()
    missing = require_fields(d, ["freelancer_id", "availability_status"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    # Validate availability status
    allowed_statuses = ["AVAILABLE", "BUSY", "ON_LEAVE"]
    if d["availability_status"] not in allowed_statuses:
        return jsonify({"success": False, "msg": "Invalid availability status"}), 400
    
    freelancer_id = int(d["freelancer_id"])
    availability_status = d["availability_status"]
    
    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    try:
        cur.execute("""
            UPDATE freelancer_profile 
            SET availability_status = %s
            WHERE freelancer_id = %s
        """, (availability_status, freelancer_id))
        conn.commit()
        
        if cur.rowcount == 0:
            return jsonify({"success": False, "msg": "Freelancer profile not found"}), 404
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": "Database error"}), 500
    finally:
        conn.close()

# ============================================================
# SEARCH (Category + Budget) + includes freelancer NAME
# ============================================================


# ============================================================
# SEARCH (Category + Budget) + specialization via FTS5 (q)
# ============================================================

@app.route("/freelancers/search", methods=["GET"])
def freelancers_search():
    category = (request.args.get("category", "") or "").strip().lower()
    q = (request.args.get("q", "") or "").strip().lower()

    try:
        budget = float(request.args.get("budget", 0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "msg": "Invalid budget"}), 400

    client_id = request.args.get("client_id")
    client_lat = client_lon = None

    if client_id:
        try:
            cid = int(client_id)
            cconn = client_db()
            ccur = get_dict_cursor(cconn)
            ccur.execute(
                "SELECT latitude, longitude FROM client_profile WHERE client_id=%s",
                (cid,),
            )
            row = ccur.fetchone()
            cconn.close()

            if row:
                client_lat, client_lon = row.get("latitude"), row.get("longitude")
        except Exception:
            client_lat = client_lon = None

    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)

        rows = []

        # ============================================
        # IF SPECIALIZATION QUERY EXISTS → USE PostgreSQL full-text search
        # ============================================
        if q:
            cond_verified = " AND COALESCE(fp.is_verified,0)=1" if FEATURE_HIDE_UNVERIFIED_FROM_SEARCH else ""
            tsvec = "to_tsvector('english', COALESCE(fs2.title,'') || ' ' || COALESCE(fs2.skills,'') || ' ' || COALESCE(fs2.bio,'') || ' ' || COALESCE(fs2.tags,'') || ' ' || COALESCE(fs2.portfolio_text,''))"
            tsq = "plainto_tsquery('english', %s)"

            try:
                sql = f"""
                    SELECT
                        fp.freelancer_id,
                        f.name,
                        fp.title,
                        fp.skills,
                        fp.experience,
                        fp.min_budget,
                        fp.max_budget,
                        fp.rating,
                        fp.category,
                        fp.latitude,
                        fp.longitude,
                        fp.availability_status,
                        COALESCE(fs.plan_name, 'BASIC') as subscription_plan,
                        ts_rank({tsvec}, {tsq}) as rank
                    FROM freelancer_search fs2
                    JOIN freelancer_profile fp ON fp.freelancer_id = fs2.freelancer_id
                    JOIN freelancer f ON f.id = fp.freelancer_id
                    LEFT JOIN freelancer_subscription fs ON fs.freelancer_id = fp.freelancer_id
                    WHERE {tsvec} @@ {tsq}
                      AND fp.min_budget <= %s
                      AND fp.max_budget >= %s{cond_verified}
                """
                cur.execute(sql, (q, q, budget, budget))
                rows = cur.fetchall()
            except Exception:
                rows = []

            # ============================================
            # FUZZY FALLBACK IF FTS RETURNS NOTHING
            # ============================================
            if not rows:
                cond_verified = " AND COALESCE(fp.is_verified,0)=1" if FEATURE_HIDE_UNVERIFIED_FROM_SEARCH else ""
                cur.execute(
                    f"""
                    SELECT
                        fp.freelancer_id,
                        f.name,
                        fp.title,
                        fp.skills,
                        fp.experience,
                        fp.min_budget,
                        fp.max_budget,
                        fp.rating,
                        fp.category,
                        fp.latitude,
                        fp.longitude,
                        fp.availability_status,
                        COALESCE(fs.plan_name, 'BASIC') as subscription_plan
                    FROM freelancer_profile fp
                    JOIN freelancer f
                        ON f.id = fp.freelancer_id
                    LEFT JOIN freelancer_subscription fs
                        ON fs.freelancer_id = fp.freelancer_id
                    WHERE fp.min_budget <= %s
                      AND fp.max_budget >= %s{cond_verified}
                    """,
                    (budget, budget),
                )

                candidates = cur.fetchall()
                scored = []

                for r in candidates:
                    combined = f"{r.get('title') or ''} {r.get('skills') or ''} {r.get('category') or ''}".lower()
                    score = fuzzy_score(q, combined)
                    scored.append((score, r))

                scored.sort(key=lambda x: x[0], reverse=True)
                scored = [x for x in scored if x[0] >= 60]

                # Add a fake 'rank' column - use dict with rank key for consistent formatting
                rows = []
                for _, r in scored[:20]:
                    rd = dict(r) if isinstance(r, dict) else {}
                    rd["rank"] = 999999.0
                    rows.append(rd)

            # ============================================
            # SEMANTIC FALLBACK (RAG-style retrieval)
            # ============================================
            if not rows:
                try:
                    sem_ids = semantic_search(q, top_k=30)
                    print("✅ SEMANTIC USED:", q, sem_ids[:10])
                except Exception:
                    sem_ids = []

                if sem_ids:
                    placeholders = ",".join(["%s"] * len(sem_ids))
                    cond_verified = " AND COALESCE(fp.is_verified,0)=1" if FEATURE_HIDE_UNVERIFIED_FROM_SEARCH else ""
                    cur.execute(
                        f"""
                        SELECT
                            fp.freelancer_id,
                            f.name,
                            fp.title,
                            fp.skills,
                            fp.experience,
                            fp.min_budget,
                            fp.max_budget,
                            fp.rating,
                            fp.category,
                            fp.latitude,
                            fp.longitude,
                            fp.availability_status,
                            COALESCE(fs.plan_name, 'BASIC') as subscription_plan,
                            999999.0 as rank
                        FROM freelancer_profile fp
                        JOIN freelancer f ON f.id = fp.freelancer_id
                        LEFT JOIN freelancer_subscription fs
                            ON fs.freelancer_id = fp.freelancer_id
                        WHERE fp.freelancer_id IN ({placeholders})
                          AND fp.min_budget <= %s
                          AND fp.max_budget >= %s{cond_verified}
                        """,
                        (*sem_ids, budget, budget),
                    )
                    rows = cur.fetchall()

        # ============================================
        # NO SPECIALIZATION → BUDGET ONLY SEARCH (with ILIKE for partial matches)
        # ============================================
        else:
            cond_verified = " AND COALESCE(fp.is_verified,0)=1" if FEATURE_HIDE_UNVERIFIED_FROM_SEARCH else ""
            params = [budget, budget]
            extra_where = ""
            if category:
                extra_where += " AND fp.category ILIKE %s"
                params.append(f"%{category}%")
            cur.execute(
                f"""
                SELECT
                    fp.freelancer_id,
                    f.name,
                    fp.title,
                    fp.skills,
                    fp.experience,
                    fp.min_budget,
                    fp.max_budget,
                    fp.rating,
                    fp.category,
                    fp.latitude,
                    fp.longitude,
                    fp.availability_status,
                    COALESCE(fs.plan_name, 'BASIC') as subscription_plan,
                    999999.0 as rank
                FROM freelancer_profile fp
                JOIN freelancer f
                    ON f.id = fp.freelancer_id
                LEFT JOIN freelancer_subscription fs
                    ON fs.freelancer_id = fp.freelancer_id
                WHERE fp.min_budget <= %s
                  AND fp.max_budget >= %s{cond_verified}{extra_where}
                """,
                tuple(params),
            )
            rows = cur.fetchall()

        conn.close()

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "msg": "DB error in /freelancers/search",
                "error": str(e),
            }
        ), 500

    # ============================================
    # FORMAT RESULTS
    # ============================================

    enriched = []

    for r in rows:
        # Support both dict (RealDictCursor) and tuple access
        def _v(r, key_or_idx, default=None):
            if isinstance(r, dict):
                return r.get(key_or_idx, default)
            try:
                return r[key_or_idx] if key_or_idx < len(r) else default
            except (TypeError, KeyError):
                return default
        _get = lambda k, d=None: _v(r, k, d)

        if category:
            cat_db = (str(_get("category", _get(8, ""))) or "").lower()
            if fuzzy_score(category, cat_db) < 70:
                continue

        spec = (q or "").strip().lower()
        if spec:
             spec_db = (str(_get("skills", _get(3, ""))) or "").strip().lower()
             if fuzzy_score(spec, spec_db) < 70:
               continue

        f_lat = _get("latitude", _get(9))
        f_lon = _get("longitude", _get(10))

        if client_lat and client_lon and f_lat and f_lon:
            dist = calculate_distance(
                client_lat, client_lon, f_lat, f_lon
            )
        else:
            dist = 999999.0

        # Apply rank boost based on subscription
        rank_boost = 0
        subscription_plan = _get("subscription_plan", _get(12))
        
        # Migrate old plans
        if subscription_plan == "FREE":
            subscription_plan = "BASIC"
        elif subscription_plan == "PRO":
            subscription_plan = "PREMIUM"
        
        if subscription_plan == "PREMIUM":
            rank_boost = 1
        
        # Adjust rank with boost
        base_rank = _get("rank", _get(13, 999999))
        adjusted_rank = (float(base_rank) if base_rank is not None else 999999) - (rank_boost * 100)  # Lower rank number = higher position
        
        # Add badge
        badge = None
        if subscription_plan == "PREMIUM":
            badge = "🟣 PREMIUM"
        
        enriched.append({
            "freelancer_id": _get("freelancer_id", _get(0)),
            "name": _get("name", _get(1)),
            "title": _get("title", _get(2)),
            "skills": _get("skills", _get(3)),
            "experience": _get("experience", _get(4)),
            "budget_range": f"{_get('min_budget', _get(5))} - {_get('max_budget', _get(6))}",
            "rating": _get("rating", _get(7)),
            "category": _get("category", _get(8)),
            "distance": round(dist, 2),
            "rank": adjusted_rank,
            "badge": badge,
            "subscription_plan": subscription_plan,
            "availability_status": _get("availability_status", _get(11))
        })
        
    # ============================================
    # GRID PRIORITY SYSTEM
    # ============================================
    
    # Split into premium and basic lists
    premium_list = []
    basic_list = []
    
    for item in enriched:
        if item["subscription_plan"] == "PREMIUM":
            premium_list.append(item)
        else:
            basic_list.append(item)
    
    # Sort both lists by rating DESC, then rank ASC, then distance ASC
    premium_list.sort(key=lambda x: (-x["rating"], x["rank"], x["distance"]))
    basic_list.sort(key=lambda x: (-x["rating"], x["rank"], x["distance"]))
    
    # Build final result list with grid priority
    final_list = []
    premium_idx = 0
    basic_idx = 0
    
    position = 1
    total_count = len(premium_list) + len(basic_list)
    
    while position <= total_count:
        if position % 3 == 0:  # Every 3rd position
            if premium_idx < len(premium_list):
                # Take highest rated premium
                final_list.append(premium_list[premium_idx])
                premium_idx += 1
            else:
                # No premium left, take from basic
                if basic_idx < len(basic_list):
                    final_list.append(basic_list[basic_idx])
                    basic_idx += 1
        else:
            # Take from basic if available, otherwise from premium
            if basic_idx < len(basic_list):
                final_list.append(basic_list[basic_idx])
                basic_idx += 1
            elif premium_idx < len(premium_list):
                final_list.append(premium_list[premium_idx])
                premium_idx += 1
        
        position += 1

    enriched = final_list

    for e in enriched:
        e.pop("rank", None)

    return jsonify({
        "success": True,
        "results": enriched
    })
# NEW: VIEW ALL FREELANCERS (even if client didn’t search)
# ============================================================

@app.route("/freelancers/all", methods=["GET"])
def freelancers_all():
    # NEW CODE: Add Row factory for safe column access
    conn = freelancer_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT
            f.id,
            f.name,
            COALESCE(fp.title, '') as title,
            COALESCE(fp.skills, '') as skills,
            COALESCE(fp.experience, 0) as experience,
            COALESCE(fp.min_budget, 0) as min_budget,
            COALESCE(fp.max_budget, 0) as max_budget,
            COALESCE(fp.rating, 0) as rating,
            COALESCE(fp.category, '') as category,
            COALESCE(fp.bio, '') as bio,
            COALESCE(fp.availability_status, 'AVAILABLE') as availability_status
        FROM freelancer f
        LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
        ORDER BY f.id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "freelancer_id": r["id"],
            "name": r["name"],
            "title": r["title"],
            "skills": r["skills"],
            "experience": r["experience"],
            "budget_range": f"{r['min_budget']} - {r['max_budget']}",
            "rating": r["rating"],
            "category": r["category"],
            "bio": r["bio"],
            "availability_status": r["availability_status"],
        })
    return jsonify({"success": True, "results": out})

@app.route("/freelancers/<int:freelancer_id>", methods=["GET"])
def freelancer_details(freelancer_id: int):
    # Use the enhanced get_freelancer_profile function that includes all new fields
    from database import get_freelancer_profile
    
    profile_data = get_freelancer_profile(freelancer_id)
    if not profile_data:
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404

    return jsonify({
        "success": True,
        "freelancer_id": profile_data["id"],
        "name": profile_data["name"],
        "email": profile_data["email"],
        "title": profile_data["title"],
        "skills": profile_data["skills"],
        "experience": profile_data["experience"],
        "experience_formatted": profile_data.get("experience_formatted"),
        "min_budget": profile_data["min_budget"],
        "max_budget": profile_data["max_budget"],
        "rating": profile_data["rating"],
        "category": profile_data["category"],
        "bio": profile_data["bio"],
        "projects_completed": profile_data.get("projects_completed"),
        "availability_status": profile_data.get("availability_status"),
        "profile_image": profile_data.get("profile_image"),
        "location": profile_data.get("location"),
        "pincode": profile_data.get("pincode"),
        "latitude": profile_data.get("latitude"),
        "longitude": profile_data.get("longitude"),
        "tags": profile_data.get("tags"),
    })

@app.route("/freelancers/filter", methods=["GET"])
def freelancers_filter():
    try:
        top_rated = request.args.get("top_rated")
        category = request.args.get("category")
        subscribed = request.args.get("subscribed")
        verified_only = request.args.get("verified_only")
        results = fetch_filtered_freelancers(top_rated, category, subscribed, verified_only)
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500
# ============================================================
# NEW: CHAT (Client <-> Freelancer)
# ============================================================

@app.route("/client/message/send", methods=["POST"])
def client_send_message():
    d = get_json()
    missing = require_fields(d, ["client_id", "freelancer_id", "text"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("""
        INSERT INTO message (sender_role, sender_id, receiver_id, text, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """, ("client", int(d["client_id"]), int(d["freelancer_id"]), str(d["text"]), now_ts()))

    # Add notification for client in client.db - get freelancer name
    cur.execute("SELECT name FROM freelancer WHERE id=%s", (int(d["freelancer_id"]),))
    freelancer_row = cur.fetchone()
    freelancer_name = (freelancer_row.get("name") if isinstance(freelancer_row, dict) else (freelancer_row[0] if freelancer_row else None)) or "Freelancer"
    
    cconn = client_db()
    ccur2 = get_dict_cursor(cconn)
    ccur2.execute("""
        INSERT INTO notification (client_id, message, created_at)
        VALUES (%s, %s, %s)
    """, (int(d["client_id"]), f"You messaged {freelancer_name}", now_ts()))
    cconn.commit()
    cconn.close()

    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route("/freelancer/message/send", methods=["POST"])
def freelancer_send_message():
    d = get_json()
    missing = require_fields(d, ["freelancer_id", "client_id", "text"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("""
        INSERT INTO message (sender_role, sender_id, receiver_id, text, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """, ("freelancer", int(d["freelancer_id"]), int(d["client_id"]), str(d["text"]), now_ts()))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route("/message/history", methods=["GET"])
def message_history():
    client_id = request.args.get("client_id")
    freelancer_id = request.args.get("freelancer_id")
    if not client_id or not freelancer_id:
        return jsonify({"success": False, "msg": "Missing ids"}), 400

    client_id = int(client_id)
    freelancer_id = int(freelancer_id)

    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT sender_role, sender_id, text, timestamp
        FROM message
        WHERE (sender_role='client' AND sender_id=%s AND receiver_id=%s)
           OR (sender_role='freelancer' AND sender_id=%s AND receiver_id=%s)
        ORDER BY timestamp
    """, (client_id, freelancer_id, freelancer_id, client_id))
    rows = cur.fetchall()
    conn.close()

    chat = []
    for r in rows:
        if isinstance(r, dict):
            chat.append({
                "sender_role": r.get("sender_role"),
                "sender_id": r.get("sender_id"),
                "text": r.get("text"),
                "timestamp": r.get("timestamp")
            })
        else:
            chat.append({"sender_role": r[0], "sender_id": r[1], "text": r[2], "timestamp": r[3]})
    return jsonify({"success": True, "messages": chat})

# ============================================================
# NEW: HIRE (Client -> Freelancer)
# ============================================================

@app.route("/client/hire", methods=["POST"])
def client_hire():
    d = get_json()
    missing = require_fields(d, ["client_id", "freelancer_id", "proposed_budget", "contract_type"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    client_id = int(d["client_id"])
    freelancer_id = int(d["freelancer_id"])
    proposed_budget = float(d["proposed_budget"])
    contract_type = str(d["contract_type"]).upper()
    note = str(d.get("note", "")).strip()
    
    # Extract and validate date/time slots
    event_date = d.get("event_date", "").strip()
    start_time = d.get("start_time", "").strip()
    end_time = d.get("end_time", "").strip()
    
    # Process venue data
    venue_choice = d.get("venue_source", "custom")  # Default to custom for backward compatibility
    custom_venue_data = {
        "event_address": d.get("event_address", "").strip(),
        "event_city": d.get("event_city", "").strip(),
        "event_pincode": d.get("event_pincode", "").strip(),
        "event_landmark": d.get("event_landmark", "").strip()
    } if venue_choice == "custom" else None
    
    # Prepare venue data
    venue_data, venue_error = prepare_venue_data(venue_choice, client_id, custom_venue_data)
    if venue_error:
        return jsonify({"success": False, "msg": venue_error}), 400
    
    # Validate venue data only for EVENT contracts
    if contract_type == "EVENT":
        is_valid, validation_error = validate_venue_data(venue_data)
        if not is_valid:
            return jsonify({"success": False, "msg": validation_error}), 400
    
    # Check location compatibility
    location_ok, location_note = check_venue_freelancer_compatibility(
        freelancer_id, 
        venue_data.get("event_pincode"), 
        venue_data.get("event_city")
    )
    
    # Validate date/time slot if provided
    if event_date or start_time or end_time:
        if not all([event_date, start_time, end_time]):
            return jsonify({"success": False, "msg": "All date/time fields (event_date, start_time, end_time) must be provided together"}), 400
        
        # Validate the time slot
        is_valid, error_msg = validate_hire_request_slot(
            freelancer_id, event_date, start_time, end_time
        )
        if not is_valid:
            return jsonify({"success": False, "msg": error_msg}), 400
    
    # Validate contract type
    if contract_type not in ["FIXED", "HOURLY", "EVENT"]:
        return jsonify({"success": False, "msg": "Invalid contract type. Use FIXED, HOURLY, or EVENT"}), 400

    # simple existence check
    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("SELECT id FROM freelancer WHERE id=%s", (freelancer_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    # Check freelancer availability status
    cur.execute("SELECT availability_status FROM freelancer_profile WHERE freelancer_id=%s", (freelancer_id,))
    availability_result = cur.fetchone()
    av = availability_result.get("availability_status") if isinstance(availability_result, dict) else (availability_result[0] if availability_result else None)
    if av == "ON_LEAVE":
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer is currently not accepting new projects"}), 403
    if FEATURE_ENFORCE_VERIFIED_FOR_HIRE_MESSAGE:
        try:
            cur.execute("SELECT COALESCE(is_verified,0) as is_verified FROM freelancer_profile WHERE freelancer_id=%s", (freelancer_id,))
            vr = cur.fetchone()
            vr_val = vr.get("is_verified", vr[0] if vr and not isinstance(vr, dict) else 0) if vr else 0
            if not vr or int(vr_val) != 1:
                conn.close()
                return jsonify({"success": False, "msg": "Freelancer not verified"}), 403
        except Exception:
            pass

    job_title = str(d.get("job_title", "")).strip()
    
    # Handle different contract types
    if contract_type == "FIXED":
        # Keep existing budget logic unchanged
        cur.execute("""
            INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, contract_type, created_at, event_date, start_time, end_time, event_address, event_city, event_pincode, event_landmark, venue_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (client_id, freelancer_id, job_title, proposed_budget, note, 'PENDING', contract_type, now_ts(), event_date, start_time, end_time, 
               venue_data.get("event_address"), venue_data.get("event_city"), venue_data.get("event_pincode"), 
               venue_data.get("event_landmark"), venue_data.get("venue_source")))
    elif contract_type == "HOURLY":
        # Require hourly rate field only
        if "contract_hourly_rate" not in d:
            return jsonify({"success": False, "msg": "HOURLY contracts require contract_hourly_rate"}), 400
        
        hourly_rate = float(d.get("contract_hourly_rate", 0))
        
        if hourly_rate <= 0:
            return jsonify({"success": False, "msg": "HOURLY contracts require positive hourly rate"}), 400
        
        cur.execute("""
            INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, contract_type, contract_hourly_rate, contract_overtime_rate, created_at, event_date, start_time, end_time, event_address, event_city, event_pincode, event_landmark, venue_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (client_id, freelancer_id, job_title, proposed_budget, note, 'PENDING', contract_type, hourly_rate, hourly_rate * 1.5, now_ts(), event_date, start_time, end_time,
               venue_data.get("event_address"), venue_data.get("event_city"), venue_data.get("event_pincode"), 
               venue_data.get("event_landmark"), venue_data.get("venue_source")))
    elif contract_type == "EVENT":
        # Require event fields
        required_event_fields = ["event_base_fee", "event_included_hours", "event_overtime_rate"]
        missing_event = [f for f in required_event_fields if f not in d]
        if missing_event:
            return jsonify({"success": False, "msg": f"EVENT contracts require: {', '.join(missing_event)}"}), 400
        
        event_base_fee = float(d.get("event_base_fee", 0))
        event_included_hours = float(d.get("event_included_hours", 0))
        event_overtime_rate = float(d.get("event_overtime_rate", 0))
        advance_paid = float(d.get("advance_paid", 0))
        
        if event_base_fee < 0 or event_included_hours < 0 or event_overtime_rate < 0 or advance_paid < 0:
            return jsonify({"success": False, "msg": "EVENT contracts require non-negative values"}), 400
        
        cur.execute("""
            INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, contract_type, event_base_fee, event_included_hours, event_overtime_rate, advance_paid, created_at, event_date, start_time, end_time, event_address, event_city, event_pincode, event_landmark, venue_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (client_id, freelancer_id, job_title, proposed_budget, note, 'PENDING', contract_type, event_base_fee, event_included_hours, event_overtime_rate, advance_paid, now_ts(), event_date, start_time, end_time,
               venue_data.get("event_address"), venue_data.get("event_city"), venue_data.get("event_pincode"), 
               venue_data.get("event_landmark"), venue_data.get("venue_source")))
    else:
        return jsonify({"success": False, "msg": "Invalid contract type"}), 400
    req_row = cur.fetchone()
    req_id = req_row["id"] if isinstance(req_row, dict) else req_row[0]

    # Add notification for client in client.db
    notification_msg = f'Job "{job_title if job_title else "Untitled"}" posted'
    cconn = client_db()
    ccur2 = get_dict_cursor(cconn)
    ccur2.execute("""
        INSERT INTO notification (client_id, message, created_at)
        VALUES (%s, %s, %s)
    """, (client_id, notification_msg, now_ts()))
    cconn.commit()
    cconn.close()

    conn.commit()
    conn.close()

    # Prepare response with venue and location info
    response_data = {
        "success": True, 
        "request_id": req_id,
        "venue": {
            "event_address": venue_data.get("event_address"),
            "event_city": venue_data.get("event_city"),
            "event_pincode": venue_data.get("event_pincode"),
            "event_landmark": venue_data.get("event_landmark"),
            "venue_source": venue_data.get("venue_source")
        },
        "location_check": {
            "location_ok": location_ok,
            "location_note": location_note
        }
    }

    return jsonify(response_data)

@app.route("/freelancer/hire/inbox", methods=["GET"])
def freelancer_hire_inbox():
    freelancer_id = request.args.get("freelancer_id")
    if not freelancer_id:
        return jsonify({"success": False, "msg": "Missing freelancer_id"}), 400
    freelancer_id = int(freelancer_id)

    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT id, client_id, proposed_budget, note, status, created_at, 
               contract_type, contract_hourly_rate, contract_overtime_rate, 
               weekly_limit, max_daily_hours, event_base_fee, event_included_hours, 
               event_overtime_rate, advance_paid
        FROM hire_request
        WHERE freelancer_id=%s
        ORDER BY created_at DESC
    """, (freelancer_id,))
    rows = cur.fetchall()
    conn.close()

    # fetch client names from client.db (separate db => done per client_id)
    client_conn = client_db()
    client_cur = get_dict_cursor(client_conn)

    out = []
    for r in rows:
        if isinstance(r, dict):
            cid = int(r.get("client_id"))
            rid = r.get("id")
            budget = r.get("proposed_budget")
            note = r.get("note")
            status = r.get("status")
            created_at = r.get("created_at")
            contract_type = r.get("contract_type")
            hourly = r.get("contract_hourly_rate")
            overtime = r.get("contract_overtime_rate")
            limit = r.get("weekly_limit")
            daily = r.get("max_daily_hours")
            base = r.get("event_base_fee")
            inc_hours = r.get("event_included_hours")
            e_overtime = r.get("event_overtime_rate")
            advance = r.get("advance_paid")
        else:
            cid = int(r[1])
            rid = r[0]
            budget = r[2]
            note = r[3]
            status = r[4]
            created_at = r[5]
            contract_type = r[6]
            hourly = r[7]
            overtime = r[8]
            limit = r[9]
            daily = r[10]
            base = r[11]
            inc_hours = r[12]
            e_overtime = r[13]
            advance = r[14]

        client_cur.execute("SELECT name, email FROM client WHERE id=%s", (cid,))
        c = client_cur.fetchone()
        if c:
            cname = c.get("name") if isinstance(c, dict) else c[0]
            cemail = c.get("email") if isinstance(c, dict) else c[1]
        else:
            cname = "Unknown"
            cemail = ""

        out.append({
            "request_id": rid,
            "client_id": cid,
            "client_name": cname,
            "client_email": cemail,
            "proposed_budget": budget,
            "note": note,
            "status": status,
            "created_at": created_at,
            "contract_type": contract_type,
            "contract_hourly_rate": hourly,
            "contract_overtime_rate": overtime,
            "weekly_limit": limit,
            "max_daily_hours": daily,
            "event_base_fee": base,
            "event_included_hours": inc_hours,
            "event_overtime_rate": e_overtime,
            "advance_paid": advance,
        })

    client_conn.close()
    return jsonify(out)

@app.route("/freelancer/hire/respond", methods=["POST"])
def freelancer_hire_respond():
    d = get_json()
    missing = require_fields(d, ["freelancer_id", "request_id", "action"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    freelancer_id = int(d["freelancer_id"])
    request_id = int(d["request_id"])
    action = str(d["action"]).strip().upper()

    if action not in ("ACCEPT", "REJECT"):
        return jsonify({"success": False, "msg": "action must be ACCEPT or REJECT"}), 400

    new_status = "ACCEPTED" if action == "ACCEPT" else "REJECTED"

    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("""
        UPDATE hire_request
        SET status=%s
        WHERE id=%s AND freelancer_id=%s
    """, (new_status, request_id, freelancer_id))

    if cur.rowcount == 0:
        conn.commit()
        conn.close()
        return jsonify({"success": False, "msg": "Request not found"}), 404

    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": new_status})

# ============================================================
# CLIENT – MESSAGE THREADS (list freelancers you chatted with)
# ============================================================

@app.route("/client/messages/threads", methods=["GET"])
def client_message_threads():
    client_id = request.args.get("client_id")
    if not client_id:
        return jsonify({"success": False, "msg": "client_id required"}), 400

    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid client_id"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT DISTINCT
                CASE
                    WHEN sender_role='client' THEN receiver_id
                    ELSE sender_id
                END AS freelancer_id
            FROM message
            WHERE (sender_role='client' AND sender_id=%s)
               OR (sender_role='freelancer' AND receiver_id=%s)
            ORDER BY freelancer_id DESC
        """, (client_id, client_id))
        all_rows = cur.fetchall()
        ids = []
        for r in all_rows:
            val = r.get("freelancer_id", r[0] if not isinstance(r, dict) else None) if r else None
            if val is not None:
                ids.append(int(val))

        if not ids:
            conn.close()
            return jsonify([])

        out = []
        for fid in ids:
            cur.execute("SELECT name, email FROM freelancer WHERE id=%s", (fid,))
            fr = cur.fetchone()
            if isinstance(fr, dict):
                out.append({"freelancer_id": fid, "name": fr.get("name") or "Freelancer", "email": fr.get("email") or ""})
            else:
                out.append({"freelancer_id": fid, "name": (fr[0] if fr else "Freelancer"), "email": (fr[1] if fr else "")})

        conn.close()
        return jsonify(out)
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# CLIENT – JOB REQUEST STATUS (detailed)
# ============================================================

@app.route("/client/job-requests", methods=["GET"])
def client_job_requests():
    client_id = request.args.get("client_id")
    if not client_id:
        return jsonify({"success": False, "msg": "client_id required"}), 400

    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid client_id"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT
                hr.id,
                hr.freelancer_id,
                f.name,
                f.email,
                hr.job_title,
                hr.proposed_budget,
                hr.note,
                hr.status,
                hr.created_at
            FROM hire_request hr
            JOIN freelancer f ON f.id = hr.freelancer_id
            WHERE hr.client_id=%s
            ORDER BY hr.created_at DESC
        """, (client_id,))
        rows = cur.fetchall()
        conn.close()

        out = []
        for r in rows:
            if isinstance(r, dict):
                out.append({
                    "request_id": r.get("id"),
                    "freelancer_id": r.get("freelancer_id"),
                    "freelancer_name": r.get("name"),
                    "freelancer_email": r.get("email"),
                    "job_title": r.get("job_title") or "",
                    "proposed_budget": r.get("proposed_budget"),
                    "note": r.get("note") or "",
                    "status": r.get("status"),
                    "created_at": r.get("created_at")
                })
            else:
                out.append({
                    "request_id": r[0], "freelancer_id": r[1], "freelancer_name": r[2], "freelancer_email": r[3],
                    "job_title": r[4] or "", "proposed_budget": r[5], "note": r[6] or "", "status": r[7], "created_at": r[8]
                })

        return jsonify(out)
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# CLIENT – VIEW MY JOBS
# ============================================================

@app.route("/client/jobs", methods=["GET"])
def client_jobs():
    client_id = request.args.get("client_id")
    if not client_id:
        return jsonify({"success": False, "msg": "client_id required"}), 400

    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid client_id"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, job_title, proposed_budget, status
            FROM hire_request
            WHERE client_id=%s
            ORDER BY created_at DESC
        """, (client_id,))
        rows = cur.fetchall()
        conn.close()

        result = []
        for r in rows:
            if isinstance(r, dict):
                st = r.get("status", "")
                result.append({
                    "id": r.get("id"),
                    "title": r.get("job_title") or "",
                    "budget": r.get("proposed_budget"),
                    "status": "open" if st == "PENDING" else str(st).lower()
                })
            else:
                st = r[3] if len(r) > 3 else r[2]
                result.append({
                    "id": r[0],
                    "title": r[1] or "",
                    "budget": r[2],
                    "status": "open" if st == "PENDING" else str(st).lower()
                })
        return jsonify(result)
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# CLIENT – SAVE FREELANCER
# ============================================================

@app.route("/client/save-freelancer", methods=["POST"])
def save_freelancer():
    d = request.get_json()
    missing = require_fields(d, ["client_id", "freelancer_id"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            INSERT INTO saved_freelancer (client_id, freelancer_id)
            VALUES (%s,%s)
            ON CONFLICT (client_id, freelancer_id) DO NOTHING
        """, (int(d["client_id"]), int(d["freelancer_id"])))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# CLIENT – VIEW SAVED FREELANCERS
# ============================================================

@app.route("/client/saved-freelancers", methods=["GET"])
def saved_freelancers():
    client_id = request.args.get("client_id")
    if not client_id:
        return jsonify({"success": False, "msg": "client_id required"}), 400

    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid client_id"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT f.id, f.name, fp.category
            FROM saved_freelancer s
            JOIN freelancer f ON f.id = s.freelancer_id
            LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
            WHERE s.client_id=%s
        """, (client_id,))
        rows = cur.fetchall()
        conn.close()

        result = []
        for r in rows:
            if isinstance(r, dict):
                result.append({"id": r.get("id"), "name": r.get("name"), "category": r.get("category") or ""})
            else:
                result.append({"id": r[0], "name": r[1], "category": (r[2] if len(r) > 2 else "") or ""})
        return jsonify(result)
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# CLIENT – SEND NOTIFICATION (for verification/test)
# ============================================================

@app.route("/client/send-notification", methods=["POST"])
def client_send_notification():
    """Create a notification for a client (used by CLI/verification)"""
    d = request.get_json() or {}
    client_id = d.get("client_id")
    message = d.get("message", "Notification")
    if not client_id:
        return jsonify({"success": False, "msg": "client_id required"}), 400
    try:
        client_id = int(client_id)
    except (ValueError, TypeError):
        return jsonify({"success": False, "msg": "Invalid client_id"}), 400
    try:
        conn = client_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            INSERT INTO notification (client_id, message, created_at)
            VALUES (%s, %s, %s)
        """, (client_id, str(message), now_ts()))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# CLIENT – NOTIFICATIONS
# ============================================================

@app.route("/client/notifications", methods=["GET"])
def client_notifications():
    client_id = request.args.get("client_id")
    if not client_id:
        return jsonify({"success": False, "msg": "client_id required"}), 400

    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid client_id"}), 400

    try:
        conn = client_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT message
            FROM notification
            WHERE client_id=%s
            ORDER BY created_at DESC
        """, (client_id,))
        rows = cur.fetchall()
        conn.close()

        result = []
        for r in rows:
            if isinstance(r, dict):
                result.append(r.get("message", ""))
            else:
                result.append(r[0] if r else "")
        return jsonify(result)
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# FREELANCER – STATS / EARNINGS & PERFORMANCE
# ============================================================

@app.route("/freelancer/stats", methods=["GET"])
def freelancer_stats():
    freelancer_id = request.args.get("freelancer_id")
    if not freelancer_id:
        return jsonify({"success": False, "msg": "freelancer_id required"}), 400

    try:
        freelancer_id = int(freelancer_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid freelancer_id"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)

        # Total earnings and completed jobs (ACCEPTED)
        cur.execute("""
            SELECT COUNT(*) as cnt, COALESCE(SUM(proposed_budget), 0) as total
            FROM hire_request
            WHERE freelancer_id=%s AND status='ACCEPTED'
        """, (freelancer_id,))
        row = cur.fetchone()
        if isinstance(row, dict):
            completed_jobs = int(row.get("cnt", 0) or 0)
            total_earnings = float(row.get("total", 0) or 0.0)
        else:
            completed_jobs = int(row[0] if row else 0)
            total_earnings = float(row[1] if row and len(row) > 1 else 0.0)

        # Total jobs for job success %
        cur.execute("""
            SELECT COUNT(*) as cnt
            FROM hire_request
            WHERE freelancer_id=%s
        """, (freelancer_id,))
        total_jobs_row = cur.fetchone()
        if isinstance(total_jobs_row, dict):
            total_jobs = int(total_jobs_row.get("cnt", 0) or 0)
        else:
            total_jobs = int(total_jobs_row[0] if total_jobs_row else 0)

        # Rating from profile
        cur.execute("""
            SELECT COALESCE(rating, 0) as rating
            FROM freelancer_profile
            WHERE freelancer_id=%s
        """, (freelancer_id,))
        rating_row = cur.fetchone()
        if isinstance(rating_row, dict):
            rating = float(rating_row.get("rating", 0) or 0.0)
        else:
            rating = float(rating_row[0] if rating_row else 0.0)

        job_success = 0.0
        if total_jobs > 0:
            job_success = round((completed_jobs / total_jobs) * 100.0, 2)

        conn.close()
        return jsonify({
            "success": True,
            "total_earnings": total_earnings,
            "completed_jobs": completed_jobs,
            "rating": rating,
            "job_success_percent": job_success
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# FREELANCER – SAVED CLIENTS
# ============================================================

@app.route("/freelancer/save-client", methods=["POST"])
def freelancer_save_client():
    d = get_json()
    missing = require_fields(d, ["freelancer_id", "client_id"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            INSERT INTO saved_client (freelancer_id, client_id)
            VALUES (%s, %s)
            ON CONFLICT (freelancer_id, client_id) DO NOTHING
        """, (int(d["freelancer_id"]), int(d["client_id"])))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500


@app.route("/freelancer/saved-clients", methods=["GET"])
def freelancer_saved_clients():
    freelancer_id = request.args.get("freelancer_id")
    if not freelancer_id:
        return jsonify({"success": False, "msg": "freelancer_id required"}), 400

    try:
        freelancer_id = int(freelancer_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid freelancer_id"}), 400

    conn = None
    client_conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT client_id
            FROM saved_client
            WHERE freelancer_id=%s
        """, (freelancer_id,))
        rows = cur.fetchall()
        conn.close()

        client_ids = []
        for r in rows:
            if isinstance(r, dict):
                val = r.get("client_id")
            else:
                val = r[0]
            if val is not None:
                client_ids.append(int(val))
        if not client_ids:
            return jsonify([])

        client_conn = client_db()
        client_cur = get_dict_cursor(client_conn)

        out = []
        for cid in client_ids:
            client_cur.execute("SELECT name, email FROM client WHERE id=%s", (cid,))
            c = client_cur.fetchone()
            if c:
                if isinstance(c, dict):
                    nm = c.get("name")
                    em = c.get("email")
                else:
                    nm = c[0]
                    em = c[1]
                out.append({"client_id": cid, "name": nm, "email": em})

        client_conn.close()
        return jsonify(out)
    except Exception as e:
        if client_conn:
            client_conn.close()
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# FREELANCER – ACCOUNT SETTINGS (EMAIL / PASSWORD)
# ============================================================

@app.route("/freelancer/change-password", methods=["POST"])
def freelancer_change_password():
    d = get_json()
    missing = require_fields(d, ["freelancer_id", "old_password", "new_password"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    freelancer_id = int(d["freelancer_id"])
    old_password = str(d["old_password"])
    new_password = str(d["new_password"])

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("SELECT password FROM freelancer WHERE id=%s", (freelancer_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "msg": "Freelancer not found"}), 404

        if not check_password_hash(row.get("password", row[0] if not isinstance(row, dict) else ""), old_password):
            conn.close()
            return jsonify({"success": False, "msg": "Old password incorrect"}), 400

        cur.execute(
            "UPDATE freelancer SET password=%s WHERE id=%s",
            (generate_password_hash(new_password), freelancer_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500


@app.route("/freelancer/update-email", methods=["POST"])
def freelancer_update_email():
    d = get_json()
    missing = require_fields(d, ["freelancer_id", "new_email"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    freelancer_id = int(d["freelancer_id"])
    new_email = str(d["new_email"]).strip().lower()

    if not valid_email(new_email):
        return jsonify({"success": False, "msg": "Invalid email"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute(
            "UPDATE freelancer SET email=%s WHERE id=%s",
            (new_email, freelancer_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except psycopg2.errors.UniqueViolation:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": "Email already in use"}), 409
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# FREELANCER – NOTIFICATIONS / ACTIVITY (derived)
# ============================================================

@app.route("/freelancer/notifications", methods=["GET"])
def freelancer_notifications():
    freelancer_id = request.args.get("freelancer_id")
    if not freelancer_id:
        return jsonify({"success": False, "msg": "freelancer_id required"}), 400

    try:
        freelancer_id = int(freelancer_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid freelancer_id"}), 400

    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)

        notifications = []

        # From hire requests
        cur.execute("""
            SELECT job_title, status, created_at
            FROM hire_request
            WHERE freelancer_id=%s
            ORDER BY created_at DESC
            LIMIT 20
        """, (freelancer_id,))
        for title, status, _created_at in cur.fetchall():
            job_title = title or "Untitled"
            notifications.append(f'Job "{job_title}" status: {status}')

        # From messages (client -> freelancer)
        cur.execute("""
            SELECT timestamp
            FROM message
            WHERE receiver_id=%s AND sender_role='client'
            ORDER BY timestamp DESC
            LIMIT 20
        """, (freelancer_id,))
        msg_rows = cur.fetchall()
        if msg_rows:
            notifications.append("Clients have recently sent you messages.")

        conn.close()
        return jsonify(notifications)
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "msg": str(e)}), 500

# ============================================================
# GOOGLE OAUTH ROUTES (ADDED)
# - DOES NOT TOUCH EXISTING LOGIN/SIGNUP/OTP
# ============================================================

@app.route("/auth/google/start", methods=["GET"])
def google_oauth_start():
    _google_state_cleanup()

    role = (request.args.get("role", "") or "").strip().lower()
    if role not in ("client", "freelancer"):
        return jsonify({"success": False, "msg": "role must be client or freelancer"}), 400

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({
            "success": False,
            "msg": "Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        }), 500

    state = secrets.token_urlsafe(24)

    GOOGLE_OAUTH_STATES[state] = {
        "role": role,
        "created_at": now_ts(),
        "done": False,
        "result": None
    }

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account"
    }

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return jsonify({"success": True, "auth_url": auth_url, "state": state})


@app.route("/auth/google/callback", methods=["GET"])
def google_oauth_callback():
    _google_state_cleanup()

    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state:
        return "Missing code/state", 400

    st = GOOGLE_OAUTH_STATES.get(state)
    if not st:
        return "Invalid or expired state. Please try again.", 400

    role = st["role"]

    # 1) Exchange code -> tokens
    token_res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        },
        timeout=15
    )

    if token_res.status_code != 200:
        st["done"] = True
        st["result"] = {"success": False, "msg": "Token exchange failed"}
        return "Google token exchange failed. You can close this tab.", 400

    token_data = token_res.json()
    id_token = token_data.get("id_token")
    if not id_token:
        st["done"] = True
        st["result"] = {"success": False, "msg": "No id_token returned"}
        return "Google did not return an ID token. You can close this tab.", 400

    # 2) Verify ID token using Google's tokeninfo endpoint (no extra libs needed)
    info_res = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": id_token},
        timeout=15
    )

    if info_res.status_code != 200:
        st["done"] = True
        st["result"] = {"success": False, "msg": "Token verification failed"}
        return "Google token verification failed. You can close this tab.", 400

    info = info_res.json()

    # Basic checks
    aud = info.get("aud")
    email = (info.get("email") or "").strip().lower()
    name = (info.get("name") or "").strip()
    sub = (info.get("sub") or "").strip()
    email_verified = str(info.get("email_verified", "")).lower()

    if aud != GOOGLE_CLIENT_ID:
        st["done"] = True
        st["result"] = {"success": False, "msg": "Invalid token audience"}
        return "Invalid Google token (audience). You can close this tab.", 400

    if not email or not sub:
        st["done"] = True
        st["result"] = {"success": False, "msg": "Email not available"}
        return "Google email not available. You can close this tab.", 400

    # optional strict check
    if email_verified and email_verified not in ("true", "1", "yes"):
        st["done"] = True
        st["result"] = {"success": False, "msg": "Email not verified"}
        return "Google email not verified. You can close this tab.", 400

    # 3) Upsert user into correct DB based on role
    if role == "client":
        conn = client_db()
        cur = get_dict_cursor(conn)

        cur.execute("SELECT id, password, auth_provider, google_sub FROM client WHERE email=%s", (email,))
        row = cur.fetchone()

        if row:
            client_id = row.get("id")
            pwd = row.get("password")
            provider = row.get("auth_provider") or "local"
            gsub = row.get("google_sub")
            if not provider:
                provider = "local"
            if not gsub:
                cur.execute("UPDATE client SET google_sub=%s WHERE id=%s", (sub, client_id))
            conn.commit()
            conn.close()

            st["done"] = True
            st["result"] = {"success": True, "role": "client", "client_id": client_id, "email": email}

            return f"""
            <h3>✅ Google Login Success (Client)</h3>
            <p>You can close this tab and return to the app.</p>
            """

        if not name:
            name = email.split("@")[0]

        # ✅ IMPORTANT FIX: store a random hashed password so existing login logic never crashes
        random_pwd_hash = generate_password_hash(secrets.token_urlsafe(32))

        cur.execute("""
            INSERT INTO client (name, email, password, auth_provider, google_sub)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING id
        """, (name, email, random_pwd_hash, "google", sub))
        row = cur.fetchone()
        client_id = row["id"] if isinstance(row, dict) else row[0]
        conn.commit()
        conn.close()

        st["done"] = True
        st["result"] = {"success": True, "role": "client", "client_id": client_id, "email": email}

        return f"""
        <h3>✅ Google Signup/Login Success (Client)</h3>
        <p>You can close this tab and return to the app.</p>
        """

    else:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)

        cur.execute("SELECT id, password, auth_provider, google_sub FROM freelancer WHERE email=%s", (email,))
        row = cur.fetchone()

        if row:
            freelancer_id = row.get("id")
            pwd = row.get("password")
            provider = row.get("auth_provider") or "local"
            gsub = row.get("google_sub")
            if not provider:
                provider = "local"
            if not gsub:
                cur.execute("UPDATE freelancer SET google_sub=%s WHERE id=%s", (sub, freelancer_id))
            conn.commit()
            conn.close()

            st["done"] = True
            st["result"] = {"success": True, "role": "freelancer", "freelancer_id": freelancer_id, "email": email}

            return f"""
            <h3>✅ Google Login Success (Freelancer)</h3>
            <p>You can close this tab and return to the app.</p>
            """

        if not name:
            name = email.split("@")[0]

        # ✅ IMPORTANT FIX: store a random hashed password so existing login logic never crashes
        random_pwd_hash = generate_password_hash(secrets.token_urlsafe(32))

        cur.execute("""
            INSERT INTO freelancer (name, email, password, auth_provider, google_sub)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING id
        """, (name, email, random_pwd_hash, "google", sub))
        row = cur.fetchone()
        freelancer_id = row["id"] if isinstance(row, dict) else row[0]
        conn.commit()
        conn.close()

        st["done"] = True
        st["result"] = {"success": True, "role": "freelancer", "freelancer_id": freelancer_id, "email": email}

        return f"""
        <h3>✅ Google Signup/Login Success (Freelancer)</h3>
        <p>You can close this tab and return to the app.</p>
        """


@app.route("/auth/google/status", methods=["GET"])
def google_oauth_status():
    _google_state_cleanup()

    state = request.args.get("state")
    if not state:
        return jsonify({"success": False, "msg": "state required"}), 400

    st = GOOGLE_OAUTH_STATES.get(state)
    if not st:
        return jsonify({"success": False, "msg": "invalid/expired state"}), 404

    if not st.get("done"):
        return jsonify({"success": True, "done": False})

    return jsonify({"success": True, "done": True, "result": st.get("result")})

# ============================================================
# NEW CODE: PROFILE PHOTO SUPPORT
# ============================================================

# Create uploads folder if it doesn't exist
UPLOADS_FOLDER = "uploads"
if not os.path.exists(UPLOADS_FOLDER):
    os.makedirs(UPLOADS_FOLDER)

def copy_image_to_uploads(image_path):
    """Copy image to uploads folder and return relative path"""
    # Strip quotes and whitespace from path
    image_path = str(image_path).strip().strip('"').strip("'")
    
    if not os.path.exists(image_path):
        print(f"DEBUG: File not found at path: {image_path}")
        return None
    
    filename = os.path.basename(image_path)
    # Generate unique filename to avoid conflicts
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{int(time.time())}{ext}"
    dest_path = os.path.join(UPLOADS_FOLDER, unique_filename)
    
    try:
        shutil.copy2(image_path, dest_path)
        print(f"DEBUG: Successfully copied file to: {dest_path}")
        return dest_path
    except Exception as e:
        print(f"DEBUG: Error copying file: {e}")
        return None

@app.route("/client/upload-photo", methods=["POST"])
def client_upload_photo():
    """NEW CODE: Upload profile photo for client"""
    d = get_json()
    missing = require_fields(d, ["client_id", "image_path"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    client_id = int(d["client_id"])
    image_path = str(d["image_path"]).strip()
    
    # Validate client exists
    conn = client_db()
    cur = get_dict_cursor(conn)
    cur.execute("SELECT id FROM client WHERE id=%s", (client_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Client not found"}), 404
    
    # Copy image to uploads
    uploaded_path = copy_image_to_uploads(image_path)
    if not uploaded_path:
        conn.close()
        return jsonify({"success": False, "msg": "Failed to upload image"}), 400
    
    # Update database
    cur.execute("UPDATE client SET profile_image=%s WHERE id=%s", (uploaded_path, client_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "image_path": uploaded_path})

@app.route("/freelancer/upload-photo", methods=["POST"])
def freelancer_upload_photo():
    """NEW CODE: Upload profile photo for freelancer"""
    d = get_json()
    missing = require_fields(d, ["freelancer_id", "image_path"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    freelancer_id = int(d["freelancer_id"])
    image_path = str(d["image_path"]).strip()
    
    # Validate freelancer exists
    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("SELECT id FROM freelancer WHERE id=%s", (freelancer_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    # Copy image to uploads
    uploaded_path = copy_image_to_uploads(image_path)
    if not uploaded_path:
        conn.close()
        return jsonify({"success": False, "msg": "Failed to upload image"}), 400
    
    # Update database
    cur.execute("UPDATE freelancer SET profile_image=%s WHERE id=%s", (uploaded_path, freelancer_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "image_path": uploaded_path})

@app.route("/client/profile/<int:client_id>", methods=["GET"])
def get_client_profile(client_id):
    """NEW CODE: Get client profile with photo"""
    conn = client_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT c.id, c.name, c.email, c.profile_image,
               cp.phone, cp.location, cp.bio
        FROM client c
        LEFT JOIN client_profile cp ON cp.client_id = c.id
        WHERE c.id = %s
    """, (client_id,))
    
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"success": False, "msg": "Client not found"}), 404
    
    return jsonify({
        "success": True,
        "client_id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "profile_image": row["profile_image"],
        "phone": row["phone"],
        "location": row["location"],
        "bio": row["bio"]
    })

@app.route("/freelancer/profile/<int:freelancer_id>", methods=["GET"])
def get_freelancer_profile(freelancer_id):
    """NEW CODE: Get freelancer profile with photo"""
    conn = freelancer_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT f.id, f.name, f.email, f.profile_image,
               fp.title, fp.skills, fp.experience, fp.min_budget, fp.max_budget,
               fp.rating, fp.category, fp.bio, fp.availability_status
        FROM freelancer f
        LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
        WHERE f.id = %s
    """, (freelancer_id,))
    
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    return jsonify({
        "success": True,
        "freelancer_id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "profile_image": row["profile_image"],
        "title": row["title"],
        "skills": row["skills"],
        "experience": row["experience"],
        "min_budget": row["min_budget"],
        "max_budget": row["max_budget"],
        "rating": row["rating"],
        "category": row["category"],
        "bio": row["bio"],
        "availability_status": row["availability_status"]
    })

# ============================================================
# NEW CODE: PORTFOLIO SYSTEM
# ============================================================

@app.route("/freelancer/portfolio/add", methods=["POST"])
def add_portfolio_item():
    """NEW CODE: Add portfolio item for freelancer"""
    d = get_json()
    # Always require freelancer_id, title, description
    base_missing = require_fields(d, ["freelancer_id", "title", "description"])
    if base_missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    media_type = (str(d.get("media_type") or "IMAGE")).strip().upper()
    if media_type not in ("IMAGE", "VIDEO", "DOC"):
        media_type = "IMAGE"
    # Validate media specific requirements
    if media_type == "IMAGE":
        missing = require_fields(d, ["image_path"])
        if missing:
            return jsonify({"success": False, "msg": "Missing fields"}), 400
    else:
        # VIDEO/DOC require media_url
        if not str(d.get("media_url") or "").strip():
            return jsonify({"success": False, "msg": "media_url required"}), 400
    
    freelancer_id = int(d["freelancer_id"])
    title = str(d["title"]).strip()
    description = str(d["description"]).strip()
    image_path = str(d.get("image_path") or "").strip()
    media_url = str(d.get("media_url") or "").strip() if media_type in ("VIDEO", "DOC") else None
    
    # Validate freelancer exists
    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    cur.execute("SELECT id FROM freelancer WHERE id=%s", (freelancer_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    image_binary = None
    if media_type == "IMAGE":
        # Read image file as binary data instead of copying to uploads folder
        try:
            with open(image_path, "rb") as f:
                image_binary = f.read()
        except Exception as e:
            conn.close()
            return jsonify({"success": False, "msg": f"Failed to read image file: {str(e)}"}), 400
    else:
        image_path = ""  # not required for link types
    # Insert portfolio item with media columns
    cur.execute("""
        INSERT INTO portfolio (freelancer_id, title, description, image_path, image_data, created_at, media_type, media_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (freelancer_id, title, description, image_path, image_binary, now_ts(), media_type, media_url))
    
    portfolio_id = cur.lastrowid
    conn.commit()
    conn.close()
    rebuild_freelancer_search_index(freelancer_id)
    return jsonify({"success": True, "portfolio_id": portfolio_id})

@app.route("/freelancer/portfolio/<int:freelancer_id>", methods=["GET"])
def get_freelancer_portfolio(freelancer_id):
    """NEW CODE: Get all portfolio items for a freelancer"""
    conn = freelancer_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT id, title, description, image_path, image_data, created_at, media_type, media_url
        FROM portfolio
        WHERE freelancer_id = %s
        ORDER BY created_at DESC
    """, (freelancer_id,))
    
    rows = cur.fetchall()
    conn.close()
    
    import base64
    
    portfolio_items = []
    for row in rows:
        item_data = {
            "portfolio_id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "created_at": row["created_at"],
            "media_type": row["media_type"] if "media_type" in row.keys() else "IMAGE",
            "media_url": row["media_url"] if "media_url" in row.keys() else None
        }
        
        # Return image as Base64 if BLOB data exists, otherwise fallback to image_path
        if row["image_data"] is not None:
            encoded_image = base64.b64encode(row["image_data"]).decode("utf-8")
            item_data["image_base64"] = encoded_image
        else:
            item_data["image_path"] = row["image_path"]
        
        portfolio_items.append(item_data)
    
    return jsonify({"success": True, "portfolio_items": portfolio_items})

# ============================================================
# ===== NEW: AI Recommendation Engine =====
# ============================================================

def calculate_recommendation_score(freelancer_data, target_category, target_budget):
    """
    Calculate recommendation score for a freelancer based on:
    - Category match (+20 points)
    - Budget match (+20 points)  
    - Rating weight (rating * 10)
    - Experience weight (experience * 2)
    - Job success percentage (success_percentage * 0.3)
    """
    score = 0
    
    # Category match (+20 points)
    if freelancer_data.get("category") and freelancer_data["category"].lower() == target_category.lower():
        score += 20
    
    # Budget match (+20 points if client budget within freelancer range)
    min_budget = freelancer_data.get("min_budget", 0)
    max_budget = freelancer_data.get("max_budget", float('inf'))
    if min_budget <= target_budget <= max_budget:
        score += 20
    
    # Rating weight (rating * 10)
    rating = freelancer_data.get("rating", 0)
    score += rating * 10
    
    # Experience weight (experience * 2)
    experience = freelancer_data.get("experience", 0)
    score += experience * 2
    
    # Job success percentage (success_percentage * 0.3)
    total_projects = freelancer_data.get("total_projects", 0)
    completed_jobs = freelancer_data.get("completed_jobs", 0)
    
    if total_projects > 0:
        success_percentage = (completed_jobs / total_projects) * 100
        score += success_percentage * 0.3
    
    return round(score, 2)

@app.route("/freelancers/recommend", methods=["POST"])
def recommend_freelancers():
    """NEW CODE: AI-powered freelancer recommendation engine"""
    d = get_json()
    missing = require_fields(d, ["category", "budget"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    target_category = str(d["category"]).strip()
    target_budget = float(d["budget"])
    
    # Fetch all freelancers with profile data
    conn = freelancer_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT
            f.id,
            f.name,
            fp.title,
            fp.skills,
            fp.experience,
            fp.min_budget,
            fp.max_budget,
            fp.rating,
            fp.total_projects,
            fp.category,
            fp.bio
        FROM freelancer f
        LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
        WHERE fp.freelancer_id IS NOT NULL
        ORDER BY f.id DESC
    """)
    
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        return jsonify([])
    
    # Calculate scores for all freelancers
    scored_freelancers = []
    for row in rows:
        freelancer_data = dict(row)
        
        # Get completed jobs from stats (simulate calculation)
        # For now, we'll estimate completed jobs as 80% of total projects
        total_projects = freelancer_data.get("total_projects", 0)
        completed_jobs = int(total_projects * 0.8) if total_projects > 0 else 0
        freelancer_data["completed_jobs"] = completed_jobs
        
        # Calculate recommendation score
        score = calculate_recommendation_score(freelancer_data, target_category, target_budget)
        
        scored_freelancers.append({
            "freelancer_id": freelancer_data["id"],
            "name": freelancer_data["name"],
            "category": freelancer_data["category"] or "",
            "rating": freelancer_data["rating"] or 0,
            "experience": freelancer_data["experience"] or 0,
            "budget_range": f"{freelancer_data.get('min_budget', 0)} - {freelancer_data.get('max_budget', 0)}",
            "match_score": score
        })
    
    # Sort by score descending and return top 5
    scored_freelancers.sort(key=lambda x: x["match_score"], reverse=True)
    top_recommendations = scored_freelancers[:5]
    
    return jsonify(top_recommendations)

# ============================================================
# ============================================================
# CALL ROUTES (Voice/Video Calls) - UPDATED VERSION
# ============================================================

# ============================================================
# RUN
# ============================================================

@app.route("/ai/health", methods=["GET"])
def ai_health():
    try:
        res = generate_ai_response(0, "__health__", "__ping__")
        health = res.get("health") or {}
        status_code = 200 if health.get("ollama") == "ok" else 503
        return jsonify(health), status_code
    except Exception:
        return jsonify({"ollama": "down", "model": ""}), 503

@app.route("/ai/chat", methods=["POST"])
def ai_chat():
    d = request.get_json() or {}
    if not all(k in d for k in ("user_id", "role", "message")):
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    try:
        user_id = int(d["user_id"])
    except Exception:
        return jsonify({"success": False, "msg": "user_id must be int"}), 400
    role = str(d["role"]).strip().lower()
    if role not in ("client", "freelancer"):
        return jsonify({"success": False, "msg": "role must be client or freelancer"}), 400
    message = str(d["message"]).strip()
    if not message:
        return jsonify({"success": False, "msg": "message required"}), 400
    if role == "client":
        from database import get_client_profile
        if not get_client_profile(user_id):
            return jsonify({"success": False, "msg": "Client not found"}), 404
    else:
        from database import get_freelancer_profile
        if not get_freelancer_profile(user_id):
            return jsonify({"success": False, "msg": "Freelancer not found"}), 404

    # Check pending action confirmation
    if user_id in PENDING_ACTIONS:
        user_reply = message.strip().lower()
        if user_reply in ["yes", "confirm"]:
            action_data = PENDING_ACTIONS.pop(user_id)
            exec_res = execute_agent_action(user_id, role, action_data.get("action", ""), action_data.get("parameters") or {})
            return jsonify({
                "success": True,
                "mode": "action",
                "result": exec_res
            })
        elif user_reply in ["no", "cancel"]:
            PENDING_ACTIONS.pop(user_id, None)
            return jsonify({
                "success": True,
                "mode": "answer",
                "answer": "Action cancelled."
            })

    # NEW: Try natural language query parsing first
    from query_parser import parse_query
    parsed_filters = parse_query(message)
    
    if parsed_filters:
        # Use existing freelancer search logic with parsed filters
        try:
            # Build search parameters from parsed filters
            search_params = {}
            
            if 'category' in parsed_filters:
                search_params['category'] = parsed_filters['category']
            
            # Use max_budget for the budget parameter
            if 'max_budget' in parsed_filters:
                search_params['budget'] = parsed_filters['max_budget']
            elif 'min_budget' in parsed_filters:
                search_params['budget'] = parsed_filters['min_budget']
            else:
                search_params['budget'] = 0  # Default budget
            
            # Use location as specialization query for better matching
            if 'location' in parsed_filters:
                search_params['q'] = parsed_filters['location']
            
            # Add tags to query if present
            if 'tags' in parsed_filters and parsed_filters['tags']:
                tag_query = ' '.join(parsed_filters['tags'])
                if 'q' in search_params:
                    search_params['q'] += ' ' + tag_query
                else:
                    search_params['q'] = tag_query
            
            # Call existing search logic
            conn = freelancer_db()
            from psycopg2.extras import RealDictCursor
            cur = get_dict_cursor(conn)
            
            rows = []
            q = search_params.get('q', '')
            budget = search_params.get('budget', 0)
            category = search_params.get('category', '')
            
            # Use similar logic as /freelancers/search endpoint
            if q:
                # PostgreSQL full-text search
                tokens = [t.strip() for t in q.split() if t.strip()]
                fts_query = " ".join([t + "*" for t in tokens]) if tokens else ""
                
                if fts_query:
                    cond_verified = " AND COALESCE(fp.is_verified,0)=1" if FEATURE_HIDE_UNVERIFIED_FROM_SEARCH else ""
                    sql = f"""
                        SELECT
                            fp.freelancer_id,
                            f.name,
                            fp.title,
                            fp.skills,
                            fp.experience,
                            fp.min_budget,
                            fp.max_budget,
                            fp.rating,
                            fp.category,
                            fp.latitude,
                            fp.longitude,
                            COALESCE(fs.plan_name, 'BASIC') as subscription_plan,
                            ts_rank(to_tsvector('english', freelancer_search.title || ' ' || freelancer_search.skills || ' ' || freelancer_search.bio || ' ' || freelancer_search.tags || ' ' || freelancer_search.portfolio_text), plainto_tsquery('english', ?)) as rank
                        FROM freelancer_search
                        JOIN freelancer_profile fp
                            ON fp.freelancer_id = freelancer_search.freelancer_id
                        JOIN freelancer f
                            ON f.id = fp.freelancer_id
                        LEFT JOIN freelancer_subscription fs
                            ON fs.freelancer_id = fp.freelancer_id
                        WHERE to_tsvector('english', freelancer_search.title || ' ' || freelancer_search.skills || ' ' || freelancer_search.bio || ' ' || freelancer_search.tags || ' ' || freelancer_search.portfolio_text) @@ plainto_tsquery('english', %s)
                          AND fp.min_budget <= %s
                          AND fp.max_budget >= %s{cond_verified}
                    """
                    if category:
                        sql += " AND LOWER(fp.category) = LOWER(%s)"
                        cur.execute(sql, (fts_query, fts_query, budget, budget, category))
                    else:
                        cur.execute(sql, (fts_query, fts_query, budget, budget))
                    rows = cur.fetchall()
            
            # Fallback to category/budget search if no results
            if not rows:
                cond_verified = " AND COALESCE(fp.is_verified,0)=1" if FEATURE_HIDE_UNVERIFIED_FROM_SEARCH else ""
                sql = f"""
                    SELECT
                        fp.freelancer_id,
                        f.name,
                        fp.title,
                        fp.skills,
                        fp.experience,
                        fp.min_budget,
                        fp.max_budget,
                        fp.rating,
                        fp.category,
                        fp.latitude,
                        fp.longitude,
                        COALESCE(fs.plan_name, 'BASIC') as subscription_plan,
                        999999.0 as rank
                    FROM freelancer_profile fp
                    JOIN freelancer f
                        ON f.id = fp.freelancer_id
                    LEFT JOIN freelancer_subscription fs
                        ON fs.freelancer_id = fp.freelancer_id
                    WHERE fp.min_budget <= %s
                      AND fp.max_budget >= %s{cond_verified}
                """
                params = [budget, budget]
                if category:
                    sql += " AND LOWER(fp.category) = LOWER(%s)"
                    params.append(category)
                
                cur.execute(sql, params)
                rows = cur.fetchall()
            
            conn.close()
            
            # Format results for chatbot response
            if rows:
                # Calculate distances if location was specified
                location_specified = 'location' in parsed_filters
                formatted_results = []
                
                for i, row in enumerate(rows[:5], 1):  # Limit to top 5 results
                    freelancer_data = dict(row)
                    
                    # Calculate distance if location specified and we have coordinates
                    distance_text = ""
                    if location_specified and freelancer_data.get('latitude') and freelancer_data.get('longitude'):
                        # For now, just show location info
                        distance_text = f"Location: {freelancer_data.get('category', 'Unknown')}\n"
                    
                    result_text = f"{i}. {freelancer_data['name']}"
                    if freelancer_data.get('title'):
                        result_text += f" — {freelancer_data['title']}"
                    result_text += f"\nRating: {freelancer_data.get('rating', 0)}"
                    
                    if freelancer_data.get('min_budget') or freelancer_data.get('max_budget'):
                        result_text += f"\nBudget: ₹{freelancer_data.get('min_budget', 0)}-₹{freelancer_data.get('max_budget', 0)}"
                    
                    if freelancer_data.get('category'):
                        result_text += f"\nCategory: {freelancer_data['category']}"
                    
                    if distance_text:
                        result_text += f"\n{distance_text}"
                    
                    formatted_results.append(result_text)
                
                # Create response header based on filters
                header = "Top matching freelancers"
                if 'category' in parsed_filters:
                    header += f" in {parsed_filters['category']}"
                if 'location' in parsed_filters:
                    header += f" near {parsed_filters['location'].title()}"
                header += ":\n\n"
                
                response_text = header + "\n\n".join(formatted_results)
                
                return jsonify({
                    "success": True,
                    "mode": "answer",
                    "answer": response_text,
                    "sources": ["query_parser", "database"]
                })
            else:
                return jsonify({
                    "success": True,
                    "mode": "answer", 
                    "answer": "No freelancers found matching your query.",
                    "sources": ["query_parser", "database"]
                })
                
        except Exception as e:
            print(f"Error in query parsing search: {e}")
            # Fall through to existing chatbot logic on error
    
    result = generate_ai_response(user_id, role, message)
    
    # If the AI system already executed an action, return the result
    if isinstance(result, dict) and result.get("type") == "action":
        # This means the AI system returned an action that needs to be executed
        action = str(result.get("action") or "").strip()
        params = result.get("parameters") or {}
        requires_confirmation = action in {"hire_freelancer", "accept_request", "reject_request", "send_message"}
        if requires_confirmation:
            PENDING_ACTIONS[user_id] = {
                "action": action,
                "parameters": params
            }
            confirm_msg = "You are about to perform an action. Confirm? (yes/no)"
            if action == "hire_freelancer":
                fname = params.get("name", "Unknown")
                confirm_msg = f"You are about to hire {fname}. Confirm? (yes/no)"
            elif action == "accept_request":
                rid = params.get("request_id")
                confirm_msg = f"You are about to accept Request ID {rid}. Confirm? (yes/no)"
            elif action == "reject_request":
                rid = params.get("request_id")
                confirm_msg = f"You are about to reject Request ID {rid}. Confirm? (yes/no)"
            elif action == "send_message":
                if role == "client":
                    fid = params.get("freelancer_id")
                    confirm_msg = f"You are about to send a message to Freelancer ID {fid}. Confirm? (yes/no)"
                else:
                    cid = params.get("client_id")
                    confirm_msg = f"You are about to send a message to Client ID {cid}. Confirm? (yes/no)"
            return jsonify({
                "success": True,
                "mode": "answer",
                "answer": confirm_msg
            })
        else:
            # Execute action immediately without confirmation
            exec_res = execute_agent_action(user_id, role, action, params)
            return jsonify({
                "success": True,
                "mode": "action",
                "result": exec_res,
                "answer": ""
            })
    else:
        # This is already an answer response (either from AI system or from executed action)
        text = str(result.get("text", ""))
        return jsonify({
            "success": True,
            "mode": "answer",
            "answer": text,
            "sources": result.get("sources", ["kb"])
        })


# ============================================================
# FREELANCER VERIFICATION
# ============================================================

@app.route("/freelancer/verification/upload", methods=["POST"])
def freelancer_verification_upload():
    """Upload verification documents for freelancer"""
    data = request.get_json() or {}
    freelancer_id = data.get("freelancer_id")
    government_id_path = data.get("government_id_path")
    pan_card_path = data.get("pan_card_path")
    artist_proof_path = data.get("artist_proof_path")  # Optional
    
    if not all([freelancer_id, government_id_path, pan_card_path]):
        return jsonify({"success": False, "msg": "Missing required fields: freelancer_id, government_id_path, pan_card_path"}), 400
    
    # Validate freelancer exists
    from database import get_freelancer_profile
    if not get_freelancer_profile(freelancer_id):
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    # Validate file extensions
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
    
    def validate_file_path(file_path):
        if not file_path:
            return True  # Optional file
        ext = os.path.splitext(file_path)[1].lower()
        return ext in allowed_extensions
    
    if not validate_file_path(government_id_path):
        return jsonify({"success": False, "msg": "Invalid government ID file type. Allowed: PDF, JPG, PNG"}), 400
    
    if not validate_file_path(pan_card_path):
        return jsonify({"success": False, "msg": "Invalid PAN card file type. Allowed: PDF, JPG, PNG"}), 400
    
    if artist_proof_path and not validate_file_path(artist_proof_path):
        return jsonify({"success": False, "msg": "Invalid artist proof file type. Allowed: PDF, JPG, PNG"}), 400
    
    # Create upload directory if not exists
    upload_dir = f"uploads/verification/{freelancer_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Update verification record
    success = update_freelancer_verification(
        freelancer_id, 
        government_id_path, 
        pan_card_path, 
        artist_proof_path
    )
    
    if success:
        return jsonify({
            "success": True, 
            "msg": "Documents submitted successfully. Status: PENDING"
        })
    else:
        return jsonify({
            "success": False, 
            "msg": "Failed to save verification documents"
        }), 500


@app.route("/freelancer/verification/status", methods=["GET"])
def freelancer_verification_status():
    """Get verification status for freelancer"""
    freelancer_id = request.args.get("freelancer_id")
    
    if not freelancer_id:
        return jsonify({"success": False, "msg": "freelancer_id required"}), 400
    
    # Validate freelancer exists
    from database import get_freelancer_profile
    if not get_freelancer_profile(freelancer_id):
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    verification = get_freelancer_verification(freelancer_id)
    
    if not verification:
        return jsonify({
            "success": True,
            "status": None,
            "submitted_at": None,
            "rejection_reason": None,
            "msg": "Verification not submitted yet"
        })
    
    return jsonify({
        "success": True,
        "status": verification["status"],
        "submitted_at": verification["submitted_at"],
        "rejection_reason": verification["rejection_reason"]
    })


# ============================================================
# FREELANCER SUBSCRIPTION
# ============================================================

@app.route("/freelancer/subscription/plans", methods=["GET"])
def freelancer_subscription_plans():
    """Get available subscription plans"""
    return jsonify({
        "success": True,
        "plans": {
            "BASIC": {
                "name": "BASIC",
                "price": 0,
                "portfolio_limit": 5,
                "job_applies_limit": 10,
                "rank_boost": 0,
                "badge": None,
                "features": [
                    "5 Portfolio Projects",
                    "10 Job Applies per Month",
                    "Standard Search Visibility",
                    "Full Messaging Access"
                ]
            },
            "PREMIUM": {
                "name": "PREMIUM",
                "price": 699,
                "portfolio_limit": float('inf'),
                "job_applies_limit": float('inf'),
                "rank_boost": 1,
                "badge": "🔵 PREMIUM",
                "features": [
                    "Unlimited Portfolio",
                    "Unlimited Job Applies",
                    "Moderate Rank Boost",
                    "PREMIUM Badge",
                    "Highlight 3 Projects",
                    "Featured Grid Priority Placement",
                    "Basic Analytics",
                    "Early Job Alerts"
                ]
            }
        }
    })


@app.route("/freelancer/subscription/upgrade", methods=["POST"])
def freelancer_subscription_upgrade():
    """Upgrade freelancer subscription"""
    data = request.get_json() or {}
    freelancer_id = data.get("freelancer_id")
    plan_name = data.get("plan_name")
    
    if not all([freelancer_id, plan_name]):
        return jsonify({"success": False, "msg": "Missing fields: freelancer_id, plan_name"}), 400
    
    if plan_name != "PREMIUM":
        return jsonify({"success": False, "msg": "Only PREMIUM plan is available for upgrade"}), 400
    
    # Validate freelancer exists
    from database import get_freelancer_profile
    if not get_freelancer_profile(freelancer_id):
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    # Simulate payment (always succeed for now)
    success = update_freelancer_subscription(freelancer_id, plan_name, 30)
    
    if success:
        import time
        end_date = int(time.time()) + (30 * 24 * 60 * 60)
        from datetime import datetime
        expiry_date = datetime.fromtimestamp(end_date)
        
        # Add notification for subscription upgrade
        try:
            conn = freelancer_db()
            cur = get_dict_cursor(conn)
            cur.execute("""
                INSERT INTO notification (freelancer_id, message, created_at)
                VALUES (%s, %s, %s)
            """, (freelancer_id, f"Successfully upgraded to {plan_name}! Active until {expiry_date.strftime('%Y-%m-%d')}", int(time.time())))
            conn.commit()
            conn.close()
        except:
            pass  # Don't fail the upgrade if notification fails
        
        return jsonify({
            "success": True,
            "msg": f"Successfully upgraded to {plan_name}!",
            "plan_name": plan_name,
            "active_until": expiry_date.strftime("%Y-%m-%d")
        })
    else:
        return jsonify({
            "success": False,
            "msg": "Failed to upgrade subscription"
        }), 500


@app.route("/freelancer/subscription/status", methods=["GET"])
def freelancer_subscription_status():
    """Get freelancer subscription status"""
    freelancer_id = request.args.get("freelancer_id")
    if not freelancer_id:
        return jsonify({"success": False, "msg": "Missing freelancer_id"}), 400
    
    try:
        freelancer_id = int(freelancer_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid freelancer_id"}), 400
    
    # Get subscription info
    from database import get_freelancer_subscription, get_freelancer_job_applies, get_freelancer_plan
    
    subscription = get_freelancer_subscription(freelancer_id)
    job_applies = get_freelancer_job_applies(freelancer_id)
    
    # Get current plan (fallback to profile if subscription table is empty)
    current_plan = "BASIC"
    if subscription:
        current_plan = subscription.get("plan_name", "BASIC")
    else:
        # Fallback to profile table
        profile_plan = get_freelancer_plan(freelancer_id)
        if profile_plan:
            current_plan = profile_plan
    
    return jsonify({
        "success": True,
        "subscription": subscription or {"plan_name": "BASIC"},
        "job_applies": job_applies or {"applies_used": 0, "limit": 10, "current_plan": current_plan}
    })


# ============================================================
# PROJECT POSTING (Optional Hiring Flow)
# ============================================================

@app.route("/client/projects/create", methods=["POST"])
def client_projects_create():
    d = get_json()
    missing = require_fields(d, ["client_id", "title", "description", "category", "skills", "budget_type"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    try:
        client_id = int(d["client_id"])
        title = str(d["title"]).strip()
        description = str(d["description"]).strip()
        category = str(d["category"]).strip()
        skills = str(d["skills"]).strip()
        budget_type = str(d["budget_type"]).strip().upper()
        
        # Validate budget type - only FIXED or HOURLY allowed
        if budget_type not in ("FIXED", "HOURLY"):
            return jsonify({"success": False, "msg": "Invalid budget_type. Use FIXED or HOURLY"}), 400
        
        # Get single budget value based on type
        if budget_type == "FIXED":
            budget_value = float(d.get("budget", 0))
        elif budget_type == "HOURLY":
            budget_value = float(d.get("hourly_rate", 0))
        else:
            return jsonify({"success": False, "msg": "Invalid budget_type"}), 400
        
        if budget_value <= 0:
            return jsonify({"success": False, "msg": "Budget must be greater than 0"}), 400
    
    except Exception:
        return jsonify({"success": False, "msg": "Invalid payload"}), 400
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        # PostgreSQL syntax with RETURNING id and default status 'pending'
        cur.execute("""
            INSERT INTO project_post (client_id, title, description, category, skills, budget_type, budget_min, budget_max, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'OPEN', %s) RETURNING id
        """, (client_id, title, description, category, skills, budget_type, budget_value, budget_value, now_ts()))

        proj_row = cur.fetchone()
        project_id = proj_row["id"] if isinstance(proj_row, dict) else proj_row[0]
        conn.commit()

        # Enhanced response with status and next actions
        return jsonify({
            "success": True,
            "msg": "Project posted successfully",
            "project_id": project_id,
            "status": "pending",
            "budget_type": budget_type,
            "budget_value": budget_value,
            "next_actions": [
                "view_profile",
                "edit_profile"
            ]
        })
        
    except psycopg2.Error as e:
        print(f"Database error in project creation: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error in project creation: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500
    finally:
        conn.close()


@app.route("/client/projects", methods=["GET"])
def client_projects_list():
    client_id = request.args.get("client_id", "")
    try:
        cid = int(client_id)
    except Exception:
        return jsonify({"success": False, "msg": "client_id required"}), 400
    conn = freelancer_db()
    from psycopg2.extras import RealDictCursor
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, title, description, category, skills, budget_type, budget_min, budget_max, status, created_at
            FROM project_post
            WHERE client_id=%s
            ORDER BY created_at DESC
        """, (cid,))
        rows = cur.fetchall()
        projects = []
        for r in rows:
            projects.append({
                "project_id": r["id"],
                "title": r["title"],
                "description": r["description"],
                "category": r["category"],
                "skills": r["skills"],
                "budget_type": r["budget_type"],
                "budget_min": r["budget_min"],
                "budget_max": r["budget_max"],
                "status": r["status"],
                "created_at": r["created_at"],
            })
        return jsonify({"success": True, "projects": projects})
    finally:
        conn.close()


@app.route("/client/projects/applicants", methods=["GET"])
def client_projects_applicants():
    client_id = request.args.get("client_id", "")
    project_id = request.args.get("project_id", "")
    try:
        cid = int(client_id)
        pid = int(project_id)
    except Exception:
        return jsonify({"success": False, "msg": "client_id and project_id required"}), 400
    conn = freelancer_db()
    from psycopg2.extras import RealDictCursor
    try:
        cur = get_dict_cursor(conn)
        cur.execute("SELECT client_id FROM project_post WHERE id=%s", (pid,))
        r = cur.fetchone()
        if not r or int(r["client_id"]) != cid:
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        cur.execute("""
            SELECT id, freelancer_id, proposal_text, bid_amount, hourly_rate, event_base_fee, status, created_at
            FROM project_application
            WHERE project_id=%s
            ORDER BY created_at DESC
        """, (pid,))
        rows = cur.fetchall()
        applicants = []
        for a in rows:
            applicants.append({
                "application_id": a["id"],
                "freelancer_id": a["freelancer_id"],
                "proposal_text": a["proposal_text"],
                "bid_amount": a["bid_amount"],
                "hourly_rate": a["hourly_rate"],
                "event_base_fee": a["event_base_fee"],
                "status": a["status"],
                "created_at": a["created_at"],
            })
        return jsonify({"success": True, "applicants": applicants})
    finally:
        conn.close()


@app.route("/client/projects/close", methods=["POST"])
def client_projects_close():
    d = get_json()
    missing = require_fields(d, ["client_id", "project_id"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    try:
        cid = int(d["client_id"])
        pid = int(d["project_id"])
    except Exception:
        return jsonify({"success": False, "msg": "Invalid payload"}), 400
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("SELECT client_id FROM project_post WHERE id=%s", (pid,))
        r = cur.fetchone()
        if not r or int(r.get("client_id", r[0] if not isinstance(r, dict) else 0)) != cid:
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        cur.execute("UPDATE project_post SET status='CLOSED' WHERE id=%s", (pid,))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()


@app.route("/client/projects/accept_application", methods=["POST"])
def client_projects_accept_application():
    d = get_json()
    missing = require_fields(d, ["client_id", "project_id", "application_id"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    try:
        cid = int(d["client_id"])
        pid = int(d["project_id"])
        aid = int(d["application_id"])
    except Exception:
        return jsonify({"success": False, "msg": "Invalid payload"}), 400
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("SELECT client_id, title, budget_type FROM project_post WHERE id=%s", (pid,))
        pr = cur.fetchone()
        if not pr or int(pr["client_id"]) != cid:
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        project_title = pr["title"]
        budget_type = (pr["budget_type"] or "FIXED").upper()
        cur.execute("""
            SELECT freelancer_id, bid_amount, hourly_rate, event_base_fee, status
            FROM project_application
            WHERE id=%s AND project_id=%s
        """, (aid, pid))
        ar = cur.fetchone()
        if not ar:
            return jsonify({"success": False, "msg": "Application not found"}), 404
        ar_status = ar["status"]
        if ar_status != "APPLIED":
            return jsonify({"success": False, "msg": "Application not in APPLIED state"}), 400
        freelancer_id = int(ar["freelancer_id"])
        bid_amount = ar["bid_amount"] or 0
        hourly_rate = ar["hourly_rate"] or 0
        event_base_fee = ar["event_base_fee"] or 0
        if budget_type == "FIXED":
            proposed_budget = bid_amount
        elif budget_type == "HOURLY":
            proposed_budget = hourly_rate
        else:
            proposed_budget = event_base_fee
        cur.execute("UPDATE project_application SET status='ACCEPTED' WHERE id=%s", (aid,))
        cur.execute("UPDATE project_post SET status='HIRED' WHERE id=%s", (pid,))
        cur.execute("""
            INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, created_at, contract_type)
            VALUES (%s, %s, %s, %s, %s, 'PENDING', %s, %s)
        """, (cid, freelancer_id, project_title, proposed_budget, f"Created from project application #{aid}", now_ts(), budget_type))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()


@app.route("/freelancer/projects/feed", methods=["GET"])
def freelancer_projects_feed():
    conn = freelancer_db()
    from psycopg2.extras import RealDictCursor
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, client_id, title, description, category, skills, budget_type, budget_min, budget_max, created_at
            FROM project_post
            WHERE status='OPEN'
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        feed = []
        for r in rows:
            feed.append({
                "project_id": r["id"],
                "client_id": r["client_id"],
                "title": r["title"],
                "description": r["description"],
                "category": r["category"],
                "skills": r["skills"],
                "budget_type": r["budget_type"],
                "budget_min": r["budget_min"],
                "budget_max": r["budget_max"],
                "created_at": r["created_at"],
            })
        return jsonify({"success": True, "projects": feed})
    finally:
        conn.close()


@app.route("/freelancer/projects/apply", methods=["POST"])
def freelancer_projects_apply():
    d = get_json()
    missing = require_fields(d, ["freelancer_id", "project_id", "proposal_text"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    try:
        fid = int(d["freelancer_id"])
        pid = int(d["project_id"])
        proposal_text = str(d["proposal_text"]).strip()
        bid_amount = float(d.get("bid_amount")) if d.get("bid_amount") is not None else None
        hourly_rate = float(d.get("hourly_rate")) if d.get("hourly_rate") is not None else None
        event_base_fee = float(d.get("event_base_fee")) if d.get("event_base_fee") is not None else None
    except Exception:
        return jsonify({"success": False, "msg": "Invalid payload"}), 400
    
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        # PostgreSQL syntax
        cur.execute("SELECT 1 FROM project_application WHERE project_id=%s AND freelancer_id=%s", (pid, fid))
        if cur.fetchone():
            return jsonify({"success": False, "msg": "Already applied"}), 400
        
        # Insert application with PostgreSQL syntax
        cur.execute("""
            INSERT INTO project_application (project_id, freelancer_id, proposal_text, bid_amount, hourly_rate, event_base_fee, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'APPLIED', %s)
            RETURNING id
        """, (pid, fid, proposal_text, bid_amount, hourly_rate, event_base_fee, now_ts()))
        app_row = cur.fetchone()
        application_id = app_row["id"] if isinstance(app_row, dict) else app_row[0]
        
        # Update project status to 'applied' when freelancer applies
        cur.execute("UPDATE project_post SET status='applied' WHERE id=%s", (pid,))
        
        conn.commit()
        return jsonify({"success": True, "msg": "Application submitted successfully", "application_id": application_id})
        
    except psycopg2.Error as e:
        print(f"Database error in project application: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error in project application: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route("/client/rate", methods=["POST"])
def client_rate():
    d = get_json()
    missing = require_fields(d, ["client_id", "hire_request_id", "rating", "review"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    # Validate rating range
    rating = float(d["rating"])
    if rating < 1 or rating > 5:
        return jsonify({"success": False, "msg": "Rating must be between 1 and 5"}), 400
    
    client_id = int(d["client_id"])
    hire_request_id = int(d["hire_request_id"])
    review_text = d["review"]
    
    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    
    # Check if hire request belongs to client and status is PAID
    cur.execute("""
        SELECT freelancer_id, status 
        FROM hire_request 
        WHERE id = %s AND client_id = %s
    """, (hire_request_id, client_id))
    
    request = cur.fetchone()
    if not request:
        conn.close()
        return jsonify({"success": False, "msg": "Hire request not found"}), 404
    
    freelancer_id, status = request
    if status != "PAID":
        conn.close()
        return jsonify({"success": False, "msg": "Rating only allowed for paid jobs"}), 400
    
    # Check if already rated
    cur.execute("SELECT id FROM review WHERE hire_request_id = %s", (hire_request_id,))
    if cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Already rated"}), 400
    
    # Get current freelancer stats
    cur.execute("""
        SELECT rating, total_projects, total_rating_sum 
        FROM freelancer_profile 
        WHERE freelancer_id = %s
    """, (freelancer_id,))
    
    stats = cur.fetchone()
    if not stats:
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    current_rating, total_projects, total_rating_sum = stats
    total_projects = total_projects or 0
    total_rating_sum = total_rating_sum or 0
    
    # Calculate new rating
    new_total_projects = total_projects + 1
    new_total_rating_sum = total_rating_sum + rating
    new_average = new_total_rating_sum / new_total_projects
    
    # Update freelancer profile
    cur.execute("""
        UPDATE freelancer_profile 
        SET rating = %s, total_projects = %s, total_rating_sum = %s
        WHERE freelancer_id = %s
    """, (new_average, new_total_projects, new_total_rating_sum, freelancer_id))
    
    # Insert review
    cur.execute("""
        INSERT INTO review (hire_request_id, client_id, freelancer_id, rating, review_text, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (hire_request_id, client_id, freelancer_id, rating, review_text, now_ts()))
    
    # Update hire request status
    cur.execute("""
        UPDATE hire_request 
        SET status = 'RATED' 
        WHERE id = %s
    """, (hire_request_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "new_rating": new_average,
        "total_reviews": new_total_projects
    }), 500


@app.route("/hourly/log", methods=["POST"])
def hourly_log():
    d = get_json()
    missing = require_fields(d, ["hire_request_id", "freelancer_id", "hours"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    hire_request_id = int(d["hire_request_id"])
    freelancer_id = int(d["freelancer_id"])
    hours = float(d["hours"])
    
    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    
    # Fetch contract snapshot
    cur.execute("""
        SELECT contract_type, contract_hourly_rate, contract_overtime_rate, max_daily_hours
        FROM hire_request 
        WHERE id = %s AND freelancer_id = %s
    """, (hire_request_id, freelancer_id))
    
    contract = cur.fetchone()
    if not contract:
        conn.close()
        return jsonify({"success": False, "msg": "Hire request not found"}), 404
    
    contract_type, hourly_rate, overtime_rate, max_daily_hours = contract
    
    # Ensure contract type is HOURLY
    if contract_type != "HOURLY":
        conn.close()
        return jsonify({"success": False, "msg": "Work logging only available for HOURLY contracts"}), 400
    
    hourly_rate = hourly_rate or 0
    overtime_rate = overtime_rate or 0
    max_daily_hours = max_daily_hours or 8
    
    # Calculate regular and overtime
    if hours > max_daily_hours:
        overtime = hours - max_daily_hours
        regular = max_daily_hours
    else:
        overtime = 0
        regular = hours
    
    # Calculate amount
    amount = (regular * hourly_rate) + (overtime * overtime_rate)
    
    # Insert work log
    cur.execute("""
        INSERT INTO work_log (hire_request_id, freelancer_id, work_date, hours, calculated_regular, calculated_overtime, calculated_amount, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (hire_request_id, freelancer_id, now_ts().split()[0], hours, regular, overtime, amount, now_ts()))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "regular_hours": regular,
        "overtime_hours": overtime,
        "calculated_amount": amount
    })


@app.route("/hourly/generate_invoice", methods=["POST"])
def hourly_generate_invoice():
    d = get_json()
    missing = require_fields(d, ["hire_request_id"])
    if missing:
        return jsonify({"success": False, "msg": "Missing hire_request_id"}), 400
    
    hire_request_id = int(d["hire_request_id"])
    
    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    
    # Verify contract is HOURLY
    cur.execute("""
        SELECT contract_type
        FROM hire_request 
        WHERE id = %s
    """, (hire_request_id,))
    
    contract = cur.fetchone()
    if not contract:
        conn.close()
        return jsonify({"success": False, "msg": "Hire request not found"}), 404
    
    contract_type = contract[0]
    if contract_type != "HOURLY":
        conn.close()
        return jsonify({"success": False, "msg": "Invoice generation only available for HOURLY contracts"}), 400
    
    # Sum approved logs
    cur.execute("""
        SELECT SUM(calculated_amount)
        FROM work_log 
        WHERE hire_request_id = %s AND approved = 1
    """, (hire_request_id,))
    
    result = cur.fetchone()
    total_amount = result[0] if result and result[0] else 0
    
    # Create invoice entry
    from datetime import datetime, timedelta
    week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = datetime.now().strftime("%Y-%m-%d")
    
    cur.execute("""
        INSERT INTO invoice (hire_request_id, total_amount, week_start, week_end, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (hire_request_id, total_amount, week_start, week_end, now_ts()))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "total_amount": total_amount,
        "week_start": week_start,
        "week_end": week_end
    })


@app.route("/event/complete", methods=["POST"])
def event_complete():
    d = get_json()
    missing = require_fields(d, ["hire_request_id", "actual_hours"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    hire_request_id = int(d["hire_request_id"])
    actual_hours = float(d["actual_hours"])
    
    conn = freelancer_db()
    cur = get_dict_cursor(conn)
    
    # Verify contract is EVENT
    cur.execute("""
        SELECT contract_type, event_base_fee, event_included_hours, event_overtime_rate, advance_paid
        FROM hire_request 
        WHERE id = %s
    """, (hire_request_id,))
    
    contract = cur.fetchone()
    if not contract:
        conn.close()
        return jsonify({"success": False, "msg": "Hire request not found"}), 404
    
    contract_type, event_base_fee, event_included_hours, event_overtime_rate, advance_paid = contract
    
    # Ensure contract type is EVENT
    if contract_type != "EVENT":
        conn.close()
        return jsonify({"success": False, "msg": "Event completion only available for EVENT contracts"}), 400
    
    event_base_fee = event_base_fee or 0
    event_included_hours = event_included_hours or 0
    event_overtime_rate = event_overtime_rate or 0
    advance_paid = advance_paid or 0
    
    # Calculate overtime and amounts
    if actual_hours > event_included_hours:
        overtime_hours = actual_hours - event_included_hours
        extra = overtime_hours * event_overtime_rate
    else:
        overtime_hours = 0
        extra = 0
    
    total_due = event_base_fee + extra
    remaining_due = total_due - advance_paid
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "actual_hours": actual_hours,
        "overtime_hours": overtime_hours,
        "extra_amount": extra,
        "total_due": total_due,
        "remaining_due": remaining_due
    })


# ============================================================
# PLATFORM STATISTICS
# ============================================================

@app.route("/platform/stats", methods=["GET"])
def platform_stats():
    """Get platform-wide statistics"""
    try:
        # Get total freelancers
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("SELECT COUNT(*) as cnt FROM freelancer")
        total_freelancers = (cur.fetchone() or {}).get("cnt", 0) or 0
        conn.close()
        
        # Get total clients
        conn = client_db()
        cur = get_dict_cursor(conn)
        cur.execute("SELECT COUNT(*) as cnt FROM client")
        total_clients = (cur.fetchone() or {}).get("cnt", 0) or 0
        conn.close()
        
        # Get gigs completed
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("SELECT COUNT(*) as cnt FROM hire_request WHERE status='ACCEPTED'")
        gigs_completed = (cur.fetchone() or {}).get("cnt", 0) or 0
        conn.close()
        
        return jsonify({
            "success": True,
            "total_freelancers": total_freelancers,
            "total_clients": total_clients,
            "gigs_completed": gigs_completed
        })
        
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


@app.route("/freelancer/<int:freelancer_id>/stats", methods=["GET"])
def freelancer_profile_stats(freelancer_id):
    """Get freelancer-specific statistics"""
    try:
        # Get rating
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("SELECT rating FROM freelancer_profile WHERE freelancer_id=%s", (freelancer_id,))
        rating_row = cur.fetchone()
        rating = (rating_row.get("rating", rating_row[0] if rating_row and not isinstance(rating_row, dict) else 0) or 0.0) if rating_row else 0.0
        conn.close()
        
        # Get gigs completed
        conn = client_db()
        cur = get_dict_cursor(conn)
        cur.execute("SELECT COUNT(*) as cnt FROM hire_request WHERE freelancer_id=%s AND status='ACCEPTED'", (freelancer_id,))
        gigs_completed = (cur.fetchone() or {}).get("cnt", 0) or 0
        
        # Get earnings
        cur.execute("SELECT SUM(proposed_budget) as total FROM hire_request WHERE freelancer_id=%s AND status='ACCEPTED'", (freelancer_id,))
        earnings_row = cur.fetchone()
        earnings = (earnings_row.get("total") if isinstance(earnings_row, dict) else (earnings_row[0] if earnings_row else None)) or 0
        conn.close()
        
        return jsonify({
            "success": True,
            "rating": float(rating),
            "gigs_completed": gigs_completed,
            "earnings": earnings
        })
        
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


# ============================================================
# CALL ROUTES (Voice/Video Calls)
# ============================================================

@app.route("/call/start", methods=["POST"])
def call_start():
    """Start a voice or video call"""
    d = get_json()
    print(f"DEBUG: Received data: {d}")
    missing = require_fields(d, ["caller_id", "receiver_id", "call_type"])
    if missing:
        print(f"DEBUG: Missing fields: {missing}")
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    try:
        caller_id = int(d["caller_id"])
        receiver_id = int(d["receiver_id"])
        call_type = str(d["call_type"]).lower()
        
        if call_type not in ["voice", "video"]:
            return jsonify({"success": False, "msg": "Invalid call type"}), 400
        
        result, error = start_call(caller_id, receiver_id, call_type)
        if error:
            return jsonify({"success": False, "msg": error}), 400
        
        return jsonify({
            "success": True,
            "call_id": result["call_id"],
            "meeting_url": result["meeting_url"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

@app.route("/call/accept", methods=["POST"])
def call_accept():
    """Accept an incoming call"""
    d = get_json()
    missing = require_fields(d, ["call_id"])
    if missing:
        return jsonify({"success": False, "msg": "Missing call_id"}), 400
    
    try:
        call_id = int(d["call_id"])
        success, error = update_call_status(call_id, "accepted")
        if error:
            return jsonify({"success": False, "msg": error}), 400
        
        # Get call details to return meeting URL
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("SELECT room_name FROM calls WHERE call_id = %s", (call_id,))
        result = cur.fetchone()
        conn.close()
        
        meeting_url = f"https://meet.jit.si/{result['room_name']}" if result else None
        
        return jsonify({
            "success": True, 
            "msg": "Call accepted",
            "meeting_url": meeting_url
        })
        
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

@app.route("/call/reject", methods=["POST"])
def call_reject():
    """Reject an incoming call"""
    d = get_json()
    missing = require_fields(d, ["call_id"])
    if missing:
        return jsonify({"success": False, "msg": "Missing call_id"}), 400
    
    try:
        call_id = int(d["call_id"])
        success, error = update_call_status(call_id, "rejected")
        if error:
            return jsonify({"success": False, "msg": error}), 400
        
        return jsonify({"success": True, "msg": "Call rejected"})
        
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

@app.route("/call/incoming", methods=["GET"])
def call_incoming():
    """Get incoming calls for a user"""
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"success": False, "msg": "Missing user_id"}), 400
    
    try:
        user_id = int(user_id)
        calls = get_incoming_calls(user_id)
        
        return jsonify({
            "success": True,
            "calls": calls
        })
        
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
