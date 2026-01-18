import requests

BASE_URL = "http://127.0.0.1:5000"

current_client_id = None
current_freelancer_id = None


# ---------- AUTH ----------
def signup():
    global current_client_id, current_freelancer_id

    role = input("Sign up as (client/freelancer): ").lower()

    name = input("Name: ")
    email = input("Email: ")
    password = input("Password: ")

    data = {
        "name": name,
        "email": email,
        "password": password
    }

    if role == "client":
        res = requests.post(f"{BASE_URL}/client/signup", json=data)
    elif role == "freelancer":
        res = requests.post(f"{BASE_URL}/freelancer/signup", json=data)
    else:
        print("❌ Invalid role")
        return

    response = res.json()
    print(response)

    # Auto-login after signup
    if response.get("success"):
        print("✅ Signup Successful! Logging you in automatically...")
        login(auto=True, role=role, email=email, password=password)
    else:
        print("❌ Signup failed. Try again.")


def login(auto=False, role=None, email=None, password=None):
    global current_client_id, current_freelancer_id

    if not auto:
        role = input("Login as (client/freelancer): ").lower()
        email = input("Email: ")
        password = input("Password: ")

    data = {
        "email": email,
        "password": password
    }

    if role == "client":
        res = requests.post(f"{BASE_URL}/client/login", json=data)
        response = res.json()

        if not response.get("client_id"):
            print("❌ Account not found. Please Sign Up first.")
            return False

        print("✅ Login Successful")
        current_client_id = response.get("client_id")
        return True

    elif role == "freelancer":
        res = requests.post(f"{BASE_URL}/freelancer/login", json=data)
        response = res.json()

        if not response.get("freelancer_id"):
            print("❌ Account not found. Please Sign Up first.")
            return False

        print("✅ Login Successful")
        current_freelancer_id = response.get("freelancer_id")
        return True

    else:
        print("❌ Invalid role")
        return False


# ---------- CLIENT FLOW ----------
def client_flow():
    global current_client_id

    if not current_client_id:
        print("❌ Please login/signup first")
        login_or_signup()
        return

    while True:
        print("\n--- CLIENT DASHBOARD ---")
        print("1. Create / Update Profile")
        print("2. Search Freelancers")
        print("3. Exit")

        choice = input("Choose: ")

        if choice == "1":
            data = {
                "client_id": current_client_id,
                "phone": input("Phone: "),
                "location": input("Location: "),
                "bio": input("Bio: ")
            }
            res = requests.post(f"{BASE_URL}/client/profile", json=data)
            print(res.json())

        elif choice == "2":
            skill = input("Required Skill: ")
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
            break

        else:
            print("❌ Invalid option")


# ---------- FREELANCER FLOW ----------
def freelancer_flow():
    global current_freelancer_id

    if not current_freelancer_id:
        print("❌ Please login/signup first")
        login_or_signup()
        return

    while True:
        print("\n--- FREELANCER DASHBOARD ---")
        print("1. Create / Update Profile")
        print("2. Exit")

        choice = input("Choose: ")

        if choice == "1":
            data = {
                "freelancer_id": current_freelancer_id,
                "title": input("Professional Title: "),
                "skills": input("Skills (comma separated): "),
                "experience": int(input("Experience (years): ")),
                "min_budget": float(input("Min Budget: ")),
                "max_budget": float(input("Max Budget: ")),
                "bio": input("Bio: ")
            }

            res = requests.post(f"{BASE_URL}/freelancer/profile", json=data)
            print(res.json())

        elif choice == "2":
            break

        else:
            print("❌ Invalid option")


# ---------- LOGIN OR SIGNUP ----------
def login_or_signup():
    print("\n1️⃣ Login")
    print("2️⃣ Signup")
    choice = input("Choose option: ")

    if choice == "1":
        login()
    elif choice == "2":
        signup()
    else:
        print("❌ Invalid choice")


# ---------- MAIN MENU ----------
while True:
    print("\n====== GIGBRIDGE ======")
    print("1️⃣ Login")
    print("2️⃣ Sign Up")
    print("3️⃣ Continue as Client")
    print("4️⃣ Continue as Freelancer")
    print("5️⃣ Exit")

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
