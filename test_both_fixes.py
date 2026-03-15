#!/usr/bin/env python3
"""
Test both username fix and project budget changes
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_username_in_profile():
    print("🧪 Testing Username in Client Profile Creation...")
    
    # Test client profile creation with username
    print("\n--- Test 1: Client Profile Creation with Username ---")
    profile_data = {
        "client_id": 1,
        "name": "TestUsername123",  # ✅ Username field now included
        "phone": "9876543210",
        "location": "Test Location",
        "bio": "Test bio",
        "dob": "1990-01-01"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/profile", json=profile_data)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ Client profile created with username")
        else:
            print(f"❌ Failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_project_budget_changes():
    print("\n--- Test 2: Project Budget Changes ---")
    
    # Test FIXED project with single budget
    print("\nTest 2a: FIXED Project with Single Budget")
    fixed_project = {
        "client_id": 1,
        "title": "Test Fixed Budget Project",
        "description": "Test project with single fixed budget",
        "category": "Web Development",
        "skills": "Python, Django",
        "budget_type": "FIXED",
        "budget": 25000  # ✅ Single budget value
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/projects/create", json=fixed_project)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ FIXED project posted successfully")
            print(f"Budget Type: {result.get('budget_type')}")
            print(f"Budget Value: {result.get('budget_value')}")
        else:
            print(f"❌ Failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test HOURLY project with single rate
    print("\nTest 2b: HOURLY Project with Single Rate")
    hourly_project = {
        "client_id": 1,
        "title": "Test Hourly Budget Project",
        "description": "Test project with single hourly rate",
        "category": "Web Development",
        "skills": "Python, Django",
        "budget_type": "HOURLY",
        "hourly_rate": 500  # ✅ Single hourly rate
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/projects/create", json=hourly_project)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ HOURLY project posted successfully")
            print(f"Budget Type: {result.get('budget_type')}")
            print(f"Budget Value: {result.get('budget_value')}")
        else:
            print(f"❌ Failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_username_in_profile()
    test_project_budget_changes()
