#!/usr/bin/env python3
"""
Test script for enhanced Agentic AI action layer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_actions import parse_natural_language_command, execute_agent_action, resolve_freelancer_name

def test_enhanced_parsing():
    """Test enhanced natural language command parsing"""
    print("=== Testing Enhanced Command Parsing ===")
    
    test_commands = [
        "hire john",
        "hire john with budget 300",
        "hire freelancer john with my proposed budget 300",
        "message alex hello how are you",
        "call david",
        "save rahul",
        "accept request 4",
        "reject request 4",
        "show my requests",
        "show my messages",
        "show freelancers",
        "give me his location",
        "what is his budget",
        "give me his experience",
        "invalid command that should not match"
    ]
    
    for cmd in test_commands:
        result = parse_natural_language_command(cmd)
        print(f"'{cmd}' -> {result}")
    
    print()

def test_memory_functionality():
    """Test conversation memory functionality"""
    print("=== Testing Memory Functionality ===")
    
    user_id = 1
    role = "client"
    
    # Simulate sequence: show freelancers, then ask for info
    commands = [
        "show freelancers",
        "give me his location",
        "what is his budget"
    ]
    
    for cmd in commands:
        print(f"\nProcessing: '{cmd}'")
        parsed = parse_natural_language_command(cmd)
        
        if parsed:
            action_name = parsed.get("action")
            action_params = parsed.get("parameters", {})
            
            try:
                result = execute_agent_action(user_id, role, action_name, action_params)
                print(f"Result: {result.get('text', result)[:100]}...")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("No action parsed - would fall back to AI")

def test_budget_support():
    """Test budget support in hire commands"""
    print("\n=== Testing Budget Support ===")
    
    user_id = 1
    role = "client"
    
    budget_commands = [
        "hire john with budget 500",
        "hire freelancer alex with my proposed budget 750",
        "hire sarah"  # No budget
    ]
    
    for cmd in budget_commands:
        print(f"\nProcessing: '{cmd}'")
        parsed = parse_natural_language_command(cmd)
        
        if parsed:
            action_name = parsed.get("action")
            action_params = parsed.get("parameters", {})
            print(f"Parsed: {action_name} with params: {action_params}")
        else:
            print("No action parsed")

def test_request_handling():
    """Test accept/reject request functionality"""
    print("\n=== Testing Request Handling ===")
    
    user_id = 1
    role = "freelancer"  # Test as freelancer
    
    request_commands = [
        "accept request 4",
        "reject request 5"
    ]
    
    for cmd in request_commands:
        print(f"\nProcessing: '{cmd}'")
        parsed = parse_natural_language_command(cmd)
        
        if parsed:
            action_name = parsed.get("action")
            action_params = parsed.get("parameters", {})
            print(f"Parsed: {action_name} with params: {action_params}")
        else:
            print("No action parsed")

if __name__ == "__main__":
    print("GigBridge Enhanced Agentic AI Layer - Test Suite")
    print("=" * 60)
    
    test_enhanced_parsing()
    test_memory_functionality()
    test_budget_support()
    test_request_handling()
    
    print("\n" + "=" * 60)
    print("Enhanced test suite completed!")
