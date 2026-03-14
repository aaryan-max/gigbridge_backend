"""
Test the AI Chat API endpoint
"""

import json
import requests


def test_ai_chat_endpoint():
    """Test the /ai/chat endpoint with various requests"""
    base_url = "http://127.0.0.1:5000"
    
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
            "name": "List verified singers",
            "data": {
                "user_id": 1,
                "role": "client", 
                "message": "show verified singers"
            }
        },
        {
            "name": "Show client projects",
            "data": {
                "user_id": 1,
                "role": "client",
                "message": "show my projects"
            }
        },
        {
            "name": "Show freelancer profile",
            "data": {
                "user_id": 1,
                "role": "freelancer",
                "message": "my profile"
            }
        },
        {
            "name": "Blocked question",
            "data": {
                "user_id": 1,
                "role": "client",
                "message": "who is PM of India"
            }
        },
        {
            "name": "Invalid request - missing fields",
            "data": {
                "user_id": 1,
                "message": "show freelancers"
            }
        }
    ]
    
    print("=== Testing AI Chat API Endpoint ===")
    print("Make sure the Flask server is running on http://127.0.0.1:5000")
    print()
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        print(f"Request: {json.dumps(test_case['data'], indent=2)}")
        
        try:
            response = requests.post(
                f"{base_url}/ai/chat",
                json=test_case['data'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to server. Make sure Flask app is running.")
        except requests.exceptions.Timeout:
            print("ERROR: Request timed out.")
        except Exception as e:
            print(f"ERROR: {str(e)}")
        
        print("-" * 50)


if __name__ == "__main__":
    test_ai_chat_endpoint()
