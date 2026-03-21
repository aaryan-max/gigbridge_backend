import sqlite3

def check_project_application():
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Check project_application table
    cur.execute("PRAGMA table_info(project_application)")
    columns = cur.fetchall()
    
    print("project_application table schema:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")
    
    # Check sample data
    cur.execute("SELECT * FROM project_application LIMIT 5")
    rows = cur.fetchall()
    
    print("\nSample data:")
    for i, row in enumerate(rows):
        print(f"  Row {i+1}: {row}")
    
    # Check if hire_request is created from project_application
    cur.execute("""
        SELECT pa.*, hr.id as hire_request_id
        FROM project_application pa
        LEFT JOIN hire_request hr ON pa.id = hr.id
        WHERE pa.client_id = 1
        LIMIT 5
    """)
    
    rows = cur.fetchall()
    print("\nproject_application with hire_request mapping:")
    for row in rows:
        print(f"  {row}")
    
    conn.close()

if __name__ == "__main__":
    check_project_application()
