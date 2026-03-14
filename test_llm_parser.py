"""
Test the LLM-based Intent Parser
"""

import os
import sys

# Set a dummy API key for testing (you'll need to set real GEMINI_API_KEY)
os.environ["GEMINI_API_KEY"] = "test-key-placeholder"

from intent_parser_llm import LLMIntentParser
from intent_validator_llm import LLMIntentValidator


def test_llm_parser():
    """Test LLM-based intent parser"""
    parser = LLMIntentParser()
    validator = LLMIntentValidator()
    
    test_cases = [
        # Basic freelancer queries
        {"message": "show all freelancers", "user_id": 1, "role": "client"},
        {"message": "list all singers", "user_id": 1, "role": "client"},
        {"message": "give information about Aaryan", "user_id": 1, "role": "client"},
        {"message": "give information about singer Aaryan", "user_id": 1, "role": "client"},
        {"message": "tell me about dancer Rahul", "user_id": 1, "role": "client"},
        
        # User-specific queries
        {"message": "show my messages", "user_id": 1, "role": "client"},
        {"message": "show my hire requests", "user_id": 1, "role": "client"},
        {"message": "my profile", "user_id": 1, "role": "freelancer"},
        
        # Out of scope queries
        {"message": "who is PM of India", "user_id": 1, "role": "client"},
        {"message": "what is the weather", "user_id": 1, "role": "client"},
        
        # Edge cases
        {"message": "", "user_id": 1, "role": "client"},
        {"message": "   ", "user_id": 1, "role": "client"},
    ]
    
    print("=== Testing LLM-based Intent Parser ===")
    print("Note: This requires GEMINI_API_KEY environment variable to be set")
    print()
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['message']}")
        
        if not test['message'].strip():
            print("  Result: Empty message - should return None")
            print()
            continue
        
        try:
            # Parse intent
            parsed = parser.parse(test['message'], test['user_id'], test['role'])
            
            if parsed is None:
                print("  Result: Parsing failed (returned None)")
                print("  Expected: Emergency fallback or graceful failure")
            else:
                print(f"  Parsed Intent: {parsed.get('intent')}")
                print(f"  Entity Type: {parsed.get('entity_type')}")
                print(f"  Filters: {parsed.get('filters')}")
                print(f"  Sort: {parsed.get('sort')}")
                print(f"  Limit: {parsed.get('limit')}")
                
                # Validate
                validation = validator.validate(parsed, test['role'], test['user_id'])
                print(f"  Validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
                if not validation['valid']:
                    print(f"  Reason: {validation['reason']}")
            
        except Exception as e:
            print(f"  Error: {type(e).__name__}: {str(e)}")
        
        print("-" * 60)


def test_emergency_fallback():
    """Test emergency fallback functionality"""
    parser = LLMIntentParser()
    
    print("\n=== Testing Emergency Fallback ===")
    
    test_cases = [
        "show all freelancers",
        "my profile", 
        "my messages",
        "my hire requests",
        "invalid query that should fail"
    ]
    
    for message in test_cases:
        print(f"Message: {message}")
        fallback = parser.emergency_fallback(message)
        print(f"Fallback: {fallback}")
        print("-" * 40)


if __name__ == "__main__":
    test_llm_parser()
    test_emergency_fallback()
