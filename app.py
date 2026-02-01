from flask import Flask, request, jsonify
import sqlite3
from database import create_tables

app = Flask(__name__)
create_tables()

# ---------- CLIENT ----------
@app.route("/client/signup", methods=["POST"])
def client_signup():
    data = request.json
    try:
        conn = sqlite3.connect("client.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO client (name,email,password) VALUES (?,?,?)",
            (data["name"], data["email"], data["password"])
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/client/login", methods=["POST"])
def client_login():
    data = request.json
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM client WHERE email=? AND password=?",
        (data["email"], data["password"])
    )
    row = cur.fetchone()
    return jsonify({"client_id": row[0]}) if row else jsonify({})


@app.route("/client/profile", methods=["POST"])
def client_profile():
    d = request.json
    try:
        conn = sqlite3.connect("client.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO client_profile
            VALUES (?,?,?,?)
        """, (d["client_id"], d["phone"], d["location"], d["bio"]))
        conn.commit()
        return jsonify({"success": True, "msg": "Profile updated"})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})


# ---------- FREELANCER ----------
@app.route("/freelancer/signup", methods=["POST"])
def freelancer_signup():
    data = request.json
    try:
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO freelancer (name,email,password) VALUES (?,?,?)",
            (data["name"], data["email"], data["password"])
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})


@app.route("/freelancer/login", methods=["POST"])
def freelancer_login():
    data = request.json
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM freelancer WHERE email=? AND password=?",
        (data["email"], data["password"])
    )
    row = cur.fetchone()
    return jsonify({"freelancer_id": row[0]}) if row else jsonify({})


@app.route("/freelancer/profile", methods=["POST"])
def freelancer_profile():
    d = request.json
    try:
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO freelancer_profile
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            d["freelancer_id"], d["title"], d["skills"],
            d["experience"], d["min_budget"], d["max_budget"],
            d["bio"], 0
        ))
        conn.commit()
        return jsonify({"success": True, "msg": "Profile updated"})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})


# ---------- SEARCH ----------
@app.route("/freelancers/search", methods=["GET"])
def search_freelancers():
    skill = request.args.get("skill", "").lower()
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
