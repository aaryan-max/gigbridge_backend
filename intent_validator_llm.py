"""
Intent Validator for LLM-based GigBridge AI Chat
Validates structured intent from LLM parser against security and business rules
"""

from typing import Dict, List
from categories import get_all_categories, is_valid_category

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

# Valid sort options
VALID_SORT_OPTIONS = [
    "name_asc", "name_desc", "rating_desc", "rating_asc",
    "budget_asc", "budget_desc", "experience_desc", "created_at_desc"
]

# Allowed table names (for security)
ALLOWED_TABLES = [
    "freelancer", "freelancer_profile", "client", "client_profile",
    "hire_request", "message", "portfolio", "notification"
]

# Allowed actions (only SELECT for security)
ALLOWED_ACTIONS = ["SELECT"]


class LLMIntentValidator:
    """Validates LLM-parsed intents against security and business rules"""
    
    def __init__(self):
        self.allowed_intents = ALLOWED_INTENTS
        self.valid_categories = VALID_CATEGORIES
        self.valid_sort_options = VALID_SORT_OPTIONS
        self.allowed_tables = ALLOWED_TABLES
        self.allowed_actions = ALLOWED_ACTIONS
    
    def validate(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """
        Validate parsed intent against security and business rules
        
        Args:
            parsed_intent: Structured intent from LLM parser
            role: User role (client/freelancer)
            user_id: Current user ID
            
        Returns:
            Dict with validation result
        """
        if not parsed_intent:
            return {
                "valid": False,
                "reason": "Invalid intent structure"
            }
        
        # Check for out of scope
        if parsed_intent.get("intent") == "out_of_scope":
            return {
                "valid": False,
                "reason": "I can only answer GigBridge-related questions about freelancers, clients, projects, hire requests, reviews, portfolio, and messages."
            }
        
        # Validate intent
        intent = parsed_intent.get("intent")
        if not intent or intent not in self.allowed_intents:
            return {
                "valid": False,
                "reason": f"Intent '{intent}' is not supported"
            }
        
        # Validate role-based access
        role_validation = self._validate_role_access(intent, role)
        if not role_validation["valid"]:
            return role_validation
        
        # Validate filters
        filter_validation = self._validate_filters(parsed_intent.get("filters", {}), role, user_id)
        if not filter_validation["valid"]:
            return filter_validation
        
        # Validate sort option
        sort = parsed_intent.get("sort")
        if sort and sort not in self.valid_sort_options:
            return {
                "valid": False,
                "reason": f"Sort option '{sort}' is not valid"
            }
        
        # Validate limit
        limit = parsed_intent.get("limit", 50)
        try:
            limit_int = int(limit)
            if limit_int <= 0 or limit_int > 100:
                return {
                    "valid": False,
                    "reason": "Limit must be between 1 and 100"
                }
        except (ValueError, TypeError):
            return {
                "valid": False,
                "reason": "Invalid limit value"
            }
        
        return {"valid": True}
    
    def _validate_role_access(self, intent: str, role: str) -> Dict:
        """Validate if role can access the intent"""
        # Client-only intents
        client_intents = [
            "client_hire_requests",
            "client_messages", 
            "client_projects"
        ]
        
        # Freelancer-only intents
        freelancer_intents = [
            "freelancer_hire_requests",
            "freelancer_messages",
            "freelancer_profile"
        ]
        
        # Shared intents (both roles can access)
        shared_intents = [
            "list_freelancers",
            "freelancer_detail",
            "freelancer_reviews", 
            "freelancer_portfolio"
        ]
        
        if intent in client_intents and role != "client":
            return {
                "valid": False,
                "reason": "This action is only available for clients"
            }
        
        if intent in freelancer_intents and role != "freelancer":
            return {
                "valid": False,
                "reason": "This action is only available for freelancers"
            }
        
        if intent not in shared_intents and intent not in client_intents and intent not in freelancer_intents:
            return {
                "valid": False,
                "reason": f"Intent '{intent}' is not recognized"
            }
        
        return {"valid": True}
    
    def _validate_filters(self, filters: Dict, role: str, user_id: int) -> Dict:
        """Validate filter parameters"""
        if not isinstance(filters, dict):
            return {
                "valid": False,
                "reason": "Invalid filters structure"
            }
        
        # Validate category filter
        if "category" in filters:
            category = filters["category"]
            if category and not is_valid_category(str(category)):
                return {
                    "valid": False,
                    "reason": f"Category '{category}' is not valid. Valid categories: {', '.join(self.valid_categories[:5])}..."
                }
        
        # Validate budget filters
        for budget_field in ["budget_min", "budget_max"]:
            if budget_field in filters:
                try:
                    budget = float(filters[budget_field])
                    if budget < 0:
                        return {
                            "valid": False,
                            "reason": f"{budget_field} cannot be negative"
                        }
                except (ValueError, TypeError):
                    return {
                        "valid": False,
                        "reason": f"Invalid {budget_field} value"
                    }
        
        # Validate budget range logic
        if "budget_min" in filters and "budget_max" in filters:
            try:
                min_budget = float(filters["budget_min"])
                max_budget = float(filters["budget_max"])
                if min_budget > max_budget:
                    return {
                        "valid": False,
                        "reason": "Minimum budget cannot be greater than maximum budget"
                    }
            except (ValueError, TypeError):
                pass
        
        # Validate boolean filters
        for bool_filter in ["verified_only", "subscribed_only", "top_rated"]:
            if bool_filter in filters:
                if not isinstance(filters[bool_filter], bool):
                    return {
                        "valid": False,
                        "reason": f"{bool_filter} must be true or false"
                    }
        
        # Validate user-specific filters
        if "user_id" in filters:
            user_filter = filters["user_id"]
            try:
                user_filter_int = int(user_filter)
                if user_filter_int != user_id:
                    return {
                        "valid": False,
                        "reason": "User ID mismatch"
                    }
            except (ValueError, TypeError):
                return {
                    "valid": False,
                    "reason": "Invalid user ID"
                }
        
        return {"valid": True}
