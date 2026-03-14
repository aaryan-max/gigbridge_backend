"""
Query Executor for AI Chat Module
Safely executes parameterized SQL queries and returns results
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from database import client_db, freelancer_db
from typing import Dict, List, Any


class QueryExecutor:
    def __init__(self):
        pass
    
    def execute(self, query: str, params: List[Any], db_type: str = "freelancer") -> Dict:
        """Execute a parameterized SQL query safely"""
        conn = None
        try:
            # Get appropriate database connection
            if db_type == "client":
                conn = client_db()
            else:
                conn = freelancer_db()
            
            # Use RealDictCursor for better results
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Execute the parameterized query
            cur.execute(query, params)
            
            # Fetch results
            if query.strip().upper().startswith("SELECT"):
                results = cur.fetchall()
                # Convert RealDictRow to regular dict for JSON serialization
                data = [dict(row) for row in results]
            else:
                # For non-SELECT queries (shouldn't happen with our guardrails)
                conn.commit()
                data = []
            
            return {
                "success": True,
                "data": data,
                "row_count": len(data)
            }
            
        except psycopg2.Error as e:
            print(f"Database error in query executor: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": "Database query failed",
                "details": str(e)
            }
        except Exception as e:
            print(f"Unexpected error in query executor: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": "Query execution failed",
                "details": str(e)
            }
        finally:
            if conn:
                conn.close()
    
    def execute_with_db(self, query_result: Dict) -> Dict:
        """Execute query using the result from query_builder"""
        if not query_result.get("success"):
            return {
                "success": False,
                "error": query_result.get("error", "Unknown query building error")
            }
        
        return self.execute(
            query_result["query"],
            query_result["params"],
            query_result["db"]
        )
