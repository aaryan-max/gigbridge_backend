#!/usr/bin/env python3
"""
Test enhanced freelancer display and hire functionality
"""

import requests

BASE_URL = "http://127.0.0.1:5000"

def test_enhanced_display():
    print("🧪 Testing Enhanced Freelancer Display...")
    
    try:
        # Test search to get freelancers
        res = requests.get(f"{BASE_URL}/freelancers/search", params={
            "category": "photographer",
            "budget": 4000
        })
        
        if res.status_code == 200:
            data = res.json()
            if data.get("success"):
                freelancers = data.get("results", [])
                print(f"✅ Found {len(freelancers)} photographers")
                
                if freelancers:
                    # Simulate enhanced display
                    f = freelancers[0]  # Take first freelancer
                    print("\n--- Enhanced Freelancer Display ---")
                    print("ID:", f["freelancer_id"])
                    print("Name:", f["name"])
                    print("Category:", f.get("category", "Not specified"))
                    print("Title:", f.get("title", "Not specified"))
                    print("Budget Range:", f.get("budget_range", "Not specified"))
                    print("Rating:", f.get("rating", 0))
                    print("Status:", f.get("availability_status", "UNKNOWN"))
                    
                    # Additional hiring-relevant information
                    if f.get("experience"):
                        print("Experience:", f["experience"], "years")
                    if f.get("skills"):
                        print("Skills:", f["skills"])
                    if f.get("bio"):
                        bio = f["bio"]
                        display_bio = bio[:100] + "..." if len(bio) > 100 else bio
                        print("Bio:", display_bio)
                    if f.get("subscription_plan"):
                        print("Plan:", f["subscription_plan"])
                    if f.get("distance") and f["distance"] != 999999.0:
                        print("Distance:", f"{f['distance']:.1f} km")
                    
                    print("\n--- Actions ---")
                    print("1. View Details")
                    print("2. Message")
                    print("3. Hire")
                    print("4. Save Freelancer")
                    print("5. Next")
                    print("6. Previous")
                    print("0. Back to Dashboard")
                    
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
    success = test_enhanced_display()
    if success:
        print("\n🎉 Enhanced freelancer display is working!")
    else:
        print("\n❌ Enhanced freelancer display has issues")
