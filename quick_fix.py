#!/usr/bin/env python3

import psycopg2
from postgres_config import POSTGRES_CONFIG

def quick_fix():
    """Quick database fix"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        # Create profile for freelancer 2 (Sarthak Sawant)
        cur.execute("""
            INSERT INTO freelancer_profile (freelancer_id, title, skills, experience, min_budget, max_budget, rating, category, bio, availability_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
                2,
                "Sarthak Sawant's Profile",
                "Various skills",
                2.0,
                1000,
                10000,
                0.0,
                "General",
                "Experienced Sarthak Sawant",
                "AVAILABLE"
            ))
        
        conn.commit()
        conn.close()
        print("✅ Created freelancer profile for Sarthak Sawant")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    quick_fix()
