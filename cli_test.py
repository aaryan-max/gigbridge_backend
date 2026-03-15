import requests
import time
from datetime import datetime
import webbrowser
import uuid

BASE_URL = "http://127.0.0.1:5000"

current_client_id = None
current_freelancer_id = None

def check_server_connection():
    """Check if Flask server is running"""
    try:
        response = requests.get(f"{BASE_URL}/freelancers/1", timeout=3)
        return True
    except requests.exceptions.ConnectionError:
        return False
    except:
        return False

def show_server_error():
    """Show helpful error message when server is not running"""
    print("\n" + "="*60)
    print("❌ SERVER CONNECTION ERROR")
    print("="*60)
    print("🔧 The Flask server is not running!")
    print()
    print("💡 TO FIX THIS:")
    print("1. Open a NEW terminal window")
    print("2. Navigate to: cd gigbridge_backend")
    print("3. Run: python start_server.py")
    print("   OR run: python app.py")
    print()
    print("⏳ Wait for server to start, then try again")
    print("🌐 Server should run at: http://127.0.0.1:5000")
    print("="*60)
    print()

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
            "caller_id": caller_id,
            "receiver_id": receiver_id,
            "call_type": call_type
        })
        
        result = res.json()
        if result.get("success"):
            print(f"✅ {call_type.title()} call started!")
            print(f"📞 Meeting URL: {result['meeting_url']}")
            print("🌐 Opening browser in 3 seconds...")
            
            time.sleep(3)
            webbrowser.open(result["meeting_url"])
        else:
            print("❌ Failed to start call:", result.get("msg"))
    except Exception as e:
        print("❌ Error starting call:", str(e))

def check_incoming_calls():
    """Check for incoming calls"""
    try:
        # Determine current user role and ID
        if current_client_id:
            user_id = current_client_id
        else:
            user_id = current_freelancer_id
        
        # Safe guard for user_id
        if not user_id:
            print("❌ Please login first")
            return
        
        res = requests.get(
            f"{BASE_URL}/call/incoming",
            params={"user_id": user_id}
        )
        
        data = res.json()
        if data.get("success") and data.get("calls"):
            print("\n--- INCOMING CALLS ---")
            for call in data["calls"]:
                call_type = call["call_type"].title()
                caller_name = call.get("caller_name", "Unknown")
                print(f"📞 {call_type} call from {caller_name}")
                print(f"   Call ID: {call['call_id']}")
                print(f"   Meeting URL: {call['meeting_url']}")
                print()
                print("1. Accept Call")
                print("2. Reject Call")
                print("3. Message Instead")
                print("4. Back")
                
                action = input("Choose: ")
                if action == "1":
                    # Accept call
                    accept_res = requests.post(f"{BASE_URL}/call/accept", json={
                        "call_id": call["call_id"]
                    })
                    if accept_res.json().get("success"):
                        print("✅ Call accepted!")
                        print("🌐 Opening meeting in browser...")
                        import webbrowser
                        # Use meeting URL from accept response or fall back to call data
                        accept_data = accept_res.json()
                        meeting_url = accept_data.get("meeting_url") or call.get("meeting_url")
                        if meeting_url:
                            webbrowser.open(meeting_url)
                    else:
                        print("❌ Failed to accept call")
                elif action == "2":
                    # Reject call
                    reject_res = requests.post(f"{BASE_URL}/call/reject", json={
                        "call_id": call["call_id"]
                    })
                    if reject_res.json().get("success"):
                        print("✅ Call rejected")
                    else:
                        print("❌ Failed to reject call")
                elif action == "3":
                    print("📱 Opening chat...")
                    # Would open chat functionality here
                elif action == "4":
                    continue
                else:
                    print("❌ Invalid choice")
        else:
            print("✅ No incoming calls")
            
    except Exception as e:
        print("❌ Error checking incoming calls:", str(e))

# ---------- MAIN CLI ENTRY POINT ----------

# ---------- VALIDATORS ----------
def valid_email(email):
    return "@" in email and "." in email

def valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

def get_valid_dob():
    """Get valid Date of Birth with age validation (18-60 years)"""
    from datetime import datetime
    
    while True:
        dob = input("Date of Birth (YYYY-MM-DD): ").strip()
        
        # Validate format
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD format.")
            continue
        
        # Calculate age
        today = datetime.now().date()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        
        # Validate age range
        if age < 18:
            print("❌ User must be at least 18 years old.")
            print("   Please enter valid DOB (18+ required).")
            continue
        elif age > 60:
            print("❌ Maximum allowed age is 60 years.")
            print("   Please enter valid DOB.")
            continue
        
        # Valid DOB entered
        return dob

# ---------- RATING FUNCTION ----------
def rate_freelancer_for_job(job):
    """Rate freelancer for a completed job"""
    try:
        print(f"\n--- Rate Freelancer for: {job['title']} ---")
        print(f"Freelancer ID: {job.get('freelancer_id')}")
        print(f"Job Budget: ₹{job.get('budget')}")
        
        # Get rating
        while True:
            rating_input = input("Rating (1-5): ")
            try:
                rating = float(rating_input)
                if 1 <= rating <= 5:
                    break
                else:
                    print("❌ Rating must be between 1 and 5")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Get review
        review = input("Review (optional): ").strip()
        
        # Submit rating
        res = requests.post(f"{BASE_URL}/client/rate", json={
            "client_id": current_client_id,
            "hire_request_id": job['id'],
            "rating": rating,
            "review": review
        })
        
        result = res.json()
        if result.get("success"):
            print(f"✅ Rating submitted successfully!")
            print(f"New average rating: {result.get('new_rating', 'N/A'):.2f}")
            print(f"Total reviews: {result.get('total_reviews', 'N/A')}")
        else:
            print(f"❌ Failed to submit rating: {result.get('msg', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error submitting rating: {str(e)}")

# ---------- SIGNUP WITH OTP (AUTO-LOGIN AFTER SIGNUP) ----------
def signup_with_role(role):
    global current_client_id, current_freelancer_id

    # Check if server is running before proceeding
    if not check_server_connection():
        show_server_error()
        return

    name = input("Name: ")

    while True:
        email = input("Email: ")
        if valid_email(email):
            break
        print("❌ Invalid email")

    password = input("Password: ")

    # STEP 1: SEND OTP
    try:
        if role == "client":
            res = requests.post(f"{BASE_URL}/client/send-otp", json={"email": email})
        else:
            res = requests.post(f"{BASE_URL}/freelancer/send-otp", json={"email": email})
        
        # Check if response is valid JSON
        try:
            result = res.json()
            if not result.get("success"):
                print("❌ Failed to send OTP:", result.get("msg", "Unknown error"))
                return
        except requests.exceptions.JSONDecodeError:
            print(f"❌ Server returned non-JSON response (HTTP {res.status_code})")
            print(f"Response content: {res.text[:200]}...")
            return
        except Exception as e:
            print(f"❌ Error parsing OTP response: {str(e)}")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while sending OTP: {str(e)}")
        return

    print("📩 OTP sent to your email")

    # STEP 2: VERIFY OTP
    otp = input("Enter OTP: ")

    try:
        if role == "client":
            res = requests.post(f"{BASE_URL}/client/verify-otp", json={
                "name": name, "email": email, "password": password, "otp": otp
            })
        else:
            res = requests.post(f"{BASE_URL}/freelancer/verify-otp", json={
                "name": name, "email": email, "password": password, "otp": otp
            })

        # Safe JSON parsing with detailed error handling
        try:
            response = res.json()
            print(f"Server response: {response}")
        except requests.exceptions.JSONDecodeError as e:
            print(f"❌ JSONDecodeError: Failed to parse server response")
            print(f"HTTP Status: {res.status_code}")
            print(f"Response Content-Type: {res.headers.get('content-type', 'Unknown')}")
            print(f"Response text: {res.text[:500]}...")
            print(f"Error details: {str(e)}")
            return
        except Exception as e:
            print(f"❌ Unexpected error parsing response: {str(e)}")
            return

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

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during OTP verification: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error during signup: {str(e)}")

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

    # Check if server is running before proceeding
    if not check_server_connection():
        show_server_error()
        return

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
    # Get client name via API
    try:
        res = requests.get(f"{BASE_URL}/clients/{client_id}")
        client_data = res.json()
        client_name = client_data.get("name", "Client")
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

    # Safe dictionary access
    print("\n--- FREELANCER DETAILS ---")
    print("ID:", data.get("freelancer_id", fid))
    print("Name:", data.get("name", "N/A"))
    print("Email:", data.get("email", "N/A"))
    print("Category:", data.get("category", "N/A"))
    print("Title:", data.get("title", "N/A"))
    print("Skills:", data.get("skills", "N/A"))
    
    # Display formatted experience if available, otherwise show decimal
    if data.get("experience_formatted"):
        print("Experience:", data["experience_formatted"])
    else:
        print("Experience:", data.get("experience", "N/A"))
    
    print("Min Budget:", data.get("min_budget", "N/A"))
    print("Max Budget:", data.get("max_budget", "N/A"))
    print("Rating:", data.get("rating", "N/A"))
    print("Bio:", data.get("bio", "N/A"))
    
    # Display completed projects count if available
    if data.get("projects_completed") is not None:
        print("Projects Completed:", data["projects_completed"])
    
    # Display availability status with emoji formatting
    if data.get("availability_status"):
        status = data["availability_status"]
        if status == "AVAILABLE":
            print("Availability: 🟢 Available")
        elif status == "BUSY":
            print("Availability: 🟡 Busy")
        elif status == "ON_LEAVE":
            print("Availability: 🔴 On Leave")
        else:
            print("Availability:", status)
    
    # Display profile image if available
    if data.get("profile_image"):
        print("Profile Image:", data["profile_image"])
    
    # Get freelancer stats - separate section with emojis
    print("\n--- PERFORMANCE STATS ---")
    try:
        stats_res = requests.get(f"{BASE_URL}/freelancer/{fid}/stats")
        stats_data = stats_res.json()
        
        if stats_data.get("success"):
            print(f"⭐ Rating: {stats_data.get('rating', 0.0)}")
            print(f"🎯 Gigs Completed: {stats_data.get('gigs_completed', 0)}")
            print(f"💰 Earned: ₹{stats_data.get('earnings', 0)}")
        else:
            print("⭐ Rating: 0.0")
            print("🎯 Gigs Completed: 0")
            print("💰 Earned: ₹0")
    except:
        print("⭐ Rating: 0.0")
        print("🎯 Gigs Completed: 0")
        print("💰 Earned: ₹0")
    
    # Display portfolio items
    try:
        portfolio_res = requests.get(f"{BASE_URL}/freelancer/portfolio/{fid}")
        if portfolio_res.status_code == 200:
            portfolio_data = portfolio_res.json()
            if portfolio_data.get("success") and portfolio_data.get("portfolio_items"):
                print("\n--- PORTFOLIO ---")
                for item in portfolio_data["portfolio_items"]:
                    print(f"\n📁 {item['title']}")
                    print(f"   Description: {item['description']}")
                    if item.get('image_path'):
                        print(f"   Image: {item['image_path']}")
                    elif item.get('image_base64'):
                        print(f"   Image: [Base64 encoded image]")
                    print(f"   Added: {item.get('created_at', 'Unknown')}")
            else:
                print("\n--- PORTFOLIO ---")
                print("📭 No portfolio items")
        else:
            print("\n--- PORTFOLIO ---")
            print(f"❌ Error loading portfolio: HTTP {portfolio_res.status_code}")
            try:
                error_data = portfolio_res.json()
                print(f"   Details: {error_data.get('msg', 'Unknown error')}")
            except:
                pass
    except Exception as e:
        print("\n--- PORTFOLIO ---")
        print(f"❌ Error loading portfolio: {str(e)}")

# ---------- CLIENT: HIRE ----------
def hire_freelancer(fid):
    print(f"\n--- Hiring Freelancer ID: {fid} ---")
    
    # Quick hire options
    print("Hire Options:")
    print("1. Quick Hire (Simple Contract)")
    print("2. Custom Hire (Advanced Options)")
    print("0. Cancel")
    
    hire_choice = input("Choose option (1-2): ").strip()
    if hire_choice == "0":
        print("❌ Hire cancelled")
        return
    elif hire_choice == "1":
        # Quick hire - simplified process
        job_title = input("Job Title: ")
        budget = input("Proposed Budget: ")
        note = input("Note (optional): ")
        
        # Event venue collection for quick hire
        print("\n--- Event Venue ---")
        print("1. Use my saved profile address")
        print("2. Enter custom event venue")
        venue_choice = input("Choose venue option (1-2): ").strip()
        
        if venue_choice == "1":
            venue_source = "profile"
            event_address = ""
            event_city = ""
            event_pincode = ""
            event_landmark = ""
        elif venue_choice == "2":
            venue_source = "custom"
            event_address = input("Event Address: ")
            event_city = input("Event City: ")
            event_pincode = input("Event Pincode: ")
            event_landmark = input("Event Landmark (optional): ")
        else:
            print("❌ Invalid venue choice")
            return
        
        # Default to FIXED contract for quick hire
        hire_data = {
            "client_id": current_client_id,
            "freelancer_id": fid,
            "job_title": job_title,
            "proposed_budget": budget,
            "note": note,
            "contract_type": "FIXED",
            "venue_source": venue_source,
            "event_address": event_address,
            "event_city": event_city,
            "event_pincode": event_pincode,
            "event_landmark": event_landmark
        }
        
        print(f"\n--- Quick Hire Summary ---")
        print(f"Freelancer ID: {fid}")
        print(f"Job Title: {job_title}")
        print(f"Budget: {budget}")
        print(f"Contract Type: FIXED (Milestone Based)")
        print(f"Venue: {event_address if venue_source == 'custom' else 'Saved Profile Address'}")
        if venue_source == "custom":
            print(f"Event City: {event_city}")
            print(f"Event Pincode: {event_pincode}")
        
    elif hire_choice == "2":
        # Custom hire - full options
        job_title = input("Job Title: ")
        budget = input("Proposed Budget: ")
        note = input("Note (optional): ")
        
        # Collect date/time slot information
        print("\n--- Event Date & Time ---")
        while True:
            event_date = input("Enter Event Date (YYYY-MM-DD): ").strip()
            start_time = input("Enter Start Time (HH:MM): ").strip()
            end_time = input("Enter End Time (HH:MM): ").strip()
            
            # Validate using booking service
            try:
                from booking_service import validate_hire_request_slot, format_time_slot_display
                is_valid, error_msg = validate_hire_request_slot(
                    fid, event_date, start_time, end_time
                )
                if is_valid:
                    print(f"\nSelected Event Slot:")
                    print(format_time_slot_display(event_date, start_time, end_time))
                    break
                else:
                    print(f"❌ {error_msg}")
                    print("Please try again.\n")
            except ImportError:
                print("⚠️  Booking validation not available, proceeding without validation")
                break
        
        # Event venue collection for custom hire
        print("\n--- Event Venue ---")
        print("1. Use my saved profile address")
        print("2. Enter custom event venue")
        venue_choice = input("Choose venue option (1-2): ").strip()
        
        if venue_choice == "1":
            venue_source = "profile"
            event_address = ""
            event_city = ""
            event_pincode = ""
            event_landmark = ""
        elif venue_choice == "2":
            venue_source = "custom"
            event_address = input("Event Address: ")
            event_city = input("Event City: ")
            event_pincode = input("Event Pincode: ")
            event_landmark = input("Event Landmark (optional): ")
        else:
            print("❌ Invalid venue choice")
            return
        
        # Contract type selection
        print("\n--- Contract Type ---")
        print("1. FIXED (Milestone Based)")
        print("2. HOURLY (Weekly Billing with Overtime)")
        print("3. EVENT (Performance-Based with Overtime Clause)")
        
        while True:
            contract_choice = input("Choose contract type (1-3): ")
            if contract_choice in ["1", "2", "3"]:
                break
            print("❌ Invalid choice. Please enter 1, 2, or 3")
        
        contract_types = {"1": "FIXED", "2": "HOURLY", "3": "EVENT"}
        contract_type = contract_types[contract_choice]
        
        # Prepare hire request data
        hire_data = {
            "client_id": current_client_id,
            "freelancer_id": fid,
            "job_title": job_title,
            "proposed_budget": budget,
            "note": note,
            "contract_type": contract_type,
            "event_date": event_date,
            "start_time": start_time,
            "end_time": end_time,
            "venue_source": venue_source,
            "event_address": event_address,
            "event_city": event_city,
            "event_pincode": event_pincode,
            "event_landmark": event_landmark
        }
        
        # Add contract-specific fields
        if contract_type == "HOURLY":
            hourly_rate = input("Hourly Rate: ")
            weekly_limit = input("Weekly Hours Limit: ")
            max_daily_hours = input("Max Daily Hours (default 8): ") or "8"
            
            hire_data.update({
                "contract_hourly_rate": float(hourly_rate),
                "weekly_limit": float(weekly_limit),
                "max_daily_hours": float(max_daily_hours)
            })
            
        elif contract_type == "EVENT":
            event_base_fee = input("Event Base Fee: ")
            event_included_hours = input("Included Hours: ")
            event_overtime_rate = input("Overtime Rate per Hour: ")
            advance_paid = input("Advance Paid (0 if none): ") or "0"
            
            hire_data.update({
                "event_base_fee": float(event_base_fee),
                "event_included_hours": float(event_included_hours),
                "event_overtime_rate": float(event_overtime_rate),
                "advance_paid": float(advance_paid)
            })

        # Confirmation step
        print(f"\n--- Custom Hire Summary ---")
        print(f"Freelancer ID: {fid}")
        print(f"Job Title: {job_title}")
        print(f"Budget: {budget}")
        print(f"Event Date: {event_date}")
        print(f"Time Slot: {start_time} - {end_time}")
        print(f"Contract Type: {contract_type}")
        print(f"Venue: {event_address if venue_source == 'custom' else 'Saved Profile Address'}")
        if venue_source == "custom":
            print(f"Event City: {event_city}")
            print(f"Event Pincode: {event_pincode}")
        
    else:
        print("❌ Invalid choice")
        return
    
    confirm = input("\nConfirm Hire Request? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Hire request cancelled")
        return

    res = requests.post(f"{BASE_URL}/client/hire", json=hire_data)
    result = res.json()
    
    if result.get("success"):
        print("\n✅ Hire request sent successfully!")
        print(f"Freelancer ID: {fid}")
        print(f"Job Title: {job_title}")
        print(f"Budget: {budget}")
        
        # Show venue information
        venue_info = result.get("venue", {})
        print(f"\n--- Event Venue ---")
        print(f"Venue: {venue_info.get('event_address', 'Not specified')}")
        if venue_info.get('event_city'):
            print(f"City: {venue_info.get('event_city')}")
        if venue_info.get('event_pincode'):
            print(f"Pincode: {venue_info.get('event_pincode')}")
        print(f"Source: {venue_info.get('venue_source', 'custom')}")
        
        # Show location compatibility check
        location_check = result.get("location_check", {})
        print(f"\n--- Location Compatibility ---")
        print(f"Status: {'✅ Compatible' if location_check.get('location_ok') else '⚠️  May be far'}")
        print(f"Note: {location_check.get('location_note', 'No location check performed')}")
        
        print(f"Status: PENDING")
        print(f"Request ID: {result.get('request_id')}")
    else:
        print(f"\n❌ Failed to send hire request: {result.get('msg', 'Unknown error')}")

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

# ---------- PLATFORM STATS ----------
def show_platform_stats():
    """Display platform-wide statistics"""
    try:
        res = requests.get(f"{BASE_URL}/platform/stats")
        data = res.json()
        
        if not data.get("success"):
            print("❌ Error:", data.get("msg", "Unknown error"))
            return
        
        print("\n" + "="*50)
        print("🌟 GIGBRIDGE PLATFORM STATS")
        print("="*50)
        print(f"👥 Total Freelancers: {data.get('total_freelancers', 0)}")
        print(f"🏢 Total Clients: {data.get('total_clients', 0)}")
        print(f"✅ Gigs Completed: {data.get('gigs_completed', 0)}")
        print("="*50)
        
    except Exception as e:
        print("❌ Error fetching platform stats:", str(e))


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
        print("2. View All")
        print("3. Search")
        print("4. View My Jobs")
        print("5. Rate Freelancers")
        print("6. Saved Freelancers")
        print("7. Notifications")
        print("8. Messages")
        print("9. Job Request Status")
        print("10. Recommended Freelancers (AI)")
        print("11. Check Incoming Calls")
        print("12. Post Project")
        print("13. My Projects")
        print("14. View Applicants")
        print("15. Accept Applicant")
        print("16. Upload Verification Documents")
        print("17. Check Verification Status")
        print("18. Contact Freelancer")
        print("19. Logout")
        print("20. Exit")

        choice = input("Choose: ")
        
        if choice == "20":
            print("👋 Exiting GigBridge CLI")
            return
        
        if choice == "19":
            current_client_id = None
            print("✅ Logged out successfully")
            return
        
        if choice == "1":
            # Get username
            while True:
                name = input("Username: ").strip()
                if not name:
                    print("❌ Username is required")
                    continue
                break
            
            # Get phone
            while True:
                phone = input("Phone (10 digits): ")
                if valid_phone(phone):
                    break
                print(" Phone must be 10 digits")
                print("❌ Phone must be 10 digits")

            pincode = input("PIN Code (6 digits): ")
            dob = get_valid_dob()

            res = requests.post(f"{BASE_URL}/client/profile", json={
                "client_id": current_client_id,
                "name": name,
                "phone": phone,
                "location": input("Location: "),
                "bio": input("Bio: "),
                "pincode": pincode,
                "dob": dob
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

            current_index = 0
            while current_index < len(freelancers):
                f = freelancers[current_index]
                print("\n--- Freelancer ---")
                print("ID:", f["freelancer_id"])
                print("Name:", f["name"])
                print("Category:", f.get("category", "Not specified"))
                print("Title:", f.get("title", "Not specified"))
                print("Budget Range:", f.get("budget_range", "Not specified"))
                print("Rating:", f.get("rating", 0))
                print("Status:", f.get("availability_status", "UNKNOWN"))
                
                # Additional hiring-relevant information
                if f.get("experience"):
                    print("Experience:", f["experience"], "years")
                if f.get("skills"):
                    print("Skills:", f["skills"])
                if f.get("bio"):
                    print("Bio:", f["bio"][:100] + "..." if len(f["bio"]) > 100 else f["bio"])
                if f.get("subscription_plan"):
                    print("Plan:", f["subscription_plan"])
                if f.get("distance") and f["distance"] != 999999.0:
                    print("Distance:", f"{f['distance']:.1f} km")
                
                print(f"Showing {current_index + 1} of {len(freelancers)}")

                print("\n--- Actions ---")
                print("1. View Details")
                print("2. Message")
                print("3. Hire")
                print("4. Save Freelancer")
                print("5. Next")
                print("6. Previous")
                print("0. Back to Dashboard")

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
                elif action == "5":
                    current_index += 1
                    if current_index >= len(freelancers):
                        current_index = 0  # Wrap around to beginning
                elif action == "6":
                    current_index -= 1
                    if current_index < 0:
                        current_index = len(freelancers) - 1  # Wrap around to end
                elif action == "0":
                    break

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
                "budget": budget
            }
            if current_client_id:
                params["client_id"] = current_client_id
            if specialization and specialization.strip() and specialization.lower() not in ["no", "none", ""]:
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

            current_index = 0
            while current_index < len(freelancers):
                f = freelancers[current_index]
                print("\n--- Freelancer ---")
                print("ID:", f["freelancer_id"])
                print("Name:", f["name"])
                print("Category:", f.get("category", "Not specified"))
                print("Title:", f.get("title", "Not specified"))
                print("Budget Range:", f.get("budget_range", "Not specified"))
                print("Rating:", f.get("rating", 0))
                print("Status:", f.get("availability_status", "UNKNOWN"))
                
                # Additional hiring-relevant information
                if f.get("experience"):
                    print("Experience:", f["experience"], "years")
                if f.get("skills"):
                    print("Skills:", f["skills"])
                if f.get("bio"):
                    print("Bio:", f["bio"][:100] + "..." if len(f["bio"]) > 100 else f["bio"])
                if f.get("subscription_plan"):
                    print("Plan:", f["subscription_plan"])
                if f.get("distance") and f["distance"] != 999999.0:
                    print("Distance:", f"{f['distance']:.1f} km")
                
                print(f"Showing {current_index + 1} of {len(freelancers)}")

                print("\n--- Actions ---")
                print("1. View Details")
                print("2. Message")
                print("3. Hire")
                print("4. Save Freelancer")
                print("5. Next")
                print("6. Previous")
                print("0. Back to Dashboard")

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
                elif action == "5":
                    current_index += 1
                    if current_index >= len(freelancers):
                        current_index = 0  # Wrap around to beginning
                elif action == "6":
                    current_index -= 1
                    if current_index < 0:
                        current_index = len(freelancers) - 1  # Wrap around to end
                elif action == "0":
                    break

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
                        
                        # Show rating option for PAID jobs
                        if j.get('status') == 'PAID':
                            print("   [R] Rate this freelancer")
                    
                    # Allow user to select a job for rating
                    action = input("\nEnter job number to rate, or 0 to go back: ")
                    if action.lower() == 'r' or (action.isdigit() and int(action) > 0):
                        try:
                            job_idx = int(action) - 1 if action.isdigit() else None
                            if job_idx is not None and 0 <= job_idx < len(jobs):
                                selected_job = jobs[job_idx]
                                if selected_job.get('status') == 'PAID':
                                    rate_freelancer_for_job(selected_job)
                                else:
                                    print("❌ Can only rate PAID jobs")
                            else:
                                print("❌ Invalid job selection")
                        except Exception as e:
                            print("❌ Error:", str(e))
            except Exception as e:
                print("❌ Error fetching jobs:", str(e))

        elif choice == "5":
            # Dedicated rating option - show only PAID jobs
            res = requests.get(f"{BASE_URL}/client/jobs", params={
                "client_id": current_client_id
            })
            print("\n--- RATE FREELANCERS ---")
            try:
                jobs = res.json()
                paid_jobs = [job for job in jobs if job.get('status') == 'PAID']
                
                if not paid_jobs:
                    print("❌ No paid jobs available for rating")
                else:
                    print("Jobs available for rating:")
                    for i, job in enumerate(paid_jobs, 1):
                        print(f"{i}. {job['title']} | ₹{job['budget']} | {job['status']}")
                    
                    action = input("\nEnter job number to rate, or 0 to go back: ")
                    if action.isdigit() and int(action) > 0:
                        job_idx = int(action) - 1
                        if 0 <= job_idx < len(paid_jobs):
                            rate_freelancer_for_job(paid_jobs[job_idx])
                        else:
                            print("❌ Invalid job selection")
            except Exception as e:
                print("❌ Error fetching jobs:", str(e))

        elif choice == "12":
            # Post Project
            title = input("Project Title: ").strip()
            description = input("Description: ").strip()
            category = input("Category: ").strip()
            skills = input("Skills: ").strip()
            print("Budget Type: 1) FIXED 2) HOURLY")
            bt_choice = input("Choose: ").strip()
            budget_type = "FIXED" if bt_choice == "1" else "HOURLY" if bt_choice == "2" else None
            if not budget_type:
                print("❌ Invalid budget type choice")
                continue
            
            try:
                if budget_type == "FIXED":
                    budget_value = float(input("Fixed Budget: "))
                elif budget_type == "HOURLY":
                    budget_value = float(input("Hourly Rate: "))
                else:
                    print("❌ Invalid budget type")
                    continue
                    
                if budget_value <= 0:
                    print("❌ Budget must be greater than 0")
                    continue
            except Exception:
                print("❌ Invalid budget value")
                continue
                
            res = requests.post(f"{BASE_URL}/client/projects/create", json={
                "client_id": current_client_id,
                "title": title,
                "description": description,
                "category": category,
                "skills": skills,
                "budget_type": budget_type,
                "budget": budget_value if budget_type == "FIXED" else None,
                "hourly_rate": budget_value if budget_type == "HOURLY" else None
            })
            print(res.json())

        elif choice == "13":
            # My Projects
            res = requests.get(f"{BASE_URL}/client/projects", params={"client_id": current_client_id})
            try:
                data = res.json()
                if data.get("success"):
                    print("\n--- My Projects ---")
                    for p in data.get("projects", []):
                        print(f"{p['project_id']}. {p['title']} [{p['status']}] {p['budget_type']} {p['budget_min']}-{p['budget_max']}")
                else:
                    print("❌", data.get("msg"))
            except Exception as e:
                print("❌ Error:", str(e))

        elif choice == "14":
            # View Applicants
            pid = input("Project ID: ").strip()
            res = requests.get(f"{BASE_URL}/client/projects/applicants", params={
                "client_id": current_client_id,
                "project_id": pid
            })
            try:
                data = res.json()
                if data.get("success"):
                    print("\n--- Applicants ---")
                    for a in data.get("applicants", []):
                        print(f"{a['application_id']}. Freelancer {a['freelancer_id']} | {a['status']}")
                        print(f"   Proposal: {a['proposal_text']}")
                        print(f"   Bid: {a.get('bid_amount')} Hourly: {a.get('hourly_rate')} Event: {a.get('event_base_fee')}")
                else:
                    print("❌", data.get("msg"))
            except Exception as e:
                print("❌ Error:", str(e))

        elif choice == "15":
            # Accept Applicant
            pid = input("Project ID: ").strip()
            aid = input("Application ID: ").strip()
            res = requests.post(f"{BASE_URL}/client/projects/accept_application", json={
                "client_id": current_client_id,
                "project_id": pid,
                "application_id": aid
            })
            print(res.json())

        elif choice == "6":
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

        elif choice == "7":
            res = requests.get(f"{BASE_URL}/client/notifications", params={
                "client_id": current_client_id
            })
            print("\n--- NOTIFICATIONS ---")
            try:
                notifications = res.json()
                if not notifications:
                    print("❌ No notifications")
                else:
                    for n in notifications:
                        print("*", n)
            except Exception as e:
                print("❌ Error getting notifications:", str(e))

        elif choice == "8":
            client_messages_menu()

        elif choice == "9":
            client_job_request_status_menu()

        elif choice == "10":
            client_ai_recommendations()

        elif choice == "11":
            check_incoming_calls()

        elif choice == "16":
            client_upload_verification()

        elif choice == "17":
            client_check_verification_status()

        elif choice == "18":
            contact_freelancer()

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

def contact_freelancer():
    """Contact a freelancer via voice/video call or message"""
    if not current_client_id:
        print("❌ Please login as client first")
        return
    
    print("\n--- CONTACT MENU ---")
    print("1. Voice Call")
    print("2. Video Call")
    print("3. Send Message")
    print("4. Back to Dashboard")
    
    choice = input("Choose: ")
    
    if choice == "1":
        start_call_flow("voice")
    elif choice == "2":
        start_call_flow("video")
    elif choice == "3":
        # Get freelancer list for messaging
        res = requests.get(f"{BASE_URL}/freelancers/all")
        data = res.json()
        if data.get("success"):
            print("\n--- Select Freelancer to Message ---")
            for f in data.get("freelancers", []):
                print(f"{f['freelancer_id']}. {f['name']} - {f.get('category', 'N/A')}")
            
            try:
                fid = input("Enter Freelancer ID: ")
                if fid.isdigit():
                    open_chat_with_freelancer(int(fid))
                else:
                    print("❌ Invalid Freelancer ID")
            except Exception as e:
                print("❌ Error opening chat:", str(e))
        else:
            print("❌ Error fetching freelancers:", data.get("msg"))
    elif choice == "4":
        return
    else:
        print("❌ Invalid choice")

def start_call_flow(call_type):
    """Start a voice or video call"""
    if not current_client_id:
        print("❌ Please login as client first")
        return
    
    print(f"DEBUG: current_client_id = {current_client_id}")
    
    # Get freelancer list
    res = requests.get(f"{BASE_URL}/freelancers/all")
    data = res.json()
    if not data.get("success"):
        print("❌ Error fetching freelancers:", data.get("msg"))
        return
    
    print(f"\n--- Select Freelancer for {call_type.title()} Call ---")
    for f in data.get("freelancers", []):
        print(f"{f['freelancer_id']}. {f['name']} - {f.get('category', 'N/A')}")
    
    try:
        fid = input("Enter Freelancer ID: ")
        if not fid.isdigit():
            print("❌ Invalid Freelancer ID")
            return
        
        freelancer_id = int(fid)
        
        # Start the call
        call_data = {
            "caller_id": current_client_id,
            "receiver_id": freelancer_id,
            "call_type": call_type
        }
        print(f"DEBUG: Sending call data: {call_data}")
        res = requests.post(f"{BASE_URL}/call/start", json=call_data)
        
        result = res.json()
        if result.get("success"):
            print(f"✅ {call_type.title()} call started!")
            print(f"Meeting URL: {result['meeting_url']}")
            print("🌐 Opening in browser...")
            
            # Open in browser
            import webbrowser
            webbrowser.open(result['meeting_url'])
        else:
            print(f"❌ Failed to start call: {result.get('msg')}")
    
    except Exception as e:
        print("❌ Error starting call:", str(e))

def contact_client():
    """Contact a client via voice/video call or message"""
    if not current_freelancer_id:
        print("❌ Please login as freelancer first")
        return
    
    print("\n--- CONTACT MENU ---")
    print("1. Voice Call")
    print("2. Video Call")
    print("3. Send Message")
    print("4. Back to Dashboard")
    
    choice = input("Choose: ")
    
    if choice == "1":
        start_call_to_client("voice")
    elif choice == "2":
        start_call_to_client("video")
    elif choice == "3":
        # Get client list for messaging
        res = requests.get(f"{BASE_URL}/freelancer/saved-clients", params={
            "freelancer_id": current_freelancer_id
        })
        data = res.json()
        if isinstance(data, list):
            clients = data
        else:
            clients = data.get("clients", [])
        
        if clients:
            print("\n--- Select Client to Message ---")
            for c in clients:
                print(f"{c['client_id']}. {c['name']}")
            
            try:
                cid = input("Enter Client ID: ")
                if cid.isdigit():
                    open_chat_with_client(int(cid))
                else:
                    print("❌ Invalid Client ID")
            except Exception as e:
                print("❌ Error opening chat:", str(e))
        else:
            print("❌ No saved clients found")
    elif choice == "4":
        return
    else:
        print("❌ Invalid choice")

def start_call_to_client(call_type):
    """Start a voice or video call to a client"""
    if not current_freelancer_id:
        print("❌ Please login as freelancer first")
        return
    
    # Get client list
    res = requests.get(f"{BASE_URL}/freelancer/saved-clients", params={
        "freelancer_id": current_freelancer_id
    })
    data = res.json()
    if isinstance(data, list):
        clients = data
    else:
        clients = data.get("clients", [])
    
    if not clients:
        print("❌ No saved clients found")
        return
    
    print(f"\n--- Select Client for {call_type.title()} Call ---")
    for c in clients:
        print(f"{c['client_id']}. {c['name']}")
    
    try:
        cid = input("Enter Client ID: ")
        if not cid.isdigit():
            print("❌ Invalid Client ID")
            return
        
        client_id = int(cid)
        
        # Start the call
        res = requests.post(f"{BASE_URL}/call/start", json={
            "caller_id": current_freelancer_id,
            "receiver_id": client_id,
            "call_type": call_type
        })
        
        result = res.json()
        if result.get("success"):
            print(f"✅ {call_type.title()} call started!")
            print(f"Meeting URL: {result['meeting_url']}")
            print("🌐 Opening in browser...")
            
            # Open in browser
            import webbrowser
            webbrowser.open(result['meeting_url'])
        else:
            print(f"❌ Failed to start call: {result.get('msg')}")
    
    except Exception as e:
        print("❌ Error starting call:", str(e))

def open_chat_with_client(client_id):
    """Open chat with a client"""
    print(f"Opening chat with client {client_id}...")
    # Implementation would be similar to existing chat functionality
    print("📱 Chat feature would be implemented here")


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
            print(" Upload failed:", result.get("msg", "Unknown error"))
    
    except Exception as e:
        print(" Error uploading verification:", str(e))


# ---------- CLIENT VERIFICATION ----------
def client_upload_verification():
    """Upload verification documents for client"""
    if not current_client_id:
        print("❌ Please login as client first")
        return
    
    print("\n--- CLIENT VERIFICATION ---")
    print("📋 Required Documents:")
    print("   1. Government ID")
    print("   2. PAN Card")
    print("\n📁 Allowed formats: PDF, JPG, PNG")
    print("📁 Maximum file size: 5MB")
    
    # Check if already submitted
    try:
        res = requests.get(f"{BASE_URL}/client/kyc/status", params={
            "client_id": current_client_id
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
        print("❌ Government ID file path required")
        return
    
    pan_card = input("PAN card file path: ").strip()
    if not pan_card:
        print("❌ PAN card file path required")
        return
    
    # Validate files exist
    import os
    if not os.path.exists(government_id):
        print(f"❌ Government ID file not found: {government_id}")
        return
    
    if not os.path.exists(pan_card):
        print(f"❌ PAN card file not found: {pan_card}")
        return
    
    # Upload files
    try:
        with open(government_id, 'rb') as gov_file, open(pan_card, 'rb') as pan_file:
            files = {
                'government_id': gov_file,
                'pan_card': pan_file
            }
            data = {
                'client_id': current_client_id
            }
            
            res = requests.post(f"{BASE_URL}/client/kyc/upload", files=files, data=data)
            result = res.json()
            
            if result.get("success"):
                print("✅ Verification documents submitted successfully!")
                print("📋 Awaiting admin approval.")
            else:
                print("❌ Upload failed:", result.get("msg", "Unknown error"))
                
    except Exception as e:
        print("❌ Error uploading verification:", str(e))


def client_check_verification_status():
    """Check verification status for client"""
    if not current_client_id:
        print("❌ Please login as client first")
        return
    
    try:
        res = requests.get(f"{BASE_URL}/client/kyc/status", params={
            "client_id": current_client_id
        })
        data = res.json()
        
        if not data.get("success"):
            print("❌ Error:", data.get("msg", "Unknown error"))
            return
        
        print("\n--- VERIFICATION STATUS ---")
        status = data.get("status")
        
        if status is None:
            print("Status: Not submitted yet")
            print("\n📋 Submit your verification documents to get verified.")
        else:
            print(f"Status: {status}")
            
            if status == "PENDING":
                print("\n📋 Your documents are under review.")
                print("   Admin will review your submission soon.")
            elif status == "REJECTED":
                print("\n❌ Your verification was rejected.")
                print("   Please contact support or re-submit with correct documents.")
            elif status == "APPROVED":
                print("\n✅ Congratulations! Your verification is approved.")
        
    except Exception as e:
        print("❌ Error checking verification status:", str(e))


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
        
        # Check if response is valid
        if res.status_code != 200:
            print("\nPlan: BASIC")
            print("Job Applies Used: 0 / 10")
            return
            
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
        else:
            print("\nPlan: BASIC")
            print("Job Applies Used: 0 / 10")
    except Exception as e:
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
        print("2. View My Profile")
        print("3. View Hire Requests")
        print("4. Manage Active Jobs")
        print("5. Messages")
        print("6. Earnings")
        print("7. Saved Clients")
        print("8. Account Settings")
        print("9. Notifications")
        print("10. Manage Portfolio")
        print("11. Upload Profile Photo")
        print("12. Check Incoming Calls 📞")
        print("13. Verification Status 🏅")
        print("14. Upload Verification Documents")
        print("15. Subscription Plans 💎")
        print("16. My Subscription")
        print("17. Update Availability Status")
        print("18. Contact Client")
        print("19. Exit")
        print("20. Logout")
        print("21. Browse Projects")
        print("22. Apply to Project")

        choice = input("Choose: ")

        if choice == "19":
            print("👋 Exiting GigBridge CLI")
            return
        
        if choice == "20":
            current_freelancer_id = None
            print("✅ Logged out successfully")
            return

        # 1️⃣ Create / Update Profile
        if choice == "1":
            from categories import ALLOWED_FREELANCER_CATEGORIES
            print("\nAllowed Categories:")
            for cat in ALLOWED_FREELANCER_CATEGORIES:
                print(f"- {cat}")

            try:
                title = input("Title: ")
                skills = input("Skills: ")
                
                # Get experience in years and months
                print("\nExperience Details:")
                years = int(input("Years (0-40): "))
                months = int(input("Months (0-11): "))
                
                min_budget = float(input("Min Budget: "))
                max_budget = float(input("Max Budget: "))
                bio = input("Bio: ")
                pincode = input("PIN Code (6 digits): ")
                location = input("Location: ")
                category = input("Category (choose from above): ")
                from categories import is_valid_category
                if not is_valid_category(category):
                    print("Invalid category. Please choose from the allowed list.")
                    continue
                dob = get_valid_dob()
                res = requests.post(f"{BASE_URL}/freelancer/profile", json={
                    "freelancer_id": current_freelancer_id,
                    "title": title,
                    "skills": skills,
                    "years": years,
                    "months": months,
                    "min_budget": min_budget,
                    "max_budget": max_budget,
                    "bio": bio,
                    "pincode": pincode,
                    "location": location,
                    "category": category,
                    "dob": dob
                })
                print(res.json())
            except Exception:
                print("❌ Server error while updating profile")

        # 2️⃣ View My Profile
        elif choice == "2":
            view_freelancer_details(current_freelancer_id)

        # 3️⃣ View Hire Requests (Inbox)
        elif choice == "3":
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
                
                # Display based on contract type
                contract_type = r.get("contract_type", "FIXED")
                print("Contract Type:", contract_type)
                
                if contract_type == "FIXED":
                    print("Proposed Budget: ₹", r["proposed_budget"])
                elif contract_type == "HOURLY":
                    print("Hourly Rate: ₹", r.get("contract_hourly_rate", 0))
                    print("Overtime Rate: ₹", r.get("contract_overtime_rate", 0))
                    print("Weekly Limit:", r.get("weekly_limit", 0))
                    print("Max Daily Hours:", r.get("max_daily_hours", 8))
                elif contract_type == "EVENT":
                    print("Base Fee: ₹", r.get("event_base_fee", 0))
                    print("Included Hours:", r.get("event_included_hours", 0))
                    print("Overtime Rate: ₹", r.get("event_overtime_rate", 0))
                    print("Advance Paid: ₹", r.get("advance_paid", 0))
                
                print("Note:", r["note"])
                print("Status:", r["status"])

                if r["status"] == "PENDING":
                    print("1. Accept")
                    print("2. Reject")
                    print("3. Message Client")
                    print("4. Save Client")
                    print("5. Next")
                    print("0. Back")
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
                    elif a == "0":
                        break  # Back to dashboard

        # 4️⃣ Manage Active Jobs
        elif choice == "4":
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
                    contract_type = j.get("contract_type", "FIXED")
                    
                    if contract_type == "FIXED":
                        budget_info = f"Budget: ₹{j['proposed_budget']}"
                    elif contract_type == "HOURLY":
                        budget_info = f"Rate: ₹{j.get('contract_hourly_rate', 0)}/hr"
                    elif contract_type == "EVENT":
                        budget_info = f"Base: ₹{j.get('event_base_fee', 0)}"
                    else:
                        budget_info = f"Budget: ₹{j['proposed_budget']}"
                    
                    print(f"{i}. Client: {j['client_name']} | {budget_info} | {contract_type} | {j['status']}")

        # 5️⃣ Messages
        elif choice == "5":
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

        # 6️⃣ Earnings & Performance
        elif choice == "6":
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

        # 7️⃣ Saved Clients
        elif choice == "7":
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

        # 8️⃣ Account Settings
        elif choice == "8":
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

        # 9️⃣ Notifications / Activity
        elif choice == "9":
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

        # 10️⃣ Manage Portfolio
        elif choice == "10":
            while True:
                print("\n--- MANAGE PORTFOLIO ---")
                print("1. Add Image")
                print("2. Add Video Link")
                print("3. Add Document Link")
                print("4. View My Portfolio")
                print("5. Back")
                portfolio_choice = input("Choose: ")
                
                if portfolio_choice == "1":
                    # Add Image
                    title = input("Title: ")
                    description = input("Description: ")
                    image_path = input("Image Path (local file): ")
                    
                    try:
                        res = requests.post(f"{BASE_URL}/freelancer/portfolio/add", json={
                            "freelancer_id": current_freelancer_id,
                            "title": title,
                            "description": description,
                            "image_path": image_path,
                            "media_type": "IMAGE"
                        })
                        result = res.json()
                        if result.get("success"):
                            print("✅ Portfolio image added!")
                        else:
                            print("❌ Failed:", result.get("msg"))
                    except Exception as e:
                        print("❌ Error adding portfolio item:", str(e))
                
                elif portfolio_choice == "2":
                    # Add Video Link
                    title = input("Title: ")
                    description = input("Description: ")
                    media_url = input("Video URL: ")
                    try:
                        res = requests.post(f"{BASE_URL}/freelancer/portfolio/add", json={
                            "freelancer_id": current_freelancer_id,
                            "title": title,
                            "description": description,
                            "media_type": "VIDEO",
                            "media_url": media_url
                        })
                        result = res.json()
                        if result.get("success"):
                            print("✅ Video link added!")
                        else:
                            print("❌ Failed:", result.get("msg"))
                    except Exception as e:
                        print("❌ Error adding video link:", str(e))
                
                elif portfolio_choice == "3":
                    # Add Document Link
                    title = input("Title: ")
                    description = input("Description: ")
                    media_url = input("Document URL: ")
                    try:
                        res = requests.post(f"{BASE_URL}/freelancer/portfolio/add", json={
                            "freelancer_id": current_freelancer_id,
                            "title": title,
                            "description": description,
                            "media_type": "DOC",
                            "media_url": media_url
                        })
                        result = res.json()
                        if result.get("success"):
                            print("✅ Document link added!")
                        else:
                            print("❌ Failed:", result.get("msg"))
                    except Exception as e:
                        print("❌ Error adding document link:", str(e))
                
                elif portfolio_choice == "4":
                    # View My Portfolio
                    try:
                        res = requests.get(f"{BASE_URL}/freelancer/portfolio/{current_freelancer_id}")
                        data = res.json()
                        if data.get("success") and data.get("portfolio_items"):
                            print("\n--- MY PORTFOLIO ---")
                            for item in data["portfolio_items"]:
                                print(f"\n📁 {item['title']}")
                                print(f"   Description: {item['description']}")
                                mt = item.get("media_type", "IMAGE")
                                print(f"   Type: {mt}")
                                if mt in ("VIDEO","DOC"):
                                    print(f"   URL: {item.get('media_url','')}")
                                
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
                
                elif portfolio_choice == "5":
                    break

        # 11️⃣ Upload Profile Photo
        elif choice == "11":
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

        # 12️⃣ Check Incoming Calls
        elif choice == "12":
            check_incoming_calls()

        elif choice == "17":
            freelancer_verification_status()

        # 14️⃣ Upload Verification Documents
        elif choice == "14":
            freelancer_upload_verification()

        # 15️⃣ Subscription Plans
        elif choice == "15":
            freelancer_subscription_plans()

        # 16️⃣ My Subscription
        elif choice == "16":
            freelancer_my_subscription()

        # 17️⃣ Update Availability Status
        elif choice == "17":
            print("\n--- UPDATE AVAILABILITY STATUS ---")
            print("1. 🟢 Available")
            print("2. 🟡 Busy")
            print("3. 🔴 On Leave")
            print("0. Back")
            
            status_choice = input("Choose: ")
            if status_choice == "1":
                new_status = "AVAILABLE"
            elif status_choice == "2":
                new_status = "BUSY"
            elif status_choice == "3":
                new_status = "ON_LEAVE"
            elif status_choice == "0":
                continue
            else:
                print("❌ Invalid choice")
                continue

        elif choice == "18":
            contact_client()
            
            try:
                res = requests.post(f"{BASE_URL}/freelancer/update-availability", json={
                    "freelancer_id": current_freelancer_id,
                    "availability_status": new_status
                })
                result = res.json()
                if result.get("success"):
                    status_display = {
                        "AVAILABLE": "🟢 Available",
                        "BUSY": "🟡 Busy", 
                        "ON_LEAVE": "🔴 On Leave"
                    }
                    print(f"✅ Availability updated to: {status_display[new_status]}")
                else:
                    print("❌ Failed to update availability:", result.get("msg"))
            except Exception as e:
                print("❌ Error updating availability:", str(e))

        elif choice == "20":
            # Browse Projects
            try:
                res = requests.get(f"{BASE_URL}/freelancer/projects/feed")
                data = res.json()
                if data.get("success"):
                    print("\n--- OPEN PROJECTS ---")
                    for p in data.get("projects", []):
                        print(f"{p['project_id']}. {p['title']} [{p['budget_type']}] {p['budget_min']}-{p['budget_max']}")
                        print(f"   {p['category']} | Skills: {p['skills']}")
                        print(f"   {p['description']}")
                else:
                    print("❌", data.get("msg"))
            except Exception as e:
                print("❌ Error:", str(e))

        elif choice == "21":
            # Apply to Project
            pid = input("Project ID: ").strip()
            proposal = input("Proposal Text: ").strip()
            print("Optional bid fields: leave blank if not applicable")
            bid_amount = input("Bid Amount (FIXED): ").strip()
            hourly_rate = input("Hourly Rate (HOURLY): ").strip()
            event_base_fee = input("Event Base Fee (EVENT): ").strip()
            payload = {
                "freelancer_id": current_freelancer_id,
                "project_id": pid,
                "proposal_text": proposal
            }
            if bid_amount:
                try: payload["bid_amount"] = float(bid_amount)
                except: pass
            if hourly_rate:
                try: payload["hourly_rate"] = float(hourly_rate)
                except: pass
            if event_base_fee:
                try: payload["event_base_fee"] = float(event_base_fee)
                except: pass
            res = requests.post(f"{BASE_URL}/freelancer/projects/apply", json=payload)
            print(res.json())

        # ---------- MAIN MENU ----------
# ---------- MAIN MENU ----------
while True:
    print("\n====== GIGBRIDGE ======")
    print("1. Login")
    print("2. Sign Up")
    print("3. Continue as Client")
    print("4. Continue as Freelancer")
    print("5. Platform Stats")
    print("6. Exit")

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
        show_platform_stats()

    elif option == "6":
        print("👋 Goodbye")
        break
