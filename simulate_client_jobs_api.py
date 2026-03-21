import sqlite3

def simulate_client_jobs_api():
    """Simulate what the API endpoint returns"""
    client_id = 1
    
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # This is the exact query from the API endpoint
    cur.execute("""
        SELECT id, job_title, proposed_budget, status
        FROM hire_request
        WHERE client_id=%s
        ORDER BY created_at DESC
    """.replace("%s", "?"), (client_id,))
    
    rows = cur.fetchall()
    
    print(f"Raw query results ({len(rows)} rows):")
    for i, row in enumerate(rows, 1):
        print(f"  Row {i}: {row}")
    
    # This is the exact processing logic from the API endpoint
    result = []
    for r in rows:
        # The code checks if r is a dict, but sqlite returns tuples
        if isinstance(r, dict):
            st = r.get("status", "")
            result.append({
                "id": r.get("id"),
                "title": r.get("job_title") or "",
                "budget": r.get("proposed_budget"),
                "status": "open" if st == "PENDING" else str(st).lower()
            })
        else:
            # This is the actual path taken
            st = r[3] if len(r) > 3 else r[2]
            result.append({
                "id": r[0],
                "title": r[1] or "",  # job_title
                "budget": r[2],        # proposed_budget
                "status": "open" if st == "PENDING" else str(st).lower()
            })
    
    print(f"\nProcessed API response:")
    for i, job in enumerate(result, 1):
        print(f"  Job {i}: {job}")
    
    # Check what's missing
    print(f"\nMissing fields analysis:")
    for i, job in enumerate(result, 1):
        print(f"  Job {i}:")
        print(f"    title: '{job['title']}' (empty: {job['title'] == ''})")
        print(f"    budget: {job['budget']} (null: {job['budget'] is None})")
        print(f"    status: '{job['status']}'")
        print(f"    Missing: category, description")
    
    conn.close()

if __name__ == "__main__":
    simulate_client_jobs_api()
