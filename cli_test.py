import requests

BASE_URL = "http://127.0.0.1:5000"

current_client_id = None
current_freelancer_id = None


# ---------- VALIDATORS ----------
def valid_email(email):
    return "@" in email and "." in email

def valid_phone(phone):
    return phone.isdigit() and len(phone) == 10


# ---------- SIGNUP ----------
def signup():
    global current_client_id, current_freelancer_id

    while True:
        role = input("Sign up as (client/freelancer): ").lower()
        if role in ["client", "freelancer"]:
            break
        print("❌ Enter only client or freelancer")

    name = input("Name: ")

    while True:
        email = input("Email: ")
        if valid_email(email):
            break
        print("❌ Invalid email format")

    password = input("Password: ")

    data = {"name": name, "email": email, "password": password}

    if role == "client":
        res = requests.post(f"{BASE_URL}/client/signup", json=data)
        response = res.json()
        print(response)

        if response.get("success"):
            login(role="client", email=email, password=password, auto=True)

    else:
        res = requests.post(f"{BASE_URL}/freelancer/signup", json=data)
        response = res.json()
        print(response)

        if response.get("success"):
            login(role="freelancer", email=email, password=password, auto=True)


# ---------- LOGIN ----------
def login(auto=False, role=None, email=None, password=None):
    global current_client_id, current_freelancer_id

    if not auto:
        while True:
            role = input("Login as (client/freelancer): ").lower()
            if role in ["client", "freelancer"]:
                break
            print("❌ Enter only client or freelancer")

        while True:
            email = input("Email: ")
            if valid_email(email):
                break
            print("❌ Invalid email format")

        password = input("Password: ")

    if role == "client":
        res = requests.post(f"{BASE_URL}/client/login", json={
            "email": email, "password": password
        })
        data = res.json()

        if data.get("client_id"):
            current_client_id = data["client_id"]
            print("✅ Client login successful")
            client_flow()
        else:
            print("❌ Account not found. Please sign up first.")

    else:
        res = requests.post(f"{BASE_URL}/freelancer/login", json={
            "email": email, "password": password
        })
        data = res.json()

        if data.get("freelancer_id"):
            current_freelancer_id = data["freelancer_id"]
            print("✅ Freelancer login successful")
            freelancer_flow()
        else:
            print("❌ Account not found. Please sign up first.")


# ---------- CLIENT FLOW ----------
def client_flow():
    if not current_client_id:
        login_or_signup()
        return

    while True:
        print("\n--- CLIENT DASHBOARD ---")
        print("1. Create / Update Profile")
        print("2. Search Freelancers")
        print("3. Exit")

        choice = input("Choose: ")

        if choice == "1":
            while True:
                phone = input("Phone (10 digits): ")
                if valid_phone(phone):
                    break
                print("❌ Phone must be exactly 10 digits")

            res = requests.post(f"{BASE_URL}/client/profile", json={
                "client_id": current_client_id,
                "phone": phone,
                "location": input("Location: "),
                "bio": input("Bio: ")
            })
            print(res.json())

        elif choice == "2":
            skill = input("Required Skill: ").lower()
            budget = input("Max Budget: ")

            res = requests.get(
                f"{BASE_URL}/freelancers/search",
                params={"skill": skill, "budget": budget}
            )

            freelancers = res.json()
            if not freelancers:
                print("❌ No freelancers found")
            else:
                for f in freelancers:
                    print("\n--- Freelancer ---")
                    print("ID:", f["freelancer_id"])
                    print("Title:", f["title"])
                    print("Skills:", f["skills"])
                    print("Experience:", f["experience"])
                    print("Budget:", f["budget_range"])
                    print("Rating:", f["rating"])

        elif choice == "3":
            print("⬅️ Exiting Client Dashboard")
            break

        else:
            print("❌ Invalid option")


# ---------- FREELANCER FLOW ----------
def freelancer_flow():
    if not current_freelancer_id:
        login_or_signup()
        return

    while True:
        print("\n--- FREELANCER DASHBOARD ---")
        print("1. Create / Update Profile")
        print("2. Exit")

        choice = input("Choose: ")

        if choice == "1":
            res = requests.post(f"{BASE_URL}/freelancer/profile", json={
                "freelancer_id": current_freelancer_id,
                "title": input("Title: "),
                "skills": input("Skills (comma separated): "),
                "experience": int(input("Experience (years): ")),
                "min_budget": float(input("Min Budget: ")),
                "max_budget": float(input("Max Budget: ")),
                "bio": input("Bio: ")
            })
            print(res.json())

        elif choice == "2":
            print("⬅️ Exiting Freelancer Dashboard")
            break

        else:
            print("❌ Invalid option")


# ---------- LOGIN OR SIGNUP ----------
def login_or_signup():
    print("1. Login")
    print("2. Signup")
    choice = input("Choose: ")

    if choice == "1":
        login()
    elif choice == "2":
        signup()
    else:
        print("❌ Invalid choice")


# ---------- MAIN MENU ----------
while True:
    print("\n====== GIGBRIDGE ======")
    print("1. Login")
    print("2. Sign Up")
    print("3. Continue as Client")
    print("4. Continue as Freelancer")
    print("5. Exit")

    option = input("Choose option: ")

    if option == "1":
        login()
    elif option == "2":
        signup()
    elif option == "3":
        client_flow()
    elif option == "4":
        freelancer_flow()
    elif option == "5":
        print("👋 Goodbye")
        break
    else:
        print("❌ Invalid choice")
