import requests
import time
import sqlite3
from datetime import datetime
import webbrowser


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


def continue_with_google(role):
    global current_client_id, current_freelancer_id

    try:
        res = requests.get(f"{BASE_URL}/auth/google/start", params={"role": role})
        data = res.json()
    except Exception:
        print("❌ Failed to contact server for Google OAuth")
        return

    if not data.get("success"):
        print("❌", data.get("msg", "Google OAuth failed to start"))
        return

    auth_url = data["auth_url"]
    state = data["state"]

    print("\n🌐 Opening browser for Google login...")
    print("If browser doesn't open, copy this URL and open manually:\n")
    print(auth_url)

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print("\n⏳ After login, come back here. Checking status...")

    # Poll status (simple)
    start = time.time()
    while True:
        if time.time() - start > 180:  # 3 minutes timeout
            print("❌ Timed out waiting for Google login")
            return

        try:
            st = requests.get(f"{BASE_URL}/auth/google/status", params={"state": state}).json()
        except Exception:
            time.sleep(2)
            continue

        if st.get("success") and st.get("done") is True:
            result = st.get("result") or {}
            if not result.get("success"):
                print("❌ Google login failed:", result.get("msg", "unknown error"))
                return

            if role == "client" and result.get("client_id"):
                current_client_id = result["client_id"]
                print("✅ Google login successful (Client). client_id =", current_client_id)
                return

            if role == "freelancer" and result.get("freelancer_id"):
                current_freelancer_id = result["freelancer_id"]
                print("✅ Google login successful (Freelancer). freelancer_id =", current_freelancer_id)
                return

            print("❌ Google login completed but ID not returned")
            return

        time.sleep(2)            

# ---------- LOGIN OR SIGNUP ----------

def login_or_signup(role):
    print("1. Login")
    print("2. Signup")
    print("3. Continue with Google")   # ✅ ADD THIS LINE
    choice = input("Choose: ")

    if choice == "1":
        login(role=role)
    elif choice == "2":
        signup_with_role(role)
    elif choice == "3":                # ✅ ADD THIS BLOCK
        continue_with_google(role)
    else:
        print("❌ Invalid choice")


# ---------- CHAT HELPERS ----------
def format_timestamp(ts):
    """Convert Unix timestamp to readable time"""
    try:
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%I:%M %p")  # 12-hour format like WhatsApp
    except:
        return ""

def display_message(text, is_sent, sender_name="", timestamp=None):
    """Display message in WhatsApp-like format"""
    time_str = format_timestamp(timestamp) if timestamp else ""
    max_width = 60  # Max message width
    
    if is_sent:
        # Your messages aligned to right (like WhatsApp)
        # Wrap long messages
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) < max_width:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
        
        for line in lines:
            padding = 70 - len(line) - 6  # 6 for "[You] "
            print(f"{' ' * max(0, padding)}[You] {line}")
        if time_str:
            print(f"{' ' * (70 - len(time_str) - 2)}{time_str} ✓")
    else:
        # Received messages aligned to left
        sender_label = sender_name if sender_name else "Freelancer"
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) < max_width:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
        
        for i, line in enumerate(lines):
            prefix = f"[{sender_label}]" if i == 0 else " " * (len(sender_label) + 2)
            print(f"{prefix} {line}")
        if time_str:
            print(f"{' ' * (len(sender_label) + 2)}{time_str}")

def clear_chat_display():
    """Clear screen for better chat experience"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def show_chat_header(contact_name):
    """Show WhatsApp-like header"""
    print("\n" + "=" * 70)
    print(f"💬 Chat with {contact_name}")
    print("=" * 70)
    print("Type your message and press Enter. Type 'exit' to leave chat.")
    print("-" * 70)

# ---------- CHAT ----------
def open_chat_with_freelancer(freelancer_id):
    # Get freelancer name
    try:
        res = requests.get(f"{BASE_URL}/freelancers/{freelancer_id}")
        freelancer_data = res.json()
        freelancer_name = freelancer_data.get("name", "Freelancer")
    except:
        freelancer_name = "Freelancer"
    
    show_chat_header(freelancer_name)
    
    # Load and display existing chat history
    res = requests.get(f"{BASE_URL}/message/history", params={
        "client_id": current_client_id,
        "freelancer_id": freelancer_id
    })
    
    displayed_messages = set()  # Track displayed message timestamps to avoid duplicates
    
    try:
        messages = res.json()
        if messages:
            print("\n📜 Chat History:")
            print("-" * 70)
            for m in messages:
                is_sent = m["sender_role"] == "client"
                display_message(m['text'], is_sent, freelancer_name, m.get("timestamp"))
                displayed_messages.add(m.get("timestamp", 0))
    except:
        pass
    
    print("\n" + "-" * 70)
    last_timestamp = max(displayed_messages) if displayed_messages else 0
    
    # Main chat loop
    while True:
        # Get user input
        msg = input("\n💬 You: ")
        if msg.lower() == "exit":
            print("\n👋 Left chat")
            break
        if msg.lower() == "refresh" or msg.lower() == "r":
            # Manual refresh to check for new messages
            res = requests.get(f"{BASE_URL}/message/history", params={
                "client_id": current_client_id,
                "freelancer_id": freelancer_id
            })
            try:
                messages = res.json()
                new_found = False
                for m in messages:
                    msg_timestamp = m.get("timestamp", 0)
                    if msg_timestamp > last_timestamp and msg_timestamp not in displayed_messages:
                        is_sent = m["sender_role"] == "client"
                        display_message(m['text'], is_sent, freelancer_name, msg_timestamp)
                        displayed_messages.add(msg_timestamp)
                        last_timestamp = max(last_timestamp, msg_timestamp)
                        new_found = True
                if not new_found:
                    print("📭 No new messages")
            except:
                pass
            continue
        if not msg.strip():
            continue

        # Send message
        try:
            requests.post(f"{BASE_URL}/client/message/send", json={
                "client_id": current_client_id,
                "freelancer_id": freelancer_id,
                "text": msg
            })
            
            # Immediately show the sent message
            current_time = int(time.time())
            display_message(msg, True, freelancer_name, current_time)
            displayed_messages.add(current_time)
            last_timestamp = current_time
            
            # Check for any new messages from freelancer
            time.sleep(0.5)  # Small delay
            res = requests.get(f"{BASE_URL}/message/history", params={
                "client_id": current_client_id,
                "freelancer_id": freelancer_id
            })
            try:
                messages = res.json()
                for m in messages:
                    msg_timestamp = m.get("timestamp", 0)
                    if msg_timestamp > last_timestamp and msg_timestamp not in displayed_messages:
                        is_sent = m["sender_role"] == "client"
                        display_message(m['text'], is_sent, freelancer_name, msg_timestamp)
                        displayed_messages.add(msg_timestamp)
                        last_timestamp = max(last_timestamp, msg_timestamp)
            except:
                pass
        except:
            print("❌ Failed to send message")

def open_chat_with_client(client_id):
    # Get client name
    try:
        conn = sqlite3.connect("client.db")
        cur = conn.cursor()
        cur.execute("SELECT name FROM client WHERE id=?", (client_id,))
        row = cur.fetchone()
        client_name = row[0] if row else "Client"
        conn.close()
    except:
        client_name = "Client"
    
    show_chat_header(client_name)
    
    # Load and display existing chat history
    res = requests.get(f"{BASE_URL}/message/history", params={
        "client_id": client_id,
        "freelancer_id": current_freelancer_id
    })
    
    displayed_messages = set()  # Track displayed message timestamps
    
    try:
        messages = res.json()
        if messages:
            print("\n📜 Chat History:")
            print("-" * 70)
            for m in messages:
                is_sent = m["sender_role"] == "freelancer"
                display_message(m['text'], is_sent, client_name, m.get("timestamp"))
                displayed_messages.add(m.get("timestamp", 0))
    except:
        pass
    
    print("\n" + "-" * 70)
    last_timestamp = max(displayed_messages) if displayed_messages else 0
    
    # Main chat loop
    while True:
        # Get user input
        msg = input("\n💬 You: ")
        if msg.lower() == "exit":
            print("\n👋 Left chat")
            break
        if msg.lower() == "refresh" or msg.lower() == "r":
            # Manual refresh to check for new messages
            res = requests.get(f"{BASE_URL}/message/history", params={
                "client_id": client_id,
                "freelancer_id": current_freelancer_id
            })
            try:
                messages = res.json()
                new_found = False
                for m in messages:
                    msg_timestamp = m.get("timestamp", 0)
                    if msg_timestamp > last_timestamp and msg_timestamp not in displayed_messages:
                        is_sent = m["sender_role"] == "freelancer"
                        display_message(m['text'], is_sent, client_name, msg_timestamp)
                        displayed_messages.add(msg_timestamp)
                        last_timestamp = max(last_timestamp, msg_timestamp)
                        new_found = True
                if not new_found:
                    print("📭 No new messages")
            except:
                pass
            continue
        if not msg.strip():
            continue

        # Send message
        try:
            requests.post(f"{BASE_URL}/freelancer/message/send", json={
                "freelancer_id": current_freelancer_id,
                "client_id": client_id,
                "text": msg
            })
            
            # Immediately show the sent message
            current_time = int(time.time())
            display_message(msg, True, client_name, current_time)
            displayed_messages.add(current_time)
            last_timestamp = current_time
            
            # Check for any new messages from client
            time.sleep(0.5)  # Small delay
            res = requests.get(f"{BASE_URL}/message/history", params={
                "client_id": client_id,
                "freelancer_id": current_freelancer_id
            })
            try:
                messages = res.json()
                for m in messages:
                    msg_timestamp = m.get("timestamp", 0)
                    if msg_timestamp > last_timestamp and msg_timestamp not in displayed_messages:
                        is_sent = m["sender_role"] == "freelancer"
                        display_message(m['text'], is_sent, client_name, msg_timestamp)
                        displayed_messages.add(msg_timestamp)
                        last_timestamp = max(last_timestamp, msg_timestamp)
            except:
                pass
        except:
            print("❌ Failed to send message")

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

# ---------- CLIENT: MESSAGES (THREADS) ----------
def client_messages_menu():
    """Show freelancers you have chatted with and open a chat."""
    if not current_client_id:
        print("❌ Please login as client first")
        return

    try:
        res = requests.get(f"{BASE_URL}/client/messages/threads", params={
            "client_id": current_client_id
        })
        threads = res.json()
    except Exception:
        threads = []

    print("\n--- MESSAGES ---")
    if not threads:
        print("📭 No messages yet")
        return

    mapping = []
    for idx, t in enumerate(threads, 1):
        name = t.get("name") or "Freelancer"
        fid = t.get("freelancer_id")
        print(f"{idx}. {name} (ID: {fid})")
        mapping.append((idx, fid, name))

    sel = input("Select freelancer number to open chat (or Enter to go back): ").strip()
    if not sel:
        return
    if not sel.isdigit():
        print("❌ Invalid selection")
        return

    sel = int(sel)
    for num, fid, _name in mapping:
        if num == sel:
            open_chat_with_freelancer(fid)
            return

    print("❌ Invalid selection")

# ---------- CLIENT: JOB REQUEST STATUS ----------
def client_job_request_status_menu():
    """Show detailed job request status and allow messaging the freelancer."""
    if not current_client_id:
        print("❌ Please login as client first")
        return

    try:
        res = requests.get(f"{BASE_URL}/client/job-requests", params={
            "client_id": current_client_id
        })
        data = res.json()
    except Exception:
        data = []

    print("\n--- JOB REQUEST STATUS ---")
    if not data:
        print("📭 No job requests found")
        return

    mapping = []
    for idx, r in enumerate(data, 1):
        title = (r.get("job_title") or "Untitled").strip()
        budget = r.get("proposed_budget")
        status = r.get("status")
        fname = r.get("freelancer_name") or "Freelancer"
        fid = r.get("freelancer_id")
        rid = r.get("request_id")

        print(f"\n{idx}. Request ID: {rid}")
        print(f"   Freelancer: {fname} (ID: {fid})")
        print(f"   Job Title: {title}")
        print(f"   Budget: ₹{budget}")
        print(f"   Status: {status}")

        mapping.append((idx, fid))

    print("\n1. Message a freelancer about a request")
    print("2. Back")
    ch = input("Choose: ").strip()

    if ch == "1":
        num = input("Enter request number: ").strip()
        if num.isdigit():
            num = int(num)
            for i, fid in mapping:
                if i == num:
                    open_chat_with_freelancer(fid)
                    return
        print("❌ Invalid request number")

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
        print("7. Messages")
        print("8. Job Request Status")
        print("9. Exit")

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
            client_messages_menu()

        elif choice == "8":
            client_job_request_status_menu()

        elif choice == "9":
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
        print("3. Manage Active Jobs")
        print("4. Messages")
        print("5. Earnings & Performance")
        print("6. Saved Clients")
        print("7. Account Settings")
        print("8. Notifications / Activity")
        print("9. Exit")

        choice = input("Choose: ")

        # 1️⃣ Create / Update Profile
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

        # 2️⃣ View Hire Requests (Inbox)
        elif choice == "2":
            try:
                res = requests.get(f"{BASE_URL}/freelancer/hire/inbox", params={
                    "freelancer_id": current_freelancer_id
                })
                inbox = res.json()
            except Exception:
                inbox = []

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
                    print("4. Save Client")
                    print("5. Next")
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
                    elif a == "4":
                        rr = requests.post(f"{BASE_URL}/freelancer/save-client", json={
                            "freelancer_id": current_freelancer_id,
                            "client_id": r["client_id"]
                        })
                        try:
                            print(rr.json())
                        except Exception:
                            print("❌ Failed to save client")

        # 3️⃣ Manage Active Jobs
        elif choice == "3":
            try:
                res = requests.get(f"{BASE_URL}/freelancer/hire/inbox", params={
                    "freelancer_id": current_freelancer_id
                })
                inbox = res.json()
            except Exception:
                inbox = []

            active = [r for r in inbox if r.get("status") == "ACCEPTED"]
            print("\n--- ACTIVE JOBS ---")
            if not active:
                print("📭 No active (accepted) jobs")
            else:
                for i, j in enumerate(active, 1):
                    title = j.get("note") or j.get("request_id")
                    print(f"{i}. Client: {j['client_name']} | Budget: ₹{j['proposed_budget']} | Status: {j['status']}")

        # 4️⃣ Messages
        elif choice == "4":
            # List clients you have hire-request history with
            try:
                res = requests.get(f"{BASE_URL}/freelancer/hire/inbox", params={
                    "freelancer_id": current_freelancer_id
                })
                inbox = res.json()
            except Exception:
                inbox = []

            clients = {}
            for r in inbox:
                clients[r["client_id"]] = r["client_name"]

            if not clients:
                print("📭 No clients to message yet")
            else:
                print("\n--- YOUR CLIENTS ---")
                mapping = []
                for idx, (cid, name) in enumerate(clients.items(), 1):
                    print(f"{idx}. {name} (ID: {cid})")
                    mapping.append((idx, cid))
                sel = input("Select client number (or Enter to cancel): ").strip()
                if sel.isdigit():
                    sel = int(sel)
                    for num, cid in mapping:
                        if num == sel:
                            open_chat_with_client(cid)
                            break

        # 5️⃣ Earnings & Performance
        elif choice == "5":
            try:
                res = requests.get(f"{BASE_URL}/freelancer/stats", params={
                    "freelancer_id": current_freelancer_id
                })
                data = res.json()
                if not data.get("success"):
                    print("❌", data.get("msg", "Could not fetch stats"))
                else:
                    print("\n--- EARNINGS & PERFORMANCE ---")
                    print("Total Earnings: ₹", data["total_earnings"])
                    print("Completed Jobs:", data["completed_jobs"])
                    print("Rating: ⭐", data["rating"])
                    print("Job Success:", f"{data['job_success_percent']}%")
            except Exception:
                print("❌ Error fetching stats")

        # 6️⃣ Saved Clients
        elif choice == "6":
            try:
                res = requests.get(f"{BASE_URL}/freelancer/saved-clients", params={
                    "freelancer_id": current_freelancer_id
                })
                clients = res.json()
            except Exception:
                clients = []

            print("\n--- SAVED CLIENTS ---")
            if not clients:
                print("❌ No saved clients")
            else:
                for c in clients:
                    print(f"{c['client_id']}. {c['name']} - {c['email']}")
                    print("1. Message 💬")
                    print("2. Next")
                    a = input("Choose: ")
                    if a == "1":
                        open_chat_with_client(c["client_id"])

        # 7️⃣ Account Settings
        elif choice == "7":
            while True:
                print("\n--- ACCOUNT SETTINGS ---")
                print("1. Change Password")
                print("2. Update Email")
                print("3. Notification Settings (UI only)")
                print("4. Logout")
                print("5. Back")
                a = input("Choose: ")

                if a == "1":
                    old_pwd = input("Old Password: ")
                    new_pwd = input("New Password: ")
                    try:
                        res = requests.post(f"{BASE_URL}/freelancer/change-password", json={
                            "freelancer_id": current_freelancer_id,
                            "old_password": old_pwd,
                            "new_password": new_pwd
                        })
                        print(res.json())
                    except Exception:
                        print("❌ Failed to change password")
                elif a == "2":
                    new_email = input("New Email: ")
                    try:
                        res = requests.post(f"{BASE_URL}/freelancer/update-email", json={
                            "freelancer_id": current_freelancer_id,
                            "new_email": new_email
                        })
                        print(res.json())
                    except Exception:
                        print("❌ Failed to update email")
                elif a == "3":
                    print("ℹ Notification settings are UI-only for now.")
                elif a == "4":
                    current_freelancer_id = None
                    print("✅ Logged out")
                    return
                elif a == "5":
                    break

        # 8️⃣ Notifications / Activity
        elif choice == "8":
            try:
                res = requests.get(f"{BASE_URL}/freelancer/notifications", params={
                    "freelancer_id": current_freelancer_id
                })
                notes = res.json()
            except Exception:
                notes = []

            print("\n--- NOTIFICATIONS / ACTIVITY ---")
            if not notes:
                print("📭 No recent activity")
            else:
                for n in notes:
                    print("✔", n)

        # 9️⃣ Exit
        elif choice == "9":
            break

# ---------- MAIN MENU ----------
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
            print("\nLogin method:")
            print("1. Continue with Email")
            print("2. Continue with Google")
            m = input("Choose: ")
            if m == "1":
                login(role="client")
            elif m == "2":
                continue_with_google("client")
            else:
                print("❌ Invalid choice")

        elif r == "2":
            print("\nLogin method:")
            print("1. Continue with Email")
            print("2. Continue with Google")
            m = input("Choose: ")
            if m == "1":
                login(role="freelancer")
            elif m == "2":
                continue_with_google("freelancer")
            else:
                print("❌ Invalid choice")

        else:
            print("❌ Invalid role choice")

    elif option == "2":
        print("Choose role to signup:")
        print("1. Client")
        print("2. Freelancer")
        r = input("Choose: ")

        if r == "1":
            print("\nSignup method:")
            print("1. Continue with Email (OTP)")
            print("2. Continue with Google")
            m = input("Choose: ")
            if m == "1":
                signup_with_role("client")
            elif m == "2":
                continue_with_google("client")
            else:
                print("❌ Invalid choice")

        elif r == "2":
            print("\nSignup method:")
            print("1. Continue with Email (OTP)")
            print("2. Continue with Google")
            m = input("Choose: ")
            if m == "1":
                signup_with_role("freelancer")
            elif m == "2":
                continue_with_google("freelancer")
            else:
                print("❌ Invalid choice")

        else:
            print("❌ Invalid role choice")

    elif option == "3":
        client_flow()

    elif option == "4":
        freelancer_flow()

    elif option == "5":
        print("👋 Goodbye")
        break
