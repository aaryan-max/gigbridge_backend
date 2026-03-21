import requests

BASE_URL = "http://localhost:5000"

def test_client_jobs_api():
    """Test the actual API response for client jobs"""
    try:
        res = requests.get(f"{BASE_URL}/client/jobs", params={
            "client_id": 1
        })
        
        print(f"Status Code: {res.status_code}")
        print(f"Response Headers: {dict(res.headers)}")
        
        data = res.json()
        print(f"\nRaw Response: {data}")
        print(f"\nResponse Type: {type(data)}")
        
        if isinstance(data, list):
            print(f"\nNumber of jobs: {len(data)}")
            for i, job in enumerate(data, 1):
                print(f"\nJob {i}:")
                print(f"  Keys: {list(job.keys()) if isinstance(job, dict) else 'Not a dict'}")
                if isinstance(job, dict):
                    for key, value in job.items():
                        print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_client_jobs_api()
