import requests
import time
import os

BASE_URL = "http://127.0.0.1:5000"
current_client_id = None
current_freelancer_id = None

def valid_email(email):
    return "@" in email and "." in email.split("@")[1]

def valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

def login(role):
    global current_client_id, current_freelancer_id
    
    email = input("Email: ")
    password = input("Password: ")
    
    if role == "client":
        res = requests.post(f"{BASE_URL}/client/login", json={
            "email": email,
            "password": password
        })
        data = res.json()
        if data.get("success"):
            current_client_id = data["client_id"]
            print(f"✅ Logged in as client (ID: {current_client_id})")
            client_flow()
        else:
            print("❌", data.get("msg", "Login failed"))
    else:
        res = requests.post(f"{BASE_URL}/freelancer/login", json={
            "email": email,
            "password": password
        })
        data = res.json()
        if data.get("success"):
            current_freelancer_id = data["freelancer_id"]
            print(f"✅ Logged in as freelancer (ID: {current_freelancer_id})")
            freelancer_flow()
        else:
            print("❌", data.get("msg", "Login failed"))

def signup_with_role(role):
    global current_client_id, current_freelancer_id
    
    name = input("Name: ")
    email = input("Email: ")
    password = input("Password: ")
    
    if not valid_email(email):
        print("❌ Invalid email format")
        return
    
    if role == "client":
        res = requests.post(f"{BASE_URL}/client/signup", json={
            "name": name,
            "email": email,
            "password": password
        })
        data = res.json()
        if data.get("success"):
            print("✅ Signup successful! Please check your email for OTP.")
            # OTP verification would go here
            current_client_id = data["client_id"]
            client_flow()
        else:
            print("❌", data.get("msg", "Signup failed"))
    else:
        res = requests.post(f"{BASE_URL}/freelancer/signup", json={
            "name": name,
            "email": email,
            "password": password
        })
        data = res.json()
        if data.get("success"):
            print("✅ Signup successful! Please check your email for OTP.")
            # OTP verification would go here
            current_freelancer_id = data["freelancer_id"]
            freelancer_flow()
        else:
            print("❌", data.get("msg", "Signup failed"))

def view_freelancer_details(fid):
    res = requests.get(f"{BASE_URL}/freelancer/profile/{fid}")
    data = res.json()
    if not data.get("success"):
        print("❌", data.get("msg"))
        return

    print("\n--- FREELANCER DETAILS ---")
    print("ID:", data["freelancer_id"])
    print("Name:", data["name"])
    print("Email:", data["email"])
    
    if data.get("profile_image"):
        print("Profile Photo:", data["profile_image"])
    else:
        print("Profile Photo: Not uploaded")
    
    print("Category:", data["category"])
    print("Title:", data["title"])
    print("Skills:", data["skills"])
    print("Experience:", data["experience"])
    print("Min Budget:", data["min_budget"])
    print("Max Budget:", data["max_budget"])
    print("Rating:", data["rating"])
    print("Bio:", data["bio"])
    
    # Show portfolio items
    try:
        portfolio_res = requests.get(f"{BASE_URL}/freelancer/portfolio/{fid}")
        portfolio_data = portfolio_res.json()
        if portfolio_data.get("success") and portfolio_data.get("portfolio_items"):
            print("\n--- PORTFOLIO ---")
            for item in portfolio_data["portfolio_items"]:
                print(f"\n📸 {item['title']}")
                print(f"   Description: {item['description']}")
                print(f"   Image: {item['image_path']}")
                print(f"   Added: {item['created_at']}")
        else:
            print("\n--- PORTFOLIO ---")
            print("📭 No portfolio items")
    except Exception as e:
        print("\n--- PORTFOLIO ---")
        print("❌ Error loading portfolio")

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

def open_chat_with_freelancer(fid):
    print(f"\n--- CHAT WITH FREELANCER {fid} ---")
    print("Type 'exit' to end chat")
    
    while True:
        msg = input("You: ")
        if msg.lower() == 'exit':
            break
        
        try:
            res = requests.post(f"{BASE_URL}/client/message/send", json={
                "client_id": current_client_id,
                "freelancer_id": fid,
                "text": msg
            })
            print("✅ Message sent")
        except:
            print("❌ Failed to send message")

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
        print("7. Messages")
        print("8. Job Request Status")
        print("9. Recommended Freelancers (AI)")
        print("10. Exit")

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

        elif choice == "9":
            category = input("Category: ").strip()
            budget = input("Budget: ").strip()
            
            try:
                res = requests.post(f"{BASE_URL}/freelancers/recommend", json={
                    "category": category,
                    "budget": budget
                })
                recommendations = res.json()
                
                if not recommendations:
                    print("📭 No recommended freelancers found")
                    continue
                
                print("\n--- AI RECOMMENDED FREELANCERS ---")
                for i, rec in enumerate(recommendations, 1):
                    print(f"\n{i}. {rec['name']}")
                    print(f"   Match Score: {rec['match_score']}%")
                    print(f"   Rating: {rec['rating']}")
                    print(f"   Experience: {rec['experience']} years")
                    print(f"   Budget: {rec['budget_range']}")
                    print(f"   Category: {rec['category']}")
                    
                    print("1. View Details")
                    print("2. Message")
                    print("3. Hire")
                    print("4. Save Freelancer")
                    print("5. Next")
                    
                    action = input("Choose: ")
                    if action == "1":
                        view_freelancer_details(rec["freelancer_id"])
                    elif action == "2":
                        open_chat_with_freelancer(rec["freelancer_id"])
                    elif action == "3":
                        hire_freelancer(rec["freelancer_id"])
                    elif action == "4":
                        res = requests.post(f"{BASE_URL}/client/save-freelancer", json={
                            "client_id": current_client_id,
                            "freelancer_id": rec["freelancer_id"]
                        })
                        print(res.json())
                        
            except Exception as e:
                print("❌ Error getting recommendations:", str(e))

        elif choice == "10":
            break

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
        print("3. Manage Active Jobs")
        print("4. Messages")
        print("5. Earnings & Performance")
        print("6. Saved Clients")
        print("7. Account Settings")
        print("8. Notifications / Activity")
        print("9. Manage Portfolio")
        print("10. Upload Profile Photo")
        print("11. Exit")

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

            try:
                res = requests.post(f"{BASE_URL}/freelancer/profile", json={
                    "freelancer_id": current_freelancer_id,
                    "title": input("Title: "),
                    "skills": input("Skills: "),
                    "experience": int(input("Experience (years): ")),
                    "min_budget": float(input("Min Budget: ")),
                    "max_budget": float(input("Max Budget: ")),
                    "bio": input("Bio: "),
                    "category": input("Category (choose from above): ")
                })
                print(res.json())
            except Exception:
                print("❌ Server error while updating profile")

        elif choice == "9":
            while True:
                print("\n--- MANAGE PORTFOLIO ---")
                print("1. Add Portfolio Item")
                print("2. View My Portfolio")
                print("3. Back")
                portfolio_choice = input("Choose: ")
                
                if portfolio_choice == "1":
                    title = input("Portfolio Title: ")
                    description = input("Description: ")
                    image_path = input("Image Path (local file): ")
                    image_path = image_path.strip().strip('"').strip("'")
                    
                    try:
                        res = requests.post(f"{BASE_URL}/freelancer/portfolio/add", json={
                            "freelancer_id": current_freelancer_id,
                            "title": title,
                            "description": description,
                            "image_path": image_path
                        })
                        result = res.json()
                        if result.get("success"):
                            print("✅ Portfolio item added successfully!")
                        else:
                            print("❌ Failed to add portfolio item:", result.get("msg"))
                    except Exception as e:
                        print("❌ Error adding portfolio item:", str(e))
                
                elif portfolio_choice == "2":
                    try:
                        res = requests.get(f"{BASE_URL}/freelancer/portfolio/{current_freelancer_id}")
                        result = res.json()
                        if result.get("success") and result.get("portfolio_items"):
                            print("\n--- MY PORTFOLIO ---")
                            for item in result["portfolio_items"]:
                                print(f"\nTitle: {item['title']}")
                                print(f"Description: {item['description']}")
                                print(f"Image: {item['image_path']}")
                                print(f"Added: {item['created_at']}")
                                print("-" * 30)
                        else:
                            print("📭 No portfolio items found")
                    except Exception as e:
                        print("❌ Error fetching portfolio:", str(e))
                
                elif portfolio_choice == "3":
                    break

        elif choice == "10":
            image_path = input("Enter image path (local file): ")
            image_path = image_path.strip().strip('"').strip("'")
            try:
                res = requests.post(f"{BASE_URL}/freelancer/upload-photo", json={
                    "freelancer_id": current_freelancer_id,
                    "image_path": image_path
                })
                result = res.json()
                if result.get("success"):
                    print("✅ Profile photo uploaded successfully!")
                    print(f"Image saved as: {result.get('image_path')}")
                else:
                    print("❌ Failed to upload photo:", result.get("msg"))
            except Exception as e:
                print("❌ Error uploading photo:", str(e))

        elif choice == "11":
            break

def login_or_signup(role):
    print("\nChoose option:")
    print("1. Login")
    print("2. Sign Up")
    choice = input("Choose: ")
    
    if choice == "1":
        login(role)
    elif choice == "2":
        signup_with_role(role)
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
        print("Choose role to login:")
        print("1. Client")
        print("2. Freelancer")
        r = input("Choose: ")

        if r == "1":
            login("client")
        elif r == "2":
            login("freelancer")
        else:
            print("❌ Invalid role choice")

    elif option == "2":
        print("Choose role to signup:")
        print("1. Client")
        print("2. Freelancer")
        r = input("Choose: ")

        if r == "1":
            signup_with_role("client")
        elif r == "2":
            signup_with_role("freelancer")
        else:
            print("❌ Invalid role choice")

    elif option == "3":
        client_flow()

    elif option == "4":
        freelancer_flow()

    elif option == "5":
        print("👋 Goodbye")
        break
