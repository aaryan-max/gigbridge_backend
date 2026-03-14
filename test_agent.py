#!/usr/bin/env python3
"""
Test script for the new Agentic AI action layer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_actions import parse_natural_language_command, execute_agent_action, resolve_freelancer_name

def test_command_parsing():
    """Test natural language command parsing"""
    print("=== Testing Command Parsing ===")
    
    test_commands = [
        "hire john",
        "message alex hello how are you",
        "call david",
        "save rahul",
        "show my requests",
        "show my messages",
        "show freelancers",
        "invalid command that should not match"
    ]
    
    for cmd in test_commands:
        result = parse_natural_language_command(cmd)
        print(f"'{cmd}' -> {result}")
    
    print()

def test_name_resolution():
    """Test freelancer name resolution"""
    print("=== Testing Name Resolution ===")
    
    test_names = ["john", "alex", "nonexistent"]
    
    for name in test_names:
        freelancer_id = resolve_freelancer_name(name)
        print(f"'{name}' -> ID: {freelancer_id}")
    
    print()

def test_action_execution():
    """Test action execution with mock user"""
    print("=== Testing Action Execution ===")
    
    # Test with a mock client user (user_id=1)
    user_id = 1
    role = "client"
    
    test_actions = [
        ("query_freelancers", {}),
        ("show_my_requests", {}),
        ("show_my_messages", {}),
    ]
    
    for action, params in test_actions:
        try:
            result = execute_agent_action(user_id, role, action, params)
            print(f"Action '{action}' -> {result.get('text', result)[:100]}...")
        except Exception as e:
            print(f"Action '{action}' -> ERROR: {e}")
    
    print()

def test_end_to_end():
    """Test end-to-end flow: parsing -> execution"""
    print("=== Testing End-to-End Flow ===")
    
    user_id = 1
    role = "client"
    
    commands = [
        "show my requests",
        "show my messages", 
        "show freelancers"
    ]
    
    for cmd in commands:
        print(f"\nProcessing: '{cmd}'")
        parsed = parse_natural_language_command(cmd)
        
        if parsed:
            action = parsed.get("action")
            params = parsed.get("parameters", {})
            
            try:
                result = execute_agent_action(user_id, role, action, params)
                print(f"Result: {result.get('text', result)[:100]}...")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("No action parsed - would fall back to AI")

if __name__ == "__main__":
    print("GigBridge Agentic AI Layer - Test Suite")
    print("=" * 50)
    
    test_command_parsing()
    test_name_resolution() 
    test_action_execution()
    test_end_to_end()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
