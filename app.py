# app.py (FULL UPDATED - copy paste)
from flask import Flask, request, jsonify
import sqlite3
import random
import time
import os
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage

from database import create_tables
from categories import is_valid_category, normalize

app = Flask(__name__)
create_tables()

# ---------- EMAIL CONFIG (ENV VARS) ----------
# Set these in your system / terminal:
# Windows PowerShell:
#   $env:GIGBRIDGE_SENDER_EMAIL="your@gmail.com"
#   $env:GIGBRIDGE_APP_PASSWORD="your-app-password"
SENDER_EMAIL = os.getenv("GIGBRIDGE_SENDER_EMAIL", "")
APP_PASSWORD = os.getenv("GIGBRIDGE_APP_PASSWORD", "")

OTP_TTL_SECONDS = 5 * 60  # 5 minutes


# ---------- HELPERS ----------
def _json():
    return request.get_json(silent=True) or {}


def _require_fields(data, fields):
    missing = [f for f in fields if f not in data or str(data.get(f)).strip() == ""]
    return missing


def _send_email(to_email, subject, body):
    if not SENDER_EMAIL or not APP_PASSWORD:
        # Avoid crashing server if env vars are not set
        raise RuntimeError("Email credentials not configured (env vars missing)")

    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.send_message(msg)
    server.quit()


def send_login_email(to_email, name, role, action):
    _send_email(
        to_email,
        "🎉 GigBridge Login Successful",
        f"""Hi {name},

Your {action} as a {role} on GigBridge was successful ✅

Welcome to GigBridge 🚀
"""
    )


def send_otp_email(to_email, otp):
    _send_email(
        to_email,
        "🔐 GigBridge OTP Verification",
        f"""Your OTP for GigBridge signup is:

🔢 OTP: {otp}

Valid for {OTP_TTL_SECONDS // 60} minutes.
Do NOT share it with anyone.
"""
    )


def _now():
    return int(time.time())


def _email_ok(email: str) -> bool:
    email = (email or "").strip()
    return ("@" in email) and ("." in email) and (len(email) <= 254)


# ================= OTP (DB-based) =================

@app.route("/client/send-otp", methods=["POST"])
def client_send_otp():
    d = _json()
    missing = _require_fields(d, ["email"])
    if missing:
        return jsonify({"success": False, "msg": f"Missing: {', '.join(missing)}"}), 400

    email = d["email"].strip().lower()
    if not _email_ok(email):
        return jsonify({"success": False, "msg": "Invalid email"}), 400

    otp = str(random.randint(100000, 999999))
    expires_at = _now() + OTP_TTL_SECONDS

    try:
        conn = sqlite3.connect("client.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO client_otp (email, otp, expires_at) VALUES (?,?,?)",
            (email, otp, expires_at),
        )
        conn.commit()
        conn.close()

        send_otp_email(email, otp)
        return jsonify({"success": True, "msg": "OTP sent"})
    except Exception as e:
        return jsonify({"success": False, "msg": f"OTP send failed: {str(e)}"}), 500


@app.route("/client/verify-otp", methods=["POST"])
def client_verify_otp():
    d = _json()
    missing = _require_fields(d, ["name", "email", "password", "otp"])
    if missing:
        return jsonify({"success": False, "msg": f"Missing: {', '.join(missing)}"}), 400

    name = d["name"].strip()
    email = d["email"].strip().lower()
    password = str(d["password"])
    otp = str(d["otp"]).strip()

    if not _email_ok(email):
        return jsonify({"success": False, "msg": "Invalid email"}), 400
    if len(password) < 3:
        return jsonify({"success": False, "msg": "Password too short"}), 400

    # Check OTP from DB + expiry
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("SELECT otp, expires_at FROM client_otp WHERE email=?", (email,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "msg": "OTP not found. Please resend OTP."}), 400

    db_otp, expires_at = row[0], int(row[1])
    if _now() > expires_at:
        cur.execute("DELETE FROM client_otp WHERE email=?", (email,))
        conn.commit()
        conn.close()
        return jsonify({"success": False, "msg": "OTP expired. Please resend OTP."}), 400

    if db_otp != otp:
        conn.close()
        return jsonify({"success": False, "msg": "Invalid OTP"}), 400

    # Create account (core signup logic same)
    try:
        hashed = generate_password_hash(password)
        cur.execute(
            "INSERT INTO client (name,email,password) VALUES (?,?,?)",
            (name, email, hashed)
        )
        client_id = cur.lastrowid

        # consume otp
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
        return jsonify({"success": False, "msg": "Client exists"}), 409
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500


@app.route("/freelancer/send-otp", methods=["POST"])
def freelancer_send_otp():
    d = _json()
    missing = _require_fields(d, ["email"])
    if missing:
        return jsonify({"success": False, "msg": f"Missing: {', '.join(missing)}"}), 400

    email = d["email"].strip().lower()
    if not _email_ok(email):
        return jsonify({"success": False, "msg": "Invalid email"}), 400

    otp = str(random.randint(100000, 999999))
    expires_at = _now() + OTP_TTL_SECONDS

    try:
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO freelancer_otp (email, otp, expires_at) VALUES (?,?,?)",
            (email, otp, expires_at),
        )
        conn.commit()
        conn.close()

        send_otp_email(email, otp)
        return jsonify({"success": True, "msg": "OTP sent"})
    except Exception as e:
        return jsonify({"success": False, "msg": f"OTP send failed: {str(e)}"}), 500


@app.route("/freelancer/verify-otp", methods=["POST"])
def freelancer_verify_otp():
    d = _json()
    missing = _require_fields(d, ["name", "email", "password", "otp"])
    if missing:
        return jsonify({"success": False, "msg": f"Missing: {', '.join(missing)}"}), 400

    name = d["name"].strip()
    email = d["email"].strip().lower()
    password = str(d["password"])
    otp = str(d["otp"]).strip()

    if not _email_ok(email):
        return jsonify({"success": False, "msg": "Invalid email"}), 400
    if len(password) < 3:
        return jsonify({"success": False, "msg": "Password too short"}), 400

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT otp, expires_at FROM freelancer_otp WHERE email=?", (email,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "msg": "OTP not found. Please resend OTP."}), 400

    db_otp, expires_at = row[0], int(row[1])
    if _now() > expires_at:
        cur.execute("DELETE FROM freelancer_otp WHERE email=?", (email,))
        conn.commit()
        conn.close()
        return jsonify({"success": False, "msg": "OTP expired. Please resend OTP."}), 400

    if db_otp != otp:
        conn.close()
        return jsonify({"success": False, "msg": "Invalid OTP"}), 400

    try:
        hashed = generate_password_hash(password)
        cur.execute(
            "INSERT INTO freelancer (name,email,password) VALUES (?,?,?)",
            (name, email, hashed)
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
        return jsonify({"success": False, "msg": "Freelancer exists"}), 409
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "msg": f"Server error: {str(e)}"}), 500


# ================= LOGIN APIs (CORE LOGIC SAME) =================

@app.route("/client/login", methods=["POST"])
def client_login():
    d = _json()
    missing = _require_fields(d, ["email", "password"])
    if missing:
        return jsonify({"success": False, "msg": f"Missing: {', '.join(missing)}"}), 400

    email = d["email"].strip().lower()
    password = str(d["password"])

    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("SELECT id,password,name FROM client WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row[1], password):
        try:
            send_login_email(email, row[2], "Client", "login")
        except:
            pass
        return jsonify({"client_id": row[0], "success": True})

    # keep old behavior (no client_id) so your CLI still works
    return jsonify({"success": False, "msg": "Invalid credentials"})


@app.route("/freelancer/login", methods=["POST"])
def freelancer_login():
    d = _json()
    missing = _require_fields(d, ["email", "password"])
    if missing:
        return jsonify({"success": False, "msg": f"Missing: {', '.join(missing)}"}), 400

    email = d["email"].strip().lower()
    password = str(d["password"])

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT id,password,name FROM freelancer WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row[1], password):
        try:
            send_login_email(email, row[2], "Freelancer", "login")
        except:
            pass
        return jsonify({"freelancer_id": row[0], "success": True})

    return jsonify({"success": False, "msg": "Invalid credentials"})


# ================= PROFILES =================

@app.route("/client/profile", methods=["POST"])
def client_profile():
    d = _json()
    missing = _require_fields(d, ["client_id", "phone", "location", "bio"])
    if missing:
        return jsonify({"success": False, "msg": f"Missing: {', '.join(missing)}"}), 400

    try:
        client_id = int(d["client_id"])
    except:
        return jsonify({"success": False, "msg": "client_id must be an integer"}), 400

    phone = str(d["phone"]).strip()
    if not (phone.isdigit() and len(phone) == 10):
        return jsonify({"success": False, "msg": "Phone must be 10 digits"}), 400

    location = str(d["location"]).strip()
    bio = str(d["bio"]).strip()

    conn = sqlite3.connect("client.db")
    cur = conn.cursor()

    # ensure client exists
    cur.execute("SELECT id FROM client WHERE id=?", (client_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Client not found"}), 404

    cur.execute("""
        INSERT INTO client_profile (client_id, phone, location, bio)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(client_id) DO UPDATE SET
            phone=excluded.phone,
            location=excluded.location,
            bio=excluded.bio
    """, (client_id, phone, location, bio))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": "Client profile saved"})


@app.route("/freelancer/profile", methods=["POST"])
def freelancer_profile():
    d = _json()
    missing = _require_fields(d, ["freelancer_id", "title", "skills", "experience",
                                 "min_budget", "max_budget", "bio", "category"])
    if missing:
        return jsonify({"success": False, "msg": f"Missing: {', '.join(missing)}"}), 400

    try:
        freelancer_id = int(d["freelancer_id"])
        experience = int(d["experience"])
        min_budget = float(d["min_budget"])
        max_budget = float(d["max_budget"])
    except:
        return jsonify({"success": False, "msg": "experience must be int, budgets must be numbers"}), 400

    if experience < 0:
        return jsonify({"success": False, "msg": "experience cannot be negative"}), 400
    if min_budget < 0 or max_budget < 0:
        return jsonify({"success": False, "msg": "budget cannot be negative"}), 400
    if max_budget < min_budget:
        return jsonify({"success": False, "msg": "max_budget must be >= min_budget"}), 400

    title = str(d["title"]).strip()
    skills = str(d["skills"]).strip()
    bio = str(d["bio"]).strip()

    category_raw = str(d["category"])
    if not is_valid_category(category_raw):
        return jsonify({"success": False, "msg": "Invalid category"}), 400
    category = category_raw.strip()

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()

    # ensure freelancer exists
    cur.execute("SELECT id FROM freelancer WHERE id=?", (freelancer_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404

    cur.execute("""
        INSERT INTO freelancer_profile
            (freelancer_id, title, skills, experience, min_budget, max_budget,
             bio, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(freelancer_id) DO UPDATE SET
            title=excluded.title,
            skills=excluded.skills,
            experience=excluded.experience,
            min_budget=excluded.min_budget,
            max_budget=excluded.max_budget,
            bio=excluded.bio,
            category=excluded.category
    """, (freelancer_id, title, skills, experience, min_budget, max_budget, bio, category))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": "Freelancer profile saved"})


# ================= SEARCH =================

@app.route("/freelancers/search", methods=["GET"])
def search_freelancers():
    skill = (request.args.get("skill") or "").strip().lower()
    budget_raw = (request.args.get("budget") or "").strip()
    category = (request.args.get("category") or "").strip()

    # budget is optional but your CLI always sends it
    try:
        budget = float(budget_raw) if budget_raw != "" else None
    except:
        return jsonify({"success": False, "msg": "budget must be a number"}), 400

    q = """
        SELECT
            fp.freelancer_id,
            fp.title,
            fp.skills,
            fp.experience,
            fp.min_budget,
            fp.max_budget,
            fp.rating
        FROM freelancer_profile fp
        WHERE 1=1
    """
    params = []

    if skill:
        q += " AND lower(fp.skills) LIKE ? "
        params.append(f"%{skill}%")

    if budget is not None:
        # client budget should be able to afford freelancer range
        q += " AND fp.min_budget <= ? "
        params.append(budget)

    if category:
        # validate only if provided
        if not is_valid_category(category):
            return jsonify({"success": False, "msg": "Invalid category"}), 400
        q += " AND lower(fp.category) = ? "
        params.append(category.strip().lower())

    q += " ORDER BY fp.rating DESC, fp.experience DESC"

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "freelancer_id": r[0],
            "title": r[1],
            "skills": r[2],
            "experience": r[3],
            "budget_range": f"{r[4]} - {r[5]}",
            "rating": r[6]
        })

    return jsonify(out)


if __name__ == "__main__":
    app.run(debug=True)