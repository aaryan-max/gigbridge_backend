#!/usr/bin/env python3

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_freelancer_search():
    """Test freelancer search with category filter"""
    try:
        print("Testing freelancer search with category filter...")
        
        # Test search with category "singer"
        search_data = {
            "category": "singer",
            "budget": 400,
            "client_id": 1
        }
        
        response = requests.get(f"{BASE_URL}/freelancers/search", params=search_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Search successful!")
                results = data.get('results', [])
                print(f"Number of freelancers found: {len(results)}")
                
                for i, freelancer in enumerate(results[:3]):  # Show first 3 results
                    print(f"\n--- Freelancer {i+1} ---")
                    print(f"ID: {freelancer.get('freelancer_id', 'N/A')}")
                    print(f"Name: {freelancer.get('name', 'N/A')}")
                    print(f"Category: {freelancer.get('category', 'N/A')}")
                    print(f"Title: {freelancer.get('title', 'N/A')}")
                    print(f"Budget: {freelancer.get('budget_range', 'N/A')}")
                    print(f"Rating: {freelancer.get('rating', 'N/A')}")
                    print(f"Status: {freelancer.get('availability_status', 'N/A')}")
            else:
                print(f"❌ Search failed: {data.get('msg', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_freelancer_search()
