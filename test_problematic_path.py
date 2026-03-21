#!/usr/bin/env python3
"""
Test the exact file path that's failing
"""

import requests
import os

BASE_URL = "http://127.0.0.1:5000"

def test_problematic_path():
    """Test with the exact path that's failing"""
    print("=== TESTING PROBLEMATIC PATH ===")
    
    # Use the exact path from the error
    gov_file = '"C:\\Users\\Sarthak Sawant\\Pictures\\Screenshots\\Screenshot 2025-08-06 140745.png"'
    pan_file = '"C:\\Users\\Sarthak Sawant\\Pictures\\Screenshots\\Screenshot 2025-08-06 140745.png"'
    artist_file = '"C:\\Users\\Sarthak Sawant\\Pictures\\Screenshots\\Screenshot 2025-08-06 140745.png"'
    
    print(f"Government ID: {gov_file}")
    print(f"PAN Card: {pan_file}")
    print(f"Artist Proof: {artist_file}")
    
    # Test path processing
    def validate_file_extension(file_path):
        """Validate file extension using exact method from requirements"""
        # 1. CLEAN FILE PATH INPUT
        cleaned_path = file_path.strip().strip('"').strip("'").strip()
        print(f"DEBUG CLEAN PATH: {cleaned_path}")
        
        # 2. EXTRACT FILE NAME
        import os
        filename = os.path.basename(cleaned_path)
        print(f"DEBUG FILENAME: {filename}")
        
        # 3. EXTRACT EXTENSION PROPERLY
        ext = filename.split(".")[-1].lower()
        print(f"DEBUG EXT: {ext}")
        
        # 4. VALIDATE FILE TYPE
        if ext not in ["jpg", "jpeg", "png", "pdf"]:
            return False, ext
        
        return True, ext
    
    # Test validation manually
    print("\n--- MANUAL VALIDATION TEST ---")
    gov_valid, gov_ext = validate_file_extension(gov_file)
    print(f"Government ID - Valid: {gov_valid}, Ext: {gov_ext}")
    
    try:
        res = requests.post(f"{BASE_URL}/freelancer/verification/upload", json={
            "freelancer_id": 1,
            "government_id_path": gov_file,
            "pan_card_path": pan_file,
            "artist_proof_path": artist_file
        })
        
        result = res.json()
        print(f"\nStatus Code: {res.status_code}")
        print(f"Response: {result}")
        
        if result.get("success"):
            print("✅ FREELANCER UPLOAD SUCCESS!")
            return True
        else:
            print(f"❌ FREELANCER UPLOAD FAILED: {result.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_problematic_path()
