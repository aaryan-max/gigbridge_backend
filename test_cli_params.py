#!/usr/bin/env python3
"""
Test CLI search parameter building
"""

import requests

BASE_URL = "http://127.0.0.1:5000"

def test_cli_search():
    print("🧪 Testing CLI Search Parameter Building...")
    
    # Simulate exact CLI parameters
    category = "photographer"  # User input
    budget = 4000.0
    current_client_id = None  # Not logged in
    specialization = "no"  # User input
    
    # Build params exactly like CLI does
    params = {
        "category": category,
        "budget": budget
    }
    if current_client_id:
        params["client_id"] = current_client_id
    if specialization and specialization.strip() and specialization.lower() not in ["no", "none", ""]:
        params["q"] = specialization
    
    print(f"Built params: {params}")
    
    # Test the exact URL
    import urllib.parse
    query_string = urllib.parse.urlencode(params)
    full_url = f"{BASE_URL}/freelancers/search?{query_string}"
    print(f"Full URL: {full_url}")
    
    try:
        res = requests.get(full_url)
        print(f"Status: {res.status_code}")
        data = res.json()
        print(f"Success: {data.get('success')}")
        print(f"Results count: {len(data.get('results', []))}")
        
        if data.get("results"):
            print("First result:")
            f = data["results"][0]
            print(f"  Name: {f.get('name')}")
            print(f"  Category: {f.get('category')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_cli_search()
