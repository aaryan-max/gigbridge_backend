#!/usr/bin/env python3
"""
Test script to verify call system integration
"""
import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def test_call_system():
    print("🧪 Testing Call System Integration")
    print("=" * 50)
    
    # Test 1: Start a voice call
    print("\n📞 Test 1: Start Voice Call")
    try:
        response = requests.post(f"{BASE_URL}/call/start", json={
            "caller_id": 1,
            "receiver_id": 2,
            "call_type": "voice"
        })
        data = response.json()
        if data.get("success"):
            print("✅ Voice call started successfully")
            print(f"   Call ID: {data.get('call_id')}")
            print(f"   Meeting URL: {data.get('meeting_url')}")
            
            # Verify room name format
            meeting_url = data.get('meeting_url', '')
            if 'gigbridge_1*2*' in meeting_url:
                print("✅ Room name format is correct")
            else:
                print("❌ Room name format is incorrect")
        else:
            print(f"❌ Failed to start voice call: {data.get('msg')}")
    except Exception as e:
        print(f"❌ Error testing voice call: {e}")
    
    # Test 2: Start a video call
    print("\n🎥 Test 2: Start Video Call")
    try:
        response = requests.post(f"{BASE_URL}/call/start", json={
            "caller_id": 2,
            "receiver_id": 1,
            "call_type": "video"
        })
        data = response.json()
        if data.get("success"):
            print("✅ Video call started successfully")
            print(f"   Call ID: {data.get('call_id')}")
            print(f"   Meeting URL: {data.get('meeting_url')}")
        else:
            print(f"❌ Failed to start video call: {data.get('msg')}")
    except Exception as e:
        print(f"❌ Error testing video call: {e}")
    
    # Test 3: Check incoming calls
    print("\n📲 Test 3: Check Incoming Calls")
    try:
        response = requests.get(f"{BASE_URL}/call/incoming", params={"user_id": 1})
        data = response.json()
        if data.get("success"):
            calls = data.get("calls", [])
            print(f"✅ Found {len(calls)} incoming calls")
            for call in calls:
                print(f"   - {call.get('call_type')} call from {call.get('caller_name')} (ID: {call.get('call_id')})")
                if call.get('meeting_url'):
                    print(f"     Meeting URL: {call.get('meeting_url')}")
        else:
            print(f"❌ Failed to get incoming calls: {data.get('msg')}")
    except Exception as e:
        print(f"❌ Error testing incoming calls: {e}")
    
    # Test 4: Accept call (if there are calls)
    print("\n✅ Test 4: Accept Call")
    try:
        # First get a call to accept
        response = requests.get(f"{BASE_URL}/call/incoming", params={"user_id": 1})
        data = response.json()
        if data.get("success") and data.get("calls"):
            call_id = data["calls"][0]["call_id"]
            response = requests.post(f"{BASE_URL}/call/accept", json={"call_id": call_id})
            accept_data = response.json()
            if accept_data.get("success"):
                print("✅ Call accepted successfully")
                if accept_data.get('meeting_url'):
                    print(f"   Meeting URL: {accept_data.get('meeting_url')}")
            else:
                print(f"❌ Failed to accept call: {accept_data.get('msg')}")
        else:
            print("ℹ️  No calls to accept")
    except Exception as e:
        print(f"❌ Error testing accept call: {e}")
    
    # Test 5: Reject call
    print("\n❌ Test 5: Reject Call")
    try:
        # Start a new call to reject
        response = requests.post(f"{BASE_URL}/call/start", json={
            "caller_id": 1,
            "receiver_id": 2,
            "call_type": "voice"
        })
        data = response.json()
        if data.get("success"):
            call_id = data.get("call_id")
            response = requests.post(f"{BASE_URL}/call/reject", json={"call_id": call_id})
            reject_data = response.json()
            if reject_data.get("success"):
                print("✅ Call rejected successfully")
            else:
                print(f"❌ Failed to reject call: {reject_data.get('msg')}")
        else:
            print(f"❌ Failed to start call for rejection test: {data.get('msg')}")
    except Exception as e:
        print(f"❌ Error testing reject call: {e}")
    
    # Test 6: Edge cases
    print("\n🛡️ Test 6: Edge Cases")
    
    # Test invalid call type
    try:
        response = requests.post(f"{BASE_URL}/call/start", json={
            "caller_id": 1,
            "receiver_id": 2,
            "call_type": "invalid"
        })
        data = response.json()
        if not data.get("success"):
            print("✅ Invalid call type properly rejected")
        else:
            print("❌ Invalid call type was accepted")
    except Exception as e:
        print(f"❌ Error testing invalid call type: {e}")
    
    # Test calling self
    try:
        response = requests.post(f"{BASE_URL}/call/start", json={
            "caller_id": 1,
            "receiver_id": 1,
            "call_type": "voice"
        })
        data = response.json()
        if not data.get("success"):
            print("✅ Self-call properly rejected")
        else:
            print("❌ Self-call was accepted")
    except Exception as e:
        print(f"❌ Error testing self-call: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Call System Integration Tests Complete!")
    print("✅ All critical functionality tested")

if __name__ == "__main__":
    test_call_system()
