from flask import Flask, request, jsonify
import sqlite3
import random
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage
from database import create_tables
from categories import is_valid_category

app = Flask(__name__)
create_tables()

# ---------- EMAIL CONFIG ----------
SENDER_EMAIL = "gigbridgee@gmail.com"
APP_PASSWORD = "tvtp lklb vcnr wmzt"

# ---------- OTP STORE ----------
otp_store = {}   # { email: otp }

# ---------- EMAIL HELPERS ----------
def send_email(to_email, subject, body):
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

OTP: {otp}

Do NOT share it with anyone.
"""
    )


def get_json_or_400():
    data = request.get_json(silent=True)
    if data is None:
        return None, jsonify({"success": False, "msg": "Invalid JSON"}), 400
    return data, None


# ================= OTP APIs =================

@app.route("/client/send-otp", methods=["POST"])
def client_send_otp():
    d, err = get_json_or_400()
    if err:
        return err
    email = d.get("email")
    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp
    send_otp_email(email, otp)
    return jsonify({"success": True})


@app.route("/client/verify-otp", methods=["POST"])
def client_verify_otp():
    d, err = get_json_or_400()
    if err:
        return err

    email = d["email"]
    if otp_store.get(email) != d["otp"]:
        return jsonify({"success": False, "msg": "Invalid OTP"})

    try:
        conn = sqlite3.connect("client.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO client (name,email,password) VALUES (?,?,?)",
            (d["name"], email, generate_password_hash(d["password"]))
        )
        conn.commit()
        conn.close()
        del otp_store[email]
        send_login_email(email, d["name"], "Client", "signup")
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "msg": "Client exists"})


@app.route("/freelancer/send-otp", methods=["POST"])
def freelancer_send_otp():
    d, err = get_json_or_400()
    if err:
        return err
    email = d.get("email")
    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp
    send_otp_email(email, otp)
    return jsonify({"success": True})


@app.route("/freelancer/verify-otp", methods=["POST"])
def freelancer_verify_otp():
    d, err = get_json_or_400()
    if err:
        return err

    email = d["email"]
    if otp_store.get(email) != d["otp"]:
        return jsonify({"success": False, "msg": "Invalid OTP"})

    try:
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO freelancer (name,email,password) VALUES (?,?,?)",
            (d["name"], email, generate_password_hash(d["password"]))
        )
        conn.commit()
        conn.close()
        del otp_store[email]
        send_login_email(email, d["name"], "Freelancer", "signup")
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "msg": "Freelancer exists"})


# ================= LOGIN APIs =================

@app.route("/client/login", methods=["POST"])
def client_login():
    d, _ = get_json_or_400()
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("SELECT id,password,name FROM client WHERE email=?", (d["email"],))
    row = cur.fetchone()
    conn.close()
    if row and check_password_hash(row[1], d["password"]):
        send_login_email(d["email"], row[2], "Client", "login")
        return jsonify({"client_id": row[0]})
    return jsonify({})


@app.route("/freelancer/login", methods=["POST"])
def freelancer_login():
    d, _ = get_json_or_400()
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT id,password,name FROM freelancer WHERE email=?", (d["email"],))
    row = cur.fetchone()
    conn.close()
    if row and check_password_hash(row[1], d["password"]):
        send_login_email(d["email"], row[2], "Freelancer", "login")
        return jsonify({"freelancer_id": row[0]})
    return jsonify({})

# ---------- FREELANCER PROFILE ----------
@app.route("/freelancer/profile", methods=["POST"])
def freelancer_profile():
    d = request.get_json()

    if not d or "freelancer_id" not in d:
        return jsonify({"success": False, "msg": "freelancer_id required"}), 400

    if not is_valid_category(d.get("category", "")):
        return jsonify({"success": False, "msg": "Invalid category"}), 400

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO freelancer_profile
        (freelancer_id, title, skills, experience,
         min_budget, max_budget, rating, total_projects, bio, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(freelancer_id) DO UPDATE SET
            title=excluded.title,
            skills=excluded.skills,
            experience=excluded.experience,
            min_budget=excluded.min_budget,
            max_budget=excluded.max_budget,
            bio=excluded.bio,
            category=excluded.category
    """, (
        d["freelancer_id"],
        d.get("title", ""),
        d.get("skills", ""),
        int(d.get("experience", 0)),
        float(d.get("min_budget", 0)),
        float(d.get("max_budget", 0)),
        0,
        0,
        d.get("bio", ""),
        d.get("category", "").lower()
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "msg": "Profile updated"})

# ================= SEARCH (FIXED) =================

@app.route("/freelancers/search", methods=["GET"])
def freelancers_search():
    skill = request.args.get("skill", "").lower()
    budget = request.args.get("budget")

    try:
        budget = float(budget) if budget else None
    except:
        budget = None

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            freelancer_id,
            title,
            skills,
            experience,
            min_budget,
            max_budget,
            IFNULL(rating, 0)
        FROM freelancer_profile
    """)

    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        if skill and skill not in (r[1] + r[2]).lower():
            continue
        if budget and r[4] > budget:
            continue

        results.append({
            "freelancer_id": r[0],
            "title": r[1],
            "skills": r[2],
            "experience": r[3],
            "budget_range": f"{r[4]} - {r[5]}",
            "rating": r[6]
        })

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)
