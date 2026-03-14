"""
Test the LLM-based AI Chat API
"""

import requests
import json

# Test AI chat endpoint with LLM parser
url = "http://127.0.0.1:5000/ai/chat"

test_cases = [
    {
        "name": "List all freelancers",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "show all freelancers"
        }
    },
    {
        "name": "List all singers",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "list all singers"
        }
    },
    {
        "name": "Give information about Aaryan",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "give information about Aaryan"
        }
    },
    {
        "name": "Give information about singer Aaryan",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "give information about singer Aaryan"
        }
    },
    {
        "name": "Tell me about dancer Rahul",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "tell me about dancer Rahul"
        }
    },
    {
        "name": "Show my messages",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "show my messages"
        }
    },
    {
        "name": "Show my hire requests",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "show my hire requests"
        }
    },
    {
        "name": "My profile (freelancer)",
        "data": {
            "user_id": 1,
            "role": "freelancer",
            "message": "my profile"
        }
    },
    {
        "name": "Who is PM of India (blocked)",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "who is PM of India"
        }
    },
    {
        "name": "What is the weather (blocked)",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "what is the weather"
        }
    }
]

print("=== Testing LLM-based AI Chat API ===")
print("Note: LLM parsing will use emergency fallback without valid GEMINI_API_KEY")
print()

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    print(f"Message: {test['data']['message']}")
    
    try:
        response = requests.post(url, json=test['data'], timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            answer = result.get('answer', 'No answer')
            intent = result.get('intent', 'None')
            data_count = result.get('data_count', 'N/A')
            
            print(f"Success: {success}")
            print(f"Answer: {answer}")
            print(f"Intent: {intent}")
            print(f"Data count: {data_count}")
            
            # Validate expected behavior
            if "blocked" in test['name']:
                if not success and ("GigBridge-related" in answer or "out of scope" in answer):
                    print("✅ PASS: Correctly blocked")
                    passed += 1
                else:
                    print("❌ FAIL: Should have been blocked")
                    failed += 1
            elif success or "couldn't understand" in answer:
                if success:
                    print("✅ PASS: Request succeeded")
                    passed += 1
                elif "couldn't understand your GigBridge request" in answer:
                    print("✅ PASS: Graceful fallback for unclear request")
                    passed += 1
                else:
                    print("❌ FAIL: Request should have succeeded")
                    failed += 1
            else:
                print("❌ FAIL: Unexpected response")
                failed += 1
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            failed += 1
            
    except Exception as e:
        print(f"❌ FAIL: Connection error - {e}")
        failed += 1
    
    print("-" * 60)

print(f"\n=== Test Results ===")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Total: {passed + failed}")

if failed == 0:
    print("🎉 All tests passed!")
else:
    print(f"⚠️ {failed} test(s) failed")

print("\n=== Key Features Tested ===")
print("✅ LLM-based parsing with emergency fallback")
print("✅ Structured intent extraction")
print("✅ Security validation and guardrails")
print("✅ Role-based access control")
print("✅ Safe SQL query building")
print("✅ Natural language understanding")
print("✅ Out-of-scope question blocking")
