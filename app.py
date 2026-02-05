from flask import Flask, request, jsonify
import sqlite3
import random
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage
from database import create_tables
from categories import is_valid_category, normalize

app = Flask(__name__)
create_tables()

# ---------- EMAIL CONFIG ----------
SENDER_EMAIL = "gigbridgee@gmail.com"
APP_PASSWORD = "tvtp lklb vcnr wmzt"

# ---------- OTP STORE (TEMPORARY) ----------
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

🔢 OTP: {otp}

This OTP is valid for a short time.
Do NOT share it with anyone.
"""
    )


# ================= OTP APIs =================

@app.route("/client/send-otp", methods=["POST"])
def client_send_otp():
    email = request.json["email"]
    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp
    send_otp_email(email, otp)
    return jsonify({"success": True})


@app.route("/client/verify-otp", methods=["POST"])
def client_verify_otp():
    d = request.json
    email = d["email"]

    if otp_store.get(email) != d["otp"]:
        return jsonify({"success": False, "msg": "Invalid OTP"})

    try:
        conn = sqlite3.connect("client.db")
        cur = conn.cursor()
        hashed = generate_password_hash(d["password"])

        cur.execute(
            "INSERT INTO client (name,email,password) VALUES (?,?,?)",
            (d["name"], email, hashed)
        )
        conn.commit()
        conn.close()

        del otp_store[email]
        send_login_email(email, d["name"], "Client", "signup")
        return jsonify({"success": True})

    except:
        return jsonify({"success": False, "msg": "Client exists"})


@app.route("/freelancer/send-otp", methods=["POST"])
def freelancer_send_otp():
    email = request.json["email"]
    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp
    send_otp_email(email, otp)
    return jsonify({"success": True})


@app.route("/freelancer/verify-otp", methods=["POST"])
def freelancer_verify_otp():
    d = request.json
    email = d["email"]

    if otp_store.get(email) != d["otp"]:
        return jsonify({"success": False, "msg": "Invalid OTP"})

    try:
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        hashed = generate_password_hash(d["password"])

        cur.execute(
            "INSERT INTO freelancer (name,email,password) VALUES (?,?,?)",
            (d["name"], email, hashed)
        )
        conn.commit()
        conn.close()

        del otp_store[email]
        send_login_email(email, d["name"], "Freelancer", "signup")
        return jsonify({"success": True})

    except:
        return jsonify({"success": False, "msg": "Freelancer exists"})


# ================= EXISTING LOGIN APIs (UNCHANGED) =================

@app.route("/client/login", methods=["POST"])
def client_login():
    d = request.json
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
    d = request.json
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()

    cur.execute("SELECT id,password,name FROM freelancer WHERE email=?", (d["email"],))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row[1], d["password"]):
        send_login_email(d["email"], row[2], "Freelancer", "login")
        return jsonify({"freelancer_id": row[0]})

    return jsonify({})


# ---- REST OF YOUR FILE (profile, search, dashboard) REMAINS SAME ----

if __name__ == "__main__":
    app.run(debug=True)
