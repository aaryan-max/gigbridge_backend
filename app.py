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

    try:
        cur.execute(
            "INSERT INTO clients (name, email, password) VALUES (?, ?, ?)",
            (data["name"], data["email"], data["password"])
        )
        db.commit()
        return jsonify({"message": "Client registered successfully"})
    except:
        return jsonify({"message": "Client already exists"})

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
        return jsonify({"message": "Client login successful", "client_id": user[0]})
    return jsonify({"message": "Invalid credentials"})

# ---------------- CLIENT PROFILE ----------------
@app.route("/client/profile", methods=["POST"])
def client_profile():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO client_profile
        (client_id, company_name, phone, location, bio)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["client_id"],
        data["company_name"],
        data["phone"],
        data["location"],
        data["bio"]
    ))

    db.commit()
    return jsonify({"message": "Client profile saved"})

# ---------------- FREELANCER SIGNUP ----------------
@app.route("/freelancer/signup", methods=["POST"])
def freelancer_signup():
    data = request.json
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute(
            "INSERT INTO freelancers (name, email, password) VALUES (?, ?, ?)",
            (data["name"], data["email"], data["password"])
        )
        db.commit()
        return jsonify({"message": "Freelancer registered successfully"})
    except:
        return jsonify({"message": "Freelancer already exists"})

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
        return jsonify({"message": "Freelancer login successful", "freelancer_id": user[0]})
    return jsonify({"message": "Invalid credentials"})

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
        data["skills"],
        data["experience"],
        data["min_budget"],
        data["max_budget"],
        data["bio"]
    ))

    db.commit()
    return jsonify({"message": "Freelancer profile saved"})

# ---------------- SEARCH FREELANCERS ----------------
@app.route("/freelancers/search", methods=["GET"])
def search_freelancers():
    skill = request.args.get("skill")
    budget = request.args.get("budget")

    db = get_db()
    cur = db.cursor()

    query = """
        SELECT * FROM freelancer_profile
        WHERE skills LIKE ?
        AND min_budget <= ?
        AND availability='available'
        ORDER BY rating DESC
    """

    cur.execute(query, (f"%{skill}%", budget))
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

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)
