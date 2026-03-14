"""
Flask Routes for Database-powered Chat Service
GigBridge AI Chat - Simple Database Query Bot
"""

from flask import Flask, request, jsonify
from .db_chat_service import DatabaseChatService


def register_chat_routes(app: Flask):
    """Register chat routes with Flask app"""
    
    chat_service = DatabaseChatService()
    
    @app.route("/chat/query", methods=["POST"])
    def chat_query():
        """
        Process chat query and return database results
        
        Input JSON:
        {
            "role": "client|freelancer",
            "user_id": 123,
            "message": "show my projects"
        }
        """
        try:
            # Get JSON data
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "msg": "No data provided"
                }), 400
            
            # Validate required fields
            required_fields = ["role", "user_id", "message"]
            missing_fields = []
            
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    "success": False,
                    "msg": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
            
            # Validate role
            role = str(data["role"]).strip().lower()
            if role not in ["client", "freelancer"]:
                return jsonify({
                    "success": False,
                    "msg": "Role must be 'client' or 'freelancer'"
                }), 400
            
            # Validate user_id
            try:
                user_id = int(data["user_id"])
                if user_id <= 0:
                    raise ValueError("User ID must be positive")
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "msg": "Invalid user_id"
                }), 400
            
            # Validate message
            message = str(data["message"]).strip()
            if not message:
                return jsonify({
                    "success": False,
                    "msg": "Message cannot be empty"
                }), 400
            
            # Process query through chat service
            result = chat_service.process_query(role, user_id, message)
            
            # Return appropriate HTTP status
            status_code = 200 if result.get("success", False) else 400
            return jsonify(result), status_code
            
        except Exception as e:
            print(f"Error in chat_query route: {type(e).__name__}: {str(e)}")
            return jsonify({
                "success": False,
                "msg": "Server error occurred"
            }), 500
    
    @app.route("/chat/help", methods=["GET"])
    def chat_help():
        """
        Return available chat commands
        """
        help_data = {
            "success": True,
            "data": {
                "available_commands": [
                    "show my projects",
                    "list my projects", 
                    "my projects",
                    "show projects",
                    "show my applications",
                    "list my applications",
                    "my applications", 
                    "show applications",
                    "list freelancers",
                    "show freelancers",
                    "freelancers",
                    "show my messages",
                    "list my messages",
                    "my messages",
                    "show messages",
                    "show my profile",
                    "my profile",
                    "profile"
                ],
                "examples": [
                    {
                        "command": "show my projects",
                        "description": "Display all your posted projects"
                    },
                    {
                        "command": "list freelancers", 
                        "description": "Show all available freelancers"
                    },
                    {
                        "command": "show my messages",
                        "description": "Display your recent messages"
                    },
                    {
                        "command": "my profile",
                        "description": "Show your profile information"
                    }
                ],
                "note": "This chatbot only answers questions using GigBridge database data. No external AI APIs are used."
            }
        }
        return jsonify(help_data)
    
    @app.route("/chat/status", methods=["GET"])
    def chat_status():
        """
        Return chat service status
        """
        return jsonify({
            "success": True,
            "data": {
                "service": "Database Chat Service",
                "status": "active",
                "type": "database-query",
                "external_apis": False
            }
        })
