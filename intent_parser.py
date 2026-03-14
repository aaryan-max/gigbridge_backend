"""
Intent Parser for AI Chat Module
Extracts user intent and parameters from natural language questions
"""

import re
from typing import Dict, Optional, List
from categories import is_valid_category, VALID_CATEGORIES


class IntentParser:
    def __init__(self):
        self.intent_patterns = {
            "list_freelancers": [
                r"^(?:show|list|get|find)\s+(?:all\s+)?(?:verified\s+)?(?:subscribed\s+)?(?:top\s+rated\s+)?freelancers?$",
                r"^(?:show|list|get|find)\s+(?:all\s+)?(?:verified\s+)?(?:subscribed\s+)?(?:top\s+rated\s+)?(.+?)(?:s|artists?)$",
                r"^(?:show|list|get|find)\s+(?:all\s+)?(?:verified\s+)?(?:subscribed\s+)?(?:top\s+rated\s+)?(.+?)\s+(?:in|from)\s+(.+?)$"
            ],
            "freelancer_detail": [
                r"^(?:show|give|tell)\s+(?:info|details?)\s+(?:about\s+)?(.+)$",
                r"^(.+?)\s+(?:profile|details?|info)$",
                r"^show\s+(.+?)\s+profile$"
            ],
            "freelancer_reviews": [
                r"^(?:show|list|get)\s+(?:reviews?|ratings?)\s+(?:of|for)\s+(.+)$",
                r"^(.+?)\s+(?:reviews?|ratings?)$"
            ],
            "freelancer_portfolio": [
                r"^(?:show|list|get)\s+(?:portfolio|work|projects?)\s+(?:of|for)\s+(.+)$",
                r"^(.+?)\s+(?:portfolio|work|projects?)$"
            ],
            "client_hire_requests": [
                r"^show\s+my\s+hire\s+requests?$",
                r"^list\s+my\s+hire\s+requests?$",
                r"^my\s+hire\s+requests?$"
            ],
            "client_messages": [
                r"^show\s+my\s+messages?$",
                r"^list\s+my\s+messages?$",
                r"^my\s+messages?$"
            ],
            "client_projects": [
                r"^show\s+my\s+projects?$",
                r"^list\s+my\s+projects?$",
                r"^my\s+projects?$",
                r"^show\s+my\s+posted\s+projects?$"
            ],
            "freelancer_hire_requests": [
                r"^show\s+my\s+(?:incoming\s+)?hire\s+requests?$",
                r"^list\s+my\s+(?:incoming\s+)?hire\s+requests?$",
                r"^my\s+(?:incoming\s+)?hire\s+requests?$"
            ],
            "freelancer_messages": [
                r"^show\s+my\s+messages?$",
                r"^list\s+my\s+messages?$",
                r"^my\s+messages?$"
            ],
            "freelancer_profile": [
                r"^show\s+my\s+profile$",
                r"^my\s+profile$",
                r"^my\s+freelancer\s+profile$"
            ]
        }
        
        self.filter_patterns = {
            "verified": r"\bverified\b",
            "subscribed": r"\bsubscribed\b",
            "top_rated": r"\btop\s+rated\b",
            "location": r"\b(?:in|at|from)\s+([A-Za-z\s]+?)(?:\s+(?:for|with|$))",
            "budget_min": r"\bbudget\s+(?:over|above|min|minimum)\s+(\d+)",
            "budget_max": r"\bbudget\s+(?:under|below|max|maximum)\s+(\d+)",
            "sort_by": r"\bsort\s+by\s+(\w+)"
        }
    
    def parse(self, message: str) -> Optional[Dict]:
        """Parse user message and extract intent and parameters"""
        if not message or not message.strip():
            return None
            
        message_lower = message.lower().strip()
        
        # Try to match intent patterns - check specific patterns first
        # Order matters: more specific patterns should come first
        pattern_order = [
            "client_hire_requests",
            "client_messages", 
            "client_projects",
            "freelancer_hire_requests",
            "freelancer_messages",
            "freelancer_profile",
            "freelancer_reviews",
            "freelancer_portfolio",
            "freelancer_detail",
            "list_freelancers"
        ]
        
        for intent in pattern_order:
            if intent not in self.intent_patterns:
                continue
                
            for pattern in self.intent_patterns[intent]:
                match = re.search(pattern, message_lower)
                if match:
                    result = {
                        "intent": intent,
                        "category": None,
                        "name": None,
                        "location": None,
                        "verified_only": False,
                        "subscribed_only": False,
                        "top_rated": False,
                        "budget_min": None,
                        "budget_max": None,
                        "sort_by": None
                    }
                    
                    # Extract category or name from match groups
                    if match.groups():
                        groups = match.groups()
                        
                        if intent == "list_freelancers":
                            # Handle list_freelancers patterns
                            if len(groups) >= 2:
                                # Pattern: show category in location
                                extracted_category = groups[0].strip() if groups[0] else None
                                extracted_location = groups[1].strip() if groups[1] else None
                                
                                if extracted_category and is_valid_category(extracted_category):
                                    result["category"] = extracted_category
                                elif extracted_category:
                                    result["name"] = extracted_category
                                    
                                if extracted_location:
                                    result["location"] = extracted_location.title()
                            elif len(groups) == 1:
                                # Pattern: show category
                                extracted_text = groups[0].strip()
                                if extracted_text and is_valid_category(extracted_text):
                                    result["category"] = extracted_text
                                else:
                                    result["name"] = extracted_text
                        else:
                            # For other intents, use first group as name
                            if groups[0]:
                                extracted_text = groups[0].strip()
                                # Check if it's a valid category for freelancer_detail
                                if intent == "freelancer_detail" and is_valid_category(extracted_text):
                                    result["category"] = extracted_text
                                else:
                                    result["name"] = extracted_text
                    
                    # Extract additional filters
                    self._extract_filters(message_lower, result)
                    
                    # Set sorting defaults
                    if not result["sort_by"]:
                        if result["top_rated"]:
                            result["sort_by"] = "rating_desc"
                        else:
                            result["sort_by"] = "name_asc"
                    
                    return result
        
        return None
    
    def _extract_filters(self, message: str, result: Dict):
        """Extract filters from message"""
        # Verified filter
        if re.search(self.filter_patterns["verified"], message):
            result["verified_only"] = True
        
        # Subscribed filter
        if re.search(self.filter_patterns["subscribed"], message):
            result["subscribed_only"] = True
        
        # Top rated filter
        if re.search(self.filter_patterns["top_rated"], message):
            result["top_rated"] = True
        
        # Location filter
        location_match = re.search(self.filter_patterns["location"], message)
        if location_match:
            location = location_match.group(1).strip()
            if location and len(location) > 1:
                result["location"] = location.title()
        
        # Budget filters
        budget_min_match = re.search(self.filter_patterns["budget_min"], message)
        if budget_min_match:
            try:
                result["budget_min"] = int(budget_min_match.group(1))
            except ValueError:
                pass
        
        budget_max_match = re.search(self.filter_patterns["budget_max"], message)
        if budget_max_match:
            try:
                result["budget_max"] = int(budget_max_match.group(1))
            except ValueError:
                pass
        
        # Sort by filter
        sort_match = re.search(self.filter_patterns["sort_by"], message)
        if sort_match:
            sort_field = sort_match.group(1).lower()
            if sort_field in ["rating", "name", "budget", "experience"]:
                if sort_field == "rating":
                    result["sort_by"] = "rating_desc"
                elif sort_field == "name":
                    result["sort_by"] = "name_asc"
                elif sort_field == "budget":
                    result["sort_by"] = "budget_asc"
                elif sort_field == "experience":
                    result["sort_by"] = "experience_desc"
