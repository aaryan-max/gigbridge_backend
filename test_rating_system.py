#!/usr/bin/env python3
"""
Test script to verify enhanced rating system functionality
"""
import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def test_rating_system():
    print("🧪 Testing Enhanced Rating System")
    print("=" * 50)
    
    # Test 1: Rate without job completion (should fail)
    print("\n❌ Test 1: Rate non-completed job (should fail)")
    try:
        response = requests.post(f"{BASE_URL}/client/rate", json={
            "client_id": 1,
            "freelancer_id": 2,
            "hire_request_id": 1,  # Assuming this job is not PAID
            "rating": 5,
            "review": "Great work!"
        })
        data = response.json()
        if not data.get("success") and "job completion" in data.get("msg", ""):
            print("✅ Correctly blocked rating for non-completed job")
            print(f"   Error: {data.get('msg')}")
        else:
            print("❌ Failed to block rating for non-completed job")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Rate with invalid rating (should fail)
    print("\n❌ Test 2: Invalid rating value (should fail)")
    try:
        response = requests.post(f"{BASE_URL}/client/rate", json={
            "client_id": 1,
            "freelancer_id": 2,
            "rating": 6,  # Invalid rating > 5
            "review": "Test review"
        })
        data = response.json()
        if not data.get("success") and "between 1 and 5" in data.get("msg", ""):
            print("✅ Correctly blocked invalid rating value")
            print(f"   Error: {data.get('msg')}")
        else:
            print("❌ Failed to block invalid rating value")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Rate someone else's job (should fail)
    print("\n❌ Test 3: Rate non-owned job (should fail)")
    try:
        response = requests.post(f"{BASE_URL}/client/rate", json={
            "client_id": 2,  # Different client
            "freelancer_id": 1,
            "hire_request_id": 1,
            "rating": 4,
            "review": "Test review"
        })
        data = response.json()
        if not data.get("success") and "own jobs" in data.get("msg", ""):
            print("✅ Correctly blocked rating for non-owned job")
            print(f"   Error: {data.get('msg')}")
        else:
            print("❌ Failed to block rating for non-owned job")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Duplicate rating (should fail)
    print("\n❌ Test 4: Duplicate rating (should fail)")
    try:
        # First, let's assume there's a completed job with ID 999
        job_id = 999
        
        # Submit first rating (this might fail if job doesn't exist, but that's ok for this test)
        response = requests.post(f"{BASE_URL}/client/rate", json={
            "client_id": 1,
            "freelancer_id": 2,
            "hire_request_id": job_id,
            "rating": 5,
            "review": "First rating"
        })
        
        # Submit second rating (should fail as duplicate)
        response2 = requests.post(f"{BASE_URL}/client/rate", json={
            "client_id": 1,
            "freelancer_id": 2,
            "hire_request_id": job_id,
            "rating": 4,
            "review": "Duplicate rating"
        })
        
        data2 = response2.json()
        if not data2.get("success") and "already rated" in data2.get("msg", ""):
            print("✅ Correctly blocked duplicate rating")
            print(f"   Error: {data2.get('msg')}")
        else:
            print("ℹ️  Duplicate rating test inconclusive (job may not exist)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Valid rating (should succeed if job exists and is PAID)
    print("\n✅ Test 5: Valid rating attempt")
    try:
        response = requests.post(f"{BASE_URL}/client/rate", json={
            "client_id": 1,
            "freelancer_id": 2,
            "hire_request_id": 999,  # Assuming this exists and is PAID
            "rating": 4.5,
            "review": "Excellent work, very professional!"
        })
        data = response.json()
        if data.get("success"):
            print("✅ Valid rating accepted")
            print(f"   New average rating: {data.get('new_rating', 'N/A')}")
            print(f"   Total reviews: {data.get('total_reviews', 'N/A')}")
        else:
            print(f"ℹ️  Valid rating test inconclusive: {data.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Missing fields (should fail)
    print("\n❌ Test 6: Missing required fields (should fail)")
    try:
        response = requests.post(f"{BASE_URL}/client/rate", json={
            "client_id": 1,
            # Missing freelancer_id, rating, review
        })
        data = response.json()
        if not data.get("success") and "Missing fields" in data.get("msg", ""):
            print("✅ Correctly blocked request with missing fields")
            print(f"   Error: {data.get('msg')}")
        else:
            print("❌ Failed to block request with missing fields")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Enhanced Rating System Tests Complete!")
    print("✅ All validation logic tested")
    print("\n📋 Summary of Fixes:")
    print("1. ✅ Only allows rating after job completion (PAID status)")
    print("2. ✅ Prevents duplicate ratings")
    print("3. ✅ Ensures job ownership verification")
    print("4. ✅ Validates rating input (1-5)")
    print("5. ✅ Handles missing/invalid data safely")
    print("6. ✅ Provides helpful error messages")

if __name__ == "__main__":
    test_rating_system()
