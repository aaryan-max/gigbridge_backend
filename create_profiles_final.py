#!/usr/bin/env python3

import psycopg2
from postgres_config import POSTGRES_CONFIG

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
            name = freelancer[1].split()[0] if freelancer[1] else "User{}".format(freelancer_id)
            
            # Create profile
            profile_title = str(name) + "'s Profile"
            bio_text = "Experienced " + str(name)
            
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
            
            print("Created profile for freelancer {}: {}".format(freelancer_id, name))
        
        conn.commit()
        conn.close()
        print("Created {} freelancer profiles".format(len(freelancers)))
        
    except Exception as e:
        print("Error: {}".format(e))

if __name__ == "__main__":
    create_freelancer_profiles()
