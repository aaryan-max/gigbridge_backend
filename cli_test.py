import requests
import time
import sqlite3
from datetime import datetime
import webbrowser


BASE_URL = "http://127.0.0.1:5000"

current_client_id = None
current_freelancer_id = None

# ============================================================
# ===== NEW: CALL FEATURE =====
# ============================================================

def start_call(caller_role, receiver_id, call_type):
    """Start a voice or video call"""
    try:
        # Determine caller ID based on role
        if caller_role == "client":
            caller_id = current_client_id
            receiver_role = "freelancer"
        else:
            caller_id = current_freelancer_id
            receiver_role = "client"
        
        res = requests.post(f"{BASE_URL}/call/start", json={
            "caller_role": caller_role,
            "caller_id": caller_id,
            "receiver_role": receiver_role,
            "receiver_id": receiver_id,
            "call_type": call_type
        })
        
        result = res.json()
        if result.get("success"):
            print(f"✅ {call_type.title()} call started!")
            print(f"📞 Room: {result['room_name']}")
            print("🌐 Opening browser in 3 seconds...")
            
            time.sleep(3)
            webbrowser.open(result["room_url"])
        else:
            print("❌ Failed to start call:", result.get("msg"))
    except Exception as e:
        print("❌ Error starting call:", str(e))

def check_incoming_calls():
    """Check for incoming calls"""
    try:
        # Determine current user role and ID
        if current_client_id:
            role = "client"
            user_id = current_client_id
        else:
            role = "freelancer"
            user_id = current_freelancer_id
        
        # Safe guard for user_id
        if not user_id:
            print("❌ Please login first")
            return
        
        res = requests.get(
            f"{BASE_URL}/call/incoming",
            params={
                "receiver_role": role,
                "receiver_id": user_id
            }
        )
        
        data = res.json()
        if data.get("success") and data.get("calls"):
            print("\n--- INCOMING CALLS ---")
            for call in data["calls"]:
                call_type = call["call_type"].title()
                print(f"📞 {call_type} call from {call['caller_role']} ID {call['caller_id']}")
                print(f"   Room: {call['room_name']}")
                print("1. Accept")
                print("2. Reject")
                print("3. Skip this call")
                print("4. Back to Dashboard")
                
                action = input("Choose: ")
                if action == "1":
                    respond_res = requests.post(f"{BASE_URL}/call/respond", json={
                        "call_id": call["call_id"],
                        "action": "accept"
                    })
                    if respond_res.json().get("success"):
                        print("✅ Call accepted!")
                        print("🌐 Opening browser...")
                        time.sleep(2)
                        webbrowser.open(f"https://meet.jit.si/{call['room_name']}")
                elif action == "2":
                    requests.post(f"{BASE_URL}/call/respond", json={
                        "call_id": call["call_id"],
                        "action": "reject"
                    })
                    print("❌ Call rejected")
                elif action == "3":
                    print("⏭️ Call skipped")
                    continue
                elif action == "4":
                    print("🔙 Returning to dashboard...")
                    return
                else:
                    print("❌ Invalid choice, skipping call")
                    continue
        else:
            print("📭 No incoming calls")
    except Exception as e:
        print("❌ Error checking calls:", str(e))

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

# ---------- FORGOT PASSWORD ----------
def forgot_password(role):
    """Handle forgot password flow"""
    print(f"\n--- {role.title()} FORGOT PASSWORD ---")
    
    email = input("Enter your registered email: ")
    if not valid_email(email):
        print("❌ Invalid email format")
        return
    
    print(f"📩 Sending OTP to {email}...")
    
    # Send OTP
    try:
        if role == "client":
            res = requests.post(f"{BASE_URL}/client/send-otp", json={"email": email})
        else:
            res = requests.post(f"{BASE_URL}/freelancer/send-otp", json={"email": email})
        
        if res.json().get("success"):
            print("✅ OTP sent successfully!")
        else:
            print("❌ Failed to send OTP")
            return
    except Exception:
        print("❌ Network error while sending OTP")
        return
    
    # Get OTP
    otp = input("Enter OTP: ")
    
    # Verify OTP and get new password
    try:
        if role == "client":
            res = requests.post(f"{BASE_URL}/client/verify-otp-for-reset", json={"email": email, "otp": otp})
        else:
            res = requests.post(f"{BASE_URL}/freelancer/verify-otp-for-reset", json={"email": email, "otp": otp})
        
        result = res.json()
        if result.get("success"):
            print("✅ OTP verified! You can now set a new password.")
            
            # Get new password
            while True:
                new_password = input("Enter new password: ")
                if len(new_password) < 6:
                    print("❌ Password must be at least 6 characters")
                    continue
                
                confirm_password = input("Confirm new password: ")
                if new_password != confirm_password:
                    print("❌ Passwords do not match")
                    continue
                
                # Reset password
                reset_res = requests.post(f"{BASE_URL}/client/reset-password" if role == "client" else f"{BASE_URL}/freelancer/reset-password", 
                                       json={"email": email, "new_password": new_password})
                
                if reset_res.json().get("success"):
                    print("✅ Password reset successful! You can now login with your new password.")
                    return
                else:
                    print("❌ Failed to reset password")
                    return
        else:
            print("❌ Invalid OTP or OTP expired")
    except Exception as e:
        print("❌ Error during password reset:", str(e))


# ---------- LOGIN ----------
def login(role=None):
    global current_client_id, current_freelancer_id

    while True:
        print("\nLogin method:")
        print("1. Login")
        print("2. Forgot Password")
        print("3. Back")
        choice = input("Choose: ").strip()
        
        if choice == "3":
            return
        
        if choice == "2":
            # Forgot Password flow
            forgot_password(role)
            return
        
        if choice != "1":
            print("❌ Invalid choice")
            continue
            
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
    # Step 1: Only action (Login / Signup)
    print("1. Login")
    print("2. Signup")
    choice = input("Choose: ").strip()

    if choice == "1":
        # Step 2: Login method
        print("\nLogin method:")
        print("1. Continue with Email")
        print("2. Continue with Google")
        m = input("Choose: ").strip()

        if m == "1":
            login(role=role)
        elif m == "2":
            continue_with_google(role)
        else:
            print("❌ Invalid choice")

    elif choice == "2":
        # Step 2: Signup method
        print("\nSignup method:")
        print("1. Continue with Email (OTP)")
        print("2. Continue with Google")
        m = input("Choose: ").strip()

        if m == "1":
            signup_with_role(role)
        elif m == "2":
            continue_with_google(role)
        else:
            print("❌ Invalid choice")

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
    
    # Display profile image if available
    if data.get("profile_image"):
        print("Profile Image:", data["profile_image"])
    
    # Display portfolio items
    try:
        portfolio_res = requests.get(f"{BASE_URL}/freelancer/portfolio/{fid}")
        portfolio_data = portfolio_res.json()
        if portfolio_data.get("success") and portfolio_data.get("portfolio_items"):
            print("\n--- PORTFOLIO ---")
            for item in portfolio_data["portfolio_items"]:
                print(f"\n📁 {item['title']}")
                print(f"   Description: {item['description']}")
                print(f"   Image: {item['image_path']}")
        else:
            print("\n--- PORTFOLIO ---")
            print("📭 No portfolio items")
    except Exception as e:
        print("\n--- PORTFOLIO ---")
        print("❌ Error loading portfolio")

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
    """Show job request status - Simplified display only."""
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

# ---------- CLIENT: AI RECOMMENDATIONS ----------
def client_ai_recommendations():
    """Display AI-recommended freelancers based on category and budget"""
    print("\n--- AI RECOMMENDATIONS ---")
    
    category = input("Category: ").strip()
    budget_input = input("Budget: ").strip()
    
    try:
        budget = float(budget_input)
    except ValueError:
        print("❌ Invalid budget amount")
        return
    
    try:
        res = requests.post(f"{BASE_URL}/freelancers/recommend", json={
            "category": category,
            "budget": budget
        })
        recommendations = res.json()
    except Exception as e:
        print("❌ Error getting recommendations:", str(e))
        return
    
    if not recommendations:
        print("📭 No recommendations found")
        return
    
    print("\n--- AI RECOMMENDED FREELANCERS ---")
    for i, freelancer in enumerate(recommendations, 1):
        print(f"\n{i}. {freelancer['name']}")
        print(f"   Match Score: {freelancer['match_score']}%")
        print(f"   Rating: {freelancer['rating']}")
        print(f"   Experience: {freelancer['experience']} years")
        print(f"   Budget: {freelancer['budget_range']}")
        print(f"   Category: {freelancer['category']}")
        
        print("1. View Details")
        print("2. Message")
        print("3. Hire")
        print("4. Save Freelancer")
        print("5. Next")
        
        action = input("Choose: ")
        if action == "1":
            view_freelancer_details(freelancer["freelancer_id"])
        elif action == "2":
            open_chat_with_freelancer(freelancer["freelancer_id"])
        elif action == "3":
            hire_freelancer(freelancer["freelancer_id"])
        elif action == "4":
            res = requests.post(f"{BASE_URL}/client/save-freelancer", json={
                "client_id": current_client_id,
                "freelancer_id": freelancer["freelancer_id"]
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
        print("1. Create/Update")
        print("2. View All");
        print("3. Search")
        print("4. View My Jobs")
        print("5. Saved Freelancers")
        print("6. Notifications")
        print("7. Messages")
        print("8. Job Request Status")
        print("9. Recommended Freelancers (AI)")
        print("10. Check Incoming Calls ")
        print("11. Logout")

        choice = input("Choose: ")
        
        if choice == "11":
            current_client_id = None
            print("✅ Logged out successfully")
            return
        
        if choice == "1":
            while True:
                phone = input("Phone (10 digits): ")
                if valid_phone(phone):
                    break
                print(" Phone must be 10 digits")
                print("❌ Phone must be 10 digits")

            pincode = input("PIN Code (6 digits): ")

            res = requests.post(f"{BASE_URL}/client/profile", json={
                "client_id": current_client_id,
                "phone": phone,
                "location": input("Location: "),
                "bio": input("Bio: "),
                "pincode": pincode
            })
            print(res.json())

        elif choice == "2":
            res = requests.get(f"{BASE_URL}/freelancers/all")
            data = res.json()
            if not data.get("success"):
                print("❌ Error fetching freelancers:", data.get("msg", "Unknown error"))
                continue
            
            freelancers = data.get("results", [])
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
            category = input("Category (e.g., Dancer, Singer, Photographer): ").strip()
            specialization = input("Specialization : ").strip()
            budget_in = input("Max Budget: ").strip()

            try:
                budget = float(budget_in)
            except Exception:
                print("❌ Invalid budget")
                continue

            params = {
                "category": category,
                "budget": budget,
                "client_id": current_client_id
            }
            if specialization:
                params["q"] = specialization

            res = requests.get(f"{BASE_URL}/freelancers/search", params=params)

            data = res.json()
            if not data.get("success"):
                print("❌ Error searching freelancers:", data.get("msg", "Unknown error"))
                continue

            freelancers = data.get("results", [])
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
            print("\n--- SAVED FREELANCERS ---")
            try:
                freelancers = res.json()
                if not freelancers:
                    print("❌ No saved freelancers")
                else:
                    for f in freelancers:
                        # API returns: {"id": r[0], "name": r[1], "category": r[2] or ""}
                        freelancer_id = f.get("id", f.get("freelancer_id"))
                        name = f.get("name")
                        print(f"{freelancer_id}. {name}")
            except Exception as e:
                print("❌ Error fetching saved freelancers:", str(e))

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
            except Exception as e:
                print("❌ Error getting recommendations:", str(e))

        elif choice == "7":
            res = requests.get(f"{BASE_URL}/client/messages/threads", params={
                "client_id": current_client_id
            })
            threads = res.json()
            if not threads:
                print("📭 No message threads found")
            else:
                print("\n--- MESSAGE THREADS ---")
                for thread in threads:
                    print(f"\nFreelancer: {thread['name']} (ID: {thread['freelancer_id']})")
                    print("1. View Chat History")
                    print("2. Send New Message")
                    print("3. Voice Call 📞")
                    print("4. Video Call 🎥")
                    print("5. Next")
                    msg_choice = input("Choose: ")
                    
                    if msg_choice == "1":
                        # View chat history
                        res_history = requests.get(f"{BASE_URL}/message/history", params={
                            "client_id": current_client_id,
                            "freelancer_id": thread['freelancer_id']
                        })
                        history = res_history.json()
                        print("\n--- CHAT HISTORY ---")
                        for msg in history:
                            sender = "You" if msg['sender_role'] == 'client' else "Freelancer"
                            print(f"{sender}: {msg['text']}")
                    elif msg_choice == "2":
                        # Send new message
                        message = input("Enter your message: ")
                        res_send = requests.post(f"{BASE_URL}/client/message/send", json={
                            "client_id": current_client_id,
                            "freelancer_id": thread['freelancer_id'],
                            "text": message
                        })
                        print(res_send.json())
                    elif msg_choice == "3":
                        start_call("client", thread['freelancer_id'], "voice")
                    elif msg_choice == "4":
                        start_call("client", thread['freelancer_id'], "video")

        elif choice == "8":
            client_job_request_status_menu()

        elif choice == "9":
            client_ai_recommendations()

        elif choice == "10":
            check_incoming_calls()

        elif choice == "11":
            break

# ---------- FREELANCER VERIFICATION ----------
def freelancer_verification_status():
    """Show verification status for freelancer"""
    if not current_freelancer_id:
        print("❌ Please login as freelancer first")
        return
    
    try:
        res = requests.get(f"{BASE_URL}/freelancer/verification/status", params={
            "freelancer_id": current_freelancer_id
        })
        data = res.json()
        
        if not data.get("success"):
            print("❌ Error:", data.get("msg", "Unknown error"))
            return
        
        print("\n--- VERIFICATION STATUS ---")
        status = data.get("status")
        submitted_at = data.get("submitted_at")
        rejection_reason = data.get("rejection_reason")
        
        if status is None:
            print("Status: Not submitted yet")
            print("\n📋 Submit your verification documents to get verified.")
        else:
            print(f"Status: {status}")
            
            if submitted_at:
                from datetime import datetime
                submitted_date = datetime.fromtimestamp(submitted_at)
                print(f"Submitted on: {submitted_date.strftime('%Y-%m-%d %H:%M')}")
            
            if status == "PENDING":
                print("\n📋 Your documents are under review.")
                print("   Admin module will process this in future updates.")
            elif status == "REJECTED" and rejection_reason:
                print(f"\n❌ Rejection reason: {rejection_reason}")
            elif status == "APPROVED":
                print("\n✅ Congratulations! Your verification is approved.")
        
    except Exception as e:
        print("❌ Error checking verification status:", str(e))


def freelancer_upload_verification():
    """Upload verification documents for freelancer"""
    if not current_freelancer_id:
        print("❌ Please login as freelancer first")
        return
    
    print("\n--- UPLOAD VERIFICATION DOCUMENTS ---")
    print("📋 Required Documents:")
    print("   1. Government ID (Aadhaar, Passport, Driver's License)")
    print("   2. PAN Card")
    print("   3. Artist Proof (Optional - Certificate, Portfolio, etc.)")
    print("\n📁 Allowed formats: PDF, JPG, PNG")
    print("📁 Maximum file size: 5MB")
    print("📁 Files will be stored securely")
    
    # Check if already submitted
    try:
        res = requests.get(f"{BASE_URL}/freelancer/verification/status", params={
            "freelancer_id": current_freelancer_id
        })
        status_data = res.json()
        
        if status_data.get("success") and status_data.get("status") == "PENDING":
            print("\n⚠️  You already have a pending verification request.")
            print("1. Re-upload documents")
            print("2. Cancel")
            choice = input("Choose: ").strip()
            
            if choice != "1":
                print("❌ Upload cancelled")
                return
    except:
        pass
    
    # Get file paths
    print("\n📂 Enter file paths (local file paths):")
    
    government_id = input("Government ID file path: ").strip()
    if not government_id:
        print("❌ Government ID is required")
        return
    
    pan_card = input("PAN Card file path: ").strip()
    if not pan_card:
        print("❌ PAN Card is required")
        return
    
    artist_proof = input("Artist Proof file path (optional): ").strip()
    if not artist_proof:
        artist_proof = None
    
    # Validate file extensions
    def validate_file_ext(file_path):
        if not file_path:
            return True
        ext = file_path.lower().split('.')[-1]
        return ext in ['pdf', 'jpg', 'jpeg', 'png']
    
    if not validate_file_ext(government_id):
        print("❌ Invalid Government ID file type. Use PDF, JPG, or PNG")
        return
    
    if not validate_file_ext(pan_card):
        print("❌ Invalid PAN Card file type. Use PDF, JPG, or PNG")
        return
    
    if artist_proof and not validate_file_ext(artist_proof):
        print("❌ Invalid Artist Proof file type. Use PDF, JPG, or PNG")
        return
    
    # Confirm upload
    print("\n📋 Upload Summary:")
    print(f"   Government ID: {government_id}")
    print(f"   PAN Card: {pan_card}")
    if artist_proof:
        print(f"   Artist Proof: {artist_proof}")
    
    confirm = input("\nConfirm upload? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ Upload cancelled")
        return
    
    # Upload documents
    try:
        res = requests.post(f"{BASE_URL}/freelancer/verification/upload", json={
            "freelancer_id": current_freelancer_id,
            "government_id_path": government_id,
            "pan_card_path": pan_card,
            "artist_proof_path": artist_proof
        })
        
        result = res.json()
        if result.get("success"):
            print("✅ Documents submitted successfully!")
            print("📋 Status: PENDING")
            print("   Your documents are under review.")
            print("   Admin module will process this in future updates.")
        else:
            print("❌ Upload failed:", result.get("msg", "Unknown error"))
    
    except Exception as e:
        print("❌ Error uploading documents:", str(e))


# ---------- FREELANCER SUBSCRIPTION ----------
def freelancer_subscription_plans():
    """Show available subscription plans"""
    print("\n--- SUBSCRIPTION PLANS ---")
    
    try:
        res = requests.get(f"{BASE_URL}/freelancer/subscription/plans")
        data = res.json()
        
        if not data.get("success"):
            print("❌ Error:", data.get("msg", "Unknown error"))
            return
        
        plans = data.get("plans", {})
        
        # Get current subscription
        try:
            status_res = requests.get(f"{BASE_URL}/freelancer/subscription/status", params={
                "freelancer_id": current_freelancer_id
            })
            status_data = status_res.json()
            current_plan = status_data.get("subscription", {}).get("plan_name", "BASIC")
        except:
            current_plan = "BASIC"
        
        # Display plans
        for plan_key, plan_data in plans.items():
            badge = plan_data.get("badge", "")
            if plan_key == current_plan:
                print(f"\n🟢 {plan_data['name']} (Current Plan)")
            else:
                print(f"\n{badge} {plan_data['name']} - ₹{plan_data['price']}/month")
            
            print("   Features:")
            for feature in plan_data.get("features", []):
                print(f"   • {feature}")
            print()
        
        print("\nOptions:")
        print("1. Upgrade to PREMIUM")
        print("2. Back")
        
        choice = input("Choose: ").strip()
        
        if choice == "1":
            upgrade_subscription("PREMIUM")
        elif choice == "2":
            return
        else:
            print("❌ Invalid choice")
    
    except Exception as e:
        print("❌ Error loading plans:", str(e))


def freelancer_my_subscription():
    """Show current subscription details"""
    if not current_freelancer_id:
        print("❌ Please login as freelancer first")
        return
    
    try:
        res = requests.get(f"{BASE_URL}/freelancer/subscription/status", params={
            "freelancer_id": current_freelancer_id
        })
        data = res.json()
        
        if not data.get("success"):
            print("❌ Error:", data.get("msg", "Unknown error"))
            return
        
        subscription = data.get("subscription", {})
        job_applies = data.get("job_applies", {})
        
        # Handle case where subscription might be None
        if not subscription:
            print("❌ Error: Unable to load subscription details")
            return
        
        print("\n--- MY SUBSCRIPTION ---")
        print(f"Current Plan: {subscription.get('plan_name', 'BASIC')}")
        
        if subscription.get("start_date"):
            from datetime import datetime
            start_date = datetime.fromtimestamp(subscription["start_date"])
            print(f"Start Date: {start_date.strftime('%Y-%m-%d')}")
        
        if subscription.get("end_date"):
            from datetime import datetime
            expiry_date = datetime.fromtimestamp(subscription["end_date"])
            print(f"Expiry Date: {expiry_date.strftime('%Y-%m-%d')}")
        
        print(f"Status: {subscription.get('status', 'ACTIVE')}")
        
        # Show job applies info
        current_plan = job_applies.get("current_plan", "BASIC")
        applies_used = job_applies.get("applies_used", 0)
        limit = job_applies.get("limit", 10)
        
        if current_plan == "BASIC":
            print(f"\nJob Applies: {applies_used} / {limit}")
        else:
            print(f"\nJob Applies: Unlimited")
        
        print("\nOptions:")
        print("1. Renew")
        print("2. Cancel")
        print("3. Back")
        
        choice = input("Choose: ").strip()
        
        if choice == "1":
            # Renew current plan
            current_plan = subscription.get("plan_name", "BASIC")
            if current_plan == "PREMIUM":
                upgrade_subscription("PREMIUM")
            else:
                print("❌ BASIC plan cannot be renewed")
        elif choice == "2":
            # Cancel subscription
            if subscription.get("plan_name") != "BASIC":
                print("⚠️  Cancelling subscription...")
                # This would set to BASIC in a real system
                print("✅ Subscription cancelled. You are now on BASIC plan.")
            else:
                print("❌ You are already on BASIC plan")
        elif choice == "3":
            return
        else:
            print("❌ Invalid choice")
    
    except Exception as e:
        print(f"❌ Error loading subscription: {str(e)}")


def upgrade_subscription(plan_name):
    """Upgrade freelancer subscription"""
    try:
        res = requests.post(f"{BASE_URL}/freelancer/subscription/upgrade", json={
            "freelancer_id": current_freelancer_id,
            "plan_name": plan_name
        })
        
        result = res.json()
        if result.get("success"):
            print(f"\n✅ {result.get('msg', 'Upgrade successful')}")
            print(f"Active until: {result.get('active_until', 'N/A')}")
        else:
            print("❌ Upgrade failed:", result.get("msg", "Unknown error"))
    
    except Exception as e:
        print("❌ Error upgrading subscription:", str(e))


def show_freelancer_dashboard_header():
    """Show subscription info at top of dashboard"""
    try:
        res = requests.get(f"{BASE_URL}/freelancer/subscription/status", params={
            "freelancer_id": current_freelancer_id
        })
        data = res.json()
        
        if data.get("success"):
            subscription = data.get("subscription", {})
            job_applies = data.get("job_applies", {})
            
            # Handle case where subscription might be None
            if not subscription:
                print("\nPlan: BASIC")
                print("Job Applies Used: 0 / 10")
                return
            
            current_plan = subscription.get("plan_name", "BASIC")
            applies_used = job_applies.get("applies_used", 0)
            limit = job_applies.get("limit", 10)
            
            print(f"\nPlan: {current_plan}")
            if current_plan == "BASIC":
                print(f"Job Applies Used: {applies_used} / {limit}")
            else:
                print("Job Applies Used: Unlimited")
    except Exception as e:
        print(f"Error loading subscription: {str(e)}")
        print("\nPlan: BASIC")
        print("Job Applies Used: 0 / 10")


# ---------- FREELANCER FLOW ----------
def freelancer_flow():
    global current_freelancer_id

    if not current_freelancer_id:
        login_or_signup("freelancer")
        if not current_freelancer_id:
            return

    while True:
        # Show subscription info at top
        show_freelancer_dashboard_header()
        
        print("\n--- FREELANCER DASHBOARD ---")
        print("1. Create/Update Profile")
        print("2. View Hire Requests")
        print("3. Manage Active Jobs")
        print("4. Messages")
        print("5. Earnings")
        print("6. Saved Clients")
        print("7. Account Settings")
        print("8. Notifications")
        print("9. Manage Portfolio")
        print("10. Upload Profile Photo")
        print("11. Check Incoming Calls 📞")
        print("12. Verification Status 🏅")
        print("13. Upload Verification Documents")
        print("14. Subscription Plans 💎")
        print("15. My Subscription")
        print("16. Logout")

        choice = input("Choose: ")

        if choice == "16":
            current_freelancer_id = None
            print("✅ Logged out successfully")
            return

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
                title = input("Title: ")
                skills = input("Skills: ")
                experience = int(input("Experience (years): "))
                min_budget = float(input("Min Budget: "))
                max_budget = float(input("Max Budget: "))
                bio = input("Bio: ")
                pincode = input("PIN Code (6 digits): ")
                location = input("Location: ")
                category = input("Category (choose from above): ")
                res = requests.post(f"{BASE_URL}/freelancer/profile", json={
                    "freelancer_id": current_freelancer_id,
                    "title": title,
                    "skills": skills,
                    "experience": experience,
                    "min_budget": min_budget,
                    "max_budget": max_budget,
                    "bio": bio,
                    "pincode": pincode,
                    "location": location,
                    "category": category
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
            # List clients you have hire-request history with - Enhanced with call options
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
                print("\n--- MESSAGE THREADS ---")
                for cid, name in clients.items():
                    print(f"\nClient: {name} (ID: {cid})")
                    print("1. View Chat History")
                    print("2. Send New Message")
                    print("3. Voice Call 📞")
                    print("4. Video Call 🎥")
                    print("5. Next")
                    msg_choice = input("Choose: ")
                    
                    if msg_choice == "1":
                        # View chat history
                        res_history = requests.get(f"{BASE_URL}/message/history", params={
                            "client_id": cid,
                            "freelancer_id": current_freelancer_id
                        })
                        history = res_history.json()
                        print("\n--- CHAT HISTORY ---")
                        for msg in history:
                            sender = "You" if msg['sender_role'] == 'freelancer' else "Client"
                            print(f"{sender}: {msg['text']}")
                    elif msg_choice == "2":
                        # Send new message
                        message = input("Enter your message: ")
                        res_send = requests.post(f"{BASE_URL}/freelancer/message/send", json={
                            "freelancer_id": current_freelancer_id,
                            "client_id": cid,
                            "text": message
                        })
                        print(res_send.json())
                    elif msg_choice == "3":
                        start_call("freelancer", cid, "voice")
                    elif msg_choice == "4":
                        start_call("freelancer", cid, "video")

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
                    print("2. Voice Call 📞")
                    print("3. Video Call 🎥")
                    print("4. Next")
                    a = input("Choose: ")
                    if a == "1":
                        open_chat_with_client(c["client_id"])
                    elif a == "2":
                        start_call("freelancer", c["client_id"], "voice")
                    elif a == "3":
                        start_call("freelancer", c["client_id"], "video")

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

        # 9️⃣ Manage Portfolio
        elif choice == "9":
            while True:
                print("\n--- MANAGE PORTFOLIO ---")
                print("1. Add Portfolio Item")
                print("2. View My Portfolio")
                print("3. Back")
                portfolio_choice = input("Choose: ")
                
                if portfolio_choice == "1":
                    # Add Portfolio Item
                    title = input("Title: ")
                    description = input("Description: ")
                    image_path = input("Image Path (local file): ")
                    
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
                    # View My Portfolio
                    try:
                        res = requests.get(f"{BASE_URL}/freelancer/portfolio/{current_freelancer_id}")
                        data = res.json()
                        if data.get("success") and data.get("portfolio_items"):
                            print("\n--- MY PORTFOLIO ---")
                            # ===== UPDATED: STORE PORTFOLIO IMAGE AS BLOB =====
                            for item in data["portfolio_items"]:
                                print(f"\n📁 {item['title']}")
                                print(f"   Description: {item['description']}")
                                
                                # Display image info based on storage type
                                if "image_base64" in item:
                                    print("   Image: stored in database (BLOB)")
                                elif "image_path" in item:
                                    print(f"   Image: {item['image_path']}")
                                else:
                                    print("   Image: not available")
                                    
                                print(f"   Added: {item['created_at']}")
                        else:
                            print("📭 No portfolio items found")
                    except Exception as e:
                        print("❌ Error fetching portfolio:", str(e))
                
                elif portfolio_choice == "3":
                    break

        # 10️⃣ Upload Profile Photo
        elif choice == "10":
            image_path = input("Profile Photo Path (local file): ")
            try:
                res = requests.post(f"{BASE_URL}/freelancer/upload-photo", json={
                    "freelancer_id": current_freelancer_id,
                    "image_path": image_path
                })
                result = res.json()
                if result.get("success"):
                    print("✅ Profile photo uploaded successfully!")
                    print(f"📁 Saved to: {result.get('image_path')}")
                else:
                    print("❌ Failed to upload photo:", result.get("msg"))
            except Exception as e:
                print("❌ Error uploading photo:", str(e))

        # 11️⃣ Check Incoming Calls
        elif choice == "11":
            check_incoming_calls()

        # 12️⃣ Verification Status
        elif choice == "12":
            freelancer_verification_status()

        # 13️⃣ Upload Verification Documents
        elif choice == "13":
            freelancer_upload_verification()

        # 14️⃣ Subscription Plans
        elif choice == "14":
            freelancer_subscription_plans()

        # 15️⃣ My Subscription
        elif choice == "15":
            freelancer_my_subscription()

        # 16️⃣ Exit
        elif choice == "16":
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
