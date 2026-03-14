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
        """Check if message is allowed (GigBridge-related only)"""
        if not message or not message.strip():
            return {
                "allowed": False,
                "reason": "Empty message is not allowed."
            }
        
        message_lower = message.lower().strip()
        
        # Check for blocked keywords first (more restrictive)
        for keyword in self.blocked_keywords:
            if keyword in message_lower:
                return {
                    "allowed": False,
                    "reason": "I can only answer GigBridge-related questions about freelancers, clients, projects, hire requests, reviews, portfolio, and messages."
                }
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, message_lower):
                return {
                    "allowed": False,
                    "reason": "I can only answer GigBridge-related questions about freelancers, clients, projects, hire requests, reviews, portfolio, and messages."
                }
        
        # Check if message contains GigBridge keywords or patterns
        has_gigbridge_keyword = any(keyword in message_lower for keyword in self.gigbridge_keywords)
        has_gigbridge_pattern = any(re.search(pattern, message_lower) for pattern in self.gigbridge_patterns)
        
        # Also allow very short messages that might be partial queries
        is_short_query = len(message_lower.split()) <= 3 and any(
            word in self.gigbridge_keywords for word in message_lower.split()
        )
        
        if has_gigbridge_keyword or has_gigbridge_pattern or is_short_query:
            return {
                "allowed": True,
                "reason": None
            }
        
        # Default to blocked if no clear indication of GigBridge relevance
        return {
            "allowed": False,
            "reason": "I can only answer GigBridge-related questions about freelancers, clients, projects, hire requests, reviews, portfolio, and messages."
        }
