import sqlite3

try:
    # Test the exact query from the platform stats endpoint
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM hire_request WHERE status='ACCEPTED'")
    gigs_completed = cur.fetchone()[0]
    print(f"Gigs completed: {gigs_completed}")
    conn.close()
    
    # Test total freelancers
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM freelancer")
    total_freelancers = cur.fetchone()[0]
    print(f"Total freelancers: {total_freelancers}")
    conn.close()
    
    # Test total clients
    conn = sqlite3.connect("client.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM client")
    total_clients = cur.fetchone()[0]
    print(f"Total clients: {total_clients}")
    conn.close()
    
    print("All queries successful!")
    
except Exception as e:
    print(f"Error: {e}")
