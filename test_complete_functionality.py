"""
Test script to demonstrate the updated View My Jobs functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import freelancer_db, get_dict_cursor

def test_complete_functionality():
    """Test the complete updated functionality"""
    client_id = 1
    
    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        
        # Execute the exact query from the updated API
        cur.execute("""
            SELECT pp.id, pp.title, pp.description, pp.category, 
                   pp.budget_min, pp.budget_max, pp.status as project_status,
                   latest_hr.status as hire_status
            FROM project_post pp
            LEFT JOIN (
                SELECT DISTINCT ON (client_id) client_id, status
                FROM hire_request 
                WHERE client_id = %s
                ORDER BY client_id, created_at DESC
            ) latest_hr ON pp.client_id = latest_hr.client_id
            WHERE pp.client_id = %s
            ORDER BY pp.created_at DESC
        """, (client_id, client_id))
        
        rows = cur.fetchall()
        conn.close()

        result = []
        for r in rows:
            if isinstance(r, dict):
                # Use hire_status as primary, fallback to project_status
                status = r.get("hire_status") or r.get("project_status", "unknown")
                # Format budget: show range if both min and max exist, otherwise single value
                budget_min = r.get("budget_min")
                budget_max = r.get("budget_max")
                if budget_min and budget_max and budget_min != budget_max:
                    budget = f"₹{budget_min}-{budget_max}"
                elif budget_max:
                    budget = f"₹{budget_max}"
                elif budget_min:
                    budget = f"₹{budget_min}"
                else:
                    budget = "N/A"
                
                result.append({
                    "id": r.get("id"),
                    "title": r.get("title") or "Untitled",
                    "description": r.get("description") or "N/A",
                    "category": r.get("category") or "N/A",
                    "budget": budget,
                    "status": str(status).lower()
                })

        print("=== VIEW MY JOBS - UPDATED FUNCTIONALITY ===\n")
        
        if not result:
            print("❌ No jobs found")
        else:
            for i, job in enumerate(result, 1):
                print(f"\n{i}. {job['title']}")
                print(f"Category   : {job['category']}")
                print(f"Budget     : {job['budget']}")
                print(f"Description: {job['description']}")
                print(f"Status     : {job['status']}")
                print("----------------------------------")
        
        print(f"\n=== SUMMARY ===")
        print(f"Total jobs: {len(result)}")
        print("Data source: project_post (primary) + hire_request (status)")
        print("Status priority: hire_request.status → project_post.status → 'unknown'")
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    test_complete_functionality()
