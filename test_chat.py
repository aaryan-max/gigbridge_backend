"""
Test script for Database Chat Service
"""

import requests
import json

# Base URL for local testing
BASE_URL = "http://localhost:5000"

def test_chat_service():
    print("🤖 Testing GigBridge Database Chat Service")
    print("=" * 50)
    
    # Test 1: Help endpoint
    print("\n1. Testing /chat/help endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/chat/help")
        if response.status_code == 200:
            data = response.json()
            print("✅ Help endpoint works")
            print(f"Available commands: {len(data['data']['available_commands'])}")
        else:
            print(f"❌ Help endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Help endpoint error: {e}")
    
    # Test 2: Status endpoint
    print("\n2. Testing /chat/status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/chat/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Status endpoint works")
            print(f"Service: {data['data']['service']}")
            print(f"Type: {data['data']['type']}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
    
    # Test 3: Query endpoint with invalid data
    print("\n3. Testing /chat/query with invalid data...")
    try:
        response = requests.post(
            f"{BASE_URL}/chat/query",
            json={"message": "test"}  # Missing role and user_id
        )
        if response.status_code == 400:
            data = response.json()
            print("✅ Validation works - missing fields detected")
            print(f"Error: {data['msg']}")
        else:
            print(f"❌ Validation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Query validation error: {e}")
    
    # Test 4: Query endpoint with valid data (but non-existent user)
    print("\n4. Testing /chat/query with valid format...")
    try:
        response = requests.post(
            f"{BASE_URL}/chat/query",
            json={
                "role": "client",
                "user_id": 99999,  # Non-existent user
                "message": "show my projects"
            }
        )
        if response.status_code == 400:
            data = response.json()
            print("✅ User validation works")
            print(f"Error: {data['msg']}")
        else:
            print(f"❌ User validation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Query error: {e}")
    
    # Test 5: Query endpoint with unsupported command
    print("\n5. Testing /chat/query with unsupported command...")
    try:
        response = requests.post(
            f"{BASE_URL}/chat/query",
            json={
                "role": "client",
                "user_id": 1,
                "message": "what is the weather today"
            }
        )
        if response.status_code == 400:
            data = response.json()
            print("✅ Unsupported command handled correctly")
            print(f"Error: {data['msg']}")
        else:
            print(f"❌ Unsupported command failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Unsupported command error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Database Chat Service Test Complete!")
    print("\nTo test with real data:")
    print("1. Start the Flask server: python app.py")
    print("2. Run this test script: python test_chat.py")
    print("3. Use CLI chat: python cli_test.py → Choose AI Chat option")

if __name__ == "__main__":
    test_chat_service()
