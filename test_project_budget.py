#!/usr/bin/env python3
"""
Test the project posting budget changes
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_project_posting_changes():
    print("🧪 Testing Project Posting Budget Changes...")
    
    # Test 1: FIXED project posting
    print("\n--- Test 1: FIXED Project Posting ---")
    fixed_project = {
        "client_id": 1,
        "title": "Test Fixed Budget Project",
        "description": "Test project with fixed budget",
        "category": "Web Development",
        "skills": "Python, Django",
        "budget_type": "FIXED",
        "budget": 25000
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
    
    # Test 2: HOURLY project posting
    print("\n--- Test 2: HOURLY Project Posting ---")
    hourly_project = {
        "client_id": 1,
        "title": "Test Hourly Budget Project",
        "description": "Test project with hourly rate",
        "category": "Web Development",
        "skills": "Python, Django",
        "budget_type": "HOURLY",
        "hourly_rate": 500
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
    
    # Test 3: Invalid budget type (should fail)
    print("\n--- Test 3: Invalid Budget Type (Should Fail) ---")
    invalid_project = {
        "client_id": 1,
        "title": "Test Invalid Project",
        "description": "Test with invalid budget type",
        "category": "Web Development",
        "skills": "Python, Django",
        "budget_type": "EVENT",  # This should fail
        "budget": 25000
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/projects/create", json=invalid_project)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if not result.get("success"):
            print("✅ Invalid budget type properly rejected")
        else:
            print(f"❌ Should have failed but didn't: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_project_posting_changes()
