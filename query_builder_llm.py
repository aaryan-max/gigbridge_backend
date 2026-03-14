"""
Query Builder for LLM-based GigBridge AI Chat
Builds safe parameterized SQL queries from validated LLM intents
"""

from typing import Dict, List, Optional


class LLMQueryBuilder:
    """Builds safe SQL queries from validated LLM intents"""
    
    def __init__(self):
        self.allowed_intents = [
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
    
    def build_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """
        Build safe SQL query from validated intent
        
        Args:
            parsed_intent: Validated intent from LLM parser
            role: User role (client/freelancer)
            user_id: Current user ID
            
        Returns:
            Dict with query, params, and database info
        """
        intent = parsed_intent.get("intent")
        filters = parsed_intent.get("filters", {})
        sort = parsed_intent.get("sort", "name_asc")
        limit = parsed_intent.get("limit", 50)
        
        # Route to appropriate query builder
        if intent == "list_freelancers":
            return self._build_list_freelancers_query(filters, sort, limit)
        elif intent == "freelancer_detail":
            return self._build_freelancer_detail_query(filters)
        elif intent == "freelancer_reviews":
            return self._build_freelancer_reviews_query(filters)
        elif intent == "freelancer_portfolio":
            return self._build_freelancer_portfolio_query(filters)
        elif intent == "client_hire_requests":
            return self._build_client_hire_requests_query(filters, user_id)
        elif intent == "client_messages":
            return self._build_client_messages_query(filters, user_id)
        elif intent == "client_projects":
            return self._build_client_projects_query(filters, user_id)
        elif intent == "freelancer_hire_requests":
            return self._build_freelancer_hire_requests_query(filters, user_id)
        elif intent == "freelancer_messages":
            return self._build_freelancer_messages_query(filters, user_id)
        elif intent == "freelancer_profile":
            return self._build_freelancer_profile_query(user_id)
        else:
            return {
                "success": False,
                "error": f"Unsupported intent: {intent}"
            }
    
    def _build_list_freelancers_query(self, filters: Dict, sort: str, limit: int) -> Dict:
        """Build query to list freelancers with filters"""
        conditions = []
        params = []
        
        # Base query - join freelancer and freelancer_profile tables
        query = """
            SELECT f.id, f.name, f.email, fp.category, fp.bio, fp.location, 
                   fp.rating, fp.min_budget, fp.max_budget, fp.experience
            FROM freelancer f
            LEFT JOIN freelancer_profile fp ON f.id = fp.freelancer_id 
            WHERE 1=1
        """
        
        # Category filter
        if filters.get("category"):
            conditions.append("fp.category = %s")
            params.append(filters["category"])
        
        # Name filter (partial match)
        if filters.get("name"):
            conditions.append("LOWER(f.name) LIKE LOWER(%s)")
            params.append(f"%{filters['name']}%")
        
        # Location filter (partial match)
        if filters.get("location"):
            conditions.append("LOWER(fp.location) LIKE LOWER(%s)")
            params.append(f"%{filters['location']}%")
        
        # Top rated filter (rating >= 4.0)
        if filters.get("top_rated"):
            conditions.append("fp.rating >= 4.0")
        
        # Budget filters
        if filters.get("budget_min") is not None:
            conditions.append("fp.min_budget >= %s")
            params.append(filters["budget_min"])
        
        if filters.get("budget_max") is not None:
            conditions.append("fp.max_budget <= %s")
            params.append(filters["budget_max"])
        
        # Add conditions to query
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        # Add ordering
        if sort == "name_asc":
            query += " ORDER BY f.name ASC"
        elif sort == "name_desc":
            query += " ORDER BY f.name DESC"
        elif sort == "rating_desc":
            query += " ORDER BY fp.rating DESC NULLS LAST"
        elif sort == "rating_asc":
            query += " ORDER BY fp.rating ASC NULLS LAST"
        elif sort == "budget_asc":
            query += " ORDER BY fp.min_budget ASC"
        elif sort == "budget_desc":
            query += " ORDER BY fp.max_budget DESC"
        elif sort == "experience_desc":
            query += " ORDER BY fp.experience DESC NULLS LAST"
        else:
            query += " ORDER BY f.name ASC"  # Default
        
        # Add limit
        query += f" LIMIT {min(limit, 100)}"
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_freelancer_detail_query(self, filters: Dict) -> Dict:
        """Build query to get freelancer details"""
        query = """
            SELECT f.id, f.name, f.email, fp.category, fp.bio, fp.location,
                   fp.rating, fp.min_budget, fp.max_budget, fp.experience
            FROM freelancer f
            LEFT JOIN freelancer_profile fp ON f.id = fp.freelancer_id 
            WHERE LOWER(f.name) LIKE LOWER(%s)
            LIMIT 1
        """
        
        params = [f"%{filters.get('name', '')}%"]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_freelancer_reviews_query(self, filters: Dict) -> Dict:
        """Build query to get freelancer reviews"""
        # Since reviews table doesn't exist in current schema, return empty result
        return {
            "success": True,
            "query": "SELECT 1 as dummy LIMIT 0",
            "params": [],
            "db": "freelancer"
        }
    
    def _build_freelancer_portfolio_query(self, filters: Dict) -> Dict:
        """Build query to get freelancer portfolio"""
        query = """
            SELECT p.id, p.title, p.description, p.created_at
            FROM portfolio p
            JOIN freelancer f ON p.freelancer_id = f.id
            WHERE LOWER(f.name) LIKE LOWER(%s)
            ORDER BY p.created_at DESC
            LIMIT 10
        """
        
        params = [f"%{filters.get('name', '')}%"]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_client_hire_requests_query(self, filters: Dict, user_id: int) -> Dict:
        """Build query to get client hire requests"""
        query = """
            SELECT hr.id, hr.job_title as project_title, hr.status, hr.created_at,
                   f.name as freelancer_name, fp.category as freelancer_category
            FROM hire_request hr
            JOIN freelancer f ON hr.freelancer_id = f.id
            LEFT JOIN freelancer_profile fp ON f.id = fp.freelancer_id
            WHERE hr.client_id = %s
            ORDER BY hr.created_at DESC
            LIMIT 50
        """
        
        params = [user_id]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "client"
        }
    
    def _build_client_messages_query(self, filters: Dict, user_id: int) -> Dict:
        """Build query to get client messages"""
        query = """
            SELECT m.id, m.text as message, m.timestamp as created_at, m.sender_role,
                   CASE 
                       WHEN m.sender_role = 'freelancer' THEN f.name
                       WHEN m.sender_role = 'client' THEN c.name
                   END as sender_name
            FROM message m
            LEFT JOIN freelancer f ON m.sender_id = f.id AND m.sender_role = 'freelancer'
            LEFT JOIN client c ON m.sender_id = c.id AND m.sender_role = 'client'
            WHERE (m.sender_id = %s AND m.sender_role = 'client')
            ORDER BY m.timestamp DESC
            LIMIT 50
        """
        
        params = [user_id]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "client"
        }
    
    def _build_client_projects_query(self, filters: Dict, user_id: int) -> Dict:
        """Build query to get client projects"""
        # Since projects table doesn't exist, return placeholder
        return {
            "success": True,
            "query": "SELECT 1 as dummy LIMIT 0",
            "params": [],
            "db": "client"
        }
    
    def _build_freelancer_hire_requests_query(self, filters: Dict, user_id: int) -> Dict:
        """Build query to get freelancer hire requests"""
        query = """
            SELECT hr.id, hr.job_title as project_title, hr.status, hr.created_at,
                   c.name as client_name
            FROM hire_request hr
            JOIN client c ON hr.client_id = c.id
            WHERE hr.freelancer_id = %s
            ORDER BY hr.created_at DESC
            LIMIT 50
        """
        
        params = [user_id]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_freelancer_messages_query(self, filters: Dict, user_id: int) -> Dict:
        """Build query to get freelancer messages"""
        query = """
            SELECT m.id, m.text as message, m.timestamp as created_at, m.sender_role,
                   CASE 
                       WHEN m.sender_role = 'freelancer' THEN f.name
                       WHEN m.sender_role = 'client' THEN c.name
                   END as sender_name
            FROM message m
            LEFT JOIN freelancer f ON m.sender_id = f.id AND m.sender_role = 'freelancer'
            LEFT JOIN client c ON m.sender_id = c.id AND m.sender_role = 'client'
            WHERE (m.sender_id = %s AND m.sender_role = 'freelancer')
            ORDER BY m.timestamp DESC
            LIMIT 50
        """
        
        params = [user_id]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_freelancer_profile_query(self, user_id: int) -> Dict:
        """Build query to get freelancer's own profile"""
        query = """
            SELECT f.id, f.name, f.email, fp.category, fp.bio, fp.location,
                   fp.rating, fp.min_budget, fp.max_budget, fp.experience
            FROM freelancer f
            LEFT JOIN freelancer_profile fp ON f.id = fp.freelancer_id 
            WHERE f.id = %s
            LIMIT 1
        """
        
        params = [user_id]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
