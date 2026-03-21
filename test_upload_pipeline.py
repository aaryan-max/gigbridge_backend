#!/usr/bin/env python3
"""
Test script to verify upload pipeline fixes
Tests both CLI file paths and multipart uploads
"""

import requests
import os
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_server_connection():
    """Check if Flask server is running"""
    try:
        response = requests.get(f"{BASE_URL}/freelancers/1", timeout=3)
        return True
    except requests.exceptions.ConnectionError:
        return False
    except:
        return False

def test_freelancer_upload_cli():
    """Test freelancer verification upload with CLI file paths"""
    print("\n=== TESTING FREELANCER CLI UPLOAD ===")
    
    # Use existing test files
    gov_file = "uploads/Picture3_1771346936.png"
    pan_file = "uploads/WhatsApp Image 2025-02-06 at 10.29.15_057006a7_1771348471.jpg"
    
    # Convert to absolute paths
    gov_path = os.path.abspath(gov_file)
    pan_path = os.path.abspath(pan_file)
    
    print(f"Government ID: {gov_path}")
    print(f"PAN Card: {pan_path}")
    
    # Test upload
    try:
        res = requests.post(f"{BASE_URL}/freelancer/verification/upload", json={
            "freelancer_id": 1,
            "government_id_path": gov_path,
            "pan_card_path": pan_path
        })
        
        result = res.json()
        print(f"Status Code: {res.status_code}")
        print(f"Response: {result}")
        
        if result.get("success"):
            print("✅ FREELANCER CLI UPLOAD SUCCESS")
            return True
        else:
            print(f"❌ FREELANCER CLI UPLOAD FAILED: {result.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ FREELANCER CLI UPLOAD ERROR: {str(e)}")
        return False

def test_client_upload_multipart():
    """Test client KYC upload with multipart files"""
    print("\n=== TESTING CLIENT MULTIPART UPLOAD ===")
    
    # Use existing test files
    gov_file = "uploads/Picture3_1771346936.png"
    pan_file = "uploads/WhatsApp Image 2025-02-06 at 10.29.15_057006a7_1771348471.jpg"
    
    print(f"Government ID: {gov_file}")
    print(f"PAN Card: {pan_file}")
    
    try:
        with open(gov_file, 'rb') as gov_f, open(pan_file, 'rb') as pan_f:
            files = {
                'government_id': gov_f,
                'pan_card': pan_f
            }
            data = {
                'client_id': '1'
            }
            
            res = requests.post(f"{BASE_URL}/client/kyc/upload", files=files, data=data)
            
            result = res.json()
            print(f"Status Code: {res.status_code}")
            print(f"Response: {result}")
            
            if result.get("success"):
                print("✅ CLIENT MULTIPART UPLOAD SUCCESS")
                return True
            else:
                print(f"❌ CLIENT MULTIPART UPLOAD FAILED: {result.get('msg')}")
                return False
                
    except Exception as e:
        print(f"❌ CLIENT MULTIPART UPLOAD ERROR: {str(e)}")
        return False

def test_client_upload_cli():
    """Test client KYC upload with CLI file paths"""
    print("\n=== TESTING CLIENT CLI UPLOAD ===")
    
    # Use existing test files
    gov_file = "uploads/Picture3_1771346936.png"
    pan_file = "uploads/WhatsApp Image 2025-02-06 at 10.29.15_057006a7_1771404723.jpg"
    
    # Convert to absolute paths
    gov_path = os.path.abspath(gov_file)
    pan_path = os.path.abspath(pan_file)
    
    print(f"Government ID: {gov_path}")
    print(f"PAN Card: {pan_path}")
    
    try:
        data = {
            'client_id': '1',
            'government_id_path': gov_path,
            'pan_card_path': pan_path
        }
        
        res = requests.post(f"{BASE_URL}/client/kyc/upload", data=data)
        
        result = res.json()
        print(f"Status Code: {res.status_code}")
        print(f"Response: {result}")
        
        if result.get("success"):
            print("✅ CLIENT CLI UPLOAD SUCCESS")
            return True
        else:
            print(f"❌ CLIENT CLI UPLOAD FAILED: {result.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ CLIENT CLI UPLOAD ERROR: {str(e)}")
        return False

def main():
    print("🧪 UPLOAD PIPELINE TEST")
    print("=" * 50)
    
    # Check server connection
    if not test_server_connection():
        print("❌ Server not running! Start the server first:")
        print("   cd gigbridge_backend")
        print("   python app.py")
        return False
    
    print("✅ Server connection OK")
    
    # Run tests
    tests = [
        ("Freelancer CLI Upload", test_freelancer_upload_cli),
        ("Client Multipart Upload", test_client_upload_multipart),
        ("Client CLI Upload", test_client_upload_cli),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL TESTS PASSED! Upload pipeline is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
