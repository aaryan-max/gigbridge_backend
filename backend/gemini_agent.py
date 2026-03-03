import os
import json
import re
from typing import Dict, Any, List, Tuple
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not set in environment")
genai.configure(api_key=api_key)

# Define Gemini model with tools
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    tools=[
        Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="query_freelancers",
                    description="List or filter freelancers",
                    parameters={
                        "type": "object",
                        "properties": {
                            "filters": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "category": {"type": "string"},
                                    "max_budget": {"type": "number"},
                                    "min_budget": {"type": "number"},
                                    "location": {"type": "string"}
                                }
                            }
                        }
                    }
                ),
                FunctionDeclaration(
                    name="hire_freelancer",
                    description="Hire a freelancer by ID",
                    parameters={
                        "type": "object",
                        "properties": {
                            "freelancer_id": {"type": "number"}
                        },
                        "required": ["freelancer_id"]
                    }
                ),
                FunctionDeclaration(
                    name="save_freelancer",
                    description="Save freelancer to client favorites",
                    parameters={
                        "type": "object",
                        "properties": {
                            "freelancer_id": {"type": "number"}
                        }
                    }
                )
            ]
        )
    ],
    system_instruction=(
        "You are GigBridge AI Agent. "
        "CRITICAL: You MUST use tools for ANY query related to: freelancers, hire, save, budget, location, profile, requests. "
        "NEVER generate freelancer data yourself. "
        "NEVER assume database values. "
        "ALWAYS call tools for database-related queries. "
        "Only answer directly for greetings or general platform questions. "
        "If user asks about freelancers, hiring, saving, budgets, locations, profiles, or requests - you MUST use tools."
    )
)

def call_gemini(prompt: str, user_context: Dict[str, Any] = None) -> str:
    """Call Gemini API with prompt and handle tool calls"""
    try:
        response = model.generate_content(prompt)
        
        # Handle function calls
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    return handle_function_call(part.function_call, user_context)
        
        # Return text response
        return response.text if response.text else "I couldn't process that request."
        
    except Exception as e:
        error_msg = str(e)
        print(f"Gemini API error: {e}")
        
        # Check for quota errors
        if "quota" in error_msg.lower() or "429" in error_msg or "leaked" in error_msg.lower():
            # For API errors, try to handle basic queries locally
            if user_context:
                # Extract the actual user message from the prompt
                if "User Question:" in prompt:
                    message = prompt.split("User Question:")[-1].strip()
                else:
                    message = prompt.strip()
                message_lower = message.lower()
                
                # Only handle greetings and very basic questions
                if any(greeting in message_lower for greeting in ["hi", "hello", "hey", "hii"]):
                    return "Hi! How can I assist you with GigBridge today?"
                elif any(generic in message_lower for generic in ["how are you", "what is gigbridge", "help"]):
                    return "I'm your GigBridge AI assistant. I can help you search freelancers, hire talent, and manage your requests. What would you like to do?"
                elif "show" in message_lower and "freelancer" in message_lower:
                    # Try to call the freelancer query function directly
                    try:
                        from llm_chatbot import _handle_query_freelancers
                        result = _handle_query_freelancers({})
                        return result.get("text", "Unable to fetch freelancers at the moment.")
                    except Exception as e:
                        print(f"Local freelancer query error: {e}")
                        return "I'm currently experiencing high demand. Please try again later or use the search endpoints directly."
                elif "hire" in message_lower:
                    return "I can help you hire freelancers! Please specify who you want to hire. Example: 'hire freelancer John' or provide their ID."
                elif "save" in message_lower and "freelancer" in message_lower:
                    return "I can help you save freelancers to your favorites! Please specify which freelancer. Example: 'save freelancer John' or provide their ID."
                else:
                    return "I'm currently experiencing high demand. For freelancer searches, hiring, or account-specific questions, please try again later or use the search endpoints directly."
            else:
                return "I'm currently experiencing high demand. Please try again later."
        
        return "Sorry, I'm having trouble connecting to my AI services right now."

def handle_function_call(function_call: Any, user_context: Dict[str, Any] = None) -> str:
    """Handle Gemini function calls by calling existing Flask logic"""
    from llm_chatbot import (
        _handle_query_freelancers,
        _handle_hire_freelancer,
        _handle_save_freelancer
    )
    
    func_name = function_call.name
    args = function_call.args
    user_id = user_context.get("user_id") if user_context else None
    role = user_context.get("role") if user_context else None
    
    try:
        if func_name == "query_freelancers":
            filters = args.get("filters", {})
            result = _handle_query_freelancers(filters)
            return result.get("text", "No freelancers found.")
            
        elif func_name == "hire_freelancer":
            freelancer_id = args.get("freelancer_id")
            result = _handle_hire_freelancer(user_id, {"freelancer_id": freelancer_id})
            return result.get("text", "Hire action failed.")
            
        elif func_name == "save_freelancer":
            freelancer_id = args.get("freelancer_id")
            result = _handle_save_freelancer(user_id, {"freelancer_id": freelancer_id})
            return result.get("text", "Save action failed.")
            
        else:
            return f"Unknown function: {func_name}"
            
    except Exception as e:
        print(f"Function call error: {e}")
        return f"Error executing {func_name}: {str(e)}"

def gemini_health() -> Dict[str, str]:
    """Check Gemini API health"""
    try:
        # Simple test call to verify API key works
        response = model.generate_content("test")
        return {"status": "healthy", "provider": "gemini"}
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            return {"status": "quota_exceeded", "provider": "gemini", "error": "API quota exceeded - please check billing"}
        return {"status": "error", "provider": "gemini", "error": error_msg}
