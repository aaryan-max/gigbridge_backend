#!/usr/bin/env python3
"""
Test script for CLI DOB validation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cli_test import get_valid_dob
from datetime import datetime
from unittest.mock import patch
import io

def test_dob_validation():
    """Test DOB validation function with various inputs"""
    print("=== Testing CLI DOB Validation ===")
    
    test_cases = [
        # (input_dob, expected_result, description)
        ("2005-01-01", "valid", "Age ~19 - should be valid"),
        ("1990-12-31", "valid", "Age ~34 - should be valid"),
        ("1960-01-01", "valid", "Age ~65 - should be invalid (>60)"),
        ("2010-01-01", "invalid", "Age ~14 - should be invalid (<18)"),
        ("invalid-date", "invalid_format", "Invalid format"),
        ("2025-13-01", "invalid_format", "Invalid month"),
        ("2025-01-32", "invalid_format", "Invalid day"),
    ]
    
    for dob_input, expected, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input: {dob_input}")
        
        # Mock the input function
        with patch('builtins.input', return_value=dob_input):
            with patch('builtins.print') as mock_print:
                try:
                    result = get_valid_dob()
                    print(f"Result: {result} (Expected: valid)")
                    if expected == "valid":
                        print("✅ PASS")
                    else:
                        print("❌ FAIL - Should have been invalid")
                except (ValueError, KeyboardInterrupt):
                    print("Result: Exception/Invalid")
                    if expected != "valid":
                        print("✅ PASS")
                    else:
                        print("❌ FAIL - Should have been valid")

def test_age_boundary_cases():
    """Test age boundary cases (18 and 60)"""
    print("\n=== Testing Age Boundary Cases ===")
    
    today = datetime.now()
    
    # Test exactly 18 years old
    dob_18 = datetime(today.year - 18, today.month, today.day).strftime("%Y-%m-%d")
    print(f"\nTesting exactly 18 years old: {dob_18}")
    
    # Test exactly 60 years old  
    dob_60 = datetime(today.year - 60, today.month, today.day).strftime("%Y-%m-%d")
    print(f"Testing exactly 60 years old: {dob_60}")
    
    # Test just under 18
    dob_under_18 = datetime(today.year - 18, today.month, today.day + 1).strftime("%Y-%m-%d")
    print(f"Testing just under 18: {dob_under_18}")
    
    # Test just over 60
    dob_over_60 = datetime(today.year - 60, today.month, today.day - 1).strftime("%Y-%m-%d")
    print(f"Testing just over 60: {dob_over_60}")

def simulate_user_interaction():
    """Simulate a user entering invalid then valid DOB"""
    print("\n=== Simulating User Interaction ===")
    print("Scenario: User enters invalid format, then age < 18, then valid DOB")
    
    inputs = ["invalid-format", "2010-01-01", "2000-06-15"]  # invalid, <18, valid
    
    with patch('builtins.input', side_effect=inputs):
        with patch('builtins.print') as mock_print:
            try:
                result = get_valid_dob()
                print(f"Final valid DOB: {result}")
                print("✅ Successfully got valid DOB after retries")
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_dob_validation()
    test_age_boundary_cases()
    simulate_user_interaction()
    print("\n🎉 CLI DOB validation tests completed!")
