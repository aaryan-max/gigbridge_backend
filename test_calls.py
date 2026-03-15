#!/usr/bin/env python3
"""
Test Voice/Video Call Functionality
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_call_functionality():
    print("🧪 Testing Voice/Video Call Functionality...")
    
    # Test 1: Start Voice Call
    print("\n--- Test 1: Start Voice Call ---")
    voice_call_data = {
        "caller_id": 1,
        "receiver_id": 2,
        "call_type": "voice"
    }
    
    print(f"Sending data: {json.dumps(voice_call_data, indent=2)}")
    
    try:
        res = requests.post(f"{BASE_URL}/call/start", json=voice_call_data)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ Voice call started successfully")
            call_id = result.get("call_id")
            meeting_url = result.get("meeting_url")
        else:
            print(f"❌ Failed: {result.get('msg')}")
            # If permission issue, try with different users
            if "permission" in result.get('msg', '').lower():
                print("🔄 Trying with users who have interacted...")
                voice_call_data = {
                    "caller_id": 1,
                    "receiver_id": 1,  # Same user for testing
                    "call_type": "voice"
                }
                res = requests.post(f"{BASE_URL}/call/start", json=voice_call_data)
                result = res.json()
                print(f"Status: {res.status_code}")
                print(f"Response: {json.dumps(result, indent=2)}")
                if result.get("success"):
                    call_id = result.get("call_id")
                    meeting_url = result.get("meeting_url")
                else:
                    return
            else:
                return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Start Video Call
    print("\n--- Test 2: Start Video Call ---")
    video_call_data = {
        "caller_id": 2,
        "receiver_id": 1,
        "call_type": "video"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/call/start", json=video_call_data)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ Video call started successfully")
            video_call_id = result.get("call_id")
        else:
            print(f"❌ Failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check Incoming Calls
    print("\n--- Test 3: Check Incoming Calls ---")
    try:
        res = requests.get(f"{BASE_URL}/call/incoming", params={"user_id": 1})
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print(f"✅ Found {len(result.get('calls', []))} incoming calls")
            for call in result.get("calls", []):
                print(f"   - {call['call_type']} call from {call.get('caller_name', 'Unknown')}")
        else:
            print(f"❌ Failed: {result.get('msg')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Accept Call
    if call_id:
        print("\n--- Test 4: Accept Call ---")
        try:
            res = requests.post(f"{BASE_URL}/call/accept", json={"call_id": call_id})
            result = res.json()
            print(f"Status: {res.status_code}")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                print("✅ Call accepted successfully")
            else:
                print(f"❌ Failed: {result.get('msg')}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 5: Reject Call
    if video_call_id:
        print("\n--- Test 5: Reject Call ---")
        try:
            res = requests.post(f"{BASE_URL}/call/reject", json={"call_id": video_call_id})
            result = res.json()
            print(f"Status: {res.status_code}")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                print("✅ Call rejected successfully")
            else:
                print(f"❌ Failed: {result.get('msg')}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 6: Invalid Call Type
    print("\n--- Test 6: Invalid Call Type ---")
    invalid_data = {
        "caller_id": 1,
        "receiver_id": 2,
        "call_type": "invalid"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/call/start", json=invalid_data)
        result = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if not result.get("success"):
            print("✅ Invalid call type properly rejected")
        else:
            print("❌ Should have failed but didn't")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_call_functionality()
