import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the database functions
from database import freelancer_db, get_dict_cursor

def test_api_logic():
    """Test the exact API logic"""
    client_id = 1
    
    conn = None
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT pp.id, pp.title, pp.description, pp.category, 
                   pp.budget_min, pp.budget_max, pp.status as project_status
            FROM project_post pp
            WHERE pp.client_id = ?
            ORDER BY pp.created_at DESC
        """, (client_id,))
        rows = cur.fetchall()
        conn.close()

        result = []
        for r in rows:
            if isinstance(r, dict):
                # Use project_status directly
                status = r.get("project_status", "unknown")
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

        print("API Response:")
        for i, job in enumerate(result, 1):
            print(f"\nJob {i}:")
            for key, value in job.items():
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    test_api_logic()
