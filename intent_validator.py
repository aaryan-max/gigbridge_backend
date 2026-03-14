"""
Intent Validator for AI Chat Module
Validates parsed intents and ensures they meet security and business rules
"""

from typing import Dict
from categories import is_valid_category


class IntentValidator:
    def __init__(self):
        self.allowed_intents = {
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
        }
        
        self.role_intents = {
            "client": {
                "list_freelancers",
                "freelancer_detail",
                "freelancer_reviews", 
                "freelancer_portfolio",
                "client_hire_requests",
                "client_messages",
                "client_projects"
            },
            "freelancer": {
                "list_freelancers",
                "freelancer_detail",
                "freelancer_reviews",
                "freelancer_portfolio", 
                "freelancer_hire_requests",
                "freelancer_messages",
                "freelancer_profile"
            }
        }
    
    def validate(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """Validate parsed intent against rules"""
        try:
            # Check if intent is allowed
            if parsed_intent.get("intent") not in self.allowed_intents:
                return {
                    "valid": False,
                    "reason": "This type of question is not supported."
                }
            
            # Check if intent is allowed for this role
            if role not in self.role_intents:
                return {
                    "valid": False,
                    "reason": "Invalid user role."
                }
            
            if parsed_intent["intent"] not in self.role_intents[role]:
                return {
                    "valid": False,
                    "reason": f"This question is not available for {role}s."
                }
            
            # Validate user_id
            if not isinstance(user_id, int) or user_id <= 0:
                return {
                    "valid": False,
                    "reason": "Invalid user ID."
                }
            
            # Validate category if present
            if parsed_intent.get("category"):
                if not is_valid_category(parsed_intent["category"]):
                    return {
                        "valid": False,
                        "reason": f"'{parsed_intent['category']}' is not a valid category."
                    }
            
            # Validate budget filters
            if parsed_intent.get("budget_min") is not None:
                if not isinstance(parsed_intent["budget_min"], (int, float)) or parsed_intent["budget_min"] < 0:
                    return {
                        "valid": False,
                        "reason": "Invalid minimum budget value."
                    }
            
            if parsed_intent.get("budget_max") is not None:
                if not isinstance(parsed_intent["budget_max"], (int, float)) or parsed_intent["budget_max"] < 0:
                    return {
                        "valid": False,
                        "reason": "Invalid maximum budget value."
                    }
            
            # Check budget range logic
            if (parsed_intent.get("budget_min") is not None and 
                parsed_intent.get("budget_max") is not None):
                if parsed_intent["budget_min"] > parsed_intent["budget_max"]:
                    return {
                        "valid": False,
                        "reason": "Minimum budget cannot be greater than maximum budget."
                    }
            
            # Validate sort_by
            valid_sort_options = {
                "name_asc", "name_desc", 
                "rating_asc", "rating_desc",
                "budget_asc", "budget_desc",
                "experience_asc", "experience_desc"
            }
            
            if parsed_intent.get("sort_by") and parsed_intent["sort_by"] not in valid_sort_options:
                return {
                    "valid": False,
                    "reason": "Invalid sort option."
                }
            
            # Additional validation for specific intents
            intent_specific_result = self._validate_intent_specific(parsed_intent, role)
            if not intent_specific_result["valid"]:
                return intent_specific_result
            
            return {"valid": True}
            
        except Exception as e:
            print(f"Error in intent validation: {str(e)}")
            return {
                "valid": False,
                "reason": "Validation error occurred."
            }
    
    def _validate_intent_specific(self, parsed_intent: Dict, role: str) -> Dict:
        """Validate intent-specific requirements"""
        intent = parsed_intent["intent"]
        
        # For freelancer detail, reviews, and portfolio, name is required
        if intent in ["freelancer_detail", "freelancer_reviews", "freelancer_portfolio"]:
            if not parsed_intent.get("name"):
                return {
                    "valid": False,
                    "reason": "Please specify a freelancer name for this request."
                }
        
        # For client-specific queries, ensure user is client
        if intent in ["client_hire_requests", "client_messages", "client_projects"]:
            if role != "client":
                return {
                    "valid": False,
                    "reason": "This query is only available for clients."
                }
        
        # For freelancer-specific queries, ensure user is freelancer
        if intent in ["freelancer_hire_requests", "freelancer_messages", "freelancer_profile"]:
            if role != "freelancer":
                return {
                    "valid": False,
                    "reason": "This query is only available for freelancers."
                }
        
        return {"valid": True}
