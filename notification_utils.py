"""
Enhanced Notification System Utilities
Provides message formatting, type detection, and icon mapping for notifications
"""

def get_notification_icon(message="", title="", related_entity_type=""):
    """
    Get appropriate icon for notification based on content and type
    """
    message_lower = (message or "").lower()
    title_lower = (title or "").lower()
    entity_type = (related_entity_type or "").lower()
    
    # Priority 1: Explicit entity type
    if entity_type:
        if "hire" in entity_type:
            return "📩"
        elif "job" in entity_type:
            return "⏳"
        elif "payment" in entity_type:
            return "💰"
        elif "message" in entity_type:
            return "💬"
        elif "call" in entity_type:
            return "📞"
        elif "verification" in entity_type or "kyc" in entity_type:
            return "🏅"
        elif "subscription" in entity_type:
            return "💎"
    
    # Priority 2: Message content analysis
    if any(keyword in message_lower for keyword in ["hire request", "new job", "job request"]):
        return "📩"
    elif any(keyword in message_lower for keyword in ["accepted", "approved", "success"]):
        return "✅"
    elif any(keyword in message_lower for keyword in ["rejected", "declined", "failed"]):
        return "❌"
    elif any(keyword in message_lower for keyword in ["pending", "ongoing", "in progress"]):
        return "⏳"
    elif any(keyword in message_lower for keyword in ["completed", "finished", "done"]):
        return "🎉"
    elif any(keyword in message_lower for keyword in ["message", "messaged"]):
        return "💬"
    elif any(keyword in message_lower for keyword in ["call", "calling", "missed call"]):
        return "📞"
    elif any(keyword in message_lower for keyword in ["payment", "paid", "received"]):
        return "💰"
    elif any(keyword in message_lower for keyword in ["verification", "kyc", "approved", "verified"]):
        return "🏅"
    elif any(keyword in message_lower for keyword in ["subscription", "activated", "plan"]):
        return "💎"
    
    # Priority 3: Title analysis
    if any(keyword in title_lower for keyword in ["hire", "job"]):
        return "📩"
    elif any(keyword in title_lower for keyword in ["payment", "transaction"]):
        return "💰"
    elif any(keyword in title_lower for keyword in ["message", "chat"]):
        return "💬"
    
    # Default icon
    return "ℹ️"

def enhance_notification_message(message, title="", related_entity_type="", context_data=None):
    """
    Enhance notification message with better formatting and context
    """
    if not message:
        return "No notification details available"
    
    context_data = context_data or {}
    message_lower = message.lower()
    
    # Hire request enhancements
    if any(keyword in message_lower for keyword in ["hire request", "job request"]):
        if "client_name" in context_data:
            client_name = context_data["client_name"]
            if f"new job request from {client_name}" not in message_lower:
                return f"New hire request from {client_name}"
        if "job_title" in context_data:
            job_title = context_data["job_title"]
            return f"New job request: '{job_title}'"
    
    # Job status enhancements
    elif any(keyword in message_lower for keyword in ["job", "status"]):
        job_title = context_data.get("job_title", "Unknown Job")
        status = context_data.get("status", "Updated")
        
        # Enhanced status messages
        if status == "ACCEPTED":
            return f"Your hire request has been accepted ✅"
        elif status == "REJECTED":
            return f"Your hire request was rejected"
        elif status == "ONGOING":
            return f"Your job '{job_title}' is now ONGOING"
        elif status == "COMPLETED":
            return f"Your job '{job_title}' has been COMPLETED 🎉"
        elif status == "PAID":
            return f"Job '{job_title}' marked as PAID 💰"
        else:
            return f"Your job '{job_title}' is now {status}"
    
    # Payment enhancements
    elif any(keyword in message_lower for keyword in ["payment", "paid", "received"]):
        if "amount" in context_data:
            amount = context_data["amount"]
            return f"Payment received: ₹{amount}"
        elif "transaction" in context_data:
            return "Transaction completed successfully"
    
    # Message enhancements
    elif any(keyword in message_lower for keyword in ["message", "messaged"]):
        if "sender_name" in context_data:
            sender_name = context_data["sender_name"]
            return f"New message from {sender_name}"
        return "You have a new message"
    
    # Call enhancements
    elif any(keyword in message_lower for keyword in ["call", "calling"]):
        if "caller_name" in context_data:
            caller_name = context_data["caller_name"]
            if "missed" in message_lower:
                return f"Missed call from {caller_name}"
            elif "incoming" in message_lower:
                return f"Incoming call from {caller_name}"
            else:
                return f"Call from {caller_name}"
        return "You have a new call notification"
    
    # System/Account enhancements
    elif any(keyword in message_lower for keyword in ["profile", "account", "updated"]):
        return "Profile updated successfully"
    elif any(keyword in message_lower for keyword in ["verification", "kyc", "approved"]):
        return "KYC Approved 🏅"
    elif any(keyword in message_lower for keyword in ["subscription", "activated"]):
        return "Subscription activated 💎"
    
    # Return original message if no enhancement needed
    return message

def get_notification_type(message="", title="", related_entity_type=""):
    """
    Determine notification type based on content and metadata
    """
    message_lower = (message or "").lower()
    title_lower = (title or "").lower()
    entity_type = (related_entity_type or "").lower()
    
    # Priority 1: Explicit entity type
    if entity_type:
        if "hire" in entity_type:
            return "HIRE"
        elif "job" in entity_type:
            return "JOB"
        elif "payment" in entity_type:
            return "PAYMENT"
        elif "message" in entity_type:
            return "MESSAGE"
        elif "call" in entity_type:
            return "CALL"
        elif "verification" in entity_type or "kyc" in entity_type:
            return "SYSTEM"
        elif "subscription" in entity_type:
            return "SYSTEM"
    
    # Priority 2: Message content analysis
    if any(keyword in message_lower for keyword in ["hire request", "new job", "job request"]):
        return "HIRE"
    elif any(keyword in message_lower for keyword in ["accepted", "approved"]):
        return "JOB"
    elif any(keyword in message_lower for keyword in ["rejected", "declined"]):
        return "JOB"
    elif any(keyword in message_lower for keyword in ["completed", "finished", "done"]):
        return "JOB"
    elif any(keyword in message_lower for keyword in ["payment", "paid", "received"]):
        return "PAYMENT"
    elif any(keyword in message_lower for keyword in ["message", "messaged"]):
        return "MESSAGE"
    elif any(keyword in message_lower for keyword in ["call", "calling", "missed call"]):
        return "CALL"
    elif any(keyword in message_lower for keyword in ["verification", "kyc", "approved", "verified"]):
        return "SYSTEM"
    elif any(keyword in message_lower for keyword in ["subscription", "activated", "plan"]):
        return "SYSTEM"

    return "DEFAULT"