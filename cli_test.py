import requests

BASE_URL = "http://127.0.0.1:5000"

current_client_id = None
current_freelancer_id = None


# ---------- VALIDATORS ----------
def valid_email(email):
    return "@" in email and "." in email


def valid_phone(phone):
    return phone.isdigit() and len(phone) == 10


# ---------- SIGNUP WITH OTP ----------
def signup_with_role(role):
    name = input("Name: ")

    while True:
        email = input("Email: ")
        if valid_email(email):
            break
        print("❌ Invalid email")

    password = input("Password: ")

    # STEP 1: SEND OTP
    if role == "client":
        requests.post(f"{BASE_URL}/client/send-otp", json={"email": email})
    else:
        requests.post(f"{BASE_URL}/freelancer/send-otp", json={"email": email})

    print("📩 OTP sent to your email")

    # STEP 2: VERIFY OTP
    otp = input("Enter OTP: ")

    if role == "client":
        res = requests.post(f"{BASE_URL}/client/verify-otp", json={
            "name": name,
            "email": email,
            "password": password,
            "otp": otp
        })
    else:
        res = requests.post(f"{BASE_URL}/freelancer/verify-otp", json={
            "name": name,
            "email": email,
            "password": password,
            "otp": otp
        })

    response = res.json()
    print(response)

    if response.get("success"):
        print("✅ Signup successful. You can now login.")
    else:
        print("❌ Signup failed:", response.get("msg"))

    return  # 🔴 VERY IMPORTANT (stops duplicate signup)


# ---------- LOGIN ----------
def login(auto=False, role=None, email=None, password=None):
    global current_client_id, current_freelancer_id

    if not auto:
        while True:
            email = input("Email: ")
            if valid_email(email):
                break
            print("❌ Invalid email")

        password = input("Password: ")

    if role == "client":
        res = requests.post(f"{BASE_URL}/client/login", json={
            "email": email, "password": password
        })
        data = res.json()

        if data.get("client_id"):
            current_client_id = data["client_id"]
            print("✅ Client login successful")
        else:
            print("❌ Account not found. Please sign up first.")

    elif role == "freelancer":
        res = requests.post(f"{BASE_URL}/freelancer/login", json={
            "email": email, "password": password
        })
        data = res.json()

        if data.get("freelancer_id"):
            current_freelancer_id = data["freelancer_id"]
            print("✅ Freelancer login successful")
        else:
            print("❌ Account not found. Please sign up first.")


# ---------- LOGIN OR SIGNUP ----------
def login_or_signup(role):
    print("1. Login")
    print("2. Signup")
    choice = input("Choose: ")

    if choice == "1":
        login(role=role)
    elif choice == "2":
        signup_with_role(role)
    else:
        print("❌ Invalid choice")


# ---------- CLIENT FLOW ----------
def client_flow():
    global current_client_id

    if not current_client_id:
        login_or_signup("client")
        if not current_client_id:
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
                print("❌ Phone must be 10 digits")

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
            break


# ---------- FREELANCER FLOW ----------
def freelancer_flow():
    global current_freelancer_id

    if not current_freelancer_id:
        login_or_signup("freelancer")
        if not current_freelancer_id:
            return

    while True:
        print("\n--- FREELANCER DASHBOARD ---")
        print("1. Create / Update Profile")
        print("2. Exit")

        choice = input("Choose: ")

        if choice == "1":
            print("\nAllowed Categories:")
            print("- Graphic Designer")
            print("- Video Editor")
            print("- Photographer")
            print("- Singer / Musician")
            print("- Dancer / Performer")
            print("- Illustrator / Digital Artist")
            print("- Content Creator")

            res = requests.post(f"{BASE_URL}/freelancer/profile", json={
                "freelancer_id": current_freelancer_id,
                "title": input("Title: "),
                "skills": input("Skills: "),
                "experience": int(input("Experience: ")),
                "min_budget": float(input("Min Budget: ")),
                "max_budget": float(input("Max Budget: ")),
                "bio": input("Bio: "),
                "category": input("Category (choose from above): ")
            })

            try:
                print(res.json())
            except:
                print("❌ Server error")
                print(res.text)

        elif choice == "2":
            break


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
        print("Choose role to login:")
        print("1. Client")
        print("2. Freelancer")
        r = input("Choose: ")

        if r == "1":
            login(role="client")
        elif r == "2":
            login(role="freelancer")

    elif option == "2":
        print("Choose role to signup:")
        print("1. Client")
        print("2. Freelancer")
        r = input("Choose: ")

        if r == "1":
            signup_with_role("client")
        elif r == "2":
            signup_with_role("freelancer")

    elif option == "3":
        client_flow()

    elif option == "4":
        freelancer_flow()

    elif option == "5":
        print("👋 Goodbye")
        break
