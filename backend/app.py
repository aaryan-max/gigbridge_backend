from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
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
from llm_chatbot import generate_ai_response, PENDING_ACTIONS, execute_agent_action
from admin_db import ensure_admin_tables
from admin_routes import admin_bp
from kyc_routes import kyc_bp
from client_kyc_routes import client_kyc_bp

from database import create_tables, rebuild_freelancer_search_index
from settings import (
    FEATURE_HIDE_UNVERIFIED_FROM_SEARCH,
    FEATURE_BLOCK_DISABLED_USERS,
    FEATURE_ENFORCE_VERIFIED_FOR_HIRE_MESSAGE,
)
from categories import is_valid_category


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
from database import create_tables, rebuild_freelancer_search_index, get_freelancer_verification, update_freelancer_verification, get_freelancer_subscription, update_freelancer_subscription, get_freelancer_job_applies, increment_job_applies, check_subscription_expiry, get_freelancer_plan
from categories import is_valid_category


# ============================================================
# APP INIT
# ============================================================

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})

create_tables()
ensure_admin_tables()
app.register_blueprint(admin_bp)
app.register_blueprint(kyc_bp)
app.register_blueprint(client_kyc_bp)

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
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS client_otp (
            email TEXT PRIMARY KEY,
            otp TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
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

    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO client_otp (email, otp, expires_at) VALUES (?, ?, ?)",
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
    d = get_json()
    missing = require_fields(d, ["name", "email", "password", "otp"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    name = str(d["name"]).strip()
    email = str(d["email"]).strip().lower()
    password = str(d["password"])
    otp_in = str(d["otp"]).strip()

    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("SELECT otp, expires_at FROM client_otp WHERE email=?", (email,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "msg": "OTP not found"}), 400

    db_otp, expires_at = row
    if now_ts() > int(expires_at):
        cur.execute("DELETE FROM client_otp WHERE email=?", (email,))
        conn.commit()
        conn.close()
        return jsonify({"success": False, "msg": "OTP expired"}), 400

    if str(db_otp) != otp_in:
        conn.close()
        return jsonify({"success": False, "msg": "Invalid OTP"}), 400

    try:
        cur.execute(
            "INSERT INTO client (name,email,password) VALUES (?,?,?)",
            (name, email, generate_password_hash(password))
        )
        client_id = cur.lastrowid  # ✅ auto-login return

        cur.execute("DELETE FROM client_otp WHERE email=?", (email,))
        conn.commit()
        conn.close()

        try:
            send_login_email(email, name, "Client", "signup")
        except:
            pass

        return jsonify({"success": True, "client_id": client_id})

    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "msg": "Client already exists"}), 409

# ============================================================
# OTP – FREELANCER
# ============================================================

@app.route("/freelancer/send-otp", methods=["POST"])
def freelancer_send_otp():
    d = get_json()
    missing = require_fields(d, ["email"])
    if missing:
        return jsonify({"success": False, "msg": "Email required"}), 400

    email = str(d["email"]).strip().lower()
    if not valid_email(email):
        return jsonify({"success": False, "msg": "Invalid email"}), 400

    otp = str(random.randint(100000, 999999))
    expires_at = now_ts() + OTP_TTL_SECONDS

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO freelancer_otp (email, otp, expires_at) VALUES (?, ?, ?)",
        (email, otp, expires_at)
    )
    conn.commit()
    conn.close()

    try:
        send_otp_email(email, otp)
    except:
        pass

    return jsonify({"success": True, "msg": "OTP sent"})

@app.route("/freelancer/verify-otp", methods=["POST"])
def freelancer_verify_otp():
    d = get_json()
    missing = require_fields(d, ["name", "email", "password", "otp"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    name = str(d["name"]).strip()
    email = str(d["email"]).strip().lower()
    password = str(d["password"])
    otp_in = str(d["otp"]).strip()

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT otp, expires_at FROM freelancer_otp WHERE email=?", (email,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "msg": "OTP not found"}), 400

    db_otp, expires_at = row
    if now_ts() > int(expires_at):
        cur.execute("DELETE FROM freelancer_otp WHERE email=?", (email,))
        conn.commit()
        conn.close()
        return jsonify({"success": False, "msg": "OTP expired"}), 400

    if str(db_otp) != otp_in:
        conn.close()
        return jsonify({"success": False, "msg": "Invalid OTP"}), 400

    try:
        cur.execute(
            "INSERT INTO freelancer (name,email,password) VALUES (?,?,?)",
            (name, email, generate_password_hash(password))
        )
        freelancer_id = cur.lastrowid

        cur.execute("DELETE FROM freelancer_otp WHERE email=?", (email,))
        conn.commit()
        conn.close()

        try:
            send_login_email(email, name, "Freelancer", "signup")
        except:
            pass

        return jsonify({"success": True, "freelancer_id": freelancer_id})

    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer already exists"}), 409

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
    
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    
    # Check if email already exists
    cur.execute("SELECT id FROM client WHERE email=?", (email,))
    if cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Email already exists"}), 400
    
    # Insert new client
    cur.execute("INSERT INTO client (name, email, password) VALUES (?, ?, ?)", 
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
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Check if email already exists
    cur.execute("SELECT id FROM freelancer WHERE email=?", (email,))
    if cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Email already exists"}), 400
    
    # Insert new freelancer
    cur.execute("INSERT INTO freelancer (name, email, password) VALUES (?, ?, ?)", 
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

    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("SELECT id,password,name FROM client WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row[1], password):
        if FEATURE_BLOCK_DISABLED_USERS:
            try:
                c2 = sqlite3.connect("client.db")
                cur2 = c2.cursor()
                cur2.execute("SELECT COALESCE(is_enabled,1) FROM client WHERE id=?", (row[0],))
                en = cur2.fetchone()
                c2.close()
                if en and int(en[0]) != 1:
                    return jsonify({"success": False, "msg": "Account disabled"}), 403
            except Exception:
                pass
        try:
            send_login_email(email, row[2], "Client", "login")
        except:
            pass
        return jsonify({"success": True, "client_id": row[0]})

    return jsonify({"success": False, "msg": "Invalid credentials"})

@app.route("/freelancer/login", methods=["POST"])
def freelancer_login():
    d = get_json()
    missing = require_fields(d, ["email", "password"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    email = str(d["email"]).strip().lower()
    password = str(d["password"])

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT id,password,name FROM freelancer WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row[1], password):
        if FEATURE_BLOCK_DISABLED_USERS:
            try:
                f2 = sqlite3.connect("freelancer.db")
                cur2 = f2.cursor()
                cur2.execute("SELECT COALESCE(is_enabled,1) FROM freelancer WHERE id=?", (row[0],))
                en = cur2.fetchone()
                f2.close()
                if en and int(en[0]) != 1:
                    return jsonify({"success": False, "msg": "Account disabled"}), 403
            except Exception:
                pass
        try:
            send_login_email(email, row[2], "Freelancer", "login")
        except:
            pass
        return jsonify({"success": True, "freelancer_id": row[0]})

    return jsonify({"success": False, "msg": "Invalid credentials"})

# ============================================================
# PROFILES
# ============================================================

@app.route("/client/profile", methods=["POST"])
def client_profile():
    d = get_json()
    missing = require_fields(d, ["client_id", "phone", "location", "bio", "dob"])
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
        
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO client_profile (client_id, phone, location, bio, pincode, latitude, longitude, dob)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(client_id) DO UPDATE SET
        phone=excluded.phone,
        location=excluded.location,
        bio=excluded.bio,
        pincode=excluded.pincode,
        latitude=excluded.latitude,
        longitude=excluded.longitude,
        dob=excluded.dob
    """, (d["client_id"], d["phone"], d["location"], d["bio"], pincode, lat, lon, d["dob"]))
    conn.commit()
    conn.close()

    # Add notification (store in client.db)
    c2 = sqlite3.connect("client.db")
    cur2 = c2.cursor()
    cur2.execute("""
        INSERT INTO notification (client_id, message, created_at)
        VALUES (?, ?, ?)
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

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO freelancer_profile
        (freelancer_id, title, skills, experience, min_budget, max_budget, bio, category, location, pincode, latitude, longitude, dob, availability_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE freelancer_profile 
            SET availability_status = ?
            WHERE freelancer_id = ?
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
            cconn = sqlite3.connect("client.db")
            ccur = cconn.cursor()
            ccur.execute(
                "SELECT latitude, longitude FROM client_profile WHERE client_id=?",
                (cid,),
            )
            row = ccur.fetchone()
            cconn.close()

            if row:
                client_lat, client_lon = row[0], row[1]
        except Exception:
            client_lat = client_lon = None

    try:
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()

        rows = []

        # ============================================
        # IF SPECIALIZATION QUERY EXISTS → USE FTS5
        # ============================================
        if q:
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
                        bm25(freelancer_search) as rank
                    FROM freelancer_search
                    JOIN freelancer_profile fp
                        ON fp.freelancer_id = freelancer_search.freelancer_id
                    JOIN freelancer f
                        ON f.id = fp.freelancer_id
                    LEFT JOIN freelancer_subscription fs
                        ON fs.freelancer_id = fp.freelancer_id
                    WHERE freelancer_search MATCH ?
                      AND fp.min_budget <= ?
                      AND fp.max_budget >= ?{cond_verified}
                """
                cur.execute(sql, (fts_query, budget, budget))
                rows = cur.fetchall()

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
                        COALESCE(fs.plan_name, 'BASIC') as subscription_plan
                    FROM freelancer_profile fp
                    JOIN freelancer f
                        ON f.id = fp.freelancer_id
                    LEFT JOIN freelancer_subscription fs
                        ON fs.freelancer_id = fp.freelancer_id
                    WHERE fp.min_budget <= ?
                      AND fp.max_budget >= ?{cond_verified}
                    """,
                    (budget, budget),
                )

                candidates = cur.fetchall()
                scored = []

                for r in candidates:
                    combined = f"{r[2] or ''} {r[3] or ''} {r[8] or ''}".lower()
                    score = fuzzy_score(q, combined)
                    scored.append((score, r))

                scored.sort(key=lambda x: x[0], reverse=True)
                scored = [x for x in scored if x[0] >= 60]

                # Add a fake 'rank' column at the end, so formatting stays consistent
                rows = [x[1] + (999999.0,) for x in scored[:20]]

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
                    placeholders = ",".join(["?"] * len(sem_ids))
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
                            COALESCE(fs.plan_name, 'BASIC') as subscription_plan,
                            999999.0 as rank
                        FROM freelancer_profile fp
                        JOIN freelancer f ON f.id = fp.freelancer_id
                        LEFT JOIN freelancer_subscription fs
                            ON fs.freelancer_id = fp.freelancer_id
                        WHERE fp.freelancer_id IN ({placeholders})
                          AND fp.min_budget <= ?
                          AND fp.max_budget >= ?{cond_verified}
                        """,
                        (*sem_ids, budget, budget),
                    )
                    rows = cur.fetchall()

        # ============================================
        # NO SPECIALIZATION → BUDGET ONLY SEARCH
        # ============================================
        else:
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
                    COALESCE(fs.plan_name, 'BASIC') as subscription_plan,
                    999999.0 as rank
                FROM freelancer_profile fp
                JOIN freelancer f
                    ON f.id = fp.freelancer_id
                LEFT JOIN freelancer_subscription fs
                    ON fs.freelancer_id = fp.freelancer_id
                WHERE fp.min_budget <= ?
                  AND fp.max_budget >= ?{cond_verified}
                """,
                (budget, budget),
            )
            rows = cur.fetchall()

        conn.close()

    except sqlite3.Error as e:
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

        if category:
            cat_db = (r[8] or "").lower()
            if fuzzy_score(category, cat_db) < 70:
                continue

        spec = (q or "").strip().lower()
        if spec:
             spec_db = (r[3] or "").strip().lower()
             if fuzzy_score(spec, spec_db) < 70:
               continue   

        f_lat, f_lon = r[9], r[10]

        if client_lat and client_lon and f_lat and f_lon:
            dist = calculate_distance(
                client_lat, client_lon, f_lat, f_lon
            )
        else:
            dist = 999999.0

        # Apply rank boost based on subscription
        rank_boost = 0
        subscription_plan = r[11]  # subscription_plan field
        
        # Migrate old plans
        if subscription_plan == "FREE":
            subscription_plan = "BASIC"
        elif subscription_plan == "PRO":
            subscription_plan = "PREMIUM"
        
        if subscription_plan == "PREMIUM":
            rank_boost = 1
        
        # Adjust rank with boost
        adjusted_rank = r[12] - (rank_boost * 100)  # Lower rank number = higher position
        
        # Add badge
        badge = None
        if subscription_plan == "PREMIUM":
            badge = "🟣 PREMIUM"
        
        enriched.append({
            "freelancer_id": r[0],
            "name": r[1],
            "title": r[2],
            "skills": r[3],
            "experience": r[4],
            "budget_range": f"{r[5]} - {r[6]}",
            "rating": r[7],
            "category": r[8],
            "distance": round(dist, 2),
            "rank": adjusted_rank,
            "badge": badge,
            "subscription_plan": subscription_plan
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
    conn = sqlite3.connect("freelancer.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
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
            COALESCE(fp.bio, '') as bio
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

# ============================================================
# NEW: CHAT (Client <-> Freelancer)
# ============================================================

@app.route("/client/message/send", methods=["POST"])
def client_send_message():
    d = get_json()
    missing = require_fields(d, ["client_id", "freelancer_id", "text"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO message (sender_role, sender_id, receiver_id, text, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, ("client", int(d["client_id"]), int(d["freelancer_id"]), str(d["text"]), now_ts()))

    # Add notification for client in client.db - get freelancer name
    cur.execute("SELECT name FROM freelancer WHERE id=?", (int(d["freelancer_id"]),))
    freelancer_row = cur.fetchone()
    freelancer_name = freelancer_row[0] if freelancer_row else "Freelancer"
    
    cconn = sqlite3.connect("client.db")
    ccur = cconn.cursor()
    ccur.execute("""
        INSERT INTO notification (client_id, message, created_at)
        VALUES (?, ?, ?)
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

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO message (sender_role, sender_id, receiver_id, text, timestamp)
        VALUES (?, ?, ?, ?, ?)
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

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT sender_role, sender_id, text, timestamp
        FROM message
        WHERE (sender_role='client' AND sender_id=? AND receiver_id=?)
           OR (sender_role='freelancer' AND sender_id=? AND receiver_id=?)
        ORDER BY timestamp
    """, (client_id, freelancer_id, freelancer_id, client_id))
    rows = cur.fetchall()
    conn.close()

    chat = []
    for r in rows:
        chat.append({
            "sender_role": r[0],
            "sender_id": r[1],
            "text": r[2],
            "timestamp": r[3]
        })
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
    
    # Validate contract type
    if contract_type not in ["FIXED", "HOURLY", "EVENT"]:
        return jsonify({"success": False, "msg": "Invalid contract type. Use FIXED, HOURLY, or EVENT"}), 400

    # simple existence check
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM freelancer WHERE id=?", (freelancer_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    # Check freelancer availability status
    cur.execute("SELECT availability_status FROM freelancer_profile WHERE freelancer_id=?", (freelancer_id,))
    availability_result = cur.fetchone()
    if availability_result and availability_result[0] == "ON_LEAVE":
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer is currently not accepting new projects"}), 403
    if FEATURE_ENFORCE_VERIFIED_FOR_HIRE_MESSAGE:
        try:
            cur.execute("SELECT COALESCE(is_verified,0) FROM freelancer_profile WHERE freelancer_id=?", (freelancer_id,))
            vr = cur.fetchone()
            if not vr or int(vr[0]) != 1:
                conn.close()
                return jsonify({"success": False, "msg": "Freelancer not verified"}), 403
        except Exception:
            pass

    job_title = str(d.get("job_title", "")).strip()
    
    # Handle different contract types
    if contract_type == "FIXED":
        # Keep existing budget logic unchanged
        cur.execute("""
            INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, contract_type, created_at)
            VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)
        """, (client_id, freelancer_id, job_title, proposed_budget, note, contract_type, now_ts()))
    elif contract_type == "HOURLY":
        # Require hourly rate fields
        if "contract_hourly_rate" not in d or "weekly_limit" not in d:
            return jsonify({"success": False, "msg": "HOURLY contracts require contract_hourly_rate and weekly_limit"}), 400
        
        hourly_rate = float(d.get("contract_hourly_rate", 0))
        weekly_limit = float(d.get("weekly_limit", 0))
        max_daily_hours = float(d.get("max_daily_hours", 8))
        
        if hourly_rate <= 0 or weekly_limit <= 0:
            return jsonify({"success": False, "msg": "HOURLY contracts require positive rates and limits"}), 400
        
        cur.execute("""
            INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, contract_type, contract_hourly_rate, contract_overtime_rate, weekly_limit, max_daily_hours, created_at)
            VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?, ?)
        """, (client_id, freelancer_id, job_title, proposed_budget, note, contract_type, hourly_rate, hourly_rate * 1.5, weekly_limit, max_daily_hours, now_ts()))
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
            INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, contract_type, event_base_fee, event_included_hours, event_overtime_rate, advance_paid, created_at)
            VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?, ?)
        """, (client_id, freelancer_id, job_title, proposed_budget, note, contract_type, event_base_fee, event_included_hours, event_overtime_rate, advance_paid, now_ts()))
    else:
        return jsonify({"success": False, "msg": "Invalid contract type"}), 400
    req_id = cur.lastrowid

    # Add notification for client in client.db
    notification_msg = f'Job "{job_title if job_title else "Untitled"}" posted'
    cconn = sqlite3.connect("client.db")
    ccur = cconn.cursor()
    ccur.execute("""
        INSERT INTO notification (client_id, message, created_at)
        VALUES (?, ?, ?)
    """, (client_id, notification_msg, now_ts()))
    cconn.commit()
    cconn.close()

    conn.commit()
    conn.close()

    return jsonify({"success": True, "request_id": req_id})

@app.route("/freelancer/hire/inbox", methods=["GET"])
def freelancer_hire_inbox():
    freelancer_id = request.args.get("freelancer_id")
    if not freelancer_id:
        return jsonify({"success": False, "msg": "Missing freelancer_id"}), 400
    freelancer_id = int(freelancer_id)

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT id, client_id, proposed_budget, note, status, created_at, 
               contract_type, contract_hourly_rate, contract_overtime_rate, 
               weekly_limit, max_daily_hours, event_base_fee, event_included_hours, 
               event_overtime_rate, advance_paid
        FROM hire_request
        WHERE freelancer_id=?
        ORDER BY created_at DESC
    """, (freelancer_id,))
    rows = cur.fetchall()
    conn.close()

    # fetch client names from client.db (separate db => done per client_id)
    client_conn = sqlite3.connect("client.db")
    client_cur = client_conn.cursor()

    out = []
    for r in rows:
        client_cur.execute("SELECT name, email FROM client WHERE id=?", (int(r[1]),))
        c = client_cur.fetchone()
        out.append({
            "request_id": r[0],
            "client_id": r[1],
            "client_name": (c[0] if c else "Unknown"),
            "client_email": (c[1] if c else ""),
            "proposed_budget": r[2],
            "note": r[3],
            "status": r[4],
            "created_at": r[5],
            "contract_type": r[6],
            "contract_hourly_rate": r[7],
            "contract_overtime_rate": r[8],
            "weekly_limit": r[9],
            "max_daily_hours": r[10],
            "event_base_fee": r[11],
            "event_included_hours": r[12],
            "event_overtime_rate": r[13],
            "advance_paid": r[14],
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

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        UPDATE hire_request
        SET status=?
        WHERE id=? AND freelancer_id=?
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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT
                CASE
                    WHEN sender_role='client' THEN receiver_id
                    ELSE sender_id
                END AS freelancer_id
            FROM message
            WHERE (sender_role='client' AND sender_id=?)
               OR (sender_role='freelancer' AND receiver_id=?)
            ORDER BY freelancer_id DESC
        """, (client_id, client_id))
        ids = [int(r[0]) for r in cur.fetchall() if r and r[0] is not None]

        if not ids:
            conn.close()
            return jsonify([])

        out = []
        for fid in ids:
            cur.execute("SELECT name, email FROM freelancer WHERE id=?", (fid,))
            fr = cur.fetchone()
            out.append({
                "freelancer_id": fid,
                "name": (fr[0] if fr else "Freelancer"),
                "email": (fr[1] if fr else "")
            })

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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
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
            WHERE hr.client_id=?
            ORDER BY hr.created_at DESC
        """, (client_id,))
        rows = cur.fetchall()
        conn.close()

        out = []
        for r in rows:
            out.append({
                "request_id": r[0],
                "freelancer_id": r[1],
                "freelancer_name": r[2],
                "freelancer_email": r[3],
                "job_title": r[4] or "",
                "proposed_budget": r[5],
                "note": r[6] or "",
                "status": r[7],
                "created_at": r[8]
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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT job_title, proposed_budget, status
            FROM hire_request
            WHERE client_id=?
            ORDER BY created_at DESC
        """, (client_id,))
        rows = cur.fetchall()
        conn.close()

        return jsonify([
            {
                "title": r[0] or "",
                "budget": r[1],
                "status": "open" if r[2] == "PENDING" else r[2].lower()
            }
            for r in rows
        ])
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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO saved_freelancer (client_id, freelancer_id)
            VALUES (?,?)
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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT f.id, f.name, fp.category
            FROM saved_freelancer s
            JOIN freelancer f ON f.id = s.freelancer_id
            LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
            WHERE s.client_id=?
        """, (client_id,))
        rows = cur.fetchall()
        conn.close()

        return jsonify([
            {"id": r[0], "name": r[1], "category": r[2] or ""}
            for r in rows
        ])
    except Exception as e:
        if conn:
            conn.close()
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
        conn = sqlite3.connect("client.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT message
            FROM notification
            WHERE client_id=?
            ORDER BY created_at DESC
        """, (client_id,))
        rows = cur.fetchall()
        conn.close()

        return jsonify([r[0] for r in rows])
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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()

        # Total earnings and completed jobs (ACCEPTED)
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(proposed_budget), 0)
            FROM hire_request
            WHERE freelancer_id=? AND status='ACCEPTED'
        """, (freelancer_id,))
        row = cur.fetchone()
        completed_jobs = int(row[0] or 0)
        total_earnings = float(row[1] or 0.0)

        # Total jobs for job success %
        cur.execute("""
            SELECT COUNT(*)
            FROM hire_request
            WHERE freelancer_id=?
        """, (freelancer_id,))
        total_jobs_row = cur.fetchone()
        total_jobs = int(total_jobs_row[0] or 0)

        # Rating from profile
        cur.execute("""
            SELECT COALESCE(rating, 0)
            FROM freelancer_profile
            WHERE freelancer_id=?
        """, (freelancer_id,))
        rating_row = cur.fetchone()
        rating = float(rating_row[0] or 0.0) if rating_row else 0.0

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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO saved_client (freelancer_id, client_id)
            VALUES (?, ?)
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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT client_id
            FROM saved_client
            WHERE freelancer_id=?
        """, (freelancer_id,))
        rows = cur.fetchall()
        conn.close()

        client_ids = [int(r[0]) for r in rows]
        if not client_ids:
            return jsonify([])

        client_conn = sqlite3.connect("client.db")
        client_cur = client_conn.cursor()

        out = []
        for cid in client_ids:
            client_cur.execute("SELECT name, email FROM client WHERE id=?", (cid,))
            c = client_cur.fetchone()
            if c:
                out.append({
                    "client_id": cid,
                    "name": c[0],
                    "email": c[1]
                })

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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute("SELECT password FROM freelancer WHERE id=?", (freelancer_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "msg": "Freelancer not found"}), 404

        if not check_password_hash(row[0], old_password):
            conn.close()
            return jsonify({"success": False, "msg": "Old password incorrect"}), 400

        cur.execute(
            "UPDATE freelancer SET password=? WHERE id=?",
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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute(
            "UPDATE freelancer SET email=? WHERE id=?",
            (new_email, freelancer_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
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
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()

        notifications = []

        # From hire requests
        cur.execute("""
            SELECT job_title, status, created_at
            FROM hire_request
            WHERE freelancer_id=?
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
            WHERE receiver_id=? AND sender_role='client'
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
        conn = sqlite3.connect("client.db")
        cur = conn.cursor()

        cur.execute("SELECT id, password, auth_provider, google_sub FROM client WHERE email=?", (email,))
        row = cur.fetchone()

        if row:
            client_id, pwd, provider, gsub = row
            if not provider:
                provider = "local"
            if not gsub:
                cur.execute("UPDATE client SET google_sub=? WHERE id=?", (sub, client_id))
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

        cur.execute(
            "INSERT INTO client (name, email, password, auth_provider, google_sub) VALUES (?,?,?,?,?)",
            (name, email, random_pwd_hash, "google", sub)
        )
        client_id = cur.lastrowid
        conn.commit()
        conn.close()

        st["done"] = True
        st["result"] = {"success": True, "role": "client", "client_id": client_id, "email": email}

        return f"""
        <h3>✅ Google Signup/Login Success (Client)</h3>
        <p>You can close this tab and return to the app.</p>
        """

    else:
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()

        cur.execute("SELECT id, password, auth_provider, google_sub FROM freelancer WHERE email=?", (email,))
        row = cur.fetchone()

        if row:
            freelancer_id, pwd, provider, gsub = row
            if not provider:
                provider = "local"
            if not gsub:
                cur.execute("UPDATE freelancer SET google_sub=? WHERE id=?", (sub, freelancer_id))
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

        cur.execute(
            "INSERT INTO freelancer (name, email, password, auth_provider, google_sub) VALUES (?,?,?,?,?)",
            (name, email, random_pwd_hash, "google", sub)
        )
        freelancer_id = cur.lastrowid
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
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM client WHERE id=?", (client_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Client not found"}), 404
    
    # Copy image to uploads
    uploaded_path = copy_image_to_uploads(image_path)
    if not uploaded_path:
        conn.close()
        return jsonify({"success": False, "msg": "Failed to upload image"}), 400
    
    # Update database
    cur.execute("UPDATE client SET profile_image=? WHERE id=?", (uploaded_path, client_id))
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
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM freelancer WHERE id=?", (freelancer_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    
    # Copy image to uploads
    uploaded_path = copy_image_to_uploads(image_path)
    if not uploaded_path:
        conn.close()
        return jsonify({"success": False, "msg": "Failed to upload image"}), 400
    
    # Update database
    cur.execute("UPDATE freelancer SET profile_image=? WHERE id=?", (uploaded_path, freelancer_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "image_path": uploaded_path})

@app.route("/client/profile/<int:client_id>", methods=["GET"])
def get_client_profile(client_id):
    """NEW CODE: Get client profile with photo"""
    conn = sqlite3.connect("client.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT c.id, c.name, c.email, c.profile_image,
               cp.phone, cp.location, cp.bio
        FROM client c
        LEFT JOIN client_profile cp ON cp.client_id = c.id
        WHERE c.id = ?
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
    conn = sqlite3.connect("freelancer.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT f.id, f.name, f.email, f.profile_image,
               fp.title, fp.skills, fp.experience, fp.min_budget, fp.max_budget,
               fp.rating, fp.category, fp.bio
        FROM freelancer f
        LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
        WHERE f.id = ?
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
        "bio": row["bio"]
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
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM freelancer WHERE id=?", (freelancer_id,))
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (freelancer_id, title, description, image_path, image_binary, now_ts(), media_type, media_url))
    
    portfolio_id = cur.lastrowid
    conn.commit()
    conn.close()
    rebuild_freelancer_search_index(freelancer_id)
    return jsonify({"success": True, "portfolio_id": portfolio_id})

@app.route("/freelancer/portfolio/<int:freelancer_id>", methods=["GET"])
def get_freelancer_portfolio(freelancer_id):
    """NEW CODE: Get all portfolio items for a freelancer"""
    conn = sqlite3.connect("freelancer.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, title, description, image_path, image_data, created_at, media_type, media_url
        FROM portfolio
        WHERE freelancer_id = ?
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
    conn = sqlite3.connect("freelancer.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
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
# ===== NEW: CALL FEATURE =====
# ============================================================

@app.route("/call/start", methods=["POST"])
def start_call():
    """NEW CODE: Start a voice or video call"""
    d = get_json()
    missing = require_fields(d, ["caller_role", "caller_id", "receiver_role", "receiver_id", "call_type"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    caller_role = str(d["caller_role"]).strip()
    caller_id = int(d["caller_id"])
    receiver_role = str(d["receiver_role"]).strip()
    receiver_id = int(d["receiver_id"])
    call_type = str(d["call_type"]).strip()  # "voice" or "video"
    
    # Generate unique room name
    room_name = "gigbridge_" + str(int(time.time()))
    room_url = "https://meet.jit.si/" + room_name
    
    # Insert call session
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO call_session (caller_role, caller_id, receiver_role, receiver_id, call_type, room_name, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (caller_role, caller_id, receiver_role, receiver_id, call_type, room_name, "PENDING", now_ts()))
    
    call_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "call_id": call_id,
        "room_url": room_url,
        "room_name": room_name
    })

@app.route("/call/incoming", methods=["GET", "POST"])
def get_incoming_calls():
    """NEW CODE: Get incoming calls for a user"""
    # Support both GET and POST methods
    if request.method == "GET":
        receiver_role = request.args.get("receiver_role")
        receiver_id = request.args.get("receiver_id")
    else:  # POST
        data = request.get_json() or {}
        receiver_role = data.get("receiver_role")
        receiver_id = data.get("receiver_id")
    
    if not receiver_role or not receiver_id:
        return jsonify({"success": False, "msg": "Missing parameters"}), 400
    
    try:
        receiver_id = int(receiver_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid user ID"}), 400
    
    conn = sqlite3.connect("freelancer.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, caller_role, caller_id, call_type, room_name, status, created_at
        FROM call_session
        WHERE receiver_role = ? AND receiver_id = ? AND status = 'PENDING'
        ORDER BY created_at DESC
    """, (receiver_role, receiver_id))
    
    rows = cur.fetchall()
    conn.close()
    
    calls = []
    for row in rows:
        calls.append({
            "call_id": row["id"],
            "caller_role": row["caller_role"],
            "caller_id": row["caller_id"],
            "call_type": row["call_type"],
            "room_name": row["room_name"],
            "status": row["status"],
            "created_at": row["created_at"]
        })
    
    return jsonify({"success": True, "calls": calls})

@app.route("/call/respond", methods=["POST"])
def respond_to_call():
    """NEW CODE: Accept or reject a call"""
    d = get_json()
    missing = require_fields(d, ["call_id", "action"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    call_id = int(d["call_id"])
    action = str(d["action"]).strip()  # "accept" or "reject"
    
    if action not in ["accept", "reject"]:
        return jsonify({"success": False, "msg": "Invalid action"}), 400
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Update call status
    status = "ACCEPTED" if action == "accept" else "REJECTED"
    cur.execute("UPDATE call_session SET status = ? WHERE id = ?", (status, call_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "status": status})

@app.route("/call/end", methods=["POST"])
def end_call():
    """NEW CODE: End a call"""
    d = get_json()
    missing = require_fields(d, ["call_id"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    call_id = int(d["call_id"])
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("UPDATE call_session SET status = 'ENDED' WHERE id = ?", (call_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

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
            conn = sqlite3.connect("freelancer.db")
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO notification (freelancer_id, message, created_at)
                VALUES (?, ?, ?)
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
    missing = require_fields(d, ["client_id", "title", "description", "category", "skills", "budget_type", "budget_min", "budget_max"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    try:
        client_id = int(d["client_id"])
        title = str(d["title"]).strip()
        description = str(d["description"]).strip()
        category = str(d["category"]).strip()
        skills = str(d["skills"]).strip()
        budget_type = str(d["budget_type"]).strip().upper()
        if budget_type not in ("FIXED", "HOURLY", "EVENT"):
            return jsonify({"success": False, "msg": "Invalid budget_type"}), 400
        budget_min = float(d["budget_min"])
        budget_max = float(d["budget_max"])
    except Exception:
        return jsonify({"success": False, "msg": "Invalid payload"}), 400
    conn = sqlite3.connect("freelancer.db")
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO project_post (client_id, title, description, category, skills, budget_type, budget_min, budget_max, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        """, (client_id, title, description, category, skills, budget_type, budget_min, budget_max, now_ts()))
        pid = cur.lastrowid
        conn.commit()
        return jsonify({"success": True, "project_id": pid})
    finally:
        conn.close()


@app.route("/client/projects", methods=["GET"])
def client_projects_list():
    client_id = request.args.get("client_id", "")
    try:
        cid = int(client_id)
    except Exception:
        return jsonify({"success": False, "msg": "client_id required"}), 400
    conn = sqlite3.connect("freelancer.db")
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, description, category, skills, budget_type, budget_min, budget_max, status, created_at
            FROM project_post
            WHERE client_id=?
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
    conn = sqlite3.connect("freelancer.db")
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT client_id FROM project_post WHERE id=?", (pid,))
        r = cur.fetchone()
        if not r or int(r["client_id"]) != cid:
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        cur.execute("""
            SELECT id, freelancer_id, proposal_text, bid_amount, hourly_rate, event_base_fee, status, created_at
            FROM project_application
            WHERE project_id=?
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
    conn = sqlite3.connect("freelancer.db")
    try:
        cur = conn.cursor()
        cur.execute("SELECT client_id FROM project_post WHERE id=?", (pid,))
        r = cur.fetchone()
        if not r or int(r[0]) != cid:
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        cur.execute("UPDATE project_post SET status='CLOSED' WHERE id=?", (pid,))
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
    conn = sqlite3.connect("freelancer.db")
    try:
        cur = conn.cursor()
        cur.execute("SELECT client_id, title, budget_type FROM project_post WHERE id=?", (pid,))
        pr = cur.fetchone()
        if not pr or int(pr[0]) != cid:
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        project_title = pr[1]
        budget_type = (pr[2] or "FIXED").upper()
        cur.execute("""
            SELECT freelancer_id, bid_amount, hourly_rate, event_base_fee, status
            FROM project_application
            WHERE id=? AND project_id=?
        """, (aid, pid))
        ar = cur.fetchone()
        if not ar:
            return jsonify({"success": False, "msg": "Application not found"}), 404
        if ar[4] != "APPLIED":
            return jsonify({"success": False, "msg": "Application not in APPLIED state"}), 400
        freelancer_id = int(ar[0])
        bid_amount = ar[1] or 0
        hourly_rate = ar[2] or 0
        event_base_fee = ar[3] or 0
        if budget_type == "FIXED":
            proposed_budget = bid_amount
        elif budget_type == "HOURLY":
            proposed_budget = hourly_rate
        else:
            proposed_budget = event_base_fee
        cur.execute("UPDATE project_application SET status='ACCEPTED' WHERE id=?", (aid,))
        cur.execute("UPDATE project_post SET status='HIRED' WHERE id=?", (pid,))
        cur.execute("""
            INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, created_at, contract_type)
            VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)
        """, (cid, freelancer_id, project_title, proposed_budget, f"Created from project application #{aid}", now_ts(), budget_type))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()


@app.route("/freelancer/projects/feed", methods=["GET"])
def freelancer_projects_feed():
    conn = sqlite3.connect("freelancer.db")
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
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
    conn = sqlite3.connect("freelancer.db")
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM project_application WHERE project_id=? AND freelancer_id=?", (pid, fid))
        if cur.fetchone():
            return jsonify({"success": False, "msg": "Already applied"}), 400
        cur.execute("""
            INSERT INTO project_application (project_id, freelancer_id, proposal_text, bid_amount, hourly_rate, event_base_fee, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'APPLIED', ?)
        """, (pid, fid, proposal_text, bid_amount, hourly_rate, event_base_fee, now_ts()))
        conn.commit()
        return jsonify({"success": True})
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
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Check if hire request belongs to client and status is PAID
    cur.execute("""
        SELECT freelancer_id, status 
        FROM hire_request 
        WHERE id = ? AND client_id = ?
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
    cur.execute("SELECT id FROM review WHERE hire_request_id = ?", (hire_request_id,))
    if cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Already rated"}), 400
    
    # Get current freelancer stats
    cur.execute("""
        SELECT rating, total_projects, total_rating_sum 
        FROM freelancer_profile 
        WHERE freelancer_id = ?
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
        SET rating = ?, total_projects = ?, total_rating_sum = ?
        WHERE freelancer_id = ?
    """, (new_average, new_total_projects, new_total_rating_sum, freelancer_id))
    
    # Insert review
    cur.execute("""
        INSERT INTO review (hire_request_id, client_id, freelancer_id, rating, review_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (hire_request_id, client_id, freelancer_id, rating, review_text, now_ts()))
    
    # Update hire request status
    cur.execute("""
        UPDATE hire_request 
        SET status = 'RATED' 
        WHERE id = ?
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
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Fetch contract snapshot
    cur.execute("""
        SELECT contract_type, contract_hourly_rate, contract_overtime_rate, max_daily_hours
        FROM hire_request 
        WHERE id = ? AND freelancer_id = ?
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Verify contract is HOURLY
    cur.execute("""
        SELECT contract_type
        FROM hire_request 
        WHERE id = ?
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
        WHERE hire_request_id = ? AND approved = 1
    """, (hire_request_id,))
    
    result = cur.fetchone()
    total_amount = result[0] if result and result[0] else 0
    
    # Create invoice entry
    from datetime import datetime, timedelta
    week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = datetime.now().strftime("%Y-%m-%d")
    
    cur.execute("""
        INSERT INTO invoice (hire_request_id, total_amount, week_start, week_end, created_at)
        VALUES (?, ?, ?, ?, ?)
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
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Verify contract is EVENT
    cur.execute("""
        SELECT contract_type, event_base_fee, event_included_hours, event_overtime_rate, advance_paid
        FROM hire_request 
        WHERE id = ?
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


if __name__ == "__main__":
    app.run(debug=True)
