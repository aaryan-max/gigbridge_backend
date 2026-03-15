#!/usr/bin/env python3
import requests
import time
import random

BASE_URL = "http://127.0.0.1:5000"

def test_freelancer_otp_signup():
    """Test freelancer signup with email OTP"""
    print("🧪 Testing Freelancer OTP Signup...")
    
    # Generate unique email
    timestamp = int(time.time())
    email = f"test_freelancer_{timestamp}@example.com"
    name = f"Test Freelancer {timestamp}"
    password = "test123456"
    
    print(f"📧 Email: {email}")
    
    try:
        # Step 1: Request OTP
        print("\n1️⃣ Requesting OTP...")
        otp_response = requests.post(f"{BASE_URL}/freelancer/send-otp", 
                                   json={"email": email, "name": name, "password": password})
        
        print(f"Status: {otp_response.status_code}")
        print(f"Response: {otp_response.json()}")
        
        if otp_response.status_code != 200:
            print("❌ OTP request failed")
            return False
            
        # Step 2: Get OTP from database (for testing)
        print("\n2️⃣ Getting OTP from database...")
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from database import freelancer_db
        
        conn = freelancer_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT otp, expires_at FROM freelancer_otp WHERE email=%s", (email,))
        row = cur.fetchone()
        
        if not row:
            print("❌ OTP not found in database")
            return False
            
        otp = row["otp"]
        expires_at = int(row["expires_at"])
        current_time = int(time.time())
        
        print(f"🔢 OTP: {otp}")
        print(f"⏰ Current time: {current_time}")
        print(f"⏰ Expires at: {expires_at}")
        print(f"✅ OTP valid: {current_time <= expires_at}")
        
        conn.close()
        
        # Step 3: Verify OTP and complete signup
        print("\n3️⃣ Verifying OTP and completing signup...")
        signup_response = requests.post(f"{BASE_URL}/freelancer/verify-otp", 
                                      json={"email": email, "name": name, "password": password, "otp": otp})
        
        print(f"Status: {signup_response.status_code}")
        print(f"Response: {signup_response.json()}")
        
        if signup_response.status_code == 200:
            print("✅ Freelancer OTP signup successful!")
            return True
        else:
            print("❌ Freelancer OTP signup failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_client_otp_signup():
    """Test client signup with email OTP"""
    print("\n🧪 Testing Client OTP Signup...")
    
    # Generate unique email
    timestamp = int(time.time())
    email = f"test_client_{timestamp}@example.com"
    name = f"Test Client {timestamp}"
    password = "test123456"
    
    print(f"📧 Email: {email}")
    
    try:
        # Step 1: Request OTP
        print("\n1️⃣ Requesting OTP...")
        otp_response = requests.post(f"{BASE_URL}/client/send-otp", 
                                   json={"email": email, "name": name, "password": password})
        
        print(f"Status: {otp_response.status_code}")
        print(f"Response: {otp_response.json()}")
        
        if otp_response.status_code != 200:
            print("❌ OTP request failed")
            return False
            
        # Step 2: Get OTP from database (for testing)
        print("\n2️⃣ Getting OTP from database...")
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from database import client_db
        
        conn = client_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT otp, expires_at FROM client_otp WHERE email=%s", (email,))
        row = cur.fetchone()
        
        if not row:
            print("❌ OTP not found in database")
            return False
            
        otp = row["otp"]
        expires_at = int(row["expires_at"])
        current_time = int(time.time())
        
        print(f"🔢 OTP: {otp}")
        print(f"⏰ Current time: {current_time}")
        print(f"⏰ Expires at: {expires_at}")
        print(f"✅ OTP valid: {current_time <= expires_at}")
        
        conn.close()
        
        # Step 3: Verify OTP and complete signup
        print("\n3️⃣ Verifying OTP and completing signup...")
        signup_response = requests.post(f"{BASE_URL}/client/verify-otp", 
                                      json={"email": email, "name": name, "password": password, "otp": otp})
        
        print(f"Status: {signup_response.status_code}")
        print(f"Response: {signup_response.json()}")
        
        if signup_response.status_code == 200:
            print("✅ Client OTP signup successful!")
            return True
        else:
            print("❌ Client OTP signup failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing OTP Signup Fix")
    print("=" * 50)
    
    # Test freelancer signup
    freelancer_success = test_freelancer_otp_signup()
    
    # Test client signup  
    client_success = test_client_otp_signup()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"✅ Freelancer OTP Signup: {'PASS' if freelancer_success else 'FAIL'}")
    print(f"✅ Client OTP Signup: {'PASS' if client_success else 'FAIL'}")
    
    if freelancer_success and client_success:
        print("\n🎉 ALL TESTS PASSED! OTP signup is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the logs above.")
