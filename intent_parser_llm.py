"""
LLM-based Intent Parser for GigBridge AI Chat
Uses Gemini AI to parse natural language into structured intent and parameters
"""

import os
import json
import re
from typing import Dict, Optional, List
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Import existing category validation
from categories import get_all_categories, is_valid_category

# Configure Gemini if available
if genai:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

# Get valid categories from existing codebase
VALID_CATEGORIES = get_all_categories()

# Allowed intents for security
ALLOWED_INTENTS = [
    "list_freelancers",
    "freelancer_detail", 
    "freelancer_reviews",
    "freelancer_portfolio",
    "client_hire_requests",
    "client_messages",
    "client_projects",
    "freelancer_hire_requests", 
    "freelancer_messages",
    "freelancer_profile"
]

SYSTEM_PROMPT = f"""
You are an intent parser for GigBridge, a freelancer marketplace platform.

Parse user natural language queries into structured JSON with these fields:
- intent: The primary action the user wants to perform
- entity_type: What the user is asking about (freelancer, client, project, etc.)
- filters: Dictionary of filter conditions
- sort: How to sort results (name_asc, name_desc, rating_desc, etc.)
- limit: Maximum number of results to return

Allowed intents: {json.dumps(ALLOWED_INTENTS)}

Valid categories for freelancers: {json.dumps(VALID_CATEGORIES)}

Common filters:
- category: freelancer category (must be from valid categories list)
- name: freelancer name (partial match)
- location: geographic location
- verified_only: boolean for verified freelancers
- subscribed_only: boolean for subscribed freelancers  
- top_rated: boolean for high-rated freelancers (rating >= 4.0)
- budget_min: minimum budget
- budget_max: maximum budget
- user_id: for user-specific queries

Rules:
1. Return ONLY valid JSON, no explanations
2. Only use intents from the allowed list
3. Only use categories from the valid categories list
4. For user-specific queries ("my messages", "my profile"), include user_id in filters
5. For general questions about freelancers, use "list_freelancers" intent
6. For specific freelancer info, use "freelancer_detail" intent
7. Never generate SQL or answer questions directly
8. If query is outside GigBridge scope, return {{"intent": "out_of_scope"}}

Examples:

User: "show all freelancers"
Output: {{"intent": "list_freelancers", "entity_type": "freelancer", "filters": {{}}, "sort": "name_asc", "limit": 50}}

User: "list all singers"  
Output: {{"intent": "list_freelancers", "entity_type": "freelancer", "filters": {{"category": "Singer"}}, "sort": "name_asc", "limit": 50}}

User: "give information about Aaryan"
Output: {{"intent": "freelancer_detail", "entity_type": "freelancer", "filters": {{"name": "Aaryan"}}, "sort": null, "limit": 1}}

User: "give information about singer Aaryan"
Output: {{"intent": "freelancer_detail", "entity_type": "freelancer", "filters": {{"name": "Aaryan", "category": "Singer"}}, "sort": null, "limit": 1}}

User: "tell me about dancer Rahul"
Output: {{"intent": "freelancer_detail", "entity_type": "freelancer", "filters": {{"name": "Rahul", "category": "Dancer"}}, "sort": null, "limit": 1}}

User: "show my messages"
Output: {{"intent": "client_messages", "entity_type": "message", "filters": {{"user_id": "USER_ID_PLACEHOLDER"}}, "sort": "created_at_desc", "limit": 50}}

User: "show my hire requests"
Output: {{"intent": "client_hire_requests", "entity_type": "hire_request", "filters": {{"user_id": "USER_ID_PLACEHOLDER"}}, "sort": "created_at_desc", "limit": 50}}

User: "who is PM of India"
Output: {{"intent": "out_of_scope", "entity_type": null, "filters": {{}}, "sort": null, "limit": null}}

User: "what is the weather"
Output: {{"intent": "out_of_scope", "entity_type": null, "filters": {{}}, "sort": null, "limit": null}}
"""


class LLMIntentParser:
    """LLM-based intent parser for natural language queries"""
    
    def __init__(self):
        self.model = model
        self.system_prompt = SYSTEM_PROMPT
    
    def parse(self, message: str, user_id: int = None, role: str = None) -> Optional[Dict]:
        """
        Parse user message using LLM and return structured intent
        
        Args:
            message: User's natural language query
            user_id: Current user ID (for context)
            role: User role (client/freelancer)
            
        Returns:
            Structured intent dictionary or None if parsing fails
        """
        if not message or not message.strip():
            return None
            
        try:
            # Check if model is available
            if not self.model:
                print("Gemini model not available")
                return None
                
            # Check if API key is available
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("GEMINI_API_KEY environment variable not found")
                return None
            
            # Prepare user-specific prompt
            user_prompt = self.system_prompt
            if user_id and role:
                # Replace placeholder with actual user_id for user-specific queries
                user_prompt = user_prompt.replace("USER_ID_PLACEHOLDER", str(user_id))
            
            # Generate response
            response = self.model.generate_content(
                user_prompt + "\n\nUser query:\n'" + message + "'\n\nOutput:"
            )
            
            # Extract and parse JSON response
            response_text = response.text.strip()
            
            # Clean up response text
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON
            parsed = json.loads(response_text)
            
            # Validate and clean the parsed intent
            return self._validate_and_clean_intent(parsed, message)
            
        except Exception as e:
            print(f"Error parsing query with LLM: {e}")
            return None
    
    def _validate_and_clean_intent(self, parsed: Dict, original_message: str) -> Optional[Dict]:
        """Validate and clean the parsed intent"""
        if not parsed or not isinstance(parsed, dict):
            return None
        
        # Check if intent is out of scope
        if parsed.get("intent") == "out_of_scope":
            return {"intent": "out_of_scope"}
        
        # Validate intent
        intent = parsed.get("intent")
        if not intent or intent not in ALLOWED_INTENTS:
            return None
        
        # Build clean result
        result = {
            "intent": intent,
            "entity_type": parsed.get("entity_type"),
            "filters": {},
            "sort": parsed.get("sort"),
            "limit": parsed.get("limit", 50)
        }
        
        # Validate and clean filters
        filters = parsed.get("filters", {})
        if isinstance(filters, dict):
            # Category filter
            if "category" in filters:
                category = filters["category"]
                if category and is_valid_category(str(category)):
                    result["filters"]["category"] = category
            
            # Name filter
            if "name" in filters:
                name = filters["name"]
                if name:
                    result["filters"]["name"] = str(name)
            
            # Location filter
            if "location" in filters:
                location = filters["location"]
                if location:
                    result["filters"]["location"] = str(location).title()
            
            # Boolean filters
            for bool_filter in ["verified_only", "subscribed_only", "top_rated"]:
                if bool_filter in filters:
                    result["filters"][bool_filter] = bool(filters[bool_filter])
            
            # Budget filters
            if "budget_min" in filters:
                try:
                    budget_min = float(filters["budget_min"])
                    result["filters"]["budget_min"] = budget_min
                except (ValueError, TypeError):
                    pass
            
            if "budget_max" in filters:
                try:
                    budget_max = float(filters["budget_max"])
                    result["filters"]["budget_max"] = budget_max
                except (ValueError, TypeError):
                    pass
            
            # User ID filter
            if "user_id" in filters:
                result["filters"]["user_id"] = filters["user_id"]
        
        # Validate sort
        valid_sorts = ["name_asc", "name_desc", "rating_desc", "rating_asc", 
                      "budget_asc", "budget_desc", "experience_desc", "created_at_desc"]
        if result["sort"] and result["sort"] not in valid_sorts:
            result["sort"] = "name_asc"  # Default sort
        
        # Validate limit
        try:
            limit = int(result["limit"])
            if limit <= 0 or limit > 100:
                result["limit"] = 50  # Default limit
            else:
                result["limit"] = limit
        except (ValueError, TypeError):
            result["limit"] = 50
        
        return result
    
    def emergency_fallback(self, message: str) -> Optional[Dict]:
        """Minimal emergency fallback for when LLM fails"""
        message_lower = message.lower().strip()
        
        # Basic pattern matching as last resort
        if "freelancer" in message_lower and ("all" in message_lower or "list" in message_lower or "show" in message_lower):
            return {"intent": "list_freelancers", "entity_type": "freelancer", "filters": {}, "sort": "name_asc", "limit": 50}
        
        # Handle category-based queries
        if "singer" in message_lower or "singers" in message_lower:
            if "all" in message_lower or "list" in message_lower or "show" in message_lower:
                return {"intent": "list_freelancers", "entity_type": "freelancer", "filters": {"category": "Singer"}, "sort": "name_asc", "limit": 50}
        
        if "dancer" in message_lower or "dancers" in message_lower:
            if "all" in message_lower or "list" in message_lower or "show" in message_lower:
                return {"intent": "list_freelancers", "entity_type": "freelancer", "filters": {"category": "Dancer"}, "sort": "name_asc", "limit": 50}
        
        # Handle "information about" patterns
        if "information about" in message_lower or "info about" in message_lower or "tell me about" in message_lower or "give me about" in message_lower:
            # Extract name and category
            words = message_lower.split()
            name_idx = -1
            category = None
            name_parts = []
            
            for i, word in enumerate(words):
                if word in ["about", "of"] and i + 1 < len(words):
                    name_idx = i + 1
                    break
            
            if name_idx >= 0:
                # Look for category and name in the remaining words
                remaining_words = words[name_idx:]
                
                for word in remaining_words:
                    if word in ["singer", "singers", "dancer", "dancers", "photographer", "photographers"]:
                        category = word.capitalize() if not word.endswith('s') else word[:-1].capitalize()
                    elif word not in ["singer", "singers", "dancer", "dancers", "photographer", "photographers"]:
                        name_parts.append(word.capitalize())
                
                if name_parts:
                    name = " ".join(name_parts)
                    filters = {"name": name}
                    if category:
                        filters["category"] = category
                    
                    return {
                        "intent": "freelancer_detail", 
                        "entity_type": "freelancer", 
                        "filters": filters, 
                        "sort": None, 
                        "limit": 1
                    }
        
        # Handle "give information about [name]" pattern
        if "give information about" in message_lower:
            parts = message_lower.split("give information about")
            if len(parts) > 1:
                name_part = parts[1].strip()
                # Check if it contains a category
                if "singer" in name_part:
                    return {
                        "intent": "freelancer_detail", 
                        "entity_type": "freelancer", 
                        "filters": {"name": name_part.replace("singer", "").strip(), "category": "Singer"}, 
                        "sort": None, 
                        "limit": 1
                    }
                elif "dancer" in name_part:
                    return {
                        "intent": "freelancer_detail", 
                        "entity_type": "freelancer", 
                        "filters": {"name": name_part.replace("dancer", "").strip(), "category": "Dancer"}, 
                        "sort": None, 
                        "limit": 1
                    }
                else:
                    name = name_part.strip().capitalize()
                    return {
                        "intent": "freelancer_detail", 
                        "entity_type": "freelancer", 
                        "filters": {"name": name}, 
                        "sort": None, 
                        "limit": 1
                    }
        
        # User-specific queries
        if "my profile" in message_lower:
            return {"intent": "freelancer_profile", "entity_type": "freelancer", "filters": {}, "sort": None, "limit": 1}
        
        if "my messages" in message_lower:
            return {"intent": "client_messages", "entity_type": "message", "filters": {}, "sort": "created_at_desc", "limit": 50}
        
        if "my hire requests" in message_lower:
            return {"intent": "client_hire_requests", "entity_type": "hire_request", "filters": {}, "sort": "created_at_desc", "limit": 50}
        
        return None
