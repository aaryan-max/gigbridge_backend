import sqlite3

def check_hire_request_columns():
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Get schema for hire_request table
    cur.execute("PRAGMA table_info(hire_request)")
    columns = cur.fetchall()
    
    print("hire_request table columns:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")
    
    # Check if project_id exists
    has_project_id = any(col[1] == 'project_id' for col in columns)
    print(f"\nHas project_id column: {has_project_id}")
    
    # Check how hire_request relates to project_post
    cur.execute("""
        SELECT hr.id, hr.client_id, hr.job_title, pp.id as project_id, pp.title
        FROM hire_request hr
        LEFT JOIN project_post pp ON hr.client_id = pp.client_id
        WHERE hr.client_id = 1
        LIMIT 3
    """)
    
    rows = cur.fetchall()
    print("\nSample relationship data:")
    for row in rows:
        print(f"  {row}")
    
    conn.close()

if __name__ == "__main__":
    check_hire_request_columns()
