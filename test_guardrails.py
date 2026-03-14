"""
Test guardrails for specific failing cases
"""

from ai_guardrails import AIGuardrails

def test_guardrails():
    """Test guardrails on failing cases"""
    guardrails = AIGuardrails()
    
    test_messages = [
        "tell me about dancer Rahul",
        "show my messages", 
        "show my hire requests"
    ]
    
    print("=== Testing Guardrails ===")
    
    for message in test_messages:
        result = guardrails.check_message(message)
        print(f"Message: {message}")
        print(f"Allowed: {result['allowed']}")
        if not result['allowed']:
            print(f"Reason: {result['reason']}")
        print("-" * 40)

if __name__ == "__main__":
    test_guardrails()
