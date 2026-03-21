import sqlite3

def analyze_data_relationship():
    """Analyze the relationship between project_post and hire_request"""
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    
    print("=== PROJECT_POST DATA ===")
    cur.execute("SELECT id, title, client_id FROM project_post WHERE client_id = 1")
    projects = cur.fetchall()
    for p in projects:
        print(f"Project {p[0]}: '{p[1]}' (client: {p[2]})")
    
    print("\n=== HIRE_REQUEST DATA ===")
    cur.execute("SELECT id, job_title, client_id, created_at FROM hire_request WHERE client_id = 1 ORDER BY created_at")
    hires = cur.fetchall()
    for h in hires:
        print(f"Hire {h[0]}: '{h[1]}' (client: {h[2]}, created: {h[3]})")
    
    print("\n=== MATCHING ANALYSIS ===")
    # Check if any hire_requests match project titles
    for p in projects:
        matching_hires = [h for h in hires if h[1] == p[1]]
        print(f"Project '{p[1]}' matches {len(matching_hires)} hire requests")
        for h in matching_hires:
            print(f"  -> Hire {h[0]}: '{h[1]}' (created: {h[3]})")
    
    # Check if we can match by client_id only and get latest per project
    print("\n=== LATEST HIRE PER CLIENT ===")
    if hires:
        latest_hire = max(hires, key=lambda x: x[3])  # latest by created_at
        print(f"Latest hire for client: '{latest_hire[1]}' (status: ?)")
    
    conn.close()

if __name__ == "__main__":
    analyze_data_relationship()
