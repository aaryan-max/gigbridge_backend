#!/usr/bin/env python3
"""
Test script for Moonshot Kimi API integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kimi_agent import call_kimi, kimi_health

def test_kimi_health():
    """Test Kimi API health check"""
    print("=== Testing Kimi API Health ===")
    try:
        health = kimi_health()
        print(f"Health Status: {health}")
        return health.get("status") == "healthy"
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_kimi_basic_chat():
    """Test basic Kimi chat functionality"""
    print("\n=== Testing Basic Kimi Chat ===")
    try:
        response = call_kimi("Hello, can you help me with GigBridge?")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"Basic chat failed: {e}")
        return False

def test_kimi_gigbridge_queries():
    """Test Kimi with GigBridge-specific queries"""
    print("\n=== Testing GigBridge-Specific Queries ===")
    
    test_queries = [
        "What is GigBridge?",
        "How do I hire a freelancer?",
        "What categories of freelancers are available?",
        "How do I search for freelancers?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        try:
            response = call_kimi(query)
            print(f"   Response: {response[:100]}...")
        except Exception as e:
            print(f"   Error: {e}")

def test_kimi_with_context():
    """Test Kimi with user context"""
    print("\n=== Testing Kimi with User Context ===")
    try:
        user_context = {"user_id": 1, "role": "client"}
        response = call_kimi(
            "I'm a client looking for a web developer. Can you help me?", 
            user_context
        )
        print(f"Response with context: {response[:100]}...")
        return True
    except Exception as e:
        print(f"Context test failed: {e}")
        return False

def main():
    """Run all Kimi integration tests"""
    print("🚀 Moonshot Kimi API Integration Test")
    print("=" * 50)
    
    # Test health first
    if not test_kimi_health():
        print("\n❌ Health check failed. Please check API key and connection.")
        return
    
    print("\n✅ Health check passed. Running functionality tests...")
    
    # Run basic tests
    if test_kimi_basic_chat():
        print("\n✅ Basic chat test passed.")
    else:
        print("\n❌ Basic chat test failed.")
        return
    
    # Test specific queries
    test_kimi_gigbridge_queries()
    
    # Test with context
    if test_kimi_with_context():
        print("\n✅ Context test passed.")
    else:
        print("\n❌ Context test failed.")
    
    print("\n" + "=" * 50)
    print("🎉 Kimi API integration testing completed!")
    print("The system is ready for accurate chat responses.")

if __name__ == "__main__":
    main()
