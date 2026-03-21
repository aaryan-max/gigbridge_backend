import sqlite3

def check_project_post_schema():
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Get schema for project_post table
    cur.execute("PRAGMA table_info(project_post)")
    columns = cur.fetchall()
    
    print("project_post table schema:")
    for col in columns:
        print(f"  {col[1]} - {col[2]} (nullable: {col[3] == 0})")
    
    # Check sample data
    cur.execute("SELECT * FROM project_post LIMIT 5")
    rows = cur.fetchall()
    
    print("\nSample data:")
    for i, row in enumerate(rows):
        print(f"  Row {i+1}: {row}")
    
    conn.close()

if __name__ == "__main__":
    check_project_post_schema()
