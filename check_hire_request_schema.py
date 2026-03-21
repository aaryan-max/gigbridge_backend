import sqlite3

def check_hire_request_schema():
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    # Get schema for hire_request table
    cur.execute("PRAGMA table_info(hire_request)")
    columns = cur.fetchall()
    
    print("hire_request table schema:")
    for col in columns:
        print(f"  {col[1]} - {col[2]} (nullable: {col[3] == 0})")
    
    # Check sample data
    cur.execute("SELECT * FROM hire_request LIMIT 5")
    rows = cur.fetchall()
    
    print("\nSample data:")
    for i, row in enumerate(rows):
        print(f"  Row {i+1}: {row}")
    
    conn.close()

if __name__ == "__main__":
    check_hire_request_schema()
