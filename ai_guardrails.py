"""
AI Guardrails for Chat Module
Ensures questions are restricted to GigBridge domain only
"""

import re
from typing import Dict, List


class AIGuardrails:
    def __init__(self):
        # Keywords that indicate GigBridge-related questions
        self.gigbridge_keywords = {
            # Core entities
            "freelancer", "freelancers", "artist", "artists",
            "client", "clients", "customer", "customers",
            "project", "projects", "job", "jobs", "work", "works",
            "hire", "hiring", "hire requests", "applications",
            "message", "messages", "chat", "chats",
            "review", "reviews", "rating", "ratings",
            "portfolio", "portfolios", "work", "portfolio items",
            "profile", "profiles", "bio", "bios",
            
            # Categories
            "photographer", "videographer", "dj", "singer", "dancer",
            "anchor", "makeup artist", "mehendi artist", "decorator",
            "wedding planner", "choreographer", "band", "live music",
            "magician", "entertainer", "event organizer",
            
            # Actions
            "show", "list", "get", "find", "search", "display",
            "my", "me", "i", "my profile", "my projects", "my messages",
            
            # Attributes
            "verified", "subscribed", "top rated", "rating", "budget",
            "location", "experience", "skills", "category", "categories"
        }
        
        # Keywords that indicate non-GigBridge questions
        self.blocked_keywords = {
            # General knowledge
            "weather", "temperature", "forecast", "climate",
            "news", "politics", "government", "election", "prime minister", "president",
            "sports", "cricket", "football", "tennis", "olympics",
            "movies", "films", "music", "songs", "books",
            "history", "geography", "science", "mathematics", "technology",
            "stock market", "shares", "investment", "crypto", "bitcoin",
            
            # Personal questions
            "who are you", "what is your name", "how old are you",
            "where do you live", "what do you do", "tell me about yourself",
            
            # Time/date
            "what time", "what date", "today", "tomorrow", "yesterday",
            "current time", "current date",
            
            # Jokes/entertainment
            "joke", "funny", "humor", "story", "poem",
            
            # General web queries
            "search the web", "google", "internet", "website"
        }
        
        # GigBridge-specific patterns
        self.gigbridge_patterns = [
            r'\b(?:show|list|get|find)\s+(?:my\s+)?(?:freelancers?|artists?|projects?|messages?|profile|reviews?|portfolio|work|hire\s+requests?)\b',
            r'\b(?:my\s+)?(?:freelancers?|artists?|projects?|messages?|profile|reviews?|portfolio|work|hire\s+requests?)\b',
            r'\b(?:verified|subscribed|top\s+rated)\s+(?:freelancers?|artists?)\b',
            r'\b(?:photographer|videographer|dj|singer|dancer|anchor|makeup\s+artist|mehendi\s+artist|decorator|wedding\s+planner|choreographer|band|live\s+music|magician|entertainer|event\s+organizer)\b',
            r'\bgigbridge\b'
        ]
        
        # Blocked patterns
        self.blocked_patterns = [
            r'\b(?:who\s+is|what\s+is|where\s+is|when\s+is|how\s+(?:much|many|to|do|does|did|are|is|was|were))\s+(?!my|your)\b',
            r'\b(?:tell\s+me|explain|describe)\s+(?:about|the)\s+(?!my|your)\b',
            r'\b(?:weather|news|politics|sports|movies|music|books|history|science|math|technology|stock|investment|crypto|bitcoin)\b',
            r'\b(?:joke|funny|humor|story|poem)\b',
            r'\b(?:what\s+time|what\s+date|current\s+time|current\s+date|today|tomorrow|yesterday)\b'
        ]
    
    def check_message(self, message: str) -> Dict:
        """Check if message is within allowed scope"""
        if not message or not message.strip():
            return {"allowed": False, "reason": "Empty message"}
        
        message_lower = message.lower().strip()
        
        # Check for GigBridge-related keywords first
        gigbridge_keywords = [
            "freelancer", "freelancers", "client", "project", "projects",
            "hire", "request", "requests", "message", "messages",
            "profile", "portfolio", "review", "reviews", "rating",
            "singer", "singers", "dancer", "dancers", "photographer",
            "photographers", "dj", "videographer", "videographers"
        ]
        
        has_gigbridge_keyword = any(keyword in message_lower for keyword in gigbridge_keywords)
        
        # Check for user-specific indicators
        user_specific_indicators = ["my profile", "my messages", "my hire requests", "my projects"]
        has_user_specific = any(indicator in message_lower for indicator in user_specific_indicators)
        
        # Check for action words that indicate GigBridge intent
        gigbridge_actions = ["show", "list", "get", "find", "give", "tell", "search"]
        has_gigbridge_action = any(action in message_lower for action in gigbridge_actions)
        
        # Special case: allow "give information about" if it looks like freelancer inquiry
        if "give information about" in message_lower or "tell me about" in message_lower:
            return {"allowed": True}
        
        # Allow if it has GigBridge keywords and user-specific indicators
        if has_gigbridge_keyword and (has_user_specific or has_gigbridge_action):
            return {"allowed": True}
        
        # Check for blocked patterns (more specific now)
        blocked_patterns = [
            r"who\s+is\s+(?:the\s+)?(?:president|prime minister|pm|governor)",
            r"what\s+(?:is|was|will\s+be)\s+(?:the\s+)?(?:weather|temperature|time|date)",
            r"tell\s+me\s+(?:a\s+)?(?:joke|story|fact)",
            r"what\s+(?:is|are)\s+(?:the\s+)?(?:news|stock|crypto|bitcoin)",
            r"how\s+(?:to|do|can\s+i)\s+(?:cook|learn|make|build|create)",
            r"translate\s+.+",
            r"define\s+.+",
            r"meaning\s+of\s+.+"
        ]
        
        for pattern in blocked_patterns:
            if re.search(pattern, message_lower):
                return {"allowed": False, "reason": "I can only answer GigBridge-related questions about freelancers, clients, projects, hire requests, reviews, portfolio, and messages."}
        
        # If it has GigBridge keywords but no clear action, allow it
        if has_gigbridge_keyword:
            return {"allowed": True}
        
        # Default to blocked if no clear GigBridge intent
        return {"allowed": False, "reason": "I can only answer GigBridge-related questions about freelancers, clients, projects, hire requests, reviews, portfolio, and messages."}
