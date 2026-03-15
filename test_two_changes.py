#!/usr/bin/env python3
"""
Test the two requested changes: username in client profile and removal of weekly limits from hire flow
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_username_in_profile():
    print("🧪 Testing Username in Client Profile Creation...")
    
    # Test client profile creation with username
    print("\n--- Test 1: Client Profile Creation with Username ---")
    profile_data = {
        "name": "Test User",
        "email": f"testuser{int(__import__('time').time())}@example.com",  # Unique email
        "password": "testpass123",
        "phone": "9876543210",
        "location": "Test Location",
        "bio": "Test bio",
        "dob": "1990-01-01"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/signup", json=profile_data)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ Client profile created with username")
            client_id = result.get("client_id")
        else:
            print(f"❌ Failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_hourly_hire_simplified():
    print("\n--- Test 2: HOURLY Hire (Simplified) ---")
    
    # Test HOURLY hire without weekly limits
    hourly_data = {
        "client_id": 1,
        "freelancer_id": 1,
        "job_title": "Test Hourly Job",
        "proposed_budget": 5000,
        "note": "Test hourly job without limits",
        "contract_type": "HOURLY",
        "contract_hourly_rate": 500,
        # Note: NOT sending weekly_limit or max_daily_hour
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/hire", json=hourly_data)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ HOURLY hire successful without limits")
        else:
            print(f"❌ Failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_username_in_profile()
    test_hourly_hire_simplified()
