import requests
import json

# Test the AI chat endpoint
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
        "name": "Blocked question",
        "data": {
            "user_id": 1,
            "role": "client",
            "message": "who is PM of India"
        }
    }
]

print("=== Testing AI Chat API ===")

for test in test_cases:
    print(f"\nTesting: {test['name']}")
    print(f"Message: {test['data']['message']}")
    
    try:
        response = requests.post(url, json=test['data'], timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Answer: {result.get('answer')}")
            print(f"Intent: {result.get('intent')}")
            print(f"Data count: {result.get('data_count')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Connection error: {e}")

print("\n=== Test Complete ===")
