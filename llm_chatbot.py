import os
import os
import requests
import json
import re
from typing import Tuple, Dict, Any, List

from categories import CATEGORIES
from database import (
    get_latest_hire_requests_for_client,
    get_latest_hire_requests_for_freelancer,
    get_latest_messages_for_client,
    get_latest_messages_for_freelancer,
    get_latest_notifications_for_client,
    get_client_profile,
    get_freelancer_profile,
)

# === AI CHATBOT ADDITION ===
# Gemini config
# API key loaded from environment variable GEMINI_API_KEY

# Lightweight in-memory conversation memory (per user_id)
CONVERSATION_MEMORY = {}

# === AI CHATBOT ADDITION ===
# In-memory knowledge base snippets about GigBridge
KB_SNIPPETS = [
    {
        "title": "Sign up and login",
        "content": "Use OTP signup then login with email and password. Never share OTP.",
        "keywords": ["signup", "login", "otp", "verify", "password"],
    },
    {
        "title": "Search freelancers",
        "content": "Use /freelancers/search with category and budget. Or /freelancers/all to browse.",
        "keywords": ["search", "category", "budget", "freelancers", "browse"],
    },
    {
        "title": "Send messages",
        "content": "Clients and freelancers can chat via /client/message/send or /freelancer/message/send.",
        "keywords": ["message", "chat", "inbox", "send"],
    },
    {
        "title": "Hire requests",
        "content": "Clients send hire requests. Status values: PENDING, ACCEPTED, REJECTED.",
        "keywords": ["hire", "request", "status", "job", "accept", "reject"],
    },
    {
        "title": "Job request status meanings",
        "content": "PENDING: awaiting freelancer response. ACCEPTED: confirmed. REJECTED: declined.",
        "keywords": ["pending", "accepted", "rejected", "job", "status"],
    },
    {
        "title": "Notifications",
        "content": "Clients see app updates in /client/notifications.",
        "keywords": ["notification", "updates", "client"],
    },
    {
        "title": "Allowed categories",
        "content": "Valid categories: " + ", ".join(CATEGORIES),
        "keywords": ["categories", "category", "skills"],
    },
    {
        "title": "Video Calls",
        "content": "GigBridge supports video calls using Jitsi Meet. Users join shared meeting rooms created by the system.",
        "keywords": ["call", "video", "meeting", "jitsi"],
    },
    {
        "title": "Location-based ranking",
        "content": "Freelancers are ranked using PIN code geocoding and distance calculation.",
        "keywords": ["location", "nearby", "distance", "pin"],
    },
    {
        "title": "AI Assistant",
        "content": "The AI assistant can help with platform navigation and show your recent activity.",
        "keywords": ["ai", "assistant", "chatbot"],
    },
]


def _pick_kb_snippets(user_text: str, top_n: int = 3) -> List[Dict[str, Any]]:
    t = (user_text or "").lower()
    words = [w for w in "".join([c if c.isalnum() else " " for c in t]).split() if w]
    scores = []
    for snip in KB_SNIPPETS:
        kw = set(snip.get("keywords", []))
        overlap = len([w for w in words if w in kw or w in snip["content"].lower() or w in snip["title"].lower()])
        scores.append((overlap, snip))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [s for score, s in scores[:top_n] if score > 0] or KB_SNIPPETS[:1]


def _intent_route_and_fetch(user_id: int, role: str, message: str) -> Tuple[Dict[str, Any], List[str]]:
    text = (message or "").lower()
    db_payload: Dict[str, Any] = {}
    sources: List[str] = ["kb"]

    try:
        if any(k in text for k in ["my requests", "hire status", "job status", "my jobs"]):
            if role == "client":
                db_payload["hire_requests"] = get_latest_hire_requests_for_client(user_id, 10)
            else:
                db_payload["hire_requests"] = get_latest_hire_requests_for_freelancer(user_id, 10)
            sources.append("db")
        elif any(k in text for k in ["my messages", "inbox", "chat history"]):
            if role == "client":
                db_payload["messages"] = get_latest_messages_for_client(user_id, 10)
            else:
                db_payload["messages"] = get_latest_messages_for_freelancer(user_id, 10)
            sources.append("db")
        elif any(k in text for k in ["my notifications", "alerts", "updates"]):
            if role == "client":
                db_payload["notifications"] = get_latest_notifications_for_client(user_id, 10)
                sources.append("db")
            else:
                db_payload["notifications"] = []
        elif ("my" in text) and any(k in text for k in ["profile", "location", "email", "phone", "bio"]):
            if role == "client":
                db_payload["profile"] = get_client_profile(user_id)
            else:
                db_payload["profile"] = get_freelancer_profile(user_id)
            sources.append("db")
    except Exception:
        pass

    # dedupe sources
    sources = list(dict.fromkeys(sources))
    return db_payload, sources


def _build_llm_prompt(user_msg: str, kb_snips: List[Dict[str, Any]], db_payload: Dict[str, Any], memory: List[str] = None) -> str:
    system_rules = (
        "You are GigBridge Intelligent Agent.\n"
        "You must respond ONLY in valid JSON.\n"
        "If user wants to perform an operation, return:\n"
        "{\n"
        "  \"type\": \"action\",\n"
        "  \"action\": \"action_name\",\n"
        "  \"parameters\": { ... }\n"
        "}\n"
        "If user wants information only, return:\n"
        "{\n"
        "  \"type\": \"answer\",\n"
        "  \"text\": \"natural response here\"\n"
        "}\n"
        "Never include explanations outside JSON.\n\n"
        "CRITICAL: For attribute-specific queries, you MUST use this exact format:\n"
        "User: \"what is location of se\" → {\"type\": \"action\", \"action\": \"query_freelancers\", \"parameters\": {\"filters\": {\"name\": \"se\"}, \"fields\": [\"location\"]}}\n"
        "User: \"what is budget of se\" → {\"type\": \"action\", \"action\": \"query_freelancers\", \"parameters\": {\"filters\": {\"name\": \"se\"}, \"fields\": [\"budget_range\"]}}\n"
        "User: \"where is se located\" → {\"type\": \"action\", \"action\": \"query_freelancers\", \"parameters\": {\"filters\": {\"name\": \"se\"}, \"fields\": [\"location\"]}}\n\n"
        "For general queries like \"show all freelancers\":\n"
        "Use: {\"type\": \"action\", \"action\": \"query_freelancers\", \"parameters\": {\"filters\": {}, \"fields\": []}}\n\n"
        "If user asks to hire/book:\n"
        "Use action = hire_freelancer.\n\n"
        "Always map natural language into structured filters.\n\n"
        "Allowed actions:\n"
        "- query_freelancers\n"
        "- hire_freelancer\n"
        "- save_freelancer\n"
        "- show_my_requests\n"
        "- accept_request\n"
        "- reject_request\n"
        "- show_my_profile\n"
        "- send_message"
    )
    kb_text = "\n".join([f"- {s['title']}: {s['content']}" for s in kb_snips])
    db_text = "" if not db_payload else f"\nUserData (JSON): {db_payload}"
    mem_list = memory or []
    mem_text = ""
    if mem_list:
        mem_text = "Previous Conversation:\n" + "\n".join([f"- {m}" for m in mem_list])
    allowed_actions = "\n".join([
        "- query_freelancers",
        "- hire_freelancer",
        "- save_freelancer",
        "- show_my_requests",
        "- send_message",
        "- accept_request",
        "- reject_request",
        "- show_my_profile",
    ])
    prompt = (
        f"{system_rules}\n\n"
        f"Knowledge Base:\n{kb_text}\n"
        f"{db_text}\n\n"
        f"Allowed actions:\n{allowed_actions}\n\n"
        f"{mem_text}\n\n" if mem_text else f"{db_text}\n\n"
        f"User Question:\n{user_msg}\n\n"
        f"Provide a concise helpful answer."
    )
    return prompt




# In-memory storage for pending actions (confirmations)
PENDING_ACTIONS = {}

def execute_agent_action(user_id: int, role: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute agent actions based on user role and action type"""
    
    # Role validation
    if role == "client":
        allowed_actions = ["query_freelancers", "hire_freelancer", "save_freelancer", "show_my_requests", "send_message", "show_my_profile"]
    elif role == "freelancer":
        allowed_actions = ["show_my_requests", "accept_request", "reject_request", "show_my_profile", "send_message"]
    else:
        return {"type": "answer", "text": "Invalid role specified."}
    
    if action not in allowed_actions:
        return {"type": "answer", "text": f"Action '{action}' is not allowed for your role."}
    
    try:
        if action == "query_freelancers":
            return _handle_query_freelancers(parameters)
        elif action == "hire_freelancer":
            return _handle_hire_freelancer(user_id, parameters)
        elif action == "save_freelancer":
            return _handle_save_freelancer(user_id, parameters)
        elif action == "show_my_requests":
            return _handle_show_my_requests(user_id, role)
        elif action == "accept_request":
            return _handle_accept_request(user_id, parameters)
        elif action == "reject_request":
            return _handle_reject_request(user_id, parameters)
        elif action == "show_my_profile":
            return _handle_show_my_profile(user_id, role)
        elif action == "send_message":
            return _handle_send_message(user_id, role, parameters)
        else:
            return {"type": "answer", "text": "Action not implemented yet."}
    except Exception as e:
        return {"type": "answer", "text": f"Error executing action: {str(e)}"}


def _handle_query_freelancers(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle freelancer queries with dynamic filters"""
    import sqlite3
    
    filters = parameters.get("filters", {})
    fields = parameters.get("fields", [])
    
    # Connect to database
    conn = sqlite3.connect("freelancer.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Build base query
    query = """
        SELECT
            f.id,
            f.name,
            COALESCE(fp.title, '') as title,
            COALESCE(fp.skills, '') as skills,
            COALESCE(fp.experience, 0) as experience,
            COALESCE(fp.min_budget, 0) as min_budget,
            COALESCE(fp.max_budget, 0) as max_budget,
            COALESCE(fp.rating, 0) as rating,
            COALESCE(fp.category, '') as category,
            COALESCE(fp.location, '') as location,
            COALESCE(fp.bio, '') as bio
        FROM freelancer f
        LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
        WHERE 1=1
    """
    
    query_params = []
    
    # Apply dynamic filters
    if "name" in filters:
        query += " AND LOWER(f.name) LIKE ?"
        query_params.append(f"%{filters['name'].lower()}%")
    
    if "category" in filters:
        query += " AND LOWER(fp.category) LIKE ?"
        query_params.append(f"%{filters['category'].lower()}%")
    
    if "max_budget" in filters:
        query += " AND fp.min_budget <= ?"
        query_params.append(float(filters["max_budget"]))
    
    if "min_budget" in filters:
        query += " AND fp.max_budget >= ?"
        query_params.append(float(filters["min_budget"]))
    
    if "location" in filters:
        query += " AND LOWER(fp.location) LIKE ?"
        query_params.append(f"%{filters['location'].lower()}%")
    
    query += " ORDER BY f.id DESC"
    
    cur.execute(query, query_params)
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        return {"type": "answer", "text": "No freelancers found matching your query."}
    
    # Handle attribute-specific answers
    if "name" in filters and len(fields) == 1:
        freelancer = None
        for row in rows:
            if filters["name"].lower() in row["name"].lower():
                freelancer = dict(row)
                break
        
        if freelancer:
            field = fields[0]
            if field == "budget_range":
                return {"type": "answer", "text": f"{freelancer['name']}'s budget range is {freelancer['min_budget']} - {freelancer['max_budget']}."}
            elif field == "location":
                return {"type": "answer", "text": f"{freelancer['name']} is located in {freelancer['location']}."}
            elif field == "experience":
                return {"type": "answer", "text": f"{freelancer['name']} has {freelancer['experience']} years of experience."}
            elif field == "category":
                return {"type": "answer", "text": f"{freelancer['name']} works in {freelancer['category']}."}
    
    # Format natural list of freelancers
    result_text = "Here are the matching freelancers:\n\n"
    for i, row in enumerate(rows[:10], 1):  # Limit to 10 results
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


def _handle_hire_freelancer(user_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle hire freelancer with confirmation flow"""
    freelancer_name = parameters.get("name", "")
    
    if not freelancer_name:
        return {"type": "answer", "text": "Please specify which freelancer you want to hire."}
    
    # Store pending action for confirmation
    action_key = f"{user_id}_hire"
    PENDING_ACTIONS[action_key] = {
        "action": "hire_freelancer",
        "freelancer_name": freelancer_name,
        "parameters": parameters
    }
    
    return {"type": "answer", "text": f"You are about to hire {freelancer_name}. Confirm? (yes/no)"}


def _handle_save_freelancer(user_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle save freelancer action"""
    return {"type": "answer", "text": "Save freelancer feature coming soon."}


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


def _handle_accept_request(user_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle accept request action"""
    return {"type": "answer", "text": "Accept request feature coming soon."}


def _handle_reject_request(user_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle reject request action"""
    return {"type": "answer", "text": "Reject request feature coming soon."}


def _handle_show_my_profile(user_id: int, role: str) -> Dict[str, Any]:
    """Handle show my profile action"""
    try:
        if role == "client":
            profile = get_client_profile(user_id)
        else:
            profile = get_freelancer_profile(user_id)
        
        if not profile:
            return {"type": "answer", "text": "Profile not found."}
        
        result_text = f"Profile for {profile.get('name', 'Unknown')}:\n\n"
        if profile.get("email"):
            result_text += f"Email: {profile['email']}\n"
        if profile.get("location"):
            result_text += f"Location: {profile['location']}\n"
        if profile.get("bio"):
            result_text += f"Bio: {profile['bio']}\n"
        if role == "freelancer":
            if profile.get("category"):
                result_text += f"Category: {profile['category']}\n"
            if profile.get("experience"):
                result_text += f"Experience: {profile['experience']} years\n"
        
        return {"type": "answer", "text": result_text.strip()}
    except Exception as e:
        return {"type": "answer", "text": f"Error fetching profile: {str(e)}"}


def _handle_send_message(user_id: int, role: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle send message action"""
    return {"type": "answer", "text": "Send message feature coming soon."}


def generate_ai_response(user_id: int, role: str, message: str) -> Dict[str, Any]:
    # health mode (used by /ai/health to avoid imports)
    if role == "__health__":
        from gemini_agent import gemini_health
        return {"health": gemini_health()}

    # Greeting handling - detect greetings before calling LLM
    if message.lower() in ["hi", "hello", "hii", "hey"]:
        return {
            "type": "answer",
            "text": "Hi! How can I assist you today?"
        }

    # Handle confirmation responses for pending actions
    message_lower = message.lower()
    if message_lower in ["yes", "y", "confirm"]:
        action_key = f"{user_id}_hire"
        if action_key in PENDING_ACTIONS:
            pending = PENDING_ACTIONS.pop(action_key)
            # Execute the actual hire logic here
            return {"type": "answer", "text": f"Successfully hired {pending['freelancer_name']}!"}
        else:
            return {"type": "answer", "text": "No pending action to confirm."}
    
    if message_lower in ["no", "n", "cancel"]:
        action_key = f"{user_id}_hire"
        if action_key in PENDING_ACTIONS:
            PENDING_ACTIONS.pop(action_key)
            return {"type": "answer", "text": "Action cancelled."}
        else:
            return {"type": "answer", "text": "No pending action to cancel."}

    # lightweight in-memory conversation: keep last 5 user messages
    try:
        uid = int(user_id)
    except Exception:
        uid = user_id
    memory = CONVERSATION_MEMORY.get(uid, [])
    memory = (memory + [message])[-5:]
    CONVERSATION_MEMORY[uid] = memory

    kb = _pick_kb_snippets(message, 3)
    db_payload, sources = _intent_route_and_fetch(user_id, role, message)
    prompt = _build_llm_prompt(message, kb, db_payload, memory)

    # Call Gemini API
    from gemini_agent import call_gemini
    user_context = {"user_id": user_id, "role": role}
    answer = call_gemini(prompt, user_context)
    if not answer:
        answer = kb[0]["content"] if kb else "I can help with GigBridge features and your account info."

    if not db_payload and any(k in (message or "").lower() for k in [
        "my requests", "hire status", "job status", "my messages", "inbox", "my notifications", "my profile"
    ]):
        answer = answer + " If I didn't find anything, it might be because there are no recent items."

    # Safe JSON extraction from LLM output
    raw_output = answer.strip()
    match = re.search(r'\{.*\}', raw_output, re.DOTALL)
    if match:
        json_str = match.group()
        try:
            parsed = json.loads(json_str)
        except Exception:
            return {"type": "answer", "text": raw_output, "sources": sources}
    else:
        return {"type": "answer", "text": raw_output, "sources": sources}

    if isinstance(parsed, dict) and parsed.get("type") == "action":
        # Execute the agent action
        action_name = parsed.get("action")
        action_params = parsed.get("parameters", {})
        return execute_agent_action(user_id, role, action_name, action_params)
    else:
        return {"type": "answer", "text": parsed.get("text", raw_output), "sources": sources}
