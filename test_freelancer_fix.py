#!/usr/bin/env python3
"""
Simple test for freelancer upload validation fix
"""

import requests
import os

BASE_URL = "http://127.0.0.1:5000"

def test_freelancer_upload():
    """Test freelancer verification upload with PNG file"""
    print("=== TESTING FREELANCER UPLOAD FIX ===")
    
    # Use existing PNG file
    gov_file = os.path.abspath("uploads/Picture3_1771346936.png")
    pan_file = os.path.abspath("uploads/WhatsApp Image 2025-02-06 at 10.29.15_057006a7_1771348471.jpg")
    
    print(f"Government ID (PNG): {gov_file}")
    print(f"PAN Card (JPG): {pan_file}")
    
    try:
        res = requests.post(f"{BASE_URL}/freelancer/verification/upload", json={
            "freelancer_id": 1,
            "government_id_path": gov_file,
            "pan_card_path": pan_file
        })
        
        result = res.json()
        print(f"Status Code: {res.status_code}")
        print(f"Response: {result}")
        
        if result.get("success"):
            print("✅ FREELANCER UPLOAD SUCCESS - PNG file accepted!")
            return True
        else:
            print(f"❌ FREELANCER UPLOAD FAILED: {result.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_freelancer_upload()
