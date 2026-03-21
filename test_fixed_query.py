import sqlite3

def test_fixed_query():
    """Test fixed query with proper DISTINCT ON"""
    client_id = 1
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Get the latest hire_request status for this client
    cur.execute("""
        SELECT status 
        FROM hire_request 
        WHERE client_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (client_id,))
    
    latest_hire = cur.fetchone()
    hire_status = latest_hire[0] if latest_hire else None
    
    print(f"Latest hire_request status for client {client_id}: {hire_status}")
    
    # Get project_post data
    cur.execute("""
        SELECT id, title, description, category, 
               budget_min, budget_max, status as project_status
        FROM project_post
        WHERE client_id = ?
        ORDER BY created_at DESC
    """, (client_id,))
    
    rows = cur.fetchall()
    
    print(f"\nProject data ({len(rows)} rows):")
    for i, row in enumerate(rows, 1):
        print(f"\nJob {i}:")
        print(f"  ID: {row[0]}")
        print(f"  Title: {row[1]}")
        print(f"  Description: {row[2]}")
        print(f"  Category: {row[3]}")
        print(f"  Budget Min: {row[4]}")
        print(f"  Budget Max: {row[5]}")
        print(f"  Project Status: {row[6]}")
        print(f"  Hire Status: {hire_status}")
        
        # Apply status priority logic
        status = hire_status or row[6] or "unknown"
        print(f"  Final Status: {status}")
        
        # Format budget
        budget_min, budget_max = row[4], row[5]
        if budget_min and budget_max and budget_min != budget_max:
            budget = f"₹{budget_min}-{budget_max}"
        elif budget_max:
            budget = f"₹{budget_max}"
        elif budget_min:
            budget = f"₹{budget_min}"
        else:
            budget = "N/A"
        
        print(f"  Formatted Budget: {budget}")
    
    conn.close()

if __name__ == "__main__":
    test_fixed_query()
