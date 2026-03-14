#!/usr/bin/env python3

import psycopg2
from postgres_config import POSTGRES_CONFIG
from werkzeug.security import generate_password_hash

def create_freelancer_profiles():
    """Create missing freelancer profiles"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        print("Creating freelancer profiles...")
        
        # Get existing freelancers
        cur.execute("SELECT id, name, email FROM freelancer")
        freelancers = cur.fetchall()
        
        for freelancer in freelancers:
            freelancer_id = freelancer[0]
            name = freelancer[1].split()[0] if freelancer[1] else f"User{freelancer_id}"
            
            # Create profile
            profile_title = name + "'s Profile"
            bio_text = "Experienced " + name
            
            cur.execute("""
                INSERT INTO freelancer_profile (freelancer_id, title, skills, experience, min_budget, max_budget, rating, category, bio, availability_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                freelancer_id, 
                profile_title,
                "Various skills",
                2.0,
                1000,
                10000,
                0.0,
                "General",
                bio_text,
                "AVAILABLE"
            ))
            
            print(f"Created profile for freelancer {freelancer_id}: {name}")
        
        conn.commit()
        conn.close()
        print(f"✅ Created {len(freelancers)} freelancer profiles")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_freelancer_profiles()
