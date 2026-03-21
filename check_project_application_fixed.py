import sqlite3

def check_project_application():
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Check if hire_request is created from project_application
    cur.execute("""
        SELECT pa.*, hr.id as hire_request_id
        FROM project_application pa
        LEFT JOIN hire_request hr ON pa.id = hr.id
        LIMIT 5
    """)
    
    rows = cur.fetchall()
    print("project_application with hire_request mapping:")
    for row in rows:
        print(f"  {row}")
    
    # Check the relationship through project_post
    cur.execute("""
        SELECT pp.id as project_id, pp.title, pp.category, pp.description,
               pa.id as app_id, pa.status as app_status,
               hr.id as hire_id, hr.job_title, hr.status as hire_status
        FROM project_post pp
        LEFT JOIN project_application pa ON pp.id = pa.project_id
        LEFT JOIN hire_request hr ON pa.id = hr.id
        WHERE pp.client_id = 1
        ORDER BY pp.created_at DESC
        LIMIT 5
    """)
    
    rows = cur.fetchall()
    print("\nFull relationship (project_post -> project_application -> hire_request):")
    for row in rows:
        print(f"  {row}")
    
    conn.close()

if __name__ == "__main__":
    check_project_application()
