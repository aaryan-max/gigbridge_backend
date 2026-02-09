import requests

BASE_URL = "http://127.0.0.1:5000"

current_client_id = None
current_freelancer_id = None

# ---------- VALIDATORS ----------
def valid_email(email):
    return "@" in email and "." in email

def valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

# ---------- SIGNUP WITH OTP (AUTO-LOGIN AFTER SIGNUP) ----------
def signup_with_role(role):
    global current_client_id, current_freelancer_id

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
            "name": name, "email": email, "password": password, "otp": otp
        })
    else:
        res = requests.post(f"{BASE_URL}/freelancer/verify-otp", json={
            "name": name, "email": email, "password": password, "otp": otp
        })

    response = res.json()
    print(response)

    if response.get("success"):
        if role == "client" and response.get("client_id"):
            current_client_id = response["client_id"]
            print("✅ Client signup successful (auto-logged in)")
        elif role == "freelancer" and response.get("freelancer_id"):
            current_freelancer_id = response["freelancer_id"]
            print("✅ Freelancer signup successful (auto-logged in)")
        else:
            print("✅ Signup successful. You can now login.")
    else:
        print("❌ Signup failed:", response.get("msg"))

    return

# ---------- LOGIN ----------
def login(role=None):
    global current_client_id, current_freelancer_id

    while True:
        email = input("Email: ")
        if valid_email(email):
            break
        print("❌ Invalid email")

    password = input("Password: ")

    if role == "client":
        res = requests.post(f"{BASE_URL}/client/login", json={"email": email, "password": password})
        data = res.json()
        if data.get("client_id"):
            current_client_id = data["client_id"]
            print("✅ Client login successful")
        else:
            print("❌ Account not found. Please sign up first.")

    elif role == "freelancer":
        res = requests.post(f"{BASE_URL}/freelancer/login", json={"email": email, "password": password})
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

# ---------- CHAT ----------
def open_chat_with_freelancer(freelancer_id):
    print("\n--- CHAT (type 'exit' to stop) ---")
    
    # Load and display existing chat history once
    res = requests.get(f"{BASE_URL}/message/history", params={
        "client_id": current_client_id,
        "freelancer_id": freelancer_id
    })
    
    try:
        messages = res.json()
        last_timestamp = 0
        if messages:
            for m in messages:
                role = "You" if m["sender_role"] == "client" else "Freelancer"
                print(f"{role}: {m['text']}")
                last_timestamp = max(last_timestamp, m.get("timestamp", 0))
    except:
        pass
    
    # Now handle new messages
    while True:
        msg = input("\nYou: ")
        if msg.lower() == "exit":
            break

        # Send message
        requests.post(f"{BASE_URL}/client/message/send", json={
            "client_id": current_client_id,
            "freelancer_id": freelancer_id,
            "text": msg
        })

        # Get updated history and show only new messages
        res = requests.get(f"{BASE_URL}/message/history", params={
            "client_id": current_client_id,
            "freelancer_id": freelancer_id
        })
        
        try:
            messages = res.json()
            for m in messages:
                # Only show messages newer than last_timestamp
                if m.get("timestamp", 0) > last_timestamp:
                    role = "You" if m["sender_role"] == "client" else "Freelancer"
                    print(f"{role}: {m['text']}")
                    last_timestamp = m.get("timestamp", 0)
        except:
            pass

def open_chat_with_client(client_id):
    print("\n--- CHAT (type 'exit' to stop) ---")
    
    # Load and display existing chat history once
    res = requests.get(f"{BASE_URL}/message/history", params={
        "client_id": client_id,
        "freelancer_id": current_freelancer_id
    })
    
    try:
        messages = res.json()
        last_timestamp = 0
        if messages:
            for m in messages:
                role = "You" if m["sender_role"] == "freelancer" else "Client"
                print(f"{role}: {m['text']}")
                last_timestamp = max(last_timestamp, m.get("timestamp", 0))
    except:
        pass
    
    # Now handle new messages
    while True:
        msg = input("\nYou: ")
        if msg.lower() == "exit":
            break

        # Send message
        requests.post(f"{BASE_URL}/freelancer/message/send", json={
            "freelancer_id": current_freelancer_id,
            "client_id": client_id,
            "text": msg
        })

        # Get updated history and show only new messages
        res = requests.get(f"{BASE_URL}/message/history", params={
            "client_id": client_id,
            "freelancer_id": current_freelancer_id
        })
        
        try:
            messages = res.json()
            for m in messages:
                # Only show messages newer than last_timestamp
                if m.get("timestamp", 0) > last_timestamp:
                    role = "You" if m["sender_role"] == "freelancer" else "Client"
                    print(f"{role}: {m['text']}")
                    last_timestamp = m.get("timestamp", 0)
        except:
            pass

# ---------- CLIENT: VIEW DETAILS ----------
def view_freelancer_details(fid):
    res = requests.get(f"{BASE_URL}/freelancers/{fid}")
    data = res.json()
    if not data.get("success"):
        print("❌", data.get("msg"))
        return

    print("\n--- FREELANCER DETAILS ---")
    print("ID:", data["freelancer_id"])
    print("Name:", data["name"])
    print("Email:", data["email"])
    print("Category:", data["category"])
    print("Title:", data["title"])
    print("Skills:", data["skills"])
    print("Experience:", data["experience"])
    print("Min Budget:", data["min_budget"])
    print("Max Budget:", data["max_budget"])
    print("Rating:", data["rating"])
    print("Bio:", data["bio"])

# ---------- CLIENT: HIRE ----------
def hire_freelancer(fid):
    job_title = input("Job Title: ")
    budget = input("Proposed Budget: ")
    note = input("Note (optional): ")

    res = requests.post(f"{BASE_URL}/client/hire", json={
        "client_id": current_client_id,
        "freelancer_id": fid,
        "job_title": job_title,
        "proposed_budget": budget,
        "note": note
    })
    print(res.json())

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
        print("2. View All Freelancers")
        print("3. Search Freelancers")
        print("4. View My Jobs")
        print("5. Saved Freelancers")
        print("6. Notifications")
        print("7. Exit")

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
            res = requests.get(f"{BASE_URL}/freelancers/all")
            freelancers = res.json()
            if not freelancers:
                print("❌ No freelancers found")
                continue

            for f in freelancers:
                print("\n--- Freelancer ---")
                print("ID:", f["freelancer_id"])
                print("Name:", f["name"])
                print("Category:", f["category"])
                print("Title:", f["title"])
                print("Budget:", f["budget_range"])
                print("Rating:", f["rating"])

                print("1. View Details")
                print("2. Message")
                print("3. Hire")
                print("4. Save Freelancer")
                print("5. Next")

                action = input("Choose: ")
                if action == "1":
                    view_freelancer_details(f["freelancer_id"])
                elif action == "2":
                    open_chat_with_freelancer(f["freelancer_id"])
                elif action == "3":
                    hire_freelancer(f["freelancer_id"])
                elif action == "4":
                    res = requests.post(f"{BASE_URL}/client/save-freelancer", json={
                        "client_id": current_client_id,
                        "freelancer_id": f["freelancer_id"]
                    })
                    print(res.json())

        elif choice == "3":
            category = input("Category: ").strip()
            budget = input("Max Budget: ").strip()

            res = requests.get(f"{BASE_URL}/freelancers/search", params={
                "category": category,
                "budget": budget
            })

            freelancers = res.json()
            if not freelancers:
                print("❌ No freelancers found")
                continue

            for f in freelancers:
                print("\n--- Freelancer ---")
                print("ID:", f["freelancer_id"])
                print("Name:", f["name"])
                print("Category:", f["category"])
                print("Title:", f["title"])
                print("Budget:", f["budget_range"])
                print("Rating:", f["rating"])

                print("1. View Details")
                print("2. Message")
                print("3. Hire")
                print("4. Save Freelancer")
                print("5. Next")

                action = input("Choose: ")
                if action == "1":
                    view_freelancer_details(f["freelancer_id"])
                elif action == "2":
                    open_chat_with_freelancer(f["freelancer_id"])
                elif action == "3":
                    hire_freelancer(f["freelancer_id"])
                elif action == "4":
                    res = requests.post(f"{BASE_URL}/client/save-freelancer", json={
                        "client_id": current_client_id,
                        "freelancer_id": f["freelancer_id"]
                    })
                    print(res.json())

        elif choice == "4":
            res = requests.get(f"{BASE_URL}/client/jobs", params={
                "client_id": current_client_id
            })
            print("\n--- My Jobs ---")
            try:
                jobs = res.json()
                if not jobs:
                    print("❌ No jobs found")
                else:
                    for i, j in enumerate(jobs, 1):
                        print(f"{i}. {j['title']} | ₹{j['budget']} | {j['status']}")
            except:
                print("❌ Error fetching jobs")

        elif choice == "5":
            res = requests.get(f"{BASE_URL}/client/saved-freelancers", params={
                "client_id": current_client_id
            })
            print("\n--- Saved Freelancers ---")
            try:
                freelancers = res.json()
                if not freelancers:
                    print("❌ No saved freelancers")
                else:
                    for f in freelancers:
                        print(f"{f['id']}. {f['name']} - {f['category']}")
                        print("1. Message 💬")
                        print("2. Back")
                        a = input("Choose: ")
                        if a == "1":
                            open_chat_with_freelancer(f["id"])
            except:
                print("❌ Error fetching saved freelancers")

        elif choice == "6":
            res = requests.get(f"{BASE_URL}/client/notifications", params={
                "client_id": current_client_id
            })
            print("\n--- Notifications ---")
            try:
                notifications = res.json()
                if not notifications:
                    print("❌ No notifications")
                else:
                    for n in notifications:
                        print("*", n)
            except:
                print("❌ Error fetching notifications")

        elif choice == "7":
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
        print("2. View Hire Requests (Inbox)")
        print("3. Exit")

        choice = input("Choose: ")

        if choice == "1":
            print("\nAllowed Categories (example):")
            print("- Graphic Designer")
            print("- Video Editor")
            print("- Photographer")
            print("- Singer")
            print("- Dancer")
            print("- Illustrator")
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
            res = requests.get(f"{BASE_URL}/freelancer/hire/inbox", params={
                "freelancer_id": current_freelancer_id
            })
            inbox = res.json()
            if not inbox:
                print("❌ No hire requests")
                continue

            for r in inbox:
                print("\n--- HIRE REQUEST ---")
                print("Request ID:", r["request_id"])
                print("Client:", r["client_name"], "|", r["client_email"])
                print("Budget:", r["proposed_budget"])
                print("Note:", r["note"])
                print("Status:", r["status"])

                if r["status"] == "PENDING":
                    print("1. Accept")
                    print("2. Reject")
                    print("3. Message Client")
                    print("4. Next")
                    a = input("Choose: ")

                    if a == "1":
                        rr = requests.post(f"{BASE_URL}/freelancer/hire/respond", json={
                            "freelancer_id": current_freelancer_id,
                            "request_id": r["request_id"],
                            "action": "ACCEPT"
                        })
                        print(rr.json())
                    elif a == "2":
                        rr = requests.post(f"{BASE_URL}/freelancer/hire/respond", json={
                            "freelancer_id": current_freelancer_id,
                            "request_id": r["request_id"],
                            "action": "REJECT"
                        })
                        print(rr.json())
                    elif a == "3":
                        open_chat_with_client(r["client_id"])

        elif choice == "3":
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