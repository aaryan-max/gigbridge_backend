import requests
import json

# Test the AI chat endpoint with comprehensive scenarios
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
        "name": "List singers",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "show singers"
        }
    },
    {
        "name": "List top rated freelancers",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "show top rated freelancers"
        }
    },
    {
        "name": "Freelancer detail",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "give info about Aaryan"
        }
    },
    {
        "name": "Freelancer in location",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "show singers in Mumbai"
        }
    },
    {
        "name": "Client projects",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "show my projects"
        }
    },
    {
        "name": "Freelancer profile",
        "data": {
            "user_id": 1,
            "role": "freelancer",
            "message": "my profile"
        }
    },
    {
        "name": "Blocked - weather",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "what is the weather today"
        }
    },
    {
        "name": "Blocked - politics",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "who is the prime minister"
        }
    },
    {
        "name": "Invalid request - missing role",
        "data": {
            "user_id": 1,
            "message": "show freelancers"
        }
    }
]

print("=== Comprehensive AI Chat API Test ===\n")

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    print(f"Message: {test['data'].get('message', 'N/A')}")
    
    try:
        response = requests.post(url, json=test['data'], timeout=5)
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
            if "Blocked" in test['name']:
                if not success and "GigBridge-related" in answer:
                    print("✅ PASS: Correctly blocked")
                    passed += 1
                else:
                    print("❌ FAIL: Should have been blocked")
                    failed += 1
            elif "Invalid" in test['name']:
                if not success:
                    print("✅ PASS: Correctly rejected invalid request")
                    passed += 1
                else:
                    print("❌ FAIL: Should have rejected invalid request")
                    failed += 1
            else:
                if success:
                    print("✅ PASS: Request succeeded")
                    passed += 1
                else:
                    print("❌ FAIL: Request should have succeeded")
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

    