from flask import Flask, request, jsonify
import sqlite3
from database import create_tables
from categories import is_valid_category, normalize

app = Flask(__name__)
create_tables()

# ---------- CLIENT ----------
@app.route("/client/signup", methods=["POST"])
def client_signup():
    d = request.json
    try:
        conn = sqlite3.connect("client.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO client (name,email,password) VALUES (?,?,?)",
            (d["name"], d["email"], d["password"])
        )
        conn.commit()
        return jsonify({"success": True})
    except:
        return jsonify({"success": False, "msg": "Client exists"})


@app.route("/client/login", methods=["POST"])
def client_login():
    d = request.json
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM client WHERE email=? AND password=?",
        (d["email"], d["password"])
    )
    row = cur.fetchone()
    return jsonify({"client_id": row[0]}) if row else jsonify({})


@app.route("/client/profile", methods=["POST"])
def client_profile():
    d = request.json
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO client_profile VALUES (?,?,?,?)",
        (d["client_id"], d["phone"], d["location"], d["bio"])
    )
    conn.commit()
    return jsonify({"success": True})


# ---------- FREELANCER ----------
@app.route("/freelancer/signup", methods=["POST"])
def freelancer_signup():
    d = request.json
    try:
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO freelancer (name,email,password) VALUES (?,?,?)",
            (d["name"], d["email"], d["password"])
        )
        conn.commit()
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})


@app.route("/freelancer/login", methods=["POST"])
def freelancer_login():
    d = request.json
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM freelancer WHERE email=? AND password=?",
        (d["email"], d["password"])
    )
    row = cur.fetchone()
    return jsonify({"freelancer_id": row[0]}) if row else jsonify({})


@app.route("/freelancer/profile", methods=["POST"])
def freelancer_profile():
    d = request.json

    if not is_valid_category(d["category"]):
        return jsonify({
            "success": False,
            "msg": "Invalid category"
        })

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO freelancer_profile
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        d["freelancer_id"],
        d["title"],
        d["skills"],
        d["experience"],
        d["min_budget"],
        d["max_budget"],
        0,
        d["bio"],
        normalize(d["category"])
    ))

    conn.commit()
    return jsonify({"success": True, "msg": "Profile updated"})


# ---------- SEARCH ----------
@app.route("/freelancers/search", methods=["GET"])
def search_freelancers():
    skill = normalize(request.args.get("skill", ""))
    budget = float(request.args.get("budget", 0))

    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT freelancer_id,title,skills,experience,min_budget,max_budget,rating
        FROM freelancer_profile
        WHERE lower(skills) LIKE ?
        AND min_budget <= ?
    """, (f"%{skill}%", budget))

    rows = cur.fetchall()
    result = []

    for r in rows:
        result.append({
            "freelancer_id": r[0],
            "title": r[1],
            "skills": r[2],
            "experience": r[3],
            "budget_range": f"{r[4]} - {r[5]}",
            "rating": r[6]
        })

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
