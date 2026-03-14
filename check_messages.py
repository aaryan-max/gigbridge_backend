#!/usr/bin/env python3

import psycopg2
from postgres_config import POSTGRES_CONFIG

def check_messages():
    """Check if there are any messages in the database"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        print("Checking message table...")
        cur.execute("SELECT COUNT(*) FROM message")
        count = cur.fetchone()[0]
        print(f"Total messages in database: {count}")
        
        # Check for messages involving client ID 1
        cur.execute("""
            SELECT COUNT(*) 
            FROM message 
            WHERE (sender_role='client' AND sender_id=%s) 
               OR (sender_role='freelancer' AND receiver_id=%s)
        """, (1, 1))
        client_messages = cur.fetchone()[0]
        print(f"Messages involving client ID 1: {client_messages}")
        
        # Get some sample messages
        cur.execute("""
            SELECT sender_role, sender_id, receiver_id, text, timestamp
            FROM message 
            WHERE (sender_role='client' AND sender_id=%s) 
               OR (sender_role='freelancer' AND receiver_id=%s)
            ORDER BY timestamp DESC
            LIMIT 5
        """, (1, 1))
        messages = cur.fetchall()
        
        print(f"Sample messages:")
        for msg in messages:
            print(f"  {msg[0]} -> {msg[2]}: {msg[3][:50]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_messages()
