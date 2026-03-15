#!/usr/bin/env python3
"""
Simple test for event venue feature
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_hire_endpoint():
    print("🧪 Testing Hire Endpoint...")
    
    # Test 1: Profile address hire
    print("\n--- Test 1: Profile Address Hire ---")
    profile_data = {
        "client_id": 1,
        "freelancer_id": 1,
        "job_title": "Test Job with Profile Address",
        "proposed_budget": 5000,
        "note": "Test hire using saved profile address",
        "contract_type": "FIXED",
        "venue_source": "profile"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/hire", json=profile_data)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ Profile address hire successful")
        else:
            print(f"❌ Failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Custom venue hire
    print("\n--- Test 2: Custom Venue Hire ---")
    custom_data = {
        "client_id": 1,
        "freelancer_id": 1,
        "job_title": "Test Job with Custom Venue",
        "proposed_budget": 6000,
        "note": "Test hire using custom venue address",
        "contract_type": "EVENT",
        "event_base_fee": 2000,
        "event_included_hours": 4,
        "event_overtime_rate": 500,
        "venue_source": "custom",
        "event_address": "123 Test Street, Mumbai",
        "event_city": "Mumbai",
        "event_pincode": "400001",
        "event_landmark": "Near Test Station"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/hire", json=custom_data)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ Custom venue hire successful")
            venue = result.get("venue", {})
            location = result.get("location_check", {})
            print(f"Venue stored: {venue.get('event_address')}")
            print(f"Location OK: {location.get('location_ok')}")
        else:
            print(f"❌ Failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_hire_endpoint()
