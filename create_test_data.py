"""
Create test data for AI chat testing
"""

import psycopg2
from postgres_config import get_postgres_connection


def create_test_freelancers():
    """Create test freelancer data"""
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Insert test freelancers
        freelancers = [
            ('Aaryan', 'aaryan@example.com', 'password123'),
            ('Priya', 'priya@example.com', 'password123'),
            ('Rahul', 'rahul@example.com', 'password123')
        ]
        
        for name, email, password in freelancers:
            cur.execute("""
                INSERT INTO freelancer (name, email, password) 
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                RETURNING id
            """, (name, email, password))
            result = cur.fetchone()
            if result:
                freelancer_id = result[0]
                print(f"Created freelancer: {name} (ID: {freelancer_id})")
                
                # Add profile data
                if name == 'Aaryan':
                    cur.execute("""
                        INSERT INTO freelancer_profile 
                        (freelancer_id, category, bio, location, rating, min_budget, max_budget, experience)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (freelancer_id) DO UPDATE SET
                        category = EXCLUDED.category,
                        bio = EXCLUDED.bio,
                        location = EXCLUDED.location,
                        rating = EXCLUDED.rating,
                        min_budget = EXCLUDED.min_budget,
                        max_budget = EXCLUDED.max_budget,
                        experience = EXCLUDED.experience
                    """, (freelancer_id, 'Singer', 'Professional singer with 5 years experience', 'Mumbai', 4.5, 5000, 15000, 5))
                
                elif name == 'Priya':
                    cur.execute("""
                        INSERT INTO freelancer_profile 
                        (freelancer_id, category, bio, location, rating, min_budget, max_budget, experience)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (freelancer_id) DO UPDATE SET
                        category = EXCLUDED.category,
                        bio = EXCLUDED.bio,
                        location = EXCLUDED.location,
                        rating = EXCLUDED.rating,
                        min_budget = EXCLUDED.min_budget,
                        max_budget = EXCLUDED.max_budget,
                        experience = EXCLUDED.experience
                    """, (freelancer_id, 'Dancer', 'Professional dancer', 'Delhi', 4.2, 3000, 10000, 3))
                
                elif name == 'Rahul':
                    cur.execute("""
                        INSERT INTO freelancer_profile 
                        (freelancer_id, category, bio, location, rating, min_budget, max_budget, experience)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (freelancer_id) DO UPDATE SET
                        category = EXCLUDED.category,
                        bio = EXCLUDED.bio,
                        location = EXCLUDED.location,
                        rating = EXCLUDED.rating,
                        min_budget = EXCLUDED.min_budget,
                        max_budget = EXCLUDED.max_budget,
                        experience = EXCLUDED.experience
                    """, (freelancer_id, 'Photographer', 'Wedding and event photographer', 'Bangalore', 4.8, 8000, 20000, 7))
        
        conn.commit()
        print("Test data created successfully!")
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_test_client():
    """Create test client data"""
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO client (name, email, password) 
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, ('Test Client', 'client@example.com', 'password123'))
        
        result = cur.fetchone()
        if result:
            client_id = result[0]
            print(f"Created client: Test Client (ID: {client_id})")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error creating test client: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    create_test_freelancers()
    create_test_client()
