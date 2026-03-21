import sqlite3

def test_title_based_join():
    """Test updated query with title-based join"""
    client_id = 1
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Test the updated query logic (SQLite version)
    cur.execute("""
        SELECT pp.id, pp.title, pp.description, pp.category, 
               pp.budget_min, pp.budget_max, pp.status as project_status,
               latest_hr.status as hire_status
        FROM project_post pp
        LEFT JOIN (
            SELECT client_id, job_title, status, MAX(created_at) as created_at
            FROM hire_request 
            WHERE client_id = ?
            GROUP BY client_id, job_title, status
        ) latest_hr ON pp.client_id = latest_hr.client_id 
                     AND pp.title = latest_hr.job_title
        WHERE pp.client_id = ?
        ORDER BY pp.created_at DESC
    """, (client_id, client_id))
    
    rows = cur.fetchall()
    
    print(f"Title-based join results ({len(rows)} rows):")
    for i, row in enumerate(rows, 1):
        print(f"\nJob {i}:")
        print(f"  Project ID: {row[0]}")
        print(f"  Title: {row[1]}")
        print(f"  Description: {row[2]}")
        print(f"  Category: {row[3]}")
        print(f"  Budget Min: {row[4]}")
        print(f"  Budget Max: {row[5]}")
        print(f"  Project Status: {row[6]}")
        print(f"  Hire Status: {row[7]}")
        
        # Apply status priority logic
        status = row[7] or row[6] or "unknown"
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
    
    # Also show the raw hire_requests for verification
    print("\n" + "="*50)
    print("RAW hire_requests for comparison:")
    cur.execute("""
        SELECT id, job_title, status, created_at
        FROM hire_request 
        WHERE client_id = ?
        ORDER BY created_at DESC
    """, (client_id,))
    
    hire_rows = cur.fetchall()
    for row in hire_rows:
        print(f"  ID: {row[0]}, Title: {row[1]}, Status: {row[2]}, Created: {row[3]}")
    
    conn.close()

if __name__ == "__main__":
    test_title_based_join()
