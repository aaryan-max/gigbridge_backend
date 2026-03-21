import requests
import json

BASE_URL = "http://localhost:5000"

def test_client_jobs_endpoint():
    """Test the actual client jobs endpoint"""
    try:
        print("Testing /client/jobs endpoint...")
        res = requests.get(f"{BASE_URL}/client/jobs", params={
            "client_id": 1
        }, timeout=5)
        
        print(f"Status Code: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            print(f"Response type: {type(data)}")
            print(f"Number of jobs: {len(data) if isinstance(data, list) else 'N/A'}")
            
            if isinstance(data, list) and data:
                print("\nSample job data:")
                for i, job in enumerate(data[:2], 1):
                    print(f"\nJob {i}:")
                    for key, value in job.items():
                        print(f"  {key}: {value}")
            else:
                print(f"Raw response: {data}")
        else:
            print(f"Error response: {res.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Please start the server first with: python app.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_client_jobs_endpoint()
