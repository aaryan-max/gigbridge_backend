#!/usr/bin/env python3
"""
Demo script to showcase the new Agentic AI action layer
This simulates the CLI interaction without requiring the server to be running
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_chatbot import generate_ai_response

def demo_agent_actions():
    """Demo the new agentic AI action layer"""
    
    print("=" * 60)
    print("GigBridge Agentic AI Layer - Demo")
    print("=" * 60)
    print()
    
    # Mock user setup
    user_id = 1
    role = "client"
    
    print(f"Mock User: {role} (ID: {user_id})")
    print()
    
    # Test commands that should trigger agent actions
    demo_commands = [
        "hi",
        "show my requests", 
        "show my messages",
        "show freelancers",
        "hire john",
        "save alex",
        "message alex hello how are you?",
        "call david",
        "what is the weather today?",  # Should fall back to AI
        "help me find a developer"
    ]
    
    for i, command in enumerate(demo_commands, 1):
        print(f"{i}. User: {command}")
        print("-" * 40)
        
        try:
            response = generate_ai_response(user_id, role, command)
            
            if response.get("type") == "action":
                # This was handled by our agent layer
                result_text = response.get("text", "No response")
                print(f"   Agent Action: {result_text}")
            else:
                # This fell through to the regular AI
                answer = response.get("text", "No response")
                print(f"   AI Response: {answer}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        print()

if __name__ == "__main__":
    demo_agent_actions()
