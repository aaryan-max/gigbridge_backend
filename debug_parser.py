"""
Debug the LLM parser for specific failing cases
"""

import os
os.environ["GEMINI_API_KEY"] = "test-key-placeholder"

from intent_parser_llm import LLMIntentParser
from intent_validator_llm import LLMIntentValidator

def debug_specific_cases():
    """Debug specific failing test cases"""
    parser = LLMIntentParser()
    validator = LLMIntentValidator()
    
    failing_cases = [
        {"message": "tell me about dancer Rahul", "user_id": 1, "role": "client"},
        {"message": "show my messages", "user_id": 1, "role": "client"},
        {"message": "show my hire requests", "user_id": 1, "role": "client"},
    ]
    
    print("=== Debugging Failing Cases ===")
    
    for test in failing_cases:
        print(f"\nMessage: {test['message']}")
        
        # Test emergency fallback directly
        fallback = parser.emergency_fallback(test['message'])
        print(f"Emergency fallback: {fallback}")
        
        if fallback:
            # Test validation
            validation = validator.validate(fallback, test['role'], test['user_id'])
            print(f"Validation: {validation}")
        else:
            print("No fallback found")

if __name__ == "__main__":
    debug_specific_cases()
