#!/usr/bin/env python3

import psycopg2
from postgres_config import POSTGRES_CONFIG

def check_all_tables():
    """Check all critical tables for data existence"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        tables = [
            'client', 'freelancer', 'client_profile', 'freelancer_profile',
            'message', 'notification', 'hire_request', 'saved_freelancer',
            'saved_client', 'portfolio', 'call_session', 'project_post'
        ]
        
        print("=== DATABASE TABLE CHECK ===")
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"{table}: {count} records")
            except Exception as e:
                print(f"{table}: ERROR - {e}")
        
        # Check specific relationships
        print("\n=== RELATIONSHIP CHECK ===")
        
        # Check if client 1 has any interactions
        cur.execute("""
            SELECT COUNT(*) FROM hire_request WHERE client_id = %s
        """, (1,))
        client_hires = cur.fetchone()[0]
        print(f"Client 1 hire requests: {client_hires}")
        
        # Check if freelancer 2 has any interactions  
        cur.execute("""
            SELECT COUNT(*) FROM hire_request WHERE freelancer_id = %s
        """, (2,))
        freelancer_hires = cur.fetchone()[0]
        print(f"Freelancer 2 hire requests: {freelancer_hires}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_all_tables()
