import sqlite3

def test_updated_query():
    """Test the updated query for client jobs"""
    client_id = 1
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # This is the new query from the updated API endpoint
    cur.execute("""
        SELECT pp.id, pp.title, pp.description, pp.category, 
               pp.budget_min, pp.budget_max, pp.status as project_status
        FROM project_post pp
        WHERE pp.client_id = ?
        ORDER BY pp.created_at DESC
    """, (client_id,))
    
    rows = cur.fetchall()
    
    print(f"Updated query results ({len(rows)} rows):")
    for i, row in enumerate(rows, 1):
        print(f"\nJob {i}:")
        print(f"  ID: {row[0]}")
        print(f"  Title: {row[1]}")
        print(f"  Description: {row[2]}")
        print(f"  Category: {row[3]}")
        print(f"  Budget Min: {row[4]}")
        print(f"  Budget Max: {row[5]}")
        print(f"  Status: {row[6]}")
        
        # Format budget as per API logic
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
    test_updated_query()
