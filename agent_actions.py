import re
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from database import get_latest_hire_requests_for_client, get_latest_hire_requests_for_freelancer
from database import get_latest_messages_for_client, get_latest_messages_for_freelancer


# Lightweight conversation memory for agent layer
AGENT_MEMORY = {}


def parse_natural_language_command(message: str) -> Dict[str, Any]:
    """
    Parse natural language commands into structured actions.
    
    Examples:
    - "hire john" → {"type": "action", "action": "hire_freelancer", "parameters": {"name": "john"}}
    - "hire john with budget 300" → {"type": "action", "action": "hire_freelancer", "parameters": {"name": "john", "budget": "300"}}
    - "message alex hello" → {"type": "action", "action": "send_message", "parameters": {"name": "alex", "message": "hello"}}
    - "call david" → {"type": "action", "action": "start_call", "parameters": {"name": "david"}}
    - "save rahul" → {"type": "action", "action": "save_freelancer", "parameters": {"name": "rahul"}}
    - "accept request 4" → {"type": "action", "action": "handle_request", "parameters": {"action_type": "accept", "request_id": "4"}}
    - "reject request 4" → {"type": "action", "action": "handle_request", "parameters": {"action_type": "reject", "request_id": "4"}}
    - "give me his location" → {"type": "action", "action": "get_freelancer_info", "parameters": {"field": "location"}}
    - "show my requests" → {"type": "action", "action": "show_my_requests", "parameters": {}}
    - "show my messages" → {"type": "action", "action": "show_my_messages", "parameters": {}}
    """
    
    message = message.strip().lower()
    
    # Pattern matching for different command types
    patterns = [
        # Hire commands with optional budget: "hire john", "hire john with budget 300", "hire john budget 300"
        {
            "pattern": r'^hire\s+(?:freelancer\s+)?(\w+(?:\s+\w+)*?)(?:\s+(?:with\s+)?(?:my\s+)?(?:proposed\s+)?budget\s+(\d+))?$',
            "action": "hire_freelancer",
            "param_mapping": {"name": 1, "budget": 2}
        },
        
        # Save commands: "save alex", "save freelancer alex"
        {
            "pattern": r'^save\s+(?:freelancer\s+)?(\w+(?:\s+\w+)*)$',
            "action": "save_freelancer", 
            "param_mapping": {"name": 1}
        },
        
        # Call commands: "call david", "call freelancer david"
        {
            "pattern": r'^call\s+(?:freelancer\s+)?(\w+(?:\s+\w+)*)$',
            "action": "start_call",
            "param_mapping": {"name": 1}
        },
        
        # Message commands: "message alex hello how are you", "msg alex hi"
        {
            "pattern": r'^(?:message|msg)\s+(\w+)\s+(.+)$',
            "action": "send_message",
            "param_mapping": {"name": 1, "message": 2}
        },
        
        # Accept/Reject request commands: "accept request 4", "reject request 4"
        {
            "pattern": r'^(accept|reject)\s+request\s+(\d+)$',
            "action": "handle_request",
            "param_mapping": {"action_type": 1, "request_id": 2}
        },
        
        # Show requests: "show my requests", "my requests", "requests"
        {
            "pattern": r'^(?:show\s+)?my\s+requests?$',
            "action": "show_my_requests",
            "param_mapping": {}
        },
        
        # Show messages: "show my messages", "my messages", "messages", "inbox"
        {
            "pattern": r'^(?:show\s+)?my\s+messages?$|^inbox$',
            "action": "show_my_messages",
            "param_mapping": {}
        },
        
        # Context-aware commands: "give me his location", "give me his budget", "what is his location"
        {
            "pattern": r'^(?:give\s+me\s+)?(?:what\s+is\s+)?(?:his|her|their)\s+(location|budget|experience|category|skills)$',
            "action": "get_freelancer_info",
            "param_mapping": {"field": 1}
        },
        
        # Query freelancers: "show freelancers", "list freelancers", "freelancers"
        {
            "pattern": r'^(?:show\s+)?(?:all\s+)?freelancers?$|^list\s+freelancers?$',
            "action": "query_freelancers",
            "param_mapping": {}
        }
    ]
    
    for pattern_info in patterns:
        match = re.match(pattern_info["pattern"], message, re.IGNORECASE)
        if match:
            parameters = {}
            for param_name, group_index in pattern_info["param_mapping"].items():
                param_value = match.group(group_index).strip() if match.group(group_index) else ""
                if param_value:
                    parameters[param_name] = param_value
            
            return {
                "type": "action",
                "action": pattern_info["action"],
                "parameters": parameters
            }
    
    # If no pattern matches, return None to let the existing AI handle it
    return None


def resolve_freelancer_name(name: str) -> Optional[int]:
    """
    Resolve freelancer name to freelancer_id using improved search logic.
    Returns the freelancer_id if found, None otherwise.
    """
    try:
        conn = sqlite3.connect("freelancer.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # First try exact match
        cur.execute("""
            SELECT id, name FROM freelancer 
            WHERE LOWER(name) = LOWER(?)
        """, (name.strip(),))
        
        result = cur.fetchone()
        if result:
            return result["id"]
        
        # Try partial match with better scoring
        cur.execute("""
            SELECT id, name FROM freelancer 
            WHERE LOWER(name) LIKE LOWER(?)
            ORDER BY 
                CASE 
                    WHEN LOWER(name) = LOWER(?) THEN 1
                    WHEN LOWER(name) LIKE LOWER(?) THEN 2
                    ELSE 3
                END,
                LENGTH(name)
            LIMIT 5
        """, (f"%{name.strip()}%", name.strip(), f"{name.strip()}%"))
        
        results = cur.fetchall()
        if results:
            # Return best match (first in ordered results)
            return results[0]["id"]
        
        conn.close()
        return None
        
    except Exception as e:
        print(f"Error resolving freelancer name '{name}': {e}")
        return None


def execute_agent_action(user_id: int, role: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute agent actions with name resolution and existing logic integration.
    """
    
    # Role validation
    if role == "client":
        allowed_actions = ["hire_freelancer", "save_freelancer", "send_message", "start_call", "query_freelancers", "show_my_requests", "show_my_messages", "handle_request", "get_freelancer_info"]
    elif role == "freelancer":
        allowed_actions = ["send_message", "start_call", "query_freelancers", "show_my_requests", "show_my_messages", "handle_request", "get_freelancer_info"]
    else:
        return {"type": "answer", "text": "Invalid role specified."}
    
    if action not in allowed_actions:
        return {"type": "answer", "text": f"Action '{action}' is not allowed for your role."}
    
    try:
        if action == "hire_freelancer":
            return _handle_hire_freelancer(user_id, parameters)
        elif action == "save_freelancer":
            return _handle_save_freelancer(user_id, parameters)
        elif action == "send_message":
            return _handle_send_message(user_id, role, parameters)
        elif action == "start_call":
            return _handle_start_call(user_id, role, parameters)
        elif action == "query_freelancers":
            return _handle_query_freelancers(parameters)
        elif action == "show_my_requests":
            return _handle_show_my_requests(user_id, role)
        elif action == "show_my_messages":
            return _handle_show_my_messages(user_id, role)
        elif action == "handle_request":
            return _handle_request_action(user_id, role, parameters)
        elif action == "get_freelancer_info":
            return _handle_get_freelancer_info(user_id, role, parameters)
        else:
            return {"type": "answer", "text": "Action not implemented yet."}
            
    except Exception as e:
        return {"type": "answer", "text": f"Error executing action: {str(e)}"}


def _handle_hire_freelancer(user_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle hire freelancer with name resolution and budget support"""
    freelancer_name = parameters.get("name", "")
    budget = parameters.get("budget")  # Optional budget
    
    if not freelancer_name:
        return {"type": "answer", "text": "Please specify which freelancer you want to hire."}
    
    # Resolve name to ID
    freelancer_id = resolve_freelancer_name(freelancer_name)
    if not freelancer_id:
        return {"type": "answer", "text": "Freelancer not found."}
    
    # Store in memory for context
    AGENT_MEMORY[user_id] = {
        "last_freelancer_id": freelancer_id,
        "last_freelancer_name": freelancer_name
    }
    
    # Use existing hire logic from database
    try:
        import sqlite3
        from datetime import datetime
        
        # hire_request table is in freelancer.db
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        
        # Insert hire request with optional budget
        if budget:
            cur.execute("""
                INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, freelancer_id, "Hire Request", float(budget), "PENDING", int(datetime.now().timestamp())))
        else:
            cur.execute("""
                INSERT INTO hire_request (client_id, freelancer_id, job_title, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, freelancer_id, "Hire Request", "PENDING", int(datetime.now().timestamp())))
        
        conn.commit()
        conn.close()
        
        budget_text = f" with budget {budget}" if budget else ""
        return {"type": "answer", "text": f"Hire request sent to {freelancer_name.title()}{budget_text}."}
        
    except Exception as e:
        return {"type": "answer", "text": f"Failed to send hire request: {str(e)}"}


def _handle_save_freelancer(user_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle save freelancer with name resolution"""
    freelancer_name = parameters.get("name", "")
    
    if not freelancer_name:
        return {"type": "answer", "text": "Please specify which freelancer you want to save."}
    
    # Resolve name to ID
    freelancer_id = resolve_freelancer_name(freelancer_name)
    if not freelancer_id:
        return {"type": "answer", "text": "Freelancer not found."}
    
    # Store in memory for context
    AGENT_MEMORY[user_id] = {
        "last_freelancer_id": freelancer_id,
        "last_freelancer_name": freelancer_name
    }
    
    # Use existing save logic
    try:
        import sqlite3
        
        # saved_freelancer table is in freelancer.db
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        
        # Insert into saved freelancers
        cur.execute("""
            INSERT OR IGNORE INTO saved_freelancer (client_id, freelancer_id)
            VALUES (?, ?)
        """, (user_id, freelancer_id))
        
        conn.commit()
        conn.close()
        
        return {"type": "answer", "text": f"{freelancer_name.title()} saved to your favorites."}
        
    except Exception as e:
        return {"type": "answer", "text": f"Failed to save freelancer: {str(e)}"}


def _handle_send_message(user_id: int, role: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle send message with name resolution"""
    freelancer_name = parameters.get("name", "")
    message_text = parameters.get("message", "")
    
    if not freelancer_name:
        return {"type": "answer", "text": "Please specify who you want to message."}
    
    if not message_text:
        return {"type": "answer", "text": "Please include a message to send."}
    
    # Resolve name to ID
    freelancer_id = resolve_freelancer_name(freelancer_name)
    if not freelancer_id:
        return {"type": "answer", "text": "Freelancer not found."}
    
    # Store in memory for context
    AGENT_MEMORY[user_id] = {
        "last_freelancer_id": freelancer_id,
        "last_freelancer_name": freelancer_name
    }
    
    # Use existing message logic
    try:
        import sqlite3
        
        # message table is in freelancer.db
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        
        # Insert message
        cur.execute("""
            INSERT INTO message (sender_role, sender_id, receiver_id, text, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (role, user_id, freelancer_id, message_text, int(datetime.now().timestamp())))
        
        conn.commit()
        conn.close()
        
        return {"type": "answer", "text": f"Message sent to {freelancer_name.title()}."}
        
    except Exception as e:
        return {"type": "answer", "text": f"Failed to send message: {str(e)}"}


def _handle_start_call(user_id: int, role: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle start call with name resolution"""
    freelancer_name = parameters.get("name", "")
    
    if not freelancer_name:
        return {"type": "answer", "text": "Please specify who you want to call."}
    
    # Resolve name to ID
    freelancer_id = resolve_freelancer_name(freelancer_name)
    if not freelancer_id:
        return {"type": "answer", "text": "Freelancer not found."}
    
    # Store in memory for context
    AGENT_MEMORY[user_id] = {
        "last_freelancer_id": freelancer_id,
        "last_freelancer_name": freelancer_name
    }
    
    # Generate a simple meeting room ID
    import random
    import string
    room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    return {"type": "answer", "text": f"Call started with {freelancer_name.title()}. Meeting room: {room_id}"}


def _handle_query_freelancers(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle query freelancers action and store first one in memory"""
    try:
        import sqlite3
        
        conn = sqlite3.connect("freelancer.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = """
            SELECT
                f.id,
                f.name,
                COALESCE(fp.title, '') as title,
                COALESCE(fp.skills, '') as skills,
                COALESCE(fp.experience, 0) as experience,
                COALESCE(fp.min_budget, 0) as min_budget,
                COALESCE(fp.max_budget, 0) as max_budget,
                COALESCE(fp.category, '') as category,
                COALESCE(fp.location, '') as location,
                COALESCE(fp.bio, '') as bio
            FROM freelancer f
            LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
            ORDER BY f.id DESC
            LIMIT 10
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        
        if not rows:
            return {"type": "answer", "text": "No freelancers found."}
        
        # Store first freelancer in memory for context
        if rows:
            first_freelancer = dict(rows[0])
            # Store in a generic memory key that can be accessed by context commands
            AGENT_MEMORY["last_query_freelancer"] = {
                "id": first_freelancer["id"],
                "name": first_freelancer["name"]
            }
        
        # Format natural list of freelancers
        result_text = "Available freelancers:\n\n"
        for i, row in enumerate(rows, 1):  # Limit to 10 results
            freelancer = dict(row)
            result_text += f"{i}. {freelancer['name']} — {freelancer['title'] or 'No title'}\n"
            if freelancer['experience']:
                result_text += f"Experience: {freelancer['experience']} years\n"
            if freelancer['min_budget'] or freelancer['max_budget']:
                result_text += f"Budget: {freelancer['min_budget']} - {freelancer['max_budget']}\n"
            if freelancer['location']:
                result_text += f"Location: {freelancer['location']}\n"
            result_text += "\n"
        
        return {"type": "answer", "text": result_text.strip()}
        
    except Exception as e:
        return {"type": "answer", "text": f"Error fetching freelancers: {str(e)}"}


def _handle_show_my_requests(user_id: int, role: str) -> Dict[str, Any]:
    """Handle show my requests action"""
    try:
        if role == "client":
            requests = get_latest_hire_requests_for_client(user_id, 10)
        else:
            requests = get_latest_hire_requests_for_freelancer(user_id, 10)
        
        if not requests:
            return {"type": "answer", "text": "You have no recent requests."}
        
        result_text = "Your recent requests:\n\n"
        for req in requests:
            status_emoji = "⏳" if req.get("status") == "PENDING" else "✅" if req.get("status") == "ACCEPTED" else "❌"
            result_text += f"{status_emoji} Request {req.get('id')}: {req.get('job_title', 'No title')}\n"
            result_text += f"Status: {req.get('status', 'Unknown')}\n\n"
        
        return {"type": "answer", "text": result_text.strip()}
        
    except Exception as e:
        return {"type": "answer", "text": f"Error fetching requests: {str(e)}"}


def _handle_show_my_messages(user_id: int, role: str) -> Dict[str, Any]:
    """Handle show my messages action"""
    try:
        if role == "client":
            messages = get_latest_messages_for_client(user_id, 10)
        else:
            messages = get_latest_messages_for_freelancer(user_id, 10)
        
        if not messages:
            return {"type": "answer", "text": "You have no recent messages."}
        
        result_text = "Your recent messages:\n\n"
        for msg in messages:
            sender = msg.get("sender_name", "Unknown")
            result_text += f"📨 From {sender}: {msg.get('message', 'No message')}\n\n"
        
        return {"type": "answer", "text": result_text.strip()}
        
    except Exception as e:
        return {"type": "answer", "text": f"Error fetching messages: {str(e)}"}


def _handle_request_action(user_id: int, role: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle accept/reject request action"""
    action_type = parameters.get("action_type", "")
    request_id = parameters.get("request_id", "")
    
    if not action_type or not request_id:
        return {"type": "answer", "text": "Please specify action type and request ID."}
    
    try:
        import sqlite3
        
        # hire_request table is in freelancer.db
        conn = sqlite3.connect("freelancer.db")
        cur = conn.cursor()
        
        # Check if request exists and belongs to user
        if role == "client":
            cur.execute("""
                SELECT id FROM hire_request 
                WHERE id = ? AND client_id = ?
            """, (int(request_id), user_id))
        else:  # freelancer
            cur.execute("""
                SELECT id FROM hire_request 
                WHERE id = ? AND freelancer_id = ?
            """, (int(request_id), user_id))
        
        result = cur.fetchone()
        if not result:
            return {"type": "answer", "text": "Request not found."}
        
        # Update request status
        new_status = "ACCEPTED" if action_type == "accept" else "REJECTED"
        cur.execute("""
            UPDATE hire_request 
            SET status = ? 
            WHERE id = ?
        """, (new_status, int(request_id)))
        
        conn.commit()
        
        # Get request details for notification
        cur.execute("""
            SELECT client_id, freelancer_id, job_title 
            FROM hire_request 
            WHERE id = ?
        """, (int(request_id),))
        req_data = cur.fetchone()
        
        if req_data:
            client_id, freelancer_id, job_title = req_data
            job_title = job_title or "Untitled"
            
            # Create notifications
            from notification_helper import notify_client, notify_freelancer
            
            if action_type == "accept":
                # Notify client that freelancer accepted
                notify_client(
                    client_id=client_id,
                    message=f'Freelancer accepted your job request: "{job_title}"',
                    title="Request Accepted",
                    related_entity_type="hire_request",
                    related_entity_id=int(request_id)
                )
                
                # Notify freelancer of their own acceptance (confirmation)
                notify_freelancer(
                    freelancer_id=freelancer_id,
                    message=f'You accepted the job request: "{job_title}"',
                    title="Request Accepted",
                    related_entity_type="hire_request",
                    related_entity_id=int(request_id)
                )
                
            else:  # reject
                # Notify client that freelancer rejected
                notify_client(
                    client_id=client_id,
                    message=f'Freelancer rejected your job request: "{job_title}"',
                    title="Request Rejected",
                    related_entity_type="hire_request",
                    related_entity_id=int(request_id)
                )
                
                # Notify freelancer of their own rejection (confirmation)
                notify_freelancer(
                    freelancer_id=freelancer_id,
                    message=f'You rejected the job request: "{job_title}"',
                    title="Request Rejected",
                    related_entity_type="hire_request",
                    related_entity_id=int(request_id)
                )
        
        conn.close()
        
        return {"type": "answer", "text": f"Request {request_id} {new_status.lower()}."}
        
    except Exception as e:
        return {"type": "answer", "text": f"Failed to update request: {str(e)}"}


def _handle_get_freelancer_info(user_id: int, role: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle context-aware freelancer info requests"""
    field = parameters.get("field", "")
    
    if not field:
        return {"type": "answer", "text": "Please specify what information you want."}
    
    # Try to get freelancer from memory
    freelancer_info = AGENT_MEMORY.get(user_id) or AGENT_MEMORY.get("last_query_freelancer")
    
    if not freelancer_info:
        return {"type": "answer", "text": "No freelancer context found. Please search for a freelancer first."}
    
    freelancer_id = freelancer_info.get("last_freelancer_id") or freelancer_info.get("id")
    freelancer_name = freelancer_info.get("last_freelancer_name") or freelancer_info.get("name")
    
    if not freelancer_id:
        return {"type": "answer", "text": "No freelancer context found. Please search for a freelancer first."}
    
    try:
        import sqlite3
        
        conn = sqlite3.connect("freelancer.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get freelancer details
        cur.execute("""
            SELECT
                f.name,
                COALESCE(fp.title, '') as title,
                COALESCE(fp.skills, '') as skills,
                COALESCE(fp.experience, 0) as experience,
                COALESCE(fp.min_budget, 0) as min_budget,
                COALESCE(fp.max_budget, 0) as max_budget,
                COALESCE(fp.category, '') as category,
                COALESCE(fp.location, '') as location,
                COALESCE(fp.bio, '') as bio
            FROM freelancer f
            LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
            WHERE f.id = ?
        """, (freelancer_id,))
        
        result = cur.fetchone()
        conn.close()
        
        if not result:
            return {"type": "answer", "text": "Freelancer not found."}
        
        freelancer = dict(result)
        
        # Return requested field
        if field == "location":
            location = freelancer.get("location", "Not specified")
            return {"type": "answer", "text": f"{freelancer_name.title()} is located in {location}."}
        elif field == "budget":
            min_budget = freelancer.get("min_budget", 0)
            max_budget = freelancer.get("max_budget", 0)
            if min_budget or max_budget:
                return {"type": "answer", "text": f"{freelancer_name.title()}'s budget range is {min_budget} - {max_budget}."}
            else:
                return {"type": "answer", "text": f"{freelancer_name.title()} has not specified a budget range."}
        elif field == "experience":
            experience = freelancer.get("experience", 0)
            return {"type": "answer", "text": f"{freelancer_name.title()} has {experience} years of experience."}
        elif field == "category":
            category = freelancer.get("category", "Not specified")
            return {"type": "answer", "text": f"{freelancer_name.title()} works in {category}."}
        elif field == "skills":
            skills = freelancer.get("skills", "Not specified")
            return {"type": "answer", "text": f"{freelancer_name.title()}'s skills: {skills}."}
        else:
            return {"type": "answer", "text": f"Information about '{field}' is not available."}
        
    except Exception as e:
        return {"type": "answer", "text": f"Error fetching freelancer information: {str(e)}"}
