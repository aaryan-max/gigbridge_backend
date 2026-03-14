#!/usr/bin/env python3

import psycopg2
from postgres_config import POSTGRES_CONFIG

def fix_profiles():
    """Direct database fix for freelancer profiles"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        print("Fixing freelancer profiles...")
        
        # Get existing freelancers
        cur.execute("SELECT id, name FROM freelancer")
        freelancers = cur.fetchall()
        
        for freelancer in freelancers:
            freelancer_id = freelancer[0]
            name = freelancer[1]
            
            # Create profile with simple values
            cur.execute("""
                INSERT INTO freelancer_profile (freelancer_id, title, skills, experience, min_budget, max_budget, rating, category, bio, availability_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                freelancer_id,
                name + "'s Profile",
                "Various skills",
                2.0,
                1000,
                10000,
                0.0,
                "General",
                "Experienced " + name,
                "AVAILABLE"
            ))
            
            print(f"Created profile for freelancer {freelancer_id}: {name}")
        
        conn.commit()
        conn.close()
        print(f"✅ Fixed {len(freelancers)} freelancer profiles")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_profiles()
