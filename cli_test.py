import requests
import time
from datetime import datetime
import webbrowser
import uuid

BASE_URL = "http://127.0.0.1:5000"

try:
    from categories import (
        get_pricing_type_for_category,
        PRICING_TYPE_HOURLY,
        PRICING_TYPE_PER_PERSON,
        PRICING_TYPE_PACKAGE,
        PRICING_TYPE_PROJECT,
    )
except Exception:
    # Fallback if categories module is not available for some reason;
    # in that case CLI will behave like the legacy version and tests
    # for pricing-type-specific behavior may be limited.
    get_pricing_type_for_category = None
    PRICING_TYPE_HOURLY = "hourly"
    PRICING_TYPE_PER_PERSON = "per_person"
    PRICING_TYPE_PACKAGE = "package"
    PRICING_TYPE_PROJECT = "project"

current_client_id = None
current_freelancer_id = None
selected_package = None

def display_freelancer(f):
    """Display freelancer information with consistent formatting and dynamic pricing"""
    print("\n--- Freelancer ---")
    
    # Handle both 'id' and 'freelancer_id' fields
    freelancer_id = f.get('freelancer_id') or f.get('id')
    print(f"ID: {freelancer_id}")
    
    print(f"Name: {f.get('name', '')}")
    print(f"Category: {f.get('category', '').title()}")
    print(f"Title: {f.get('title', '')}")

    # PRICING TYPE (from backend)
    pricing_type = (f.get("pricing_type") or "").lower()
    print(f"Pricing Type: {pricing_type.upper()}")

    if pricing_type == "hourly":
        print(f"Hourly Rate: ₹{f.get('hourly_rate', 0)} / hour")

    elif pricing_type == "per_person":
        print(f"Per Person Rate: ₹{f.get('per_person_rate', 0)} per person")

    elif pricing_type == "package":
        print(f"Starting Price: ₹{f.get('starting_price', 0)}")

    elif pricing_type == "project":
        print(f"Project Price: ₹{f.get('fixed_price', 0)}")

    else:
        print("Price: Not specified")

    # KEEP EXISTING FIELDS
    print(f"Rating: ⭐ {f.get('rating', 0):.1f}")

    status = f.get("availability_status", "UNKNOWN")
    if status == "AVAILABLE":
        print("Status: 🟢 AVAILABLE")
    else:
        print("Status: 🔴 NOT AVAILABLE")

    print(f"Experience: {int(f.get('experience', 0))} years")

    if f.get("skills"):
        print(f"Skills: {f.get('skills')}")

    if f.get("current_plan"):
        print(f"Plan: {f.get('current_plan')}")

    if f.get("distance") is not None:
        print(f"Distance: {round(f.get('distance'), 1)} km")

def clean_path(p):
    """Clean file path by removing quotes and trailing spaces"""
    return p.strip().strip('"').strip("'").strip()

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

def start_call(caller_role, receiver_id=None, call_type=None):
    """Start a voice or video call"""
    try:
        # Safety check: ensure user is logged in
        if caller_role == "client" and not current_client_id:
            print("❌ Please login as client first")
            return
        elif caller_role == "freelancer" and not current_freelancer_id:
            print("❌ Please login as freelancer first")
            return
        
        # Determine caller ID based on role
        if caller_role == "client":
            caller_id = current_client_id
            receiver_role = "freelancer"
        else:
            caller_id = current_freelancer_id
            receiver_role = "client"
        
        # Ask for receiver ID if not provided
        if receiver_id is None:
            try:
                receiver_id = int(input(f"Enter {receiver_role} ID to call: ").strip())
            except ValueError:
                print("❌ Invalid ID")
                return
        
        # Ask for call type if not provided
        if call_type is None:
            print("\nCall type:")
            print("1. Voice Call")
            print("2. Video Call")
            choice = input("Choose (1-2): ").strip()
            if choice == "1":
                call_type = "voice"
            elif choice == "2":
                call_type = "video"
            else:
                print("❌ Invalid choice")
                return
        
        # Safety validation: cannot call yourself
        if caller_id == receiver_id:
            print("❌ Cannot call yourself")
            return
        
        print(f"📞 Starting {call_type} call to {receiver_role} ID {receiver_id}...")
        
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
                    # Open chat with the caller
                    caller_id = call.get("caller_id")
                    if caller_id:
                        if current_client_id:
                            # Current user is client, caller is freelancer
                            open_chat_with_freelancer(caller_id)
                        else:
                            # Current user is freelancer, caller is client
                            open_chat_with_client(caller_id)
                    else:
                        print("❌ Could not determine caller ID")
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
        # Safety check: ensure job data is valid
        if not job or not isinstance(job, dict):
            print("❌ Invalid job data")
            return
            
        job_id = job.get('id')
        freelancer_id = job.get('freelancer_id')
        
        if not job_id:
            print("❌ Job ID missing")
            return
            
        if not freelancer_id:
            print("❌ Freelancer ID missing")
            return
        
        print(f"\n--- Rate Freelancer for: {job.get('title', 'Untitled')} ---")
        print(f"Freelancer ID: {freelancer_id}")
        print(f"Job Budget: ₹{job.get('budget', 'N/A')}")
        
        # Get rating with validation
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
        
        print("📝 Submitting rating...")
        
        # Submit rating with proper job ID
        res = requests.post(f"{BASE_URL}/client/rate", json={
            "client_id": current_client_id,
            "freelancer_id": freelancer_id,
            "hire_request_id": job_id,
            "rating": rating,
            "review": review
        })
        
        result = res.json()
        if result.get("success"):
            print(f"✅ Rating submitted successfully!")
            new_rating = result.get('new_rating')
            total_reviews = result.get('total_reviews')
            if new_rating is not None:
                print(f"New average rating: {new_rating:.2f}")
            if total_reviews is not None:
                print(f"Total reviews: {total_reviews}")
        else:
            error_msg = result.get('msg', 'Unknown error')
            print(f"❌ Failed to submit rating: {error_msg}")
            
            # Show helpful messages for common errors
            if "job completion" in error_msg:
                print("💡 Note: You can only rate jobs that are marked as 'PAID'")
            elif "already rated" in error_msg:
                print("💡 Note: You can only rate each job once")
            elif "own jobs" in error_msg:
                print("💡 Note: You can only rate your own hired jobs")
            
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

    # Use the display_freelancer function for consistent formatting
    display_freelancer(data)
    
    # Additional details not covered by display_freelancer
    print("Email:", data.get("email", "N/A"))
    
    # Display formatted experience if available, otherwise show decimal
    if data.get("experience_formatted"):
        print("Experience:", data["experience_formatted"])
    
    # Keep min/max budget for legacy compatibility
    print("Min Budget:", data.get("min_budget", "N/A"))
    print("Max Budget:", data.get("max_budget", "N/A"))
    
    print("Bio:", data.get("bio", "N/A"))

    pricing_type = data.get("pricing_type")
    if pricing_type == "package":
        print("\n--- PACKAGES ---")
        try:
            packages_resp = requests.get(f"{BASE_URL}/freelancer/{fid}/packages")
            if packages_resp.status_code == 200:
                packages_data = packages_resp.json()
                packages = packages_data.get('packages', [])
                
                if packages:
                    for i, pkg in enumerate(packages, 1):
                        print(f"\n📦 Package {i}")
                        print(f"   Name: {pkg['package_name']}")
                        print(f"   Services: {pkg['services_included']}")
                        print(f"   Price: ₹{pkg['starting_price']}")
                else:
                    print("📦 No packages configured yet")
            else:
                print("📦 Unable to load packages")
        except Exception as e:
            print("📦 Error loading packages")
    
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

    # Display pricing preferences
    print("\n--- PRICING PREFERENCES ---")
    supports_fixed = data.get("supports_fixed", True)
    supports_hourly = data.get("supports_hourly", True)
    
    pricing_models = []
    if supports_fixed:
        pricing_models.append("Fixed")
    if supports_hourly:
        pricing_models.append("Hourly")
    
    print("Pricing Models:", " + ".join(pricing_models) if pricing_models else "Not set")
    
    if supports_fixed and data.get("fixed_price"):
        print(f"Fixed Price: ₹{data['fixed_price']}")
    
    if supports_hourly:
        if data.get("hourly_rate"):
            print(f"Hourly Rate: ₹{data['hourly_rate']}/hour")
        if data.get("overtime_rate_per_hour"):
            print(f"Overtime Rate: ₹{data['overtime_rate_per_hour']}/hour")

# ---------- PACKAGE SELECTION ----------
def select_freelancer_package(fid):
    """Handle package selection for a freelancer"""
    global selected_package
    
    try:
        # Fetch freelancer details to check if package-based
        freelancer_res = requests.get(f"{BASE_URL}/freelancers/{fid}")
        freelancer_data = freelancer_res.json()
        
        if not freelancer_data.get("success"):
            print("❌ Error fetching freelancer details:", freelancer_data.get("msg"))
            return False
        
        category = freelancer_data.get("category")
        pricing_type = None
        if get_pricing_type_for_category and category and category.strip():
            try:
                pricing_type = get_pricing_type_for_category(category)
            except Exception:
                pricing_type = None
        else:
            pricing_type = None
        
        if pricing_type != PRICING_TYPE_PACKAGE:
            print("❌ This freelancer is not package-based")
            return False
        
        # Fetch packages
        packages_resp = requests.get(f"{BASE_URL}/freelancer/{fid}/packages")
        if packages_resp.status_code != 200:
            print("❌ Failed to fetch packages")
            return False
        
        packages_data = packages_resp.json()
        packages = packages_data.get('packages', [])
        
        if not packages:
            print("❌ No packages available for this freelancer")
            return False
        
        print("\n## 📦 Available Packages")
        print("=" * 40)
        
        for i, pkg in enumerate(packages, 1):
            print(f"\n[{i}] {pkg['package_name']}")
            print(f"💰 Price: ₹{pkg['starting_price']}")
            print(f"🧾 Services: {pkg['services_included']}")
        
        print("=" * 40)
        
        # Package selection
        while True:
            try:
                choice = input(f"\nChoose package (1-{len(packages)}): ").strip()
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(packages):
                    selected_package = packages[choice_idx]
                    print(f"\n✅ You selected: {selected_package['package_name']}")
                    print(f"💰 Price: ₹{selected_package['starting_price']}")
                    print("\nReturning to freelancer menu...")
                    return True
                else:
                    print(f"❌ Invalid choice, select between 1 and {len(packages)}")
            except ValueError:
                print("❌ Please enter a valid number")
                
    except Exception as e:
        print(f"❌ Error selecting package: {str(e)}")
        return False
    
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
    
    try:
        # STEP 1: GET PRICING TYPE FROM PROFILE
        profile_resp = requests.get(f"{BASE_URL}/freelancer/profile/{fid}")
        profile_data = profile_resp.json()
        if not profile_data.get("success"):
            print("❌ Error fetching freelancer profile:", profile_data.get("msg"))
            return
        
        freelancer_profile = profile_data  # Data is directly in root
        pricing_type = freelancer_profile.get("pricing_type")
        
        if not pricing_type:
            print("❌ Freelancer pricing type not found")
            return
        
        print(f"\n--- {pricing_type.upper()} PRICING ---")
        
        # STEP 2: COLLECT COMMON FIELDS WITH VALIDATION
        while True:
            event_date = input("Event Date (YYYY-MM-DD): ").strip()
            # Validate date format
            try:
                from datetime import datetime
                datetime.strptime(event_date, "%Y-%m-%d")
                break
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2024-12-25)")
        
        # Event venue collection
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
            event_city = ""
            event_pincode = input("Event Pincode: ")
            event_landmark = ""
        else:
            print("❌ Invalid venue choice")
            return
        
        work_description = input("Work Description: ")
        additional_requirements = input("Additional Requirements (optional): ").strip()
        
        # STEP 3: APPLY PRICING-TYPE-SPECIFIC LOGIC
        total_amount = 0
        total_display = ""
        
        if pricing_type == PRICING_TYPE_HOURLY:
            # HOURLY PRICING
            start_time = input("Start Time (HH:MM): ").strip()
            end_time = input("End Time (HH:MM): ").strip()
            
            # Calculate hours
            from datetime import datetime, timedelta
            try:
                start_dt = datetime.strptime(f"{event_date} {start_time}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{event_date} {end_time}", "%Y-%m-%d %H:%M")
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)  # Handle overnight events
                
                number_of_hours = (end_dt - start_dt).total_seconds() / 3600
                hourly_rate = freelancer_profile.get("hourly_rate") or freelancer_profile.get("pricing", {}).get("hourly_rate", 0)
                
                if hourly_rate <= 0:
                    print("⚠️ This freelancer has not set hourly pricing. Please choose another freelancer.")
                    return
                
                total_amount = hourly_rate * number_of_hours
                total_display = f"Computed Total: ₹{total_amount} (₹{hourly_rate}/hour × {number_of_hours:.1f} hours)"
                
            except Exception as e:
                print(f"❌ Error calculating hours: {e}")
                return
        
        elif pricing_type == PRICING_TYPE_PER_PERSON:
            # PER_PERSON PRICING
            while True:
                try:
                    number_of_persons = int(input("Number of Persons: "))
                    if number_of_persons > 0:
                        break
                    print("❌ Number of persons must be greater than 0")
                except ValueError:
                    print("❌ Please enter a valid integer")
            
            per_person_rate = freelancer_profile.get("per_person_rate") or freelancer_profile.get("pricing", {}).get("per_person_rate", 0)
            if per_person_rate <= 0:
                print("⚠️ This freelancer has not set per person pricing. Please choose another freelancer.")
                return
            
            total_amount = per_person_rate * number_of_persons
            total_display = f"Computed Total: ₹{total_amount} (₹{per_person_rate} × {number_of_persons} persons)"
        
        elif pricing_type == PRICING_TYPE_PACKAGE:
            # PACKAGE PRICING
            global selected_package
            
            if not selected_package or not selected_package.get('package_id'):
                print("❌ Please select package first")
                print("Use 'Select Package 📦' option from the freelancer menu")
                return
            
            # Verify package belongs to this freelancer
            try:
                packages_resp = requests.get(f"{BASE_URL}/freelancer/{fid}/packages")
                if packages_resp.status_code == 200:
                    packages_data = packages_resp.json()
                    packages = packages_data.get('packages', [])
                    
                    package_found = False
                    for pkg in packages:
                        if pkg['package_id'] == selected_package['package_id']:
                            total_amount = selected_package['starting_price']
                            total_display = f"Selected Package: {selected_package['package_name']} — ₹{total_amount}"
                            package_found = True
                            break
                    
                    if not package_found:
                        print("❌ Selected package not found for this freelancer")
                        return
            except:
                print("❌ Error verifying package")
                return
        
        elif pricing_type == PRICING_TYPE_PROJECT:
            # PROJECT PRICING
            while True:
                proposed_budget = input("Proposed Budget: ")
                try:
                    total_amount = float(proposed_budget)
                    if total_amount > 0:
                        break
                    print("❌ Budget must be greater than 0")
                except ValueError:
                    print("❌ Invalid budget amount. Please enter a number")
            
            total_display = f"Proposed Budget: ₹{total_amount}"
        
        else:
            print("❌ Unknown pricing type")
            return
        
        # STEP 4: DISPLAY TOTAL AND CONFIRM
        print(f"\n--- HIRE SUMMARY ---")
        print(f"Freelancer ID: {fid}")
        print(f"Event Date: {event_date}")
        print(f"Work Description: {work_description}")
        if additional_requirements:
            print(f"Additional Requirements: {additional_requirements}")
        print(f"Venue: {event_address if venue_source == 'custom' else 'Saved Profile Address'}")
        print(f"Pricing Type: {pricing_type.upper()}")
        print(f"{total_display}")
        
        confirm = input("\nConfirm Hire Request? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Hire request cancelled")
            return
        
        # STEP 5: SEND REQUEST WITH BACKEND COMPATIBILITY
        hire_data = {
            "client_id": current_client_id,
            "freelancer_id": fid,
            "pricing_type": pricing_type,
            "total_amount": total_amount,
            "event_date": event_date,
            "work_description": work_description,
            "additional_requirements": additional_requirements,
            "venue_source": venue_source,
            "event_address": event_address,
            "event_city": event_city,
            "event_pincode": event_pincode,
            "event_landmark": event_landmark,
            "contract_type": "FIXED"  # Default for backend compatibility
        }
        
        # Add fallback for backend compatibility
        if pricing_type != PRICING_TYPE_PROJECT:
            hire_data["proposed_budget"] = total_amount  # Fallback for older backend
        
        # Add pricing-type-specific fields
        if pricing_type == PRICING_TYPE_HOURLY:
            hire_data["start_time"] = start_time
            hire_data["end_time"] = end_time
            hire_data["hourly_rate"] = freelancer_profile.get("hourly_rate") or freelancer_profile.get("pricing", {}).get("hourly_rate")
            hire_data["contract_type"] = "HOURLY"
        elif pricing_type == PRICING_TYPE_PER_PERSON:
            hire_data["number_of_persons"] = number_of_persons
            hire_data["per_person_rate"] = per_person_rate
        elif pricing_type == PRICING_TYPE_PACKAGE:
            hire_data["selected_package_id"] = selected_package['package_id']
        elif pricing_type == PRICING_TYPE_PROJECT:
            hire_data["proposed_budget"] = proposed_budget
            hire_data["guest_count"] = locals().get('guest_count')  # Will be None if not set
        
        res = requests.post(f"{BASE_URL}/client/hire", json=hire_data)
        result = res.json()
        
        if result.get("success"):
            print("\n✅ Hire request sent successfully!")
            print(f"Request ID: {result.get('request_id')}")
            print(f"Status: Pending approval")
        else:
            print(f"\n❌ Failed to send hire request: {result.get('msg', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in hire process: {str(e)}")
        return
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
    for item in mapping:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            num, fid, _name = item[0], item[1], item[2]
            if num == sel:
                open_chat_with_freelancer(fid)
                return
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            num, fid = item[0], item[1]
            if num == sel:
                open_chat_with_freelancer(fid)
                return

    print("❌ Invalid selection")

# ---------- CLIENT: JOB REQUEST STATUS ----------
def client_job_request_status_menu():
    """Show job request status with actionable options for COUNTERED requests."""
    if not current_client_id:
        print("❌ Please login as client first")
        return

    try:
        res = requests.get(f"{BASE_URL}/client/job-requests", params={
            "client_id": current_client_id
        })
        data = res.json()
        
        # Normalize response to handle both list and dict formats
        if isinstance(data, list):
            items = data
        else:
            items = data.get("data") or data.get("requests") or data.get("results") or []
    except Exception:
        items = []

    print("\n--- JOB REQUEST STATUS ---")
    if not items:
        print("📭 No job requests found")
        return

    # Group requests by status for better display
    countered_requests = []
    other_requests = []
    
    for idx, r in enumerate(items, 1):
        if isinstance(r, dict):
            title = (r.get("job_title") or "Untitled").strip()
            budget = r.get("proposed_budget")
            status = r.get("status")
            fname = r.get("freelancer_name") or "Freelancer"
            fid = r.get("freelancer_id")
            rid = r.get("request_id")
            
            # Add counteroffer details if available
            counter_amount = r.get("final_agreed_amount")
            counter_note = r.get("counter_note")
            negotiation_status = r.get("negotiation_status")
            
            request_data = {
                "idx": idx,
                "request_id": rid,
                "freelancer_name": fname,
                "freelancer_id": fid,
                "job_title": title,
                "proposed_budget": budget,
                "status": status,
                "counter_amount": counter_amount,
                "counter_note": counter_note,
                "negotiation_status": negotiation_status
            }
            
            if status == "COUNTERED":
                countered_requests.append(request_data)
            else:
                other_requests.append(request_data)
        else:
            # Handle non-dict items (legacy format)
            other_requests.append({
                "idx": idx,
                "request_id": str(r),
                "freelancer_name": "N/A",
                "freelancer_id": "N/A",
                "job_title": str(r),
                "proposed_budget": "N/A",
                "status": "N/A",
                "counter_amount": None,
                "counter_note": None,
                "negotiation_status": None
            })

    # Show COUNTERED requests first with conditional action options
    actionable_countered = []
    waiting_countered = []
    
    for r in countered_requests:
        # Check who made the latest offer
        if r['negotiation_status'] == "FREELANCER":
            # Client needs to respond
            actionable_countered.append(r)
        else:
            # Client made the last offer, waiting for freelancer
            waiting_countered.append(r)
    
    # Show actionable countered requests
    if actionable_countered:
        print("\n🔄 COUNTEROFFER REQUESTS (Action Required):")
        print("=" * 60)
        for r in actionable_countered:
            print(f"\n{r['idx']}. Request ID: {r['request_id']}")
            print(f"   Freelancer: {r['freelancer_name']} (ID: {r['freelancer_id']})")
            print(f"   Job Title: {r['job_title']}")
            print(f"   Original Budget: ₹{r['proposed_budget']}")
            print(f"   Status: {r['status']} 🔄")
            
            # Show counteroffer details
            if r['counter_amount']:
                print(f"   💰 Counteroffer Amount: ₹{r['counter_amount']}")
            if r['counter_note']:
                print(f"   📝 Counteroffer Note: {r['counter_note']}")
            if r['negotiation_status']:
                print(f"   🤝 Offered By: {r['negotiation_status']}")
            
            print(f"\n   📋 Available Actions:")
            print(f"      • Accept Counteroffer")
            print(f"      • Reject Counteroffer") 
            print(f"      • Counteroffer Again")
            print(f"      • Message Freelancer")
    
    # Show waiting countered requests
    if waiting_countered:
        print("\n⏳ COUNTEROFFER REQUESTS (Waiting for Freelancer):")
        print("=" * 65)
        for r in waiting_countered:
            print(f"\n{r['idx']}. Request ID: {r['request_id']}")
            print(f"   Freelancer: {r['freelancer_name']} (ID: {r['freelancer_id']})")
            print(f"   Job Title: {r['job_title']}")
            print(f"   Original Budget: ₹{r['proposed_budget']}")
            print(f"   Status: {r['status']} ⏳")
            
            # Show counteroffer details
            if r['counter_amount']:
                print(f"   💰 Your Latest Offer: ₹{r['counter_amount']}")
            if r['counter_note']:
                print(f"   📝 Your Note: {r['counter_note']}")
            if r['negotiation_status']:
                print(f"   🤝 Offered By: {r['negotiation_status']} (You)")
            
            print(f"\n   📝 Waiting for freelancer response...")
            print(f"   📋 Available Actions:")
            print(f"      • Message Freelancer")

    # Show other requests (display only)
    if other_requests:
        print(f"\n📋 OTHER REQUESTS:")
        print("=" * 40)
        for r in other_requests:
            print(f"\n{r['idx']}. Request ID: {r['request_id']}")
            print(f"   Freelancer: {r['freelancer_name']} (ID: {r['freelancer_id']})")
            print(f"   Job Title: {r['job_title']}")
            
            # Show final agreed amount if request was accepted and has final amount
            if r['status'] == "ACCEPTED" and r.get('final_agreed_amount') is not None:
                print(f"   Final Agreed Amount: ₹{r['final_agreed_amount']}")
            else:
                print(f"   Budget: ₹{r['proposed_budget']}")
            
            print(f"   Status: {r['status']}")

    # Action selection loop for actionable countered requests only
    while actionable_countered:
        print(f"\n🎯 Select a COUNTERED request to act on (or 0 to exit):")
        for r in actionable_countered:
            print(f"   {r['idx']}: {r['freelancer_name']} - {r['job_title']}")
        
        try:
            choice = input("Enter choice: ").strip()
            if choice == "0":
                break
                
            choice_idx = int(choice)
            selected_request = next((r for r in actionable_countered if r['idx'] == choice_idx), None)
            
            if not selected_request:
                print("❌ Invalid choice")
                continue
            
            # Show action menu for selected request
            handle_countered_request_actions(selected_request)
            break
            
        except ValueError:
            print("❌ Please enter a valid number")
    
    print("\n✅ Job request status review completed")

def handle_countered_request_actions(request):
    """Handle client actions on a countered request"""
    print(f"\n🔄 COUNTEROFFER ACTIONS")
    print("=" * 40)
    print(f"Request ID: {request['request_id']}")
    print(f"Freelancer: {request['freelancer_name']}")
    print(f"Job: {request['job_title']}")
    print(f"Original Budget: ₹{request['proposed_budget']}")
    
    if request['counter_amount']:
        print(f"Counteroffer Amount: ₹{request['counter_amount']}")
    if request['counter_note']:
        print(f"Counteroffer Note: {request['counter_note']}")
    
    print(f"\n🎯 Choose Action:")
    print("1. Accept Counteroffer")
    print("2. Reject Counteroffer") 
    print("3. Counteroffer Again")
    print("4. Message Freelancer")
    print("0. Back to Request List")
    
    while True:
        choice = input("Enter choice: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            # Accept counteroffer
            accept_counteroffer(request)
            break
        elif choice == "2":
            # Reject counteroffer
            reject_counteroffer(request)
            break
        elif choice == "3":
            # Counteroffer again
            counteroffer_again(request)
            break
        elif choice == "4":
            # Message freelancer
            open_chat_with_freelancer(request['freelancer_id'])
            break
        else:
            print("❌ Invalid choice, please try again")

def accept_counteroffer(request):
    """Accept the freelancer's counteroffer"""
    print(f"\n✅ Accepting counteroffer...")
    
    try:
        res = requests.post(f"{BASE_URL}/client/hire/counter", json={
            "client_id": current_client_id,
            "request_id": request['request_id'],
            "action": "ACCEPT"
        })
        
        result = res.json()
        if result.get("success"):
            print(f"✅ Counteroffer accepted successfully!")
            print(f"   Final agreed amount: ₹{request['counter_amount']}")
            print(f"   Request status: ACCEPTED")
            print(f"   🎉 You can now proceed with the hire!")
        else:
            print(f"❌ Failed to accept counteroffer: {result.get('msg')}")
            
    except Exception as e:
        print(f"❌ Error accepting counteroffer: {str(e)}")

def reject_counteroffer(request):
    """Reject the freelancer's counteroffer"""
    print(f"\n❌ Rejecting counteroffer...")
    
    try:
        res = requests.post(f"{BASE_URL}/client/hire/counter", json={
            "client_id": current_client_id,
            "request_id": request['request_id'],
            "action": "REJECT"
        })
        
        result = res.json()
        if result.get("success"):
            print(f"✅ Counteroffer rejected successfully!")
            print(f"   Request status: REJECTED")
            print(f"   💡 You can search for other freelancers")
        else:
            print(f"❌ Failed to reject counteroffer: {result.get('msg')}")
            
    except Exception as e:
        print(f"❌ Error rejecting counteroffer: {str(e)}")

def counteroffer_again(request):
    """Send a new counteroffer to the freelancer"""
    print(f"\n💰 Send New Counteroffer")
    print("=" * 30)
    
    try:
        # Get new counter amount
        while True:
            amount_input = input(f"New counter amount (current: ₹{request['counter_amount']}): ").strip()
            try:
                new_amount = float(amount_input)
                if new_amount <= 0:
                    print("❌ Amount must be greater than 0")
                    continue
                break
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Get counter note
        note = input("Counteroffer note (optional): ").strip()
        
        # Send counteroffer
        res = requests.post(f"{BASE_URL}/client/hire/counter", json={
            "client_id": current_client_id,
            "request_id": request['request_id'],
            "action": "COUNTER",
            "counter_offer_amount": new_amount,
            "counter_offer_note": note
        })
        
        result = res.json()
        if result.get("success"):
            print(f"✅ New counteroffer sent successfully!")
            print(f"   Your offer: ₹{new_amount}")
            if note:
                print(f"   Note: {note}")
            print(f"   📝 Waiting for freelancer response...")
        else:
            print(f"❌ Failed to send counteroffer: {result.get('msg')}")
            
    except Exception as e:
        print(f"❌ Error sending counteroffer: {str(e)}")

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
    
    # DEBUG: Print AI response structure
    print("DEBUG AI response:", recommendations)
    
    if not recommendations:
        print("📭 No recommendations found")
        return
    
    # NORMALIZATION LOGIC: Convert all items to dict format
    normalized_freelancers = []
    for f in recommendations:
        if isinstance(f, dict):
            # Use as-is but ensure required fields with defaults
            normalized_freelancers.append({
                "name": f.get("name", "Unknown"),
                "match_score": f.get("match_score", 0),
                "rating": f.get("rating", 0),
                "experience": f.get("experience", 0),
                "budget_range": f.get("budget_range", "Not specified"),
                "category": f.get("category", "Not specified"),
                "freelancer_id": f.get("freelancer_id")
            })
        else:
            # Convert string to dict format
            normalized_freelancers.append({
                "name": str(f),
                "match_score": 0,
                "rating": 0,
                "experience": 0,
                "budget_range": "Not specified",
                "category": "Not specified",
                "freelancer_id": None
            })
    
    print("\n--- AI RECOMMENDED FREELANCERS ---")
    for i, freelancer in enumerate(normalized_freelancers, 1):
        freelancer_id = freelancer.get("freelancer_id")
        match_score = freelancer.get("match_score", 0)
        
        print(f"\n{i}. Match Score: {match_score}%")
        display_freelancer(freelancer)
        
        print("1. View Details")
        print("2. Message")
        print("3. Hire")
        print("4. Save Freelancer")
        print("5. Next")
        
        action = input("Choose: ")
        if action == "1" and freelancer_id:
            view_freelancer_details(freelancer_id)
        elif action == "2" and freelancer_id:
            open_chat_with_freelancer(freelancer_id)
        elif action == "3" and freelancer_id:
            hire_freelancer(freelancer_id)
        elif action == "4" and freelancer_id:
            res = requests.post(f"{BASE_URL}/client/save-freelancer", json={
                "client_id": current_client_id,
                "freelancer_id": freelancer_id
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
    global current_client_id, selected_package

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
                display_freelancer(f)
                
                # Additional information not covered by display_freelancer
                if f.get("bio"):
                    print("Bio:", f["bio"][:100] + "..." if len(f["bio"]) > 100 else f["bio"])
                if f.get("distance") and f["distance"] != 999999.0:
                    print("Distance:", f"{f['distance']:.1f} km")

                freelancer_pricing_type = None
                category = f.get("category")
                if get_pricing_type_for_category is not None and category and category.strip():
                    try:
                        freelancer_pricing_type = get_pricing_type_for_category(category)
                    except Exception:
                        freelancer_pricing_type = None
                else:
                    freelancer_pricing_type = None
                
                # Show selected package if applicable
                if selected_package and selected_package.get('package_id'):
                    # Check if this package belongs to current freelancer
                    try:
                        packages_resp = requests.get(f"{BASE_URL}/freelancer/{f['freelancer_id']}/packages")
                        if packages_resp.status_code == 200:
                            packages_data = packages_resp.json()
                            packages = packages_data.get('packages', [])
                            
                            # Find if selected package belongs to this freelancer
                            for pkg in packages:
                                if pkg['package_id'] == selected_package['package_id']:
                                    print(f"\n📦 Selected Package: {selected_package['package_name']} (₹{selected_package['starting_price']})")
                                    break
                    except:
                        pass  # Don't break the flow if package check fails
                
                # For package-based categories, show package selection if no package selected yet
                elif freelancer_pricing_type == PRICING_TYPE_PACKAGE:
                    print(f"\n🔍 Package-based service detected!")
                    print("Please select a package before proceeding:")
                    
                    # Fetch packages for this freelancer
                    try:
                        packages_resp = requests.get(f"{BASE_URL}/freelancer/{f['freelancer_id']}/packages")
                        if packages_resp.status_code == 200:
                            packages_data = packages_resp.json()
                            packages = packages_data.get('packages', [])
                            
                            if not packages:
                                print("❌ No packages available for this freelancer")
                                print("Skipping to next freelancer...")
                                current_index += 1
                                continue
                            
                            print("\n## 📦 Available Packages")
                            print("=" * 40)
                            
                            for i, pkg in enumerate(packages, 1):
                                print(f"\n[{i}] {pkg['package_name']}")
                                print(f"💰 Price: ₹{pkg['starting_price']}")
                                print(f"🧾 Services: {pkg['services_included']}")
                            
                            print("=" * 40)
                            
                            # Package selection
                            while True:
                                try:
                                    choice = input(f"\nChoose package (1-{len(packages)}): ").strip()
                                    choice_idx = int(choice) - 1
                                    if 0 <= choice_idx < len(packages):
                                        selected_package = packages[choice_idx]
                                        print(f"\n✅ Package selected: {selected_package['package_name']}")
                                        print(f"💰 Price: ₹{selected_package['starting_price']}")
                                        break
                                    else:
                                        print(f"❌ Invalid choice, select between 1 and {len(packages)}")
                                except ValueError:
                                    print("❌ Please enter a valid number")
                                    
                            # After selection, show the selected package info
                            print(f"\n📦 Selected Package: {selected_package['package_name']} (₹{selected_package['starting_price']})")
                            
                        else:
                            print("❌ Failed to fetch packages")
                    except Exception as e:
                        print(f"❌ Error fetching packages: {str(e)}")
                
                # Determine pricing type for this specific freelancer (for menu display)
                freelancer_pricing_type = None
                category = f.get("category")
                if get_pricing_type_for_category is not None and category and category.strip():
                    try:
                        freelancer_pricing_type = get_pricing_type_for_category(category)
                    except Exception:
                        freelancer_pricing_type = None
                else:
                    freelancer_pricing_type = None
                
                print(f"Showing {current_index + 1} of {len(freelancers)}")

                print("\n--- Actions ---")
                print("1. View Details")
                print("2. Message")
                print("3. Hire")
                print("4. Save Freelancer")
                # Show package options ONLY for package-based freelancers
                if freelancer_pricing_type == PRICING_TYPE_PACKAGE:
                    if selected_package:
                        print("5. Switch Package 🔄")
                    else:
                        print("5. Select Package 📦")
                print("6. Next")
                print("7. Previous")
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
                    select_freelancer_package(f["freelancer_id"])
                elif action == "6":
                    current_index += 1
                    if current_index >= len(freelancers):
                        current_index = 0  # Wrap around to beginning
                elif action == "7":
                    current_index -= 1
                    if current_index < 0:
                        current_index = len(freelancers) - 1  # Wrap around to end
                elif action == "0":
                    break

        elif choice == "3":
            pricing_type = None
            category = input("Category (e.g., Dancer, Singer, Photographer): ").strip()
            specialization = input("Specialization : ").strip()
            
            # Validate category and derive pricing type
            if not category:
                print("❌ Category is required")
                continue
            
            try:
                pricing_type = get_pricing_type_for_category(category)
                print(f"\n✅ Category: {category}")
                print(f"💰 Pricing type: {pricing_type}")
            except Exception:
                print(f"❌ Invalid category: {category}")
                print("Valid categories: DJ, Singer, Anchor, Band / Live Music, Dancer, Magician / Entertainer,")
                print("                Makeup Artist, Mehendi Artist, Photographer, Videographer, Choreographer,")
                print("                Artist, Decorator, Wedding Planner, Event Organizer")
                continue
            
            # safety check
            if not pricing_type:
                print("❌ Pricing type not found")
                continue
            
            # Ask for budget based on pricing type
            if pricing_type != PRICING_TYPE_PACKAGE:
                budget_prompt = ""
                if pricing_type == PRICING_TYPE_HOURLY:
                    budget_prompt = "Enter maximum hourly rate: "
                elif pricing_type == PRICING_TYPE_PER_PERSON:
                    budget_prompt = "Enter maximum per person rate: "
                elif pricing_type == PRICING_TYPE_PROJECT:
                    budget_prompt = "Enter maximum starting price: "
                else:
                    budget_prompt = "Enter maximum budget: "
                
                budget_in = input(budget_prompt).strip()
                try:
                    budget = float(budget_in)
                    if budget <= 0:
                        print("❌ Budget must be greater than 0")
                        continue
                except Exception:
                    print("❌ Invalid budget")
                    continue
            else:
                # For package type, set budget to 0 (not used)
                budget = 0
            
            params = {
                "category": category,
                "pricing_type": pricing_type.upper(),
                "budget": budget
            }
            
            if current_client_id:
                params["client_id"] = current_client_id
            if specialization and specialization.strip() and specialization.lower() not in ["no", "none", ""]:
                params["q"] = specialization
            
            # Execute search
            try:
                res = requests.get(f"{BASE_URL}/freelancers/search", params=params)
                data = res.json()
                if not data.get("success"):
                    print("❌ Error searching freelancers:", data.get("msg", "Unknown error"))
                    continue
                
                freelancers = data.get("results", [])
                if not freelancers:
                    print("❌ No freelancers found matching your criteria")
                    continue

                current_index = 0
                while current_index < len(freelancers):
                    f = freelancers[current_index]
                    display_freelancer(f)
                    
                    # Additional information not covered by display_freelancer
                    if f.get("bio"):
                        print("Bio:", f["bio"][:100] + "..." if len(f["bio"]) > 100 else f["bio"])
                    
                    # Show selected package if applicable
                    if selected_package and selected_package.get('package_id'):
                        # Check if this package belongs to current freelancer
                        try:
                            packages_resp = requests.get(f"{BASE_URL}/freelancer/{f['freelancer_id']}/packages")
                            if packages_resp.status_code == 200:
                                packages_data = packages_resp.json()
                                packages = packages_data.get('packages', [])
                                
                                # Find if selected package belongs to this freelancer
                                for pkg in packages:
                                    if pkg['package_id'] == selected_package['package_id']:
                                        print(f"\n📦 Selected Package: {selected_package['package_name']} (₹{selected_package['starting_price']})")
                                        break
                        except:
                            pass  # Don't break the flow if package check fails
                    
                    # For package-based categories, show package selection if no package selected yet
                    elif pricing_type == PRICING_TYPE_PACKAGE:
                        print(f"\n🔍 Package-based service detected!")
                        print("Please select a package before proceeding:")
                        
                        # Fetch packages for this freelancer
                        try:
                            packages_resp = requests.get(f"{BASE_URL}/freelancer/{f['freelancer_id']}/packages")
                            if packages_resp.status_code == 200:
                                packages_data = packages_resp.json()
                                packages = packages_data.get('packages', [])
                                
                                if not packages:
                                    print("❌ No packages available for this freelancer")
                                    print("Skipping to next freelancer...")
                                    current_index += 1
                                    continue
                                
                                print("\n## 📦 Available Packages")
                                print("=" * 40)
                                
                                for i, pkg in enumerate(packages, 1):
                                    print(f"\n[{i}] {pkg['package_name']}")
                                    print(f"💰 Price: ₹{pkg['starting_price']}")
                                    print(f"🧾 Services: {pkg['services_included']}")
                                
                                print("=" * 40)
                                
                                # Package selection
                                while True:
                                    try:
                                        choice = input(f"\nChoose package (1-{len(packages)}): ").strip()
                                        choice_idx = int(choice) - 1
                                        if 0 <= choice_idx < len(packages):
                                            selected_package = packages[choice_idx]
                                            print(f"\n✅ Package selected: {selected_package['package_name']}")
                                            print(f"💰 Price: ₹{selected_package['starting_price']}")
                                            break
                                        else:
                                            print(f"❌ Invalid choice, select between 1 and {len(packages)}")
                                    except ValueError:
                                        print("❌ Please enter a valid number")
                                        
                                # After selection, show the selected package info
                                print(f"\n📦 Selected Package: {selected_package['package_name']} (₹{selected_package['starting_price']})")
                                
                            else:
                                print("❌ Failed to fetch packages")
                        except Exception as e:
                            print(f"❌ Error fetching packages: {str(e)}")
                    
                    # Determine pricing type for this specific freelancer (for menu display)
                    freelancer_pricing_type = None
                    category = f.get("category")
                    if get_pricing_type_for_category is not None and category and category.strip():
                        try:
                            freelancer_pricing_type = get_pricing_type_for_category(category)
                        except Exception:
                            freelancer_pricing_type = None
                    else:
                        freelancer_pricing_type = None
                    
                    print(f"Showing {current_index + 1} of {len(freelancers)}")

                    print("\n--- Actions ---")
                    print("1. View Details")
                    print("2. Message")
                    print("3. Hire")
                    print("4. Save Freelancer")
                    # Show package options ONLY for package-based freelancers
                    if freelancer_pricing_type == PRICING_TYPE_PACKAGE:
                        if selected_package:
                            print("5. Switch Package 🔄")
                        else:
                            print("5. Select Package 📦")
                    print("6. Next")
                    print("7. Previous")
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
                        select_freelancer_package(f["freelancer_id"])
                    elif action == "6":
                        current_index += 1
                        if current_index >= len(freelancers):
                            current_index = 0  # Wrap around to beginning
                    elif action == "7":
                        current_index -= 1
                        if current_index < 0:
                            current_index = len(freelancers) - 1  # Wrap around to end
                    elif action == "0":
                        break
                        
            except Exception as e:
                print("❌ Error during search:", str(e))
                continue

        elif choice == "4":
            res = requests.get(f"{BASE_URL}/client/jobs", params={
                "client_id": current_client_id
            })
            print("\n--- My Jobs ---")
            try:
                jobs_data = res.json()
                
                # Normalize response to handle both list and dict formats
                if isinstance(jobs_data, list):
                    jobs = jobs_data
                else:
                    jobs = jobs_data.get("data") or jobs_data.get("jobs") or jobs_data.get("results") or []
                    
                if not jobs:
                    print("❌ No jobs found")
                else:
                    for i, j in enumerate(jobs, 1):
                        if isinstance(j, dict):
                            title = j.get('title', 'Untitled')
                            category = j.get('category', 'N/A')
                            budget = j.get('budget', 'N/A')
                            description = j.get('description', 'N/A')
                            status = j.get('status', 'N/A')
                            
                            print(f"\n{i}. {title}")
                            print(f"Category   : {category}")
                            print(f"Budget     : {budget}")
                            print(f"Description: {description}")
                            print(f"Status     : {status}")
                            print("----------------------------------")
                            
                            # Show rating option for PAID jobs
                            if j.get('status') == 'PAID':
                                print("   [R] Rate this freelancer")
                        else:
                            print(f"{i}. {str(j)}")
                    
                    # Allow user to select a job for rating
                    action = input("\nEnter job number to rate, or 0 to go back: ")
                    if action.lower() == 'r' or (action.isdigit() and int(action) > 0):
                        try:
                            job_idx = int(action) - 1 if action.isdigit() else None
                            if job_idx is not None and 0 <= job_idx < len(jobs):
                                selected_job = jobs[job_idx]
                                if isinstance(selected_job, dict) and selected_job.get('status') == 'PAID':
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
                jobs_data = res.json()
                
                # Normalize response to handle both list and dict formats
                if isinstance(jobs_data, list):
                    jobs = jobs_data
                else:
                    jobs = jobs_data.get("data") or jobs_data.get("jobs") or jobs_data.get("results") or []
                
                paid_jobs = []
                for job in jobs:
                    if isinstance(job, dict) and job.get('status') == 'PAID':
                        paid_jobs.append(job)
                
                if not paid_jobs:
                    print("❌ No paid jobs available for rating")
                else:
                    print("Jobs available for rating:")
                    for i, job in enumerate(paid_jobs, 1):
                        if isinstance(job, dict):
                            title = job.get('title', 'Untitled')
                            budget = job.get('budget', 'N/A')
                            status = job.get('status', 'N/A')
                            print(f"{i}. {title} | ₹{budget} | {status}")
                        else:
                            print(f"{i}. {str(job)}")
                    
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
            print("\n--- POST PROJECT ---")
            category = input("Category: ").strip()
            description = input("Description: ").strip()
            location = input("Location: ").strip()
            pincode = input("Pincode: ").strip()
            
            if not category or not description or not location or not pincode:
                print("❌ All fields are required")
                continue
            
            try:
                res = requests.post(f"{BASE_URL}/client/projects/create", json={
                    "client_id": current_client_id,
                    "category": category,
                    "description": description,
                    "location": location,
                    "pincode": pincode
                })
                result = res.json()
                if result.get("success"):
                    print(f"✅ Project posted successfully! Project ID: {result.get('project_id')}")
                else:
                    print("❌ Failed to post project:", result.get("msg"))
            except Exception as e:
                print("❌ Error posting project:", str(e))

        elif choice == "13":
            # My Projects
            try:
                res = requests.get(f"{BASE_URL}/client/projects", params={
                    "client_id": current_client_id
                })
                data = res.json()
                if data.get("success"):
                    print("\n--- MY PROJECTS ---")
                    projects = data.get("projects", [])
                    if not projects:
                        print("No projects found")
                    else:
                        for p in projects:
                            print(f"{p['project_id']}. Category: {p['category']}")
                            print(f"   Location: {p['location']} | Pincode: {p['pincode']}")
                            print(f"   Description: {p['description']}")
                            print(f"   Status: {p['status']}")
                            print()
                else:
                    print("❌ Error:", data.get("msg"))
            except Exception as e:
                print("❌ Error fetching projects:", str(e))

        elif choice == "14":
            # View Applicants
            project_id = input("Project ID: ").strip()
            if not project_id:
                print("❌ Project ID is required")
                continue
            
            try:
                res = requests.get(f"{BASE_URL}/client/projects/applicants", params={
                    "client_id": current_client_id,
                    "project_id": project_id
                })
                data = res.json()
                if data.get("success"):
                    print("\n--- APPLICANTS ---")
                    applicants = data.get("applicants", [])
                    if not applicants:
                        print("No applicants found")
                    else:
                        for a in applicants:
                            print(f"Application ID: {a['application_id']}")
                            print(f"Freelancer: {a['freelancer_name']} ({a['freelancer_id']})")
                            print(f"Title: {a['freelancer_title']}")
                            print(f"Skills: {a['freelancer_skills']}")
                            print(f"Experience: {a['freelancer_experience']} years")
                            print(f"Email: {a['freelancer_email']}")
                            print(f"Proposal: {a['proposal']}")
                            print(f"Bid Amount: ₹{a['bid_amount']}")
                            print(f"Status: {a['status']}")
                            print("-" * 40)
                else:
                    print("❌ Error:", data.get("msg"))
            except Exception as e:
                print("❌ Error fetching applicants:", str(e))

        elif choice == "15":
            # Accept Applicant
            project_id = input("Project ID: ").strip()
            application_id = input("Application ID: ").strip()
            
            if not project_id or not application_id:
                print("❌ Project ID and Application ID are required")
                continue
            
            try:
                res = requests.post(f"{BASE_URL}/client/projects/accept_application", json={
                    "client_id": current_client_id,
                    "project_id": int(project_id),
                    "application_id": int(application_id)
                })
                result = res.json()
                if result.get("success"):
                    print("✅ Applicant accepted successfully!")
                    print("A hire request has been created and other applicants have been rejected.")
                else:
                    print("❌ Failed to accept applicant:", result.get("msg"))
            except Exception as e:
                print("❌ Error accepting applicant:", str(e))

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
                from notification_utils import get_notification_icon
                
                notifications = res.json()
                if not notifications:
                    print("📭 No notifications available")
                else:
                    for idx, notif in enumerate(notifications, 1):
                        # Safe dictionary access with fallbacks
                        if isinstance(notif, dict):
                            message = notif.get("message", notif.get("title", "No message"))
                            title = notif.get("title", "")
                            related_type = notif.get("related_entity_type", "")
                            
                            # Fix old placeholders if present
                            if "job_title" in message and "status" in message:
                                job_title = notif.get("job_title", "Unknown")
                                status = notif.get("status", "Updated")
                                message = message.replace("job_title", job_title).replace("status", status)
                        else:
                            # Handle legacy format (string only)
                            message = str(notif) if notif else "No message"
                            title = ""
                            related_type = ""
                            
                            # Fix old placeholders in legacy format
                            if "job_title" in message and "status" in message:
                                message = message.replace("job_title", "Unknown").replace("status", "Updated")
                        
                        # Get appropriate icon
                        icon = get_notification_icon(message, title, related_type)
                        
                        # Remove duplicate icons and display with single icon
                        clean_message = message.strip()
                        if clean_message.startswith("✅ ✅"):
                            clean_message = clean_message.replace("✅ ✅", "✅")
                        elif clean_message.startswith("❌ ❌"):
                            clean_message = clean_message.replace("❌ ❌", "❌")
                        
                        print(f"{idx}. {icon} {clean_message}")
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
    
    # Validate file extensions (using same logic as server)
    def validate_file_ext(file_path):
        if not file_path:
            return True
        # Clean path and extract filename first
        import os
        cleaned_path = file_path.strip().strip('"').strip("'").strip()
        filename = os.path.basename(cleaned_path)
        ext = filename.split(".")[-1].lower()
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
    
    government_id = clean_path(input("Government ID file path: "))
    print("DEBUG CLEAN PATH:", government_id)
    if not government_id:
        print("❌ Government ID file path required")
        return
    
    pan_card = clean_path(input("PAN card file path: "))
    print("DEBUG CLEAN PATH:", pan_card)
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

# ---------- PACKAGE MANAGEMENT FUNCTIONS ----------
def manage_packages_menu():
    """Package management menu for package-based freelancers"""
    if not current_freelancer_id:
        print("❌ Please login first")
        return
    
    # Check if freelancer is package-based
    try:
        profile_resp = requests.get(f"{BASE_URL}/freelancer/profile/{current_freelancer_id}")
        if profile_resp.status_code != 200:
            print("❌ Failed to fetch profile")
            return
        
        profile_data = profile_resp.json()
        pricing_type = profile_data.get('pricing_type')
        
        if pricing_type != 'package':
            print("❌ Package management is only available for package-based freelancers")
            print(f"Your current pricing type: {pricing_type}")
            return
            
    except Exception as e:
        print(f"❌ Error checking profile: {str(e)}")
        return
    
    while True:
        print("\n--- MANAGE PACKAGES 📦 ---")
        print("1. Add Package")
        print("2. View My Packages")
        print("3. Update Package")
        print("4. Delete Package")
        print("5. Back")
        
        choice = input("Choose: ")
        
        if choice == "5":
            print("🔙 Returning to dashboard...")
            break
        
        # 1️⃣ Add Package
        elif choice == "1":
            add_package_flow()
        
        # 2️⃣ View My Packages
        elif choice == "2":
            view_packages_flow()
        
        # 3️⃣ Update Package
        elif choice == "3":
            update_package_flow()
        
        # 4️⃣ Delete Package
        elif choice == "4":
            delete_package_flow()
        
        else:
            print("❌ Invalid choice")

def add_package_flow():
    """Add a new package"""
    print("\n--- ADD PACKAGE ---")
    
    while True:
        try:
            package_name = input("Enter package name: ").strip()
            if not package_name:
                print("❌ Package name is required")
                continue
            
            services_included = input("Enter services included: ").strip()
            if not services_included:
                print("❌ Services included is required")
                continue
            
            package_price_input = input("Enter package price: ₹").strip()
            try:
                package_price = float(package_price_input)
                if package_price <= 0:
                    print("❌ Package price must be greater than 0")
                    continue
            except ValueError:
                print("❌ Please enter a valid number")
                continue
            
            # Create package
            package_data = {
                "freelancer_id": current_freelancer_id,
                "package_name": package_name,
                "price": package_price,
                "services_included": services_included
            }
            
            try:
                response = requests.post(f"{BASE_URL}/freelancer/packages", json=package_data)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Package '{package_name}' added successfully! (ID: {result.get('package_id')})")
                    
                    # Ask if user wants to add another package
                    another = input("Do you want to add another package? (y/n): ").lower()
                    if another != 'y':
                        break
                else:
                    print(f"❌ Failed to add package: {response.text}")
                    break
            except Exception as e:
                print(f"❌ Error adding package: {str(e)}")
                break
            
        except KeyboardInterrupt:
            print("\n❌ Package creation cancelled")
            return

def view_packages_flow():
    """View all packages for the freelancer"""
    print("\n--- MY PACKAGES ---")
    
    try:
        response = requests.get(f"{BASE_URL}/freelancer/{current_freelancer_id}/packages")
        if response.status_code == 200:
            data = response.json()
            packages = data.get('packages', [])
            
            if not packages:
                print("📦 No packages found. Add your first package!")
                return
            
            print(f"\nFound {len(packages)} package(s):")
            print("=" * 80)
            
            for i, pkg in enumerate(packages, 1):
                print(f"\n📦 Package {i}")
                print(f"   ID: {pkg['package_id']}")
                print(f"   Name: {pkg['package_name']}")
                print(f"   Services: {pkg['services_included']}")
                print(f"   Price: ₹{pkg['starting_price']}")
                print("-" * 40)
            
        else:
            print(f"❌ Failed to fetch packages: {response.text}")
            
    except Exception as e:
        print(f"❌ Error viewing packages: {str(e)}")

def update_package_flow():
    """Update an existing package"""
    print("\n--- UPDATE PACKAGE ---")
    
    # First show packages so user can choose
    try:
        response = requests.get(f"{BASE_URL}/freelancer/{current_freelancer_id}/packages")
        if response.status_code != 200:
            print("❌ Failed to fetch packages")
            return
        
        data = response.json()
        packages = data.get('packages', [])
        
        if not packages:
            print("📦 No packages found. Add a package first!")
            return
        
        print("\nSelect package to update:")
        for i, pkg in enumerate(packages, 1):
            print(f"{i}. {pkg['package_name']} (ID: {pkg['package_id']}) - ₹{pkg['starting_price']}")
        
        choice = input("Enter package number: ").strip()
        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(packages):
                print("❌ Invalid package number")
                return
            
            selected_package = packages[choice_idx]
            package_id = selected_package['package_id']
            
            print(f"\n--- UPDATE PACKAGE: {selected_package['package_name']} ---")
            print("Leave blank to keep current value")
            
            # Get new values
            new_name = input(f"Package name [{selected_package['package_name']}]: ").strip()
            new_services = input(f"Services included [{selected_package['services_included']}]: ").strip()
            new_price_input = input(f"Package price [₹{selected_package['starting_price']}]: ").strip()
            
            # Build update data
            update_data = {}
            if new_name:
                update_data['package_name'] = new_name
            if new_services:
                update_data['services_included'] = new_services
            if new_price_input:
                try:
                    new_price = float(new_price_input)
                    if new_price <= 0:
                        print("❌ Package price must be greater than 0")
                        return
                    update_data['price'] = new_price
                except ValueError:
                    print("❌ Please enter a valid number")
                    return
            
            if not update_data:
                print("ℹ️ No changes made")
                return
            
            # Update package
            try:
                response = requests.put(f"{BASE_URL}/freelancer/packages/{package_id}", json=update_data)
                if response.status_code == 200:
                    print("✅ Package updated successfully!")
                else:
                    print(f"❌ Failed to update package: {response.text}")
            except Exception as e:
                print(f"❌ Error updating package: {str(e)}")
                
        except ValueError:
            print("❌ Invalid selection")
            
    except Exception as e:
        print(f"❌ Error in update flow: {str(e)}")

def delete_package_flow():
    """Delete an existing package"""
    print("\n--- DELETE PACKAGE ---")
    
    # First show packages so user can choose
    try:
        response = requests.get(f"{BASE_URL}/freelancer/{current_freelancer_id}/packages")
        if response.status_code != 200:
            print("❌ Failed to fetch packages")
            return
        
        data = response.json()
        packages = data.get('packages', [])
        
        if not packages:
            print("📦 No packages found.")
            return
        
        print("\nSelect package to delete:")
        for i, pkg in enumerate(packages, 1):
            print(f"{i}. {pkg['package_name']} (ID: {pkg['package_id']}) - ₹{pkg['starting_price']}")
        
        choice = input("Enter package number: ").strip()
        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(packages):
                print("❌ Invalid package number")
                return
            
            selected_package = packages[choice_idx]
            package_id = selected_package['package_id']
            
            # Confirm deletion
            confirm = input(f"Are you sure you want to delete '{selected_package['package_name']}'? (y/n): ").lower()
            if confirm != 'y':
                print("❌ Deletion cancelled")
                return
            
            # Delete package
            try:
                response = requests.delete(f"{BASE_URL}/freelancer/packages/{package_id}")
                if response.status_code == 200:
                    print(f"✅ Package '{selected_package['package_name']}' deleted successfully!")
                else:
                    print(f"❌ Failed to delete package: {response.text}")
            except Exception as e:
                print(f"❌ Error deleting package: {str(e)}")
                
        except ValueError:
            print("❌ Invalid selection")
            
    except Exception as e:
        print(f"❌ Error in delete flow: {str(e)}")

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
        
        # Get freelancer profile to determine pricing type
        freelancer_pricing_type = None
        try:
            profile_resp = requests.get(f"{BASE_URL}/freelancer/profile/{current_freelancer_id}")
            if profile_resp.status_code == 200:
                profile_data = profile_resp.json()
                if profile_data.get("success"):
                    freelancer_info = profile_data  # Data is directly in root, not under "freelancer" key
                    # Get pricing_type directly from database
                    freelancer_pricing_type = freelancer_info.get("pricing_type")
                    
                    # Fallback to category-based detection if database pricing_type is None
                    if not freelancer_pricing_type and get_pricing_type_for_category:
                        category = freelancer_info.get("category")
                        if category and category.strip():
                            try:
                                freelancer_pricing_type = get_pricing_type_for_category(category)
                            except Exception:
                                freelancer_pricing_type = None
                        else:
                            freelancer_pricing_type = None
        except Exception as e:
            print("DEBUG Error fetching profile:", str(e))
            freelancer_pricing_type = None
        
        print("\n--- FREELANCER DASHBOARD ---")
        
        # Dynamic menu numbering
        option_num = 1
        
        print(f"{option_num}. Create/Update Profile")
        option_num += 1
        print(f"{option_num}. View My Profile")
        option_num += 1
        print(f"{option_num}. View Hire Requests")
        option_num += 1
        print(f"{option_num}. Manage Active Jobs")
        option_num += 1
        print(f"{option_num}. Messages")
        option_num += 1
        print(f"{option_num}. Earnings")
        option_num += 1
        print(f"{option_num}. Saved Clients")
        option_num += 1
        print(f"{option_num}. Account Settings")
        option_num += 1
        print(f"{option_num}. Notifications")
        option_num += 1
        print(f"{option_num}. Manage Portfolio")
        option_num += 1
        print(f"{option_num}. Upload Profile Photo")
        option_num += 1
        print(f"{option_num}. Check Incoming Calls 📞")
        option_num += 1
        print(f"{option_num}. Verification Status 🏅")
        option_num += 1
        print(f"{option_num}. Upload Verification Documents")
        option_num += 1
        print(f"{option_num}. Subscription Plans 💎")
        option_num += 1
        print(f"{option_num}. My Subscription")
        option_num += 1
        print(f"{option_num}. Update Availability Status")
        option_num += 1
        print(f"{option_num}. Contact Client")
        option_num += 1
        
        # Conditionally show Manage Packages only for package-based freelancers
        if freelancer_pricing_type == PRICING_TYPE_PACKAGE:
            print(f"{option_num}. Manage Packages 📦")
            manage_package_option = option_num
            option_num += 1
        
        exit_option = option_num
        print(f"{exit_option}. Exit")
        option_num += 1
        logout_option = option_num
        print(f"{logout_option}. Logout")
        option_num += 1
        browse_option = option_num
        print(f"{browse_option}. Browse Projects")
        option_num += 1
        apply_option = option_num
        print(f"{apply_option}. Apply to Project")

        choice = input("Choose: ")

        if choice == str(exit_option):
            print("👋 Exiting GigBridge CLI")
            return
        
        if choice == str(logout_option):
            current_freelancer_id = None
            print("✅ Logged out successfully")
            return

        # Manage Packages (conditional)
        if freelancer_pricing_type == PRICING_TYPE_PACKAGE and choice == str(manage_package_option):
            manage_packages_menu()


        # 1️⃣ Create / Update Profile
        if choice == "1":
            from categories import ALLOWED_FREELANCER_CATEGORIES, is_valid_category
            print("\nAllowed Categories:")
            for cat in ALLOWED_FREELANCER_CATEGORIES:
                print(f"- {cat}")

            try:
                title = input("Title: ")
                skills = input("Skills: ")
                
                # Get experience in years only
                print("\nExperience Details:")
                years = int(input("Years of experience: "))

                bio = input("Bio: ")
                pincode = input("PIN Code (6 digits): ")
                location = input("Location: ")
                category = input("Category (choose from above): ")

                if not is_valid_category(category):
                    print("Invalid category. Please choose from the allowed list.")
                    continue

                dob = get_valid_dob()

                # Derive pricing_type from category (if helper available)
                pricing_type = None
                if get_pricing_type_for_category and category and category.strip():
                    try:
                        pricing_type = get_pricing_type_for_category(category)
                    except Exception:
                        pricing_type = None
                else:
                    pricing_type = None

                # Initialize pricing fields
                supports_fixed = True
                supports_hourly = False
                fixed_price = None
                hourly_rate = None
                overtime_rate_per_hour = None
                per_person_rate = None
                starting_price = None
                work_description = None
                services_included = None

                # Pricing-type aware prompts
                if pricing_type == PRICING_TYPE_HOURLY:
                    print("\nDetected pricing type: HOURLY (category-based)")
                    supports_fixed = False
                    supports_hourly = True
                    while True:
                        try:
                            hourly_rate = float(input("Hourly Rate (₹/hour): "))
                            if hourly_rate > 0:
                                break
                            print("❌ Hourly rate must be greater than 0")
                        except ValueError:
                            print("❌ Please enter a valid number")
                    overtime_choice = input("Set overtime rate? (y/n): ").lower()
                    if overtime_choice == "y":
                        while True:
                            try:
                                overtime_rate_per_hour = float(input("Overtime Rate (₹/hour): "))
                                if overtime_rate_per_hour > 0:
                                    break
                                print("❌ Overtime rate must be greater than 0")
                            except ValueError:
                                print("❌ Please enter a valid number")
                    # Hourly profiles do not require a fixed min/max budget
                    min_budget = 0
                    max_budget = 0
                elif pricing_type == PRICING_TYPE_PER_PERSON:
                    print("\nDetected pricing type: PER PERSON (category-based)")
                    supports_fixed = True  # keep FIXED available for legacy flows
                    supports_hourly = False
                    while True:
                        try:
                            per_person_rate = float(input("Per Person Rate (₹/person): "))
                            if per_person_rate > 0:
                                break
                            print("❌ Per person rate must be greater than 0")
                        except ValueError:
                            print("❌ Please enter a valid number")
                    # For per-person pricing, ignore min/max budget values
                    min_budget = 0
                    max_budget = 0

                elif pricing_type == PRICING_TYPE_PACKAGE:
                    print("\nDetected pricing type: PACKAGE (category-based)")
                    supports_fixed = True
                    supports_hourly = False
                    # For package pricing, no base price fields needed
                    starting_price = None
                    # For package pricing, ignore min/max budget values
                    min_budget = 0
                    max_budget = 0
                    print("Note: Packages will be managed separately via package management endpoints.")

                elif pricing_type == PRICING_TYPE_PROJECT:
                    print("\nDetected pricing type: PROJECT (category-based)")
                    supports_fixed = True
                    supports_hourly = False
                    while True:
                        try:
                            starting_price = float(input("Starting Project Price (₹): "))
                            if starting_price > 0:
                                break
                            print("❌ Starting price must be greater than 0")
                        except ValueError:
                            print("❌ Please enter a valid number")
                    work_description = input("Work Description: ").strip()
                    services_included = input("Services Included (comma-separated, optional): ").strip()
                    # For project pricing, ignore min/max budget values
                    min_budget = 0
                    max_budget = 0

                else:
                    # Legacy fallback: let user choose pricing models like before
                    print("\n--- Pricing Model Setup (legacy) ---")
                    print("Choose your pricing model(s):")
                    print("1. Fixed only")
                    print("2. Hourly only") 
                    print("3. Both Fixed and Hourly")
                    
                    while True:
                        pricing_choice = input("Choose (1-3): ")
                        if pricing_choice in ["1", "2", "3"]:
                            break
                        print("❌ Invalid choice. Please enter 1, 2, or 3")
                    
                    supports_fixed = pricing_choice in ["1", "3"]
                    supports_hourly = pricing_choice in ["2", "3"]

                    if supports_fixed:
                        while True:
                            try:
                                fixed_price = float(input("Fixed Price (₹): "))
                                if fixed_price > 0:
                                    break
                                print("❌ Fixed price must be greater than 0")
                            except ValueError:
                                print("❌ Please enter a valid number")
                    
                    if supports_hourly:
                        while True:
                            try:
                                hourly_rate = float(input("Hourly Rate (₹/hour): "))
                                if hourly_rate > 0:
                                    break
                                print("❌ Hourly rate must be greater than 0")
                            except ValueError:
                                print("❌ Please enter a valid number")
                        
                        overtime_choice = input("Set overtime rate? (y/n): ").lower()
                        if overtime_choice == 'y':
                            while True:
                                try:
                                    overtime_rate_per_hour = float(input("Overtime Rate (₹/hour): "))
                                    if overtime_rate_per_hour > 0:
                                        break
                                    print("❌ Overtime rate must be greater than 0")
                                except ValueError:
                                    print("❌ Please enter a valid number")
                    
                    # Only ask for budget if fixed pricing is enabled
                    if supports_fixed:
                        min_budget = float(input("Min Budget: "))
                        max_budget = float(input("Max Budget: "))
                    else:
                        # For hourly-only, no budget range needed
                        min_budget = 0
                        max_budget = 0
                
                # Prepare profile data with pricing preferences
                profile_data = {
                    "freelancer_id": current_freelancer_id,
                    "title": title,
                    "skills": skills,
                    "experience_years": years,
                    "min_budget": min_budget,
                    "max_budget": max_budget,
                    "bio": bio,
                    "pincode": pincode,
                    "location": location,
                    "category": category,
                    "dob": dob,
                    "supports_fixed": supports_fixed,
                    "supports_hourly": supports_hourly,
                }
                
                if fixed_price is not None:
                    profile_data["fixed_price"] = fixed_price
                if hourly_rate is not None:
                    profile_data["hourly_rate"] = hourly_rate
                if overtime_rate_per_hour is not None:
                    profile_data["overtime_rate_per_hour"] = overtime_rate_per_hour
                if per_person_rate is not None:
                    profile_data["per_person_rate"] = per_person_rate
                if starting_price is not None:
                    profile_data["starting_price"] = starting_price
                if work_description:
                    profile_data["work_description"] = work_description
                if services_included:
                    profile_data["services_included"] = services_included
                
                res = requests.post(f"{BASE_URL}/freelancer/profile", json=profile_data)
                result = res.json()
                if result.get("success"):
                    print("✅ Profile updated successfully!")
                    if pricing_type:
                        print(f"Pricing Type (category-based): {pricing_type}")
                    else:
                        print(f"Pricing Models: {'Fixed' if supports_fixed else ''}{' + ' if supports_fixed and supports_hourly else ''}{'Hourly' if supports_hourly else ''}")
                    if fixed_price:
                        print(f"Fixed Price: ₹{fixed_price}")
                    if hourly_rate:
                        print(f"Hourly Rate: ₹{hourly_rate}/hour")
                        if overtime_rate_per_hour:
                            print(f"Overtime Rate: ₹{overtime_rate_per_hour}/hour")
                    if per_person_rate:
                        print(f"Per Person Rate: ₹{per_person_rate}/person")
                    if starting_price:
                        print(f"Starting Price: ₹{starting_price}")
                else:
                    print("❌ Error updating profile:", result.get("msg"))
            except Exception as e:
                print(f"❌ Error: {str(e)}")

        # 2️⃣ View My Profile
        elif choice == "2":
            view_freelancer_details(current_freelancer_id)

        # 3️⃣ View Hire Requests (Inbox)
        elif choice == "3":
            try:
                res = requests.get(f"{BASE_URL}/freelancer/hire/inbox", params={
                    "freelancer_id": current_freelancer_id
                })
                inbox_data = res.json()
                
                # Normalize response to handle both list and dict formats
                if isinstance(inbox_data, list):
                    inbox = inbox_data
                else:
                    inbox = inbox_data.get("data") or inbox_data.get("requests") or inbox_data.get("results") or []
            except Exception:
                inbox = []

            if not inbox:
                print("❌ No hire requests")
                continue

            for r in inbox:
                if not isinstance(r, dict):
                    print(f"\n--- HIRE REQUEST ---")
                    print(f"Request: {str(r)}")
                    continue
                    
                print("\n--- HIRE REQUEST ---")
                print("Request ID:", r.get("request_id", "N/A"))
                print("Client:", r.get("client_name", "N/A"), "|", r.get("client_email", "N/A"))
                
                # Display based on contract type
                contract_type = r.get("contract_type", "FIXED")
                print("Contract Type:", contract_type)
                
                if contract_type == "FIXED":
                    print("Proposed Budget: ₹", r.get("proposed_budget", "N/A"))
                elif contract_type == "HOURLY":
                    print("Hourly Rate: ₹", r.get("contract_hourly_rate", 0))
                    print("Overtime Rate: ₹", r.get("contract_overtime_rate", 0))
                    print("Weekly Limit:", r.get("weekly_limit", 0))
                    print("Max Daily Hours:", r.get("max_daily_hours", 8))
                else:
                    print("Proposed Budget: ₹", r.get("proposed_budget", "N/A"))
                    print("Advance Paid: ₹", r.get("advance_paid", 0))
                
                print("Note:", r.get("note", "N/A"))
                print("Status:", r.get("status", "N/A"))
                
                # Show negotiation details if countered
                if r.get("status") == "COUNTERED":
                    if r.get("final_agreed_amount"):
                        print("Latest Offer: ₹", r.get("final_agreed_amount"))
                    if r.get("counter_note"):
                        print("Counter Note:", r.get("counter_note"))
                    
                    negotiation_status = r.get("negotiation_status", "Unknown")
                    offered_by = negotiation_status
                    
                    if offered_by == "FREELANCER":
                        print("Offered By: FREELANCER (You)")
                        print("📝 Waiting for client response...")
                        print("\nActions:")
                        print("4. Message Client")
                        print("5. Save Client")
                        print("6. Next")
                        print("0. Back")
                        
                        a = input("Choose: ")
                        if a == "4":
                            open_chat_with_client(r["client_id"])
                        elif a == "5":
                            rr = requests.post(f"{BASE_URL}/freelancer/save-client", json={
                                "freelancer_id": current_freelancer_id,
                                "client_id": r["client_id"]
                            })
                            try:
                                print(rr.json())
                            except Exception:
                                print("❌ Failed to save client")
                        elif a == "0":
                            break
                            
                    elif offered_by == "CLIENT":
                        print("Offered By: CLIENT")
                        print("🎯 Action required from you!")
                        print("\nActions:")
                        print("1. Accept Counteroffer")
                        print("2. Reject Counteroffer")
                        print("3. Counteroffer Again")
                        print("4. Message Client")
                        print("5. Save Client")
                        print("6. Next")
                        print("0. Back")
                        
                        a = input("Choose: ")
                        
                        if a == "1":
                            # Accept client's counteroffer
                            rr = requests.post(f"{BASE_URL}/freelancer/hire/respond", json={
                                "freelancer_id": current_freelancer_id,
                                "request_id": r["request_id"],
                                "action": "ACCEPT"
                            })
                            result = rr.json()
                            if result.get("success"):
                                print(f"✅ Counteroffer accepted!")
                                print(f"   Final agreed amount: ₹{r.get('final_agreed_amount')}")
                                print(f"   Request status: ACCEPTED")
                                print(f"   🎉 You can now proceed with the job!")
                            else:
                                print(f"❌ Failed to accept counteroffer: {result.get('msg')}")
                        elif a == "2":
                            # Reject client's counteroffer
                            rr = requests.post(f"{BASE_URL}/freelancer/hire/respond", json={
                                "freelancer_id": current_freelancer_id,
                                "request_id": r["request_id"],
                                "action": "REJECT"
                            })
                            result = rr.json()
                            if result.get("success"):
                                print(f"✅ Counteroffer rejected!")
                                print(f"   Request status: REJECTED")
                                print(f"   💡 You can wait for other opportunities")
                            else:
                                print(f"❌ Failed to reject counteroffer: {result.get('msg')}")
                        elif a == "3":
                            # Counteroffer again
                            print(f"\n💰 Send New Counteroffer")
                            print(f"Current client offer: ₹{r.get('final_agreed_amount')}")
                            
                            counter_amount = input("Your Counter Offer Amount: ₹").strip()
                            counter_note = input("Counter Offer Note (optional): ").strip()
                            
                            try:
                                counter_amount = float(counter_amount)
                                if counter_amount <= 0:
                                    print("❌ Counter offer amount must be greater than 0")
                                    continue
                            except ValueError:
                                print("❌ Please enter a valid number")
                                continue
                            
                            rr = requests.post(f"{BASE_URL}/freelancer/hire/respond", json={
                                "freelancer_id": current_freelancer_id,
                                "request_id": r["request_id"],
                                "action": "COUNTER",
                                "counter_offer_amount": counter_amount,
                                "counter_offer_note": counter_note
                            })
                            result = rr.json()
                            if result.get("success"):
                                print(f"✅ New counteroffer sent!")
                                print(f"   Your offer: ₹{counter_amount}")
                                if counter_note:
                                    print(f"   Note: {counter_note}")
                                print(f"   📝 Waiting for client response...")
                            else:
                                print(f"❌ Failed to send counteroffer: {result.get('msg')}")
                        elif a == "4":
                            open_chat_with_client(r["client_id"])
                        elif a == "5":
                            rr = requests.post(f"{BASE_URL}/freelancer/save-client", json={
                                "freelancer_id": current_freelancer_id,
                                "client_id": r["client_id"]
                            })
                            try:
                                print(rr.json())
                            except Exception:
                                print("❌ Failed to save client")
                        elif a == "0":
                            break
                    else:
                        print("Offered By: Unknown")
                        print("⚠️  Negotiation status unclear")
                        print("\nActions:")
                        print("4. Message Client")
                        print("5. Save Client")
                        print("6. Next")
                        print("0. Back")
                        
                        a = input("Choose: ")
                        if a == "4":
                            open_chat_with_client(r["client_id"])
                        elif a == "5":
                            rr = requests.post(f"{BASE_URL}/freelancer/save-client", json={
                                "freelancer_id": current_freelancer_id,
                                "client_id": r["client_id"]
                            })
                            try:
                                print(rr.json())
                            except Exception:
                                print("❌ Failed to save client")
                        elif a == "0":
                            break

                if r.get("status") == "PENDING":
                    print("1. Accept")
                    print("2. Reject")
                    print("3. Counteroffer")
                    print("4. Message Client")
                    print("5. Save Client")
                    print("6. Next")
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
                        # Counteroffer
                        counter_amount = input("Counter Offer Amount: ₹").strip()
                        counter_note = input("Counter Offer Note (optional): ").strip()
                        
                        try:
                            counter_amount = float(counter_amount)
                            if counter_amount <= 0:
                                print("❌ Counter offer amount must be greater than 0")
                                continue
                        except ValueError:
                            print("❌ Please enter a valid number")
                            continue
                        
                        rr = requests.post(f"{BASE_URL}/freelancer/hire/respond", json={
                            "freelancer_id": current_freelancer_id,
                            "request_id": r["request_id"],
                            "action": "COUNTER",
                            "counter_offer_amount": counter_amount,
                            "counter_offer_note": counter_note
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
                inbox_data = res.json()
                
                # Normalize response to handle both list and dict formats
                if isinstance(inbox_data, list):
                    inbox = inbox_data
                else:
                    inbox = inbox_data.get("data") or inbox_data.get("requests") or inbox_data.get("results") or []
            except Exception:
                inbox = []

            active = []
            for r in inbox:
                if isinstance(r, dict) and r.get("status") == "ACCEPTED":
                    active.append(r)
            print("\n--- ACTIVE JOBS ---")
            if not active:
                print("📭 No active (accepted) jobs")
            else:
                for i, j in enumerate(active, 1):
                    if isinstance(j, dict):
                        title = j.get("note") or j.get("request_id", "Untitled")
                        contract_type = j.get("contract_type", "FIXED")
                        
                        if contract_type == "FIXED":
                            budget_info = f"Budget: ₹{j.get('proposed_budget', 'N/A')}"
                        elif contract_type == "HOURLY":
                            budget_info = f"Rate: ₹{j.get('contract_hourly_rate', 0)}/hr"
                        else:
                            budget_info = f"Budget: ₹{j.get('proposed_budget', 'N/A')}"
                        
                        client_name = j.get('client_name', 'N/A')
                        status = j.get('status', 'N/A')
                    else:
                        title = str(j)
                        contract_type = "FIXED"
                        budget_info = "N/A"
                        client_name = "N/A"
                        status = "N/A"
                    
                    print(f"{i}. Client: {client_name} | {budget_info} | {contract_type} | {status}")

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
                if isinstance(r, dict):
                    client_id = r.get("client_id")
                    client_name = r.get("client_name", "Unknown")
                    if client_id:
                        clients[client_id] = client_name

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
                            if isinstance(msg, dict):
                                sender = "You" if msg.get('sender_role') == 'freelancer' else "Client"
                                text = msg.get('text', 'No text')
                                print(f"{sender}: {text}")
                            else:
                                print(f"Message: {str(msg)}")
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
                    # Safe dictionary access with type checking
                    if isinstance(c, dict):
                        client_id = c.get('client_id', 'Unknown')
                        name = c.get('name', 'Unknown')
                        email = c.get('email', 'Unknown')
                        print(f"{client_id}. {name} - {email}")
                    else:
                        # Handle legacy string format
                        print(f"Legacy client: {c}")
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
                from notification_utils import get_notification_icon
                
                for idx, note in enumerate(notes, 1):
                    # Safe handling with fallbacks
                    if isinstance(note, dict):
                        message = note.get("message", "No activity details")
                        title = note.get("title", "")
                        related_type = note.get("related_entity_type", "")
                        
                        # Fix old placeholders if present
                        if "job_title" in message and "status" in message:
                            job_title = note.get("job_title", "Unknown")
                            status = note.get("status", "Updated")
                            message = message.replace("job_title", job_title).replace("status", status)
                    else:
                        # Handle legacy format (string only)
                        message = str(note) if note else "No activity details"
                        title = ""
                        related_type = ""
                        
                        # Fix old placeholders in legacy format
                        if "job_title" in message and "status" in message:
                            message = message.replace("job_title", "Unknown").replace("status", "Updated")
                    
                    # Get appropriate icon based on content
                    icon = get_notification_icon(message=message, title=title, related_entity_type=related_type)
                    
                    # Remove duplicate icons and display with single icon
                    clean_message = message.strip()
                    if clean_message.startswith("✅ ✅"):
                        clean_message = clean_message.replace("✅ ✅", "✅")
                    elif clean_message.startswith("❌ ❌"):
                        clean_message = clean_message.replace("❌ ❌", "❌")
                    
                    print(f"{idx}. {icon} {clean_message}")

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
        elif choice == str(browse_option):
            # Browse Projects
            try:
                res = requests.get(f"{BASE_URL}/freelancer/projects/feed", params={
                    "freelancer_id": current_freelancer_id
                })
                data = res.json()
                if data.get("success"):
                    projects = data.get("projects", [])
                    if not projects:
                        print("\n❌ No relevant projects found for your category/location")
                        continue
                    
                    print("\n--- RELEVANT OPEN PROJECTS ---")
                    for i, p in enumerate(projects, 1):
                        print(f"\n📋 Project {i}")
                        print(f"   Category: {p.get('category', 'N/A').title()}")
                        print(f"   📍 Location: {p.get('location', 'N/A')} | Pincode: {p.get('pincode', 'N/A')}")
                        print(f"   📝 Description: {p.get('description', 'N/A')}")
                        
                        # Ask if freelancer wants to apply to this specific project
                        apply_choice = input(f"\nDo you want to apply to this project? (y/n): ").strip().lower()
                        
                        if apply_choice == 'y':
                            print(f"\n--- APPLY TO PROJECT {i} ---")
                            
                            proposal = input("Your Proposal/Message: ").strip()
                            bid_amount = input("Your Bid Amount: ₹").strip()
                            
                            if not proposal or not bid_amount:
                                print("❌ Proposal and bid amount are required")
                                continue
                                
                            try:
                                bid_amount = float(bid_amount)
                            except ValueError:
                                print("❌ Invalid bid amount")
                                continue
                                
                            # Submit application
                            payload = {
                                "freelancer_id": current_freelancer_id,
                                "project_id": p["project_id"],
                                "proposal": proposal,
                                "bid_amount": bid_amount
                            }
                            
                            app_res = requests.post(f"{BASE_URL}/freelancer/projects/apply", json=payload)
                            app_result = app_res.json()
                            if app_result.get("success"):
                                print("✅ Applied successfully!")
                            else:
                                print(f"❌ Failed to apply: {app_result.get('msg')}")
                            
                            # Ask if they want to continue browsing
                            continue_choice = input("\nContinue browsing other projects? (y/n): ").strip().lower()
                            if continue_choice != 'y':
                                break
                        elif apply_choice == 'n':
                            print("   Skipping this project...")
                            continue
                        else:
                            print("   Please enter 'y' or 'n'")
                            continue
                    
                    if i == len(projects):  # Finished all projects
                        print("\n📋 No more relevant projects available.")
                else:
                    print("❌", data.get("msg"))
            except Exception as e:
                print("❌ Error:", str(e))

        elif choice == str(apply_option):
            # Apply to Project (Legacy - Use Browse Projects instead)
            print("\n⚠️  This option is deprecated.")
            print("💡 Please use 'Browse Projects' to view and apply to relevant projects.")
            print("   It shows projects matched to your category and allows direct application.")
            continue

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
