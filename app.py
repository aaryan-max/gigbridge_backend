from flask import Flask, request, jsonify
from database import get_db, init_db

app = Flask(__name__)
init_db()

# ---------------- CLIENT SIGNUP ----------------
@app.route("/client/signup", methods=["POST"])
def client_signup():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM clients WHERE email=?", (data["email"],))
    if cur.fetchone():
        return jsonify({"success": False, "message": "Client already exists"})

    cur.execute(
        "INSERT INTO clients (name, email, password) VALUES (?, ?, ?)",
        (data["name"], data["email"], data["password"])
    )
    db.commit()
    return jsonify({"success": True, "message": "Client registered successfully"})


# ---------------- CLIENT LOGIN ----------------
@app.route("/client/login", methods=["POST"])
def client_login():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT * FROM clients WHERE email=? AND password=?",
        (data["email"], data["password"])
    )

    user = cur.fetchone()
    if user:
        return jsonify({"success": True, "client_id": user[0]})

    return jsonify({"success": False, "message": "Account not found. Please sign up first."})


# ---------------- CLIENT PROFILE ----------------
@app.route("/client/profile", methods=["POST"])
def client_profile():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO client_profile
        (client_id, phone, location, bio)
        VALUES (?, ?, ?, ?)
    """, (
        data["client_id"],
        data["phone"],
        data["location"],
        data["bio"]
    ))

    db.commit()
    return jsonify({"success": True, "message": "Client profile saved"})


# ---------------- FREELANCER SIGNUP ----------------
@app.route("/freelancer/signup", methods=["POST"])
def freelancer_signup():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM freelancers WHERE email=?", (data["email"],))
    if cur.fetchone():
        return jsonify({"success": False, "message": "Freelancer already exists"})

    cur.execute(
        "INSERT INTO freelancers (name, email, password) VALUES (?, ?, ?)",
        (data["name"], data["email"], data["password"])
    )
    db.commit()
    return jsonify({"success": True, "message": "Freelancer registered successfully"})


# ---------------- FREELANCER LOGIN ----------------
@app.route("/freelancer/login", methods=["POST"])
def freelancer_login():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT * FROM freelancers WHERE email=? AND password=?",
        (data["email"], data["password"])
    )

    user = cur.fetchone()
    if user:
        return jsonify({"success": True, "freelancer_id": user[0]})

    return jsonify({"success": False, "message": "Account not found. Please sign up first."})


# ---------------- FREELANCER PROFILE ----------------
@app.route("/freelancer/profile", methods=["POST"])
def freelancer_profile():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO freelancer_profile
        (freelancer_id, title, skills, experience, min_budget, max_budget, bio)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["freelancer_id"],
        data["title"],
        data["skills"].lower(),   # normalize skills
        data["experience"],
        data["min_budget"],
        data["max_budget"],
        data["bio"]
    ))

    db.commit()
    return jsonify({"success": True, "message": "Freelancer profile saved"})


# ---------------- SEARCH FREELANCERS (FIXED) ----------------
@app.route("/freelancers/search", methods=["GET"])
def search_freelancers():
    skill = request.args.get("skill", "").lower()
    budget = request.args.get("budget")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT * FROM freelancer_profile
        WHERE LOWER(skills) LIKE ?
        AND min_budget <= ?
        ORDER BY rating DESC
    """, (f"%{skill}%", budget))

    results = cur.fetchall()
    freelancers = []

    for f in results:
        freelancers.append({
            "freelancer_id": f[0],
            "title": f[1],
            "skills": f[2],
            "experience": f[3],
            "budget_range": f"{f[4]} - {f[5]}",
            "rating": f[6],
            "bio": f[8]
        })

    return jsonify(freelancers)


if __name__ == "__main__":
    app.run(debug=True)
