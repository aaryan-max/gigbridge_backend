from flask import Flask, request, jsonify
import sqlite3
import random
import time
import smtplib
import os
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash

from database import create_tables
from categories import is_valid_category

# ============================================================
# APP INIT
# ============================================================

app = Flask(__name__)
create_tables()

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

    return jsonify({"success": True})

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

    return jsonify({"success": True})

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
        freelancer_id = cur.lastrowid  # ✅ auto-login return

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

# ============================================================
# LOGIN APIs (CORE LOGIC SAME)
# ============================================================

@app.route("/client/login", methods=["POST"])
def client_login():
    d = get_json()
    missing = require_fields(d, ["email", "password"])
    if missing:
        return jsonify({}), 400

    email = str(d["email"]).strip().lower()
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
        return jsonify({"client_id": row[0]})

    return jsonify({})

@app.route("/freelancer/login", methods=["POST"])
def freelancer_login():
    d = get_json()
    missing = require_fields(d, ["email", "password"])
    if missing:
        return jsonify({}), 400

    email = str(d["email"]).strip().lower()
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
        return jsonify({"freelancer_id": row[0]})

    return jsonify({})

# ============================================================
# PROFILES
# ============================================================

@app.route("/client/profile", methods=["POST"])
def client_profile():
    d = get_json()
    missing = require_fields(d, ["client_id", "phone", "location", "bio"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO client_profile (client_id, phone, location, bio)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(client_id) DO UPDATE SET
        phone=excluded.phone, location=excluded.location, bio=excluded.bio
    """, (d["client_id"], d["phone"], d["location"], d["bio"]))
    conn.commit()
    conn.close()

    # Add notification
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO notification (client_id, message, created_at)
        VALUES (?, ?, ?)
    """, (d["client_id"], "Profile updated successfully", now_ts()))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route("/freelancer/profile", methods=["POST"])
def freelancer_profile():
    d = get_json()
    missing = require_fields(d, ["freelancer_id","title","skills","experience","min_budget","max_budget","bio","category"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    if not is_valid_category(d["category"]):
        return jsonify({"success": False, "msg": "Invalid category"}), 400

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO freelancer_profile
        (freelancer_id,title,skills,experience,min_budget,max_budget,bio,category)
        VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(freelancer_id) DO UPDATE SET
        title=excluded.title,
        skills=excluded.skills,
        experience=excluded.experience,
        min_budget=excluded.min_budget,
        max_budget=excluded.max_budget,
        bio=excluded.bio,
        category=excluded.category
    """, (
        d["freelancer_id"], d["title"], d["skills"],
        int(d["experience"]), float(d["min_budget"]), float(d["max_budget"]),
        d["bio"], d["category"]
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# ============================================================
# SEARCH (Category + Budget) + includes freelancer NAME
# ============================================================

@app.route("/freelancers/search", methods=["GET"])
def freelancers_search():
    category = (request.args.get("category", "") or "").strip().lower()
    budget = float(request.args.get("budget", 0))

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT
            fp.freelancer_id,
            f.name,
            fp.title,
            fp.skills,
            fp.experience,
            fp.min_budget,
            fp.max_budget,
            fp.rating,
            fp.category
        FROM freelancer_profile fp
        JOIN freelancer f ON f.id = fp.freelancer_id
        WHERE fp.min_budget <= ?
          AND fp.max_budget >= ?
    """, (budget, budget))

    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        if category and (category != str(r[8]).strip().lower()):
            continue
        results.append({
            "freelancer_id": r[0],
            "name": r[1],
            "title": r[2],
            "skills": r[3],
            "experience": r[4],
            "budget_range": f"{r[5]} - {r[6]}",
            "rating": r[7],
            "category": r[8],
        })
    return jsonify(results)

# ============================================================
# NEW: VIEW ALL FREELANCERS (even if client didn’t search)
# ============================================================

@app.route("/freelancers/all", methods=["GET"])
def freelancers_all():
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT
            f.id,
            f.name,
            COALESCE(fp.title, ''),
            COALESCE(fp.skills, ''),
            COALESCE(fp.experience, 0),
            COALESCE(fp.min_budget, 0),
            COALESCE(fp.max_budget, 0),
            COALESCE(fp.rating, 0),
            COALESCE(fp.category, ''),
            COALESCE(fp.bio, '')
        FROM freelancer f
        LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
        ORDER BY f.id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "freelancer_id": r[0],
            "name": r[1],
            "title": r[2],
            "skills": r[3],
            "experience": r[4],
            "budget_range": f"{r[5]} - {r[6]}",
            "rating": r[7],
            "category": r[8],
            "bio": r[9],
        })
    return jsonify(out)

# ============================================================
# NEW: VIEW ONE FREELANCER (full details)
# ============================================================

@app.route("/freelancers/<int:freelancer_id>", methods=["GET"])
def freelancer_details(freelancer_id: int):
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT
            f.id,
            f.name,
            f.email,
            COALESCE(fp.title, ''),
            COALESCE(fp.skills, ''),
            COALESCE(fp.experience, 0),
            COALESCE(fp.min_budget, 0),
            COALESCE(fp.max_budget, 0),
            COALESCE(fp.rating, 0),
            COALESCE(fp.category, ''),
            COALESCE(fp.bio, '')
        FROM freelancer f
        LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
        WHERE f.id = ?
    """, (freelancer_id,))
    r = cur.fetchone()
    conn.close()

    if not r:
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404

    return jsonify({
        "success": True,
        "freelancer_id": r[0],
        "name": r[1],
        "email": r[2],
        "title": r[3],
        "skills": r[4],
        "experience": r[5],
        "min_budget": r[6],
        "max_budget": r[7],
        "rating": r[8],
        "category": r[9],
        "bio": r[10],
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

    # Add notification - get freelancer name
    cur.execute("SELECT name FROM freelancer WHERE id=?", (int(d["freelancer_id"]),))
    freelancer_row = cur.fetchone()
    freelancer_name = freelancer_row[0] if freelancer_row else "Freelancer"
    
    cur.execute("""
        INSERT INTO notification (client_id, message, created_at)
        VALUES (?, ?, ?)
    """, (int(d["client_id"]), f"You messaged {freelancer_name}", now_ts()))

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
    return jsonify(chat)

# ============================================================
# NEW: HIRE (Client -> Freelancer)
# ============================================================

@app.route("/client/hire", methods=["POST"])
def client_hire():
    d = get_json()
    missing = require_fields(d, ["client_id", "freelancer_id", "proposed_budget"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    client_id = int(d["client_id"])
    freelancer_id = int(d["freelancer_id"])
    proposed_budget = float(d["proposed_budget"])
    note = str(d.get("note", "")).strip()

    # simple existence check
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM freelancer WHERE id=?", (freelancer_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Freelancer not found"}), 404

    job_title = str(d.get("job_title", "")).strip()
    cur.execute("""
        INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
    """, (client_id, freelancer_id, job_title, proposed_budget, note, now_ts()))
    req_id = cur.lastrowid

    # Add notification
    notification_msg = f'Job "{job_title if job_title else "Untitled"}" posted'
    cur.execute("""
        INSERT INTO notification (client_id, message, created_at)
        VALUES (?, ?, ?)
    """, (client_id, notification_msg, now_ts()))

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
        SELECT id, client_id, proposed_budget, note, status, created_at
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
        conn = sqlite3.connect("freelancer.db")
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
# RUN
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)