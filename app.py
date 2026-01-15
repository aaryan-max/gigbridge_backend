from flask import Flask, request, jsonify
from database import client_db, freelancer_db, create_tables

app = Flask(__name__)

# Create tables at startup
create_tables()

# ---------------- CLIENT SIGNUP ----------------
@app.route("/client/signup", methods=["POST"])
def client_signup():
    data = request.json
    db = client_db()
    cur = db.cursor()

    try:
        cur.execute(
            "INSERT INTO client (name, email, password) VALUES (?, ?, ?)",
            (data["name"], data["email"], data["password"])
        )
        db.commit()
        return jsonify({"message": "Client Registered Successfully"})
    except:
        return jsonify({"message": "Client already exists"})


# ---------------- CLIENT LOGIN ----------------
@app.route("/client/login", methods=["POST"])
def client_login():
    data = request.json
    db = client_db()
    cur = db.cursor()

    cur.execute(
        "SELECT * FROM client WHERE email=? AND password=?",
        (data["email"], data["password"])
    )

    user = cur.fetchone()

    if user:
        return jsonify({"message": "Client Login Successful"})
    else:
        return jsonify({"message": "Invalid Client Credentials"})


# ---------------- FREELANCER SIGNUP ----------------
@app.route("/freelancer/signup", methods=["POST"])
def freelancer_signup():
    data = request.json
    db = freelancer_db()
    cur = db.cursor()

    try:
        cur.execute(
            "INSERT INTO freelancer (name, email, password, skill, experience) VALUES (?, ?, ?, ?, ?)",
            (data["name"], data["email"], data["password"], data["skill"], data["experience"])
        )
        db.commit()
        return jsonify({"message": "Freelancer Registered Successfully"})
    except:
        return jsonify({"message": "Freelancer already exists"})


# ---------------- FREELANCER LOGIN ----------------
@app.route("/freelancer/login", methods=["POST"])
def freelancer_login():
    data = request.json
    db = freelancer_db()
    cur = db.cursor()

    cur.execute(
        "SELECT * FROM freelancer WHERE email=? AND password=?",
        (data["email"], data["password"])
    )

    user = cur.fetchone()

    if user:
        return jsonify({"message": "Freelancer Login Successful"})
    else:
        return jsonify({"message": "Invalid Freelancer Credentials"})


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)
