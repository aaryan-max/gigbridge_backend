#!/usr/bin/env python3
"""
Test freelancer upload with invalid file type
"""

import requests
import os

BASE_URL = "http://127.0.0.1:5000"

def test_freelancer_upload_invalid():
    """Test freelancer verification upload with invalid file type"""
    print("=== TESTING FREELANCER UPLOAD WITH INVALID FILE TYPE ===")
    
    # Use a non-image file (test.py)
    invalid_file = os.path.abspath("test_freelancer_fix.py")
    valid_file = os.path.abspath("uploads/Picture3_1771346936.png")
    
    print(f"Invalid file (.py): {invalid_file}")
    print(f"Valid file (.png): {valid_file}")
    
    try:
        res = requests.post(f"{BASE_URL}/freelancer/verification/upload", json={
            "freelancer_id": 1,
            "government_id_path": invalid_file,  # Invalid
            "pan_card_path": valid_file          # Valid
        })
        
        result = res.json()
        print(f"Status Code: {res.status_code}")
        print(f"Response: {result}")
        
        if res.status_code == 400 and not result.get("success"):
            print("✅ VALIDATION WORKING - Invalid file type rejected correctly!")
            print(f"   Message: {result.get('msg')}")
            return True
        else:
            print(f"❌ VALIDATION ISSUE: Expected 400 status with failure")
            print(f"   Got: Status {res.status_code}, Success: {result.get('success')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_freelancer_upload_invalid()
