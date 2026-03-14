import os
import json
import requests
from typing import Dict, Any, List, Tuple

# Initialize Moonshot Kimi API
# Note: The provided key appears to be OpenRouter format. For Moonshot Kimi, 
# you typically need a key that starts with "sk-" from moonshot.cn
# If this is indeed a Moonshot key, we'll proceed, otherwise you may need to get the correct key
api_key = "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"

# Try Moonshot Kimi first, fallback to OpenRouter if needed
moonshot_base_url = "https://api.moonshot.cn/v1"
openrouter_base_url = "https://openrouter.ai/api/v1"

# Determine which API to use based on key format
if api_key.startswith("sk-or-"):
    # OpenRouter key format - use Claude for accuracy since Kimi model name is incorrect
    base_url = openrouter_base_url
    model_name = "anthropic/claude-3-haiku"  # Very accurate and working model
    provider = "openrouter_claude"
else:
    # Moonshot key format
    base_url = moonshot_base_url
    model_name = "moonshot-v1-8k"
    provider = "moonshot_kimi"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# For OpenRouter, we need to ensure proper content-type and add required headers
if provider.startswith("openrouter"):
    headers.update({
        "HTTP-Referer": "https://gigbridge.com",
        "X-Title": "GigBridge"
    })

def call_kimi(prompt: str, user_context: Dict[str, Any] = None) -> str:
    """Call Kimi API with prompt and handle responses"""
    try:
        # Prepare the request payload
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are GigBridge AI Agent. "
                        "You help users with freelancer searches, hiring, and platform management. "
                        "Be helpful, accurate, and conversational. "
                        "For specific freelancer data, guide users to use the search features. "
                        "For general questions about the platform, provide helpful information. "
                        "Always maintain a professional and friendly tone."
                    )
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Make the API call
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract the response text
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            return "I couldn't process that request."
            
    except requests.exceptions.RequestException as e:
        print(f"Kimi API error: {e}")
        
        # Handle API errors with fallback responses
        if user_context:
            # Extract the actual user message from the prompt
            if "User Question:" in prompt:
                message = prompt.split("User Question:")[-1].strip()
            else:
                message = prompt.strip()
            message_lower = message.lower()
            
            # Handle basic queries locally
            if any(greeting in message_lower for greeting in ["hi", "hello", "hey", "hii"]):
                return "Hi! How can I assist you with GigBridge today?"
            elif any(generic in message_lower for generic in ["how are you", "what is gigbridge", "help"]):
                return "I'm your GigBridge AI assistant. I can help you search freelancers, hire talent, and manage your requests. What would you like to do?"
            elif "show" in message_lower and "freelancer" in message_lower:
                return "I can help you find freelancers! Use the search features to browse available talent, or tell me what type of freelancer you're looking for."
            elif "hire" in message_lower:
                return "I can help you hire freelancers! Please specify what type of professional you need, and I'll guide you through the process."
            elif "save" in message_lower and "freelancer" in message_lower:
                return "I can help you save freelancers to your favorites! Browse freelancers first, then let me know which ones you'd like to save."
            else:
                return "I'm currently experiencing connectivity issues. For specific freelancer searches, please use the search features, or try again later."
        else:
            return "I'm having trouble connecting right now. Please try again in a moment."
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "Sorry, I'm having trouble processing your request right now."

def kimi_health() -> Dict[str, str]:
    """Check Kimi API health"""
    try:
        # Simple test call to verify API key works
        test_payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "test"}
            ],
            "max_tokens": 10
        }
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        response.raise_for_status()
        return {"status": "healthy", "provider": provider}
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if "401" in error_msg:
            return {"status": "unauthorized", "provider": provider, "error": "Invalid API key"}
        elif "429" in error_msg:
            return {"status": "quota_exceeded", "provider": provider, "error": "API quota exceeded"}
        else:
            return {"status": "error", "provider": provider, "error": error_msg}
    except Exception as e:
        return {"status": "error", "provider": provider, "error": str(e)}
