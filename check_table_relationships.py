import sqlite3

def check_table_relationships():
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Check if hire_request has project_post_id or similar field
    cur.execute("PRAGMA table_info(hire_request)")
    columns = cur.fetchall()
    
    print("hire_request columns:")
    for col in columns:
        print(f"  {col[1]}")
    
    # Check if there are any common fields between the tables
    cur.execute("PRAGMA table_info(project_post)")
    project_columns = cur.fetchall()
    
    print("\nproject_post columns:")
    for col in project_columns:
        print(f"  {col[1]}")
    
    # Check if any hire_request entries reference project_post
    cur.execute("""
        SELECT hr.id, hr.client_id, hr.job_title, hr.status, pp.id as project_id, pp.title, pp.category, pp.description
        FROM hire_request hr
        LEFT JOIN project_post pp ON hr.client_id = pp.client_id
        WHERE hr.client_id = 1
        ORDER BY hr.created_at DESC
        LIMIT 5
    """)
    
    rows = cur.fetchall()
    print("\nJoined data (hire_request + project_post):")
    for row in rows:
        print(f"  {row}")
    
    conn.close()

if __name__ == "__main__":
    check_table_relationships()
