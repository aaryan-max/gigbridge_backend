"""
Test script for AI Chat Module
Tests various intents and edge cases
"""

import json
from intent_parser import IntentParser
from intent_validator import IntentValidator
from query_builder import QueryBuilder
from query_executor import QueryExecutor
from response_formatter import ResponseFormatter
from ai_guardrails import AIGuardrails


def test_intent_parser():
    """Test intent parsing with various queries"""
    print("=== Testing Intent Parser ===")
    parser = IntentParser()
    
    test_queries = [
        "show all freelancers",
        "list verified singers in Mumbai",
        "show top rated photographers",
        "give info about singer Aaryan",
        "show reviews of Aaryan",
        "show portfolio of Aaryan",
        "show my hire requests",
        "show my messages",
        "show my posted projects",
        "my profile",
        "who is PM of India",  # Should not match
        "what is the weather"  # Should not match
    ]
    
    for query in test_queries:
        result = parser.parse(query)
        print(f"Query: '{query}'")
        if result:
            print(f"  Intent: {result['intent']}")
            print(f"  Category: {result['category']}")
            print(f"  Name: {result['name']}")
            print(f"  Location: {result['location']}")
            print(f"  Verified: {result['verified_only']}")
        else:
            print("  No intent matched")
        print()


def test_guardrails():
    """Test AI guardrails"""
    print("=== Testing AI Guardrails ===")
    guardrails = AIGuardrails()
    
    test_messages = [
        "show all freelancers",  # Allowed
        "list verified singers",  # Allowed
        "who is PM of India",  # Blocked
        "what is the weather",  # Blocked
        "tell me a joke",  # Blocked
        "show my projects",  # Allowed
        "my profile",  # Allowed
    ]
    
    for message in test_messages:
        result = guardrails.check_message(message)
        print(f"Message: '{message}'")
        print(f"  Allowed: {result['allowed']}")
        if not result['allowed']:
            print(f"  Reason: {result['reason']}")
        print()


def test_query_builder():
    """Test query building"""
    print("=== Testing Query Builder ===")
    builder = QueryBuilder()
    
    test_intents = [
        {
            "intent": "list_freelancers",
            "category": "Singer",
            "location": "Mumbai",
            "verified_only": True,
            "sort_by": "rating_desc"
        },
        {
            "intent": "freelancer_detail",
            "name": "Aaryan"
        }
    ]
    
    for intent in test_intents:
        result = builder.build_query(intent, "client", 1)
        print(f"Intent: {intent['intent']}")
        if result['success']:
            print(f"  Query: {result['query']}")
            print(f"  Params: {result['params']}")
            print(f"  DB: {result['db']}")
        else:
            print(f"  Error: {result['error']}")
        print()


def test_response_formatter():
    """Test response formatting"""
    print("=== Testing Response Formatter ===")
    formatter = ResponseFormatter()
    
    # Test list freelancers
    test_data = [
        {"name": "Aaryan", "category": "Singer", "location": "Mumbai", "verified": True},
        {"name": "Priya", "category": "Dancer", "location": "Delhi", "verified": False}
    ]
    
    result = formatter.format_response("list_freelancers", test_data, "show singers")
    print(f"List freelancers response: {result['answer']}")
    print(f"Data count: {result['data_count']}")
    
    # Test empty results
    empty_result = formatter.format_response("list_freelancers", [], "show singers")
    print(f"Empty response: {empty_result['answer']}")
    print()


def test_end_to_end():
    """Test end-to-end flow"""
    print("=== Testing End-to-End Flow ===")
    
    # Initialize components
    guardrails = AIGuardrails()
    parser = IntentParser()
    validator = IntentValidator()
    builder = QueryBuilder()
    
    test_cases = [
        {
            "message": "show verified singers in Mumbai",
            "role": "client",
            "user_id": 1
        },
        {
            "message": "who is PM of India",
            "role": "client", 
            "user_id": 1
        }
    ]
    
    for case in test_cases:
        print(f"Testing: {case['message']}")
        
        # Step 1: Guardrails
        guardrails_result = guardrails.check_message(case['message'])
        if not guardrails_result['allowed']:
            print(f"  Blocked by guardrails: {guardrails_result['reason']}")
            continue
        
        # Step 2: Parse intent
        parsed_intent = parser.parse(case['message'])
        if not parsed_intent:
            print("  No intent matched")
            continue
        
        print(f"  Parsed intent: {parsed_intent['intent']}")
        
        # Step 3: Validate
        validation_result = validator.validate(parsed_intent, case['role'], case['user_id'])
        if not validation_result['valid']:
            print(f"  Validation failed: {validation_result['reason']}")
            continue
        
        # Step 4: Build query
        query_result = builder.build_query(parsed_intent, case['role'], case['user_id'])
        if not query_result['success']:
            print(f"  Query building failed: {query_result['error']}")
            continue
        
        print(f"  Query built successfully")
        print()


if __name__ == "__main__":
    test_intent_parser()
    test_guardrails()
    test_query_builder()
    test_response_formatter()
    test_end_to_end()
    print("All tests completed!")
