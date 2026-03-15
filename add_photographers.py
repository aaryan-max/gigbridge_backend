#!/usr/bin/env python3
"""
Check and add photographer test data for search functionality
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from database import freelancer_db
import time

def check_and_add_photographers():
    print("🔍 Checking for photographers in database...")
    
    conn = freelancer_db()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check existing photographers
        cur.execute("""
            SELECT f.id, f.name, fp.category 
            FROM freelancer f 
            LEFT JOIN freelancer_profile fp ON f.id = fp.freelancer_id 
            WHERE fp.category ILIKE '%photographer%'
        """)
        photographers = cur.fetchall()
        
        print(f"Found {len(photographers)} photographers:")
        for p in photographers:
            print(f"  ID: {p['id']}, Name: {p['name']}, Category: {p['category']}")
        
        if len(photographers) == 0:
            print("\n📝 Adding test photographers...")
            now = int(time.time())
            
            # Add test photographers
            test_photographers = [
                ("John Smith", "john@example.com", "Photographer", "Wedding Photography", 5000, 4.5),
                ("Sarah Johnson", "sarah@example.com", "Photographer", "Portrait Photography", 3000, 4.8),
                ("Mike Wilson", "mike@example.com", "Photographer", "Event Photography", 4000, 4.6),
            ]
            
            for name, email, category, specialization, rate, rating in test_photographers:
                try:
                    # Insert into freelancer table first
                    cur.execute("""
                        INSERT INTO freelancer (name, email)
                        VALUES (%s, %s)
                        RETURNING id
                    """, (name, email))
                    
                    fid = cur.fetchone()['id']
                    print(f"  ✅ Added freelancer: {name} (ID: {fid})")
                    
                    # Add profile with category
                    cur.execute("""
                        INSERT INTO freelancer_profile 
                        (freelancer_id, bio, experience, skills, category, min_budget, max_budget, rating, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (fid, f"Professional {specialization} with years of experience", 5, "Camera, Lighting, Editing", category, 1000, 10000, rating, now))
                    
                except Exception as e:
                    print(f"  ❌ Error adding {name}: {e}")
                    conn.rollback()
                    continue
            
            conn.commit()
            print(f"\n✅ Added {len(test_photographers)} test photographers!")
        
        else:
            print("\n✅ Photographers already exist in database")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    check_and_add_photographers()
