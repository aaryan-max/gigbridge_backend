#!/usr/bin/env python3
"""
Test Event Venue Feature Implementation
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_venue_feature():
    print("🧪 Testing Event Venue Feature...")
    
    # Test 1: Hire with profile address
    print("\n--- Test 1: Hire with Profile Address ---")
    hire_data_profile = {
        "client_id": 1,
        "freelancer_id": 1,
        "job_title": "Test Job with Profile Address",
        "proposed_budget": 5000,
        "note": "Test hire using saved profile address",
        "contract_type": "FIXED",
        "venue_source": "profile"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/hire", json=hire_data_profile)
        result = res.json()
        
        if result.get("success"):
            print("✅ Profile address hire successful")
            venue = result.get("venue", {})
            location = result.get("location_check", {})
            print(f"  Venue Source: {venue.get('venue_source')}")
            print(f"  Location OK: {location.get('location_ok')}")
            print(f"  Location Note: {location.get('location_note')}")
            print(f"  Request ID: {result.get('request_id')}")
        else:
            print(f"❌ Profile address hire failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Hire with custom venue
    print("\n--- Test 2: Hire with Custom Venue ---")
    hire_data_custom = {
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
        res = requests.post(f"{BASE_URL}/client/hire", json=hire_data_custom)
        result = res.json()
        
        if result.get("success"):
            print("✅ Custom venue hire successful")
            venue = result.get("venue", {})
            location = result.get("location_check", {})
            print(f"  Venue Address: {venue.get('event_address')}")
            print(f"  Event City: {venue.get('event_city')}")
            print(f"  Event Pincode: {venue.get('event_pincode')}")
            print(f"  Venue Source: {venue.get('venue_source')}")
            print(f"  Location OK: {location.get('location_ok')}")
            print(f"  Location Note: {location.get('location_note')}")
            print(f"  Request ID: {result.get('request_id')}")
        else:
            print(f"❌ Custom venue hire failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Validation tests
    print("\n--- Test 3: Validation Tests ---")
    
    # Test invalid pincode
    invalid_venue = {
        "client_id": 1,
        "freelancer_id": 1,
        "job_title": "Test Invalid Venue",
        "proposed_budget": 3000,
        "contract_type": "FIXED",
        "venue_source": "custom",
        "event_address": "Test Address",
        "event_pincode": "abc"  # Invalid pincode
    }
    
    try:
        res = requests.post(f"{BASE_URL}/client/hire", json=invalid_venue)
        result = res.json()
        
        if not result.get("success"):
            print("✅ Invalid pincode validation works")
            print(f"  Error: {result.get('msg')}")
        else:
            print("❌ Validation failed - should have caught invalid pincode")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_venue_feature()
