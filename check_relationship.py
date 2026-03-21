import sqlite3

def check_project_hire_relationship():
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Check how project_post relates to hire_request
    cur.execute("""
        SELECT pp.id as project_id, pp.title, pp.client_id as project_client_id,
               hr.id as hire_id, hr.client_id as hire_client_id, hr.status, hr.created_at
        FROM project_post pp
        LEFT JOIN hire_request hr ON pp.client_id = hr.client_id
        WHERE pp.client_id = 1
        ORDER BY pp.id, hr.created_at DESC
    """)
    
    rows = cur.fetchall()
    print("Project-Hire Request Relationship:")
    for row in rows:
        print(f"  Project {row[0]} ({row[1]}) -> Hire {row[3]} (client: {row[4]}, status: {row[5]})")
    
    # Check if there's a direct project_id in hire_request
    cur.execute("PRAGMA table_info(hire_request)")
    columns = cur.fetchall()
    print("\nHire request columns:")
    for col in columns:
        print(f"  {col[1]}")
    
    conn.close()

if __name__ == "__main__":
    check_project_hire_relationship()
