"""
Call Service for Voice/Video Calls using Jitsi Meet
"""
import uuid
from database import freelancer_db, get_dict_cursor

def generate_room_name(caller_id: int, receiver_id: int):
    """Generate unique room name for Jitsi Meet"""
    import time
    timestamp = int(time.time())
    return f"gigbridge_{caller_id}*{receiver_id}*{timestamp}"

def check_call_permission(caller_id: int, receiver_id: int):
    """Check if caller has permission to call receiver"""
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        
        # Check if they have interacted through projects, hire requests, or messages
        cur.execute("""
            SELECT 1 FROM hire_request 
            WHERE (client_id = %s AND freelancer_id = %s) 
               OR (client_id = %s AND freelancer_id = %s)
            UNION
            SELECT 1 FROM project_application pa
            JOIN project_post pp ON pa.project_id = pp.id
            WHERE (pp.client_id = %s AND pa.freelancer_id = %s)
               OR (pp.client_id = %s AND pa.freelancer_id = %s)
            UNION
            SELECT 1 FROM messages
            WHERE (sender_id = %s AND receiver_id = %s)
               OR (sender_id = %s AND receiver_id = %s)
            LIMIT 1
        """, (caller_id, receiver_id, receiver_id, caller_id, 
              caller_id, receiver_id, receiver_id, caller_id,
              caller_id, receiver_id, receiver_id, caller_id))
        
        result = cur.fetchone()
        conn.close()
        return result is not None
    except Exception:
        return False

def start_call(caller_id: int, receiver_id: int, call_type: str):
    """Start a new call"""
    try:
        if call_type not in ["voice", "video"]:
            return None, "Invalid call type"
        
        # Safety validation: caller cannot call themselves
        if caller_id == receiver_id:
            return None, "Cannot call yourself"
        
        room_name = generate_room_name(caller_id, receiver_id)
        meeting_url = f"https://meet.jit.si/{room_name}"
        
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        
        cur.execute("""
            INSERT INTO calls (caller_id, receiver_id, call_type, room_name, status)
            VALUES (%s, %s, %s, %s, 'ringing')
            RETURNING call_id
        """, (caller_id, receiver_id, call_type, room_name))
        
        result = cur.fetchone()
        call_id = result["call_id"] if isinstance(result, dict) else result[0]
        
        conn.commit()
        conn.close()
        
        return {
            "call_id": call_id,
            "meeting_url": meeting_url,
            "room_name": room_name
        }, None
        
    except Exception as e:
        return None, str(e)

def update_call_status(call_id: int, status: str):
    """Update call status"""
    try:
        if status not in ["ringing", "accepted", "rejected", "ended"]:
            return False, "Invalid status"
        
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        
        cur.execute("""
            UPDATE calls SET status = %s 
            WHERE call_id = %s
        """, (status, call_id))
        
        conn.commit()
        conn.close()
        return True, None
        
    except Exception as e:
        return False, str(e)

def get_incoming_calls(user_id: int):
    """Get incoming calls for a user"""
    try:
        if not user_id:
            return []
            
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        
        cur.execute("""
            SELECT c.call_id, c.caller_id, c.receiver_id, c.call_type, 
                   c.room_name, c.status, c.created_at,
                   f.name as caller_name, cl.name as client_name
            FROM calls c
            LEFT JOIN freelancer f ON f.id = c.caller_id
            LEFT JOIN client cl ON cl.id = c.caller_id
            WHERE c.receiver_id = %s AND c.status = 'ringing'
            ORDER BY c.created_at DESC
        """, (user_id,))
        
        calls = cur.fetchall()
        conn.close()
        
        result = []
        for call in calls:
            room_name = call.get("room_name")
            meeting_url = f"https://meet.jit.si/{room_name}" if room_name else None
            
            result.append({
                "call_id": call.get("call_id"),
                "caller_id": call.get("caller_id"),
                "receiver_id": call.get("receiver_id"),
                "call_type": call.get("call_type"),
                "room_name": room_name,
                "status": call.get("status"),
                "created_at": call.get("created_at"),
                "caller_name": call.get("caller_name") or call.get("client_name", "Unknown"),
                "meeting_url": meeting_url
            })
        
        return result
        
    except Exception as e:
        print(f"Error in get_incoming_calls: {str(e)}")
        return []
