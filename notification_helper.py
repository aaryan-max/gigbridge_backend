"""
Notification Helper Module
Production-ready implementation for freelancer and client notifications
"""

import database as db

def notify_freelancer(freelancer_id, message, title, related_entity_type=None, related_entity_id=None):
    """
    Send notification to freelancer with duplicate prevention and proper error handling
    """
    if not freelancer_id or not message or not title:
        print(f"❌ Invalid notification parameters: freelancer_id={freelancer_id}, has_message={bool(message)}, has_title={bool(title)}")
        return False
    
    try:
        conn = db.freelancer_db()
        cur = conn.cursor()
        
        # Check for duplicate notification in last 5 minutes
        cur.execute("""
            SELECT COUNT(*) FROM freelancer_notifications 
            WHERE freelancer_id = %s 
            AND message = %s 
            AND title = %s 
            AND related_entity_type = %s 
            AND related_entity_id = %s 
            AND created_at > NOW() - INTERVAL '5 minutes'
        """, (freelancer_id, message, title, related_entity_type or '', related_entity_id or 0))
        
        duplicate_count = cur.fetchone()[0]
        if duplicate_count > 0:
            print(f"⚠️  Duplicate notification prevented for freelancer {freelancer_id}: {title}")
            conn.close()
            return True
        
        # Insert notification into freelancer_notifications table
        cur.execute("""
            INSERT INTO freelancer_notifications 
            (freelancer_id, message, title, related_entity_type, related_entity_id, created_at, is_read)
            VALUES (%s, %s, %s, %s, %s, NOW(), false)
        """, (freelancer_id, message, title, related_entity_type, related_entity_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Notification sent to freelancer {freelancer_id}: {message}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending notification to freelancer {freelancer_id}: {str(e)}")
        return False

def notify_client(client_id, message, title, related_entity_type=None, related_entity_id=None):
    """
    Send notification to client with duplicate prevention and proper error handling
    """
    if not client_id or not message or not title:
        print(f"❌ Invalid notification parameters: client_id={client_id}, has_message={bool(message)}, has_title={bool(title)}")
        return False
    
    try:
        conn = db.client_db()
        cur = conn.cursor()
        
        # Check for duplicate notification in last 5 minutes
        cur.execute("""
            SELECT COUNT(*) FROM client_notifications 
            WHERE client_id = %s 
            AND message = %s 
            AND title = %s 
            AND related_entity_type = %s 
            AND related_entity_id = %s 
            AND created_at > NOW() - INTERVAL '5 minutes'
        """, (client_id, message, title, related_entity_type or '', related_entity_id or 0))
        
        duplicate_count = cur.fetchone()[0]
        if duplicate_count > 0:
            print(f"⚠️  Duplicate notification prevented for client {client_id}: {title}")
            conn.close()
            return True
        
        # Insert notification into client_notifications table
        cur.execute("""
            INSERT INTO client_notifications 
            (client_id, message, title, related_entity_type, related_entity_id, created_at, is_read)
            VALUES (%s, %s, %s, %s, %s, NOW(), false)
        """, (client_id, message, title, related_entity_type, related_entity_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Notification sent to client {client_id}: {message}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending notification to client {client_id}: {str(e)}")
        return False

def get_client_notifications(client_id, limit=50):
    """
    Get client notifications with proper ordering and error handling
    """
    if not client_id:
        return []
    
    try:
        conn = db.client_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT message, title, related_entity_type, related_entity_id, created_at, is_read
            FROM client_notifications 
            WHERE client_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (client_id, limit))
        
        notifications = []
        for row in cur.fetchall():
            notifications.append({
                'message': row[0],
                'title': row[1],
                'related_entity_type': row[2],
                'related_entity_id': row[3],
                'created_at': row[4],
                'is_read': row[5]
            })
        
        conn.close()
        return notifications
        
    except Exception as e:
        print(f"❌ Error fetching client notifications for {client_id}: {str(e)}")
        return []

def get_freelancer_notifications(freelancer_id, limit=50):
    """
    Get freelancer notifications with proper ordering and error handling
    """
    if not freelancer_id:
        return []
    
    try:
        conn = db.freelancer_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT message, title, related_entity_type, related_entity_id, created_at, is_read
            FROM freelancer_notifications 
            WHERE freelancer_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (freelancer_id, limit))
        
        notifications = []
        for row in cur.fetchall():
            notifications.append({
                'message': row[0],
                'title': row[1],
                'related_entity_type': row[2],
                'related_entity_id': row[3],
                'created_at': row[4],
                'is_read': row[5]
            })
        
        conn.close()
        return notifications
        
    except Exception as e:
        print(f"❌ Error fetching freelancer notifications for {freelancer_id}: {str(e)}")
        return []
