#!/usr/bin/env python3
"""
Test script for age validation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import calculate_age, validate_age

def test_age_calculation():
    """Test age calculation function"""
    print("=== Testing Age Calculation ===")
    
    test_cases = [
        ("2000-01-01", "current year - 2000"),
        ("1990-12-31", "current year - 1990 (adjust if birthday hasn't passed)"),
        ("2005-06-15", "current year - 2005"),
        ("invalid-date", None),
    ]
    
    for dob, expected in test_cases:
        age = calculate_age(dob)
        print(f"DOB: {dob} -> Age: {age} (Expected: {expected})")

def test_age_validation():
    """Test age validation function"""
    print("\n=== Testing Age Validation ===")
    
    test_cases = [
        (17, False, "User must be at least 18 years old."),
        (18, True, None),
        (25, True, None),
        (60, True, None),
        (61, False, "Maximum allowed age is 60 years."),
    ]
    
    for age, expected_valid, expected_msg in test_cases:
        is_valid, msg = validate_age(age)
        print(f"Age: {age} -> Valid: {is_valid}, Msg: {msg}")
        assert is_valid == expected_valid, f"Expected {expected_valid}, got {is_valid}"
        assert msg == expected_msg, f"Expected '{expected_msg}', got '{msg}'"

def test_edge_cases():
    """Test edge cases"""
    print("\n=== Testing Edge Cases ===")
    
    # Test boundary ages
    assert validate_age(18)[0] == True, "Age 18 should be valid"
    assert validate_age(60)[0] == True, "Age 60 should be valid"
    assert validate_age(17)[0] == False, "Age 17 should be invalid"
    assert validate_age(61)[0] == False, "Age 61 should be invalid"
    
    print("✅ All edge cases passed!")

if __name__ == "__main__":
    test_age_calculation()
    test_age_validation()
    test_edge_cases()
    print("\n🎉 All tests passed!")
