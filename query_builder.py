"""
Safe Query Builder for AI Chat Module
Builds parameterized SQL queries based on parsed intents
Only allows SELECT queries for security
"""

from typing import Dict, List, Tuple, Optional
from database import client_db, freelancer_db


class QueryBuilder:
    def __init__(self):
        self.query_templates = {
            "list_freelancers": self._build_list_freelancers_query,
            "freelancer_detail": self._build_freelancer_detail_query,
            "freelancer_reviews": self._build_freelancer_reviews_query,
            "freelancer_portfolio": self._build_freelancer_portfolio_query,
            "client_hire_requests": self._build_client_hire_requests_query,
            "client_messages": self._build_client_messages_query,
            "client_projects": self._build_client_projects_query,
            "freelancer_hire_requests": self._build_freelancer_hire_requests_query,
            "freelancer_messages": self._build_freelancer_messages_query,
            "freelancer_profile": self._build_freelancer_profile_query
        }
    
    def build_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """Build a safe parameterized SQL query"""
        try:
            intent = parsed_intent.get("intent")
            if not intent or intent not in self.query_templates:
                return {
                    "success": False,
                    "error": "Unsupported intent"
                }
            
            query_func = self.query_templates[intent]
            result = query_func(parsed_intent, role, user_id)
            
            # Ensure query is SELECT only
            query_upper = result["query"].upper().strip()
            if not query_upper.startswith("SELECT"):
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed"
                }
            
            return result
            
        except Exception as e:
            print(f"Error building query: {str(e)}")
            return {
                "success": False,
                "error": "Query building failed"
            }
    
    def _build_list_freelancers_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
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
        if parsed_intent.get("category"):
            conditions.append("fp.category = %s")
            params.append(parsed_intent["category"])
        
        # Name filter (partial match)
        if parsed_intent.get("name"):
            conditions.append("LOWER(f.name) LIKE LOWER(%s)")
            params.append(f"%{parsed_intent['name']}%")
        
        # Location filter (partial match)
        if parsed_intent.get("location"):
            conditions.append("LOWER(fp.location) LIKE LOWER(%s)")
            params.append(f"%{parsed_intent['location']}%")
        
        # Top rated filter (rating >= 4.0)
        if parsed_intent.get("top_rated"):
            conditions.append("fp.rating >= 4.0")
        
        # Budget filters
        if parsed_intent.get("budget_min") is not None:
            conditions.append("fp.min_budget >= %s")
            params.append(parsed_intent["budget_min"])
        
        if parsed_intent.get("budget_max") is not None:
            conditions.append("fp.max_budget <= %s")
            params.append(parsed_intent["budget_max"])
        
        # Add conditions to query
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        # Add ordering
        sort_by = parsed_intent.get("sort_by", "name_asc")
        if sort_by == "name_asc":
            query += " ORDER BY f.name ASC"
        elif sort_by == "name_desc":
            query += " ORDER BY f.name DESC"
        elif sort_by == "rating_desc":
            query += " ORDER BY fp.rating DESC NULLS LAST"
        elif sort_by == "rating_asc":
            query += " ORDER BY fp.rating ASC NULLS LAST"
        elif sort_by == "budget_asc":
            query += " ORDER BY fp.min_budget ASC"
        elif sort_by == "budget_desc":
            query += " ORDER BY fp.max_budget DESC"
        elif sort_by == "experience_desc":
            query += " ORDER BY fp.experience DESC NULLS LAST"
        
        # Limit results for performance
        query += " LIMIT 50"
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_freelancer_detail_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """Build query to get freelancer details"""
        query = """
            SELECT f.id, f.name, f.email, fp.category, fp.bio, fp.location,
                   fp.rating, fp.min_budget, fp.max_budget, fp.experience
            FROM freelancer f
            LEFT JOIN freelancer_profile fp ON f.id = fp.freelancer_id 
            WHERE LOWER(f.name) LIKE LOWER(%s)
            LIMIT 1
        """
        
        params = [f"%{parsed_intent['name']}%"]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_freelancer_reviews_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """Build query to get freelancer reviews"""
        query = """
            SELECT r.rating, r.review, r.created_at, 
                   c.name as client_name
            FROM reviews r
            JOIN freelancer f ON r.freelancer_id = f.id
            LEFT JOIN client c ON r.client_id = c.id
            WHERE LOWER(f.name) LIKE LOWER(%s)
            ORDER BY r.created_at DESC
            LIMIT 20
        """
        
        params = [f"%{parsed_intent['name']}%"]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_freelancer_portfolio_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """Build query to get freelancer portfolio"""
        query = """
            SELECT p.title, p.description, p.file_url, p.created_at
            FROM portfolio p
            JOIN freelancer f ON p.freelancer_id = f.id
            WHERE LOWER(f.name) LIKE LOWER(%s)
            ORDER BY p.created_at DESC
            LIMIT 20
        """
        
        params = [f"%{parsed_intent['name']}%"]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_client_hire_requests_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """Build query to get client hire requests"""
        query = """
            SELECT hr.id, hr.job_title as project_title, hr.status, hr.created_at,
                   f.name as freelancer_name, fp.category as freelancer_category
            FROM hire_requests hr
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
    
    def _build_client_messages_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
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
               OR (m.receiver_id = %s AND m.receiver_role = 'client')
            ORDER BY m.timestamp DESC
            LIMIT 50
        """
        
        params = [user_id, user_id]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "client"
        }
    
    def _build_client_projects_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """Build query to get client projects"""
        # Since projects table doesn't exist, return a placeholder response
        return {
            "success": True,
            "query": "SELECT 1 as dummy LIMIT 0",
            "params": [],
            "db": "client"
        }
    
    def _build_freelancer_hire_requests_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
        """Build query to get freelancer hire requests"""
        query = """
            SELECT hr.id, hr.job_title as project_title, hr.status, hr.created_at,
                   c.name as client_name
            FROM hire_requests hr
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
    
    def _build_freelancer_messages_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
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
               OR (m.receiver_id = %s AND m.receiver_role = 'freelancer')
            ORDER BY m.timestamp DESC
            LIMIT 50
        """
        
        params = [user_id, user_id]
        
        return {
            "success": True,
            "query": query,
            "params": params,
            "db": "freelancer"
        }
    
    def _build_freelancer_profile_query(self, parsed_intent: Dict, role: str, user_id: int) -> Dict:
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
