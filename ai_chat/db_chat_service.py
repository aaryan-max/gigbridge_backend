"""
Database-powered Chat Service for GigBridge
Simple rule-based chatbot that answers questions using PostgreSQL data only
"""

import re
import psycopg2
from database import client_db, freelancer_db


class DatabaseChatService:
    def __init__(self):
        self.query_patterns = {
            # Client queries
            'show my projects': self._get_client_projects,
            'list my projects': self._get_client_projects,
            'my projects': self._get_client_projects,
            'show projects': self._get_client_projects,
            
            # Freelancer queries  
            'show my applications': self._get_freelancer_applications,
            'list my applications': self._get_freelancer_applications,
            'my applications': self._get_freelancer_applications,
            'show applications': self._get_freelancer_applications,
            
            # General queries
            'list freelancers': self._list_freelancers,
            'show freelancers': self._list_freelancers,
            'freelancers': self._list_freelancers,
            
            # Messages
            'show my messages': self._get_user_messages,
            'list my messages': self._get_user_messages,
            'my messages': self._get_user_messages,
            'show messages': self._get_user_messages,
            
            # Profile queries
            'show my profile': self._get_user_profile,
            'my profile': self._get_user_profile,
            'profile': self._get_user_profile,
        }
    
    def process_query(self, role: str, user_id: int, message: str):
        """
        Process user query and return database results
        """
        try:
            # Normalize message
            normalized_message = message.lower().strip()
            
            # Check if user exists
            if not self._user_exists(role, user_id):
                return {
                    "success": False,
                    "msg": "User not found"
                }
            
            # Find matching query pattern
            for pattern, handler in self.query_patterns.items():
                if pattern in normalized_message:
                    return handler(role, user_id)
            
            # No pattern matched
            return {
                "success": False,
                "msg": "Sorry, I can only answer questions related to your GigBridge data."
            }
            
        except Exception as e:
            print(f"Error in chat service: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "msg": "Database error occurred"
            }
    
    def _user_exists(self, role: str, user_id: int) -> bool:
        """Check if user exists in database"""
        try:
            if role == "client":
                conn = client_db()
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM client WHERE id=%s", (user_id,))
            else:  # freelancer
                conn = freelancer_db()
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM freelancer WHERE id=%s", (user_id,))
            
            exists = cur.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            print(f"Error checking user existence: {str(e)}")
            return False
    
    def _get_client_projects(self, role: str, user_id: int):
        """Get projects for a client"""
        try:
            conn = freelancer_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, title, description, category, skills, 
                       budget_type, budget_min, budget_max, status, created_at
                FROM project_post 
                WHERE client_id=%s 
                ORDER BY created_at DESC
            """, (user_id,))
            
            rows = cur.fetchall()
            projects = []
            for row in rows:
                projects.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "category": row[3],
                    "skills": row[4],
                    "budget_type": row[5],
                    "budget_min": float(row[6]) if row[6] else None,
                    "budget_max": float(row[7]) if row[7] else None,
                    "status": row[8],
                    "created_at": row[9]
                })
            
            conn.close()
            
            return {
                "success": True,
                "data": projects,
                "msg": f"Found {len(projects)} project(s)"
            }
            
        except Exception as e:
            print(f"Error getting client projects: {str(e)}")
            return {
                "success": False,
                "msg": "Failed to retrieve projects"
            }
    
    def _get_freelancer_applications(self, role: str, user_id: int):
        """Get applications for a freelancer"""
        try:
            conn = freelancer_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT pa.id, pa.project_id, pa.proposal_text, pa.bid_amount, 
                       pa.hourly_rate, pa.status, pa.created_at,
                       pp.title, pp.budget_type, pp.client_id
                FROM project_application pa
                JOIN project_post pp ON pa.project_id = pp.id
                WHERE pa.freelancer_id=%s 
                ORDER BY pa.created_at DESC
            """, (user_id,))
            
            rows = cur.fetchall()
            applications = []
            for row in rows:
                applications.append({
                    "id": row[0],
                    "project_id": row[1],
                    "project_title": row[7],
                    "proposal_text": row[2],
                    "bid_amount": float(row[3]) if row[3] else None,
                    "hourly_rate": float(row[4]) if row[4] else None,
                    "status": row[5],
                    "created_at": row[6],
                    "budget_type": row[8],
                    "client_id": row[9]
                })
            
            conn.close()
            
            return {
                "success": True,
                "data": applications,
                "msg": f"Found {len(applications)} application(s)"
            }
            
        except Exception as e:
            print(f"Error getting freelancer applications: {str(e)}")
            return {
                "success": False,
                "msg": "Failed to retrieve applications"
            }
    
    def _list_freelancers(self, role: str, user_id: int):
        """List all freelancers"""
        try:
            conn = freelancer_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT f.id, f.name, f.email, f.created_at,
                       fp.category, fp.bio, fp.rating, fp.total_projects
                FROM freelancer f
                LEFT JOIN freelancer_profile fp ON f.id = fp.freelancer_id
                ORDER BY f.created_at DESC
            """)
            
            rows = cur.fetchall()
            freelancers = []
            for row in rows:
                freelancers.append({
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "created_at": row[3],
                    "category": row[4],
                    "bio": row[5],
                    "rating": float(row[6]) if row[6] else None,
                    "total_projects": int(row[7]) if row[7] else 0
                })
            
            conn.close()
            
            return {
                "success": True,
                "data": freelancers,
                "msg": f"Found {len(freelancers)} freelancer(s)"
            }
            
        except Exception as e:
            print(f"Error listing freelancers: {str(e)}")
            return {
                "success": False,
                "msg": "Failed to retrieve freelancers"
            }
    
    def _get_user_messages(self, role: str, user_id: int):
        """Get messages for a user"""
        try:
            conn = freelancer_db()
            cur = conn.cursor()
            
            # Get messages where user is either sender or receiver
            cur.execute("""
                SELECT id, sender_id, receiver_id, message_text, created_at
                FROM messages 
                WHERE sender_id=%s OR receiver_id=%s
                ORDER BY created_at DESC
                LIMIT 50
            """, (user_id, user_id))
            
            rows = cur.fetchall()
            messages = []
            for row in rows:
                messages.append({
                    "id": row[0],
                    "sender_id": row[1],
                    "receiver_id": row[2],
                    "message_text": row[3],
                    "created_at": row[4],
                    "is_sent": row[1] == user_id
                })
            
            conn.close()
            
            return {
                "success": True,
                "data": messages,
                "msg": f"Found {len(messages)} message(s)"
            }
            
        except Exception as e:
            print(f"Error getting messages: {str(e)}")
            return {
                "success": False,
                "msg": "Failed to retrieve messages"
            }
    
    def _get_user_profile(self, role: str, user_id: int):
        """Get user profile"""
        try:
            conn = client_db() if role == "client" else freelancer_db()
            cur = conn.cursor()
            
            if role == "client":
                cur.execute("""
                    SELECT id, name, email, created_at
                    FROM client 
                    WHERE id=%s
                """, (user_id,))
                
                row = cur.fetchone()
                if row:
                    profile = {
                        "id": row[0],
                        "name": row[1],
                        "email": row[2],
                        "created_at": row[3],
                        "role": "client"
                    }
            else:  # freelancer
                cur.execute("""
                    SELECT f.id, f.name, f.email, f.created_at,
                           fp.category, fp.bio, fp.rating, fp.total_projects
                    FROM freelancer f
                    LEFT JOIN freelancer_profile fp ON f.id = fp.freelancer_id
                    WHERE f.id=%s
                """, (user_id,))
                
                row = cur.fetchone()
                if row:
                    profile = {
                        "id": row[0],
                        "name": row[1],
                        "email": row[2],
                        "created_at": row[3],
                        "category": row[4],
                        "bio": row[5],
                        "rating": float(row[6]) if row[6] else None,
                        "total_projects": int(row[7]) if row[7] else 0,
                        "role": "freelancer"
                    }
            
            conn.close()
            
            if 'profile' in locals():
                return {
                    "success": True,
                    "data": profile,
                    "msg": "Profile retrieved successfully"
                }
            else:
                return {
                    "success": False,
                    "msg": "Profile not found"
                }
                
        except Exception as e:
            print(f"Error getting profile: {str(e)}")
            return {
                "success": False,
                "msg": "Failed to retrieve profile"
            }
