"""
Notification Helper Module
Minimal implementation for freelancer and client notifications
"""

import database as db

def notify_freelancer(freelancer_id, message, title, related_entity_type=None, related_entity_id=None):
    """
    Send notification to freelancer
    """
    try:
        conn = db.freelancer_db()
        cur = conn.cursor()
        
        # Insert notification into freelancer_notifications table
        cur.execute("""
            INSERT INTO freelancer_notifications 
            (freelancer_id, message, title, related_entity_type, related_entity_id, created_at, is_read)
            VALUES (%s, %s, %s, %s, %s, NOW(), false)
        """, (freelancer_id, message, title, related_entity_type, related_entity_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Notification sent to freelancer {freelancer_id}: {message}")
        
    except Exception as e:
        print(f"❌ Error sending notification to freelancer {freelancer_id}: {str(e)}")

def notify_client(client_id, message, title, related_entity_type=None, related_entity_id=None):
    """
    Send notification to client
    """
    try:
        conn = db.client_db()
        cur = conn.cursor()
        
        # Insert notification into client_notifications table
        cur.execute("""
            INSERT INTO client_notifications 
            (client_id, message, title, related_entity_type, related_entity_id, created_at, is_read)
            VALUES (%s, %s, %s, %s, %s, NOW(), false)
        """, (client_id, message, title, related_entity_type, related_entity_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Notification sent to client {client_id}: {message}")
        
    except Exception as e:
        print(f"❌ Error sending notification to client {client_id}: {str(e)}")
