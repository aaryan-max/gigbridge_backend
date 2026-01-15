from database import client_db, freelancer_db, create_tables

create_tables()

# ---------- CLIENT AUTH ----------
def client_signup():
    print("\n--- Client Sign Up ---")
    name = input("Name: ")
    email = input("Email: ")
    password = input("Password: ")

    db = client_db()
    cur = db.cursor()

    try:
        cur.execute(
            "INSERT INTO client (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
        db.commit()
        print("✅ Client account created")
    except:
        print("❌ Account already exists. Please login.")

    db.close()


def client_login():
    print("\n--- Client Login ---")
    email = input("Email: ")
    password = input("Password: ")

    db = client_db()
    cur = db.cursor()

    # Check if account exists
    cur.execute("SELECT password FROM client WHERE email=?", (email,))
    record = cur.fetchone()

    if not record:
        print("❌ Account not found. Please sign up first.")
        db.close()
        return

    # Check password
    if record[0] == password:
        print("✅ Client login successful")
    else:
        print("❌ Incorrect password")

    db.close()


# ---------- FREELANCER AUTH ----------
def freelancer_signup():
    print("\n--- Freelancer Sign Up ---")
    name = input("Name: ")
    email = input("Email: ")
    password = input("Password: ")

    db = freelancer_db()
    cur = db.cursor()

    try:
        cur.execute(
            "INSERT INTO freelancer (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
        db.commit()
        print("✅ Freelancer account created")
    except:
        print("❌ Account already exists. Please login.")

    db.close()


def freelancer_login():
    print("\n--- Freelancer Login ---")
    email = input("Email: ")
    password = input("Password: ")

    db = freelancer_db()
    cur = db.cursor()

    # Check if account exists
    cur.execute("SELECT password FROM freelancer WHERE email=?", (email,))
    record = cur.fetchone()

    if not record:
        print("❌ Account not found. Please sign up first.")
        db.close()
        return

    # Check password
    if record[0] == password:
        print("✅ Freelancer login successful")
    else:
        print("❌ Incorrect password")

    db.close()


# ---------- MAIN MENU ----------
while True:
    print("\n====== GIGBRIDGE CLI ======")
    print("1️⃣ Login")
    print("2️⃣ Sign Up")
    print("3️⃣ Hire a Freelancer (Client)")
    print("4️⃣ Earn Money (Freelancer)")
    print("5️⃣ Exit")

    choice = input("Choose option: ")

    if choice == "1":
        role = input("Login as (client/freelancer): ").lower()
        if role == "client":
            client_login()
        elif role == "freelancer":
            freelancer_login()
        else:
            print("❌ Invalid role")

    elif choice == "2":
        role = input("Sign up as (client/freelancer): ").lower()
        if role == "client":
            client_signup()
        elif role == "freelancer":
            freelancer_signup()
        else:
            print("❌ Invalid role")

    elif choice == "3":
        print("\n👉 Hire a Freelancer")
        sub = input("1. Login\n2. Sign Up\nChoose: ")
        if sub == "1":
            client_login()
        elif sub == "2":
            client_signup()

    elif choice == "4":
        print("\n👉 Earn Money")
        sub = input("1. Login\n2. Sign Up\nChoose: ")
        if sub == "1":
            freelancer_login()
        elif sub == "2":
            freelancer_signup()

    elif choice == "5":
        print("👋 Exiting...")
        break

    else:
        print("❌ Invalid choice")
