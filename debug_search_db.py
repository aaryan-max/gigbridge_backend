#!/usr/bin/env python3
"""
Debug search functionality - check database content
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from database import freelancer_db

def debug_database():
    print("🔍 Debugging database content...")
    
    conn = freelancer_db()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check all categories in database
        print("\n--- All Categories in Database ---")
        cur.execute("SELECT DISTINCT fp.category FROM freelancer_profile fp WHERE fp.category IS NOT NULL")
        categories = cur.fetchall()
        for cat in categories:
            print(f"  Category: '{cat['category']}'")
        
        # Check photographers specifically
        print("\n--- Photographer Entries ---")
        cur.execute("""
            SELECT f.name, fp.category, fp.title, fp.min_budget, fp.max_budget, fp.rating
            FROM freelancer f 
            JOIN freelancer_profile fp ON f.id = fp.freelancer_id 
            WHERE fp.category ILIKE '%photographer%'
        """)
        photographers = cur.fetchall()
        
        print(f"Found {len(photographers)} photographer entries:")
        for p in photographers:
            print(f"  Name: {p['name']}")
            print(f"  Category: '{p['category']}'")
            print(f"  Title: '{p['title']}'")
            print(f"  Budget: {p['min_budget']} - {p['max_budget']}")
            print(f"  Rating: {p['rating']}")
            print()
        
        # Test the exact query that search uses
        print("\n--- Testing Search Query ---")
        budget = 4000
        category = "photographer"
        cur.execute("""
            SELECT
                fp.freelancer_id,
                f.name,
                fp.title,
                fp.skills,
                fp.experience,
                fp.min_budget,
                fp.max_budget,
                fp.rating,
                fp.category,
                fp.latitude,
                fp.longitude,
                fp.availability_status,
                999999.0 as rank
            FROM freelancer_profile fp
            JOIN freelancer f ON f.id = fp.freelancer_id
            LEFT JOIN freelancer_subscription fs
                ON fs.freelancer_id = fp.freelancer_id
            WHERE fp.min_budget <= %s
              AND fp.max_budget >= %s AND fp.category ILIKE %s
        """, (budget, budget, f"%{category}%"))
        
        results = cur.fetchall()
        print(f"Search query results: {len(results)} photographers found")
        for r in results:
            print(f"  Found: {r['name']} - {r['category']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_database()
