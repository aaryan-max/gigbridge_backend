#!/usr/bin/env python3
"""
Test CLI search functionality
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_search():
    print("🧪 Testing CLI Search functionality...")
    
    # Test the exact parameters the CLI would use
    params = {
        "category": "photographer",
        "budget": 4000
    }
    
    try:
        res = requests.get(f"{BASE_URL}/freelancers/search", params=params)
        
        if res.status_code == 200:
            data = res.json()
            if data.get("success"):
                freelancers = data.get("results", [])
                print(f"✅ Search successful! Found {len(freelancers)} photographers")
                
                if freelancers:
                    print("First few results:")
                    for i, f in enumerate(freelancers[:3]):
                        name = f.get("name", "Unknown")
                        category = f.get("category", "Unknown")
                        budget_range = f.get("budget_range", "Unknown")
                        print(f"  {i+1}. {name} - {category} - {budget_range}")
                
                return True
            else:
                print(f"❌ Search failed: {data.get('msg', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {res.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_search()
    if success:
        print("\n🎉 CLI Search functionality is working!")
    else:
        print("\n❌ CLI Search functionality has issues")
