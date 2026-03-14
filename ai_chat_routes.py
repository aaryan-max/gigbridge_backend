"""
AI Chat Routes for GigBridge Database Questions
POST /ai/chat endpoint for natural language database queries
"""

from flask import request, jsonify
from intent_parser_llm import LLMIntentParser
from intent_validator_llm import LLMIntentValidator
from query_builder_llm import LLMQueryBuilder
from query_executor import QueryExecutor
from response_formatter import ResponseFormatter
from ai_guardrails import AIGuardrails


def register_ai_chat_routes(app):
    """Register AI chat routes with Flask app"""
    
    # Initialize LLM-based components
    intent_parser = LLMIntentParser()
    intent_validator = LLMIntentValidator()
    query_builder = LLMQueryBuilder()
    query_executor = QueryExecutor()
    response_formatter = ResponseFormatter()
    guardrails = AIGuardrails()
    
    @app.route("/ai/chat", methods=["POST"])
    def ai_chat_endpoint():
        """
        Process AI chat query for GigBridge database questions
        
        Request JSON:
        {
            "user_id": 1,
            "role": "client",
            "message": "Show verified singers in Mumbai"
        }
        
        Response JSON:
        {
            "success": true,
            "answer": "I found 3 verified singers in Mumbai.",
            "intent": "list_freelancers",
            "data_count": 3
        }
        """
        try:
            # Get and validate JSON data
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "answer": "No data provided"
                }), 400
            
            # Validate required fields
            required_fields = ["user_id", "role", "message"]
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                return jsonify({
                    "success": False,
                    "answer": f"Missing required fields: {', '.join(missing)}"
                }), 400
            
            user_id = int(data["user_id"])
            role = str(data["role"]).strip().lower()
            message = str(data["message"]).strip()
            
            # Basic validation
            if role not in ["client", "freelancer"]:
                return jsonify({
                    "success": False,
                    "answer": "Role must be 'client' or 'freelancer'"
                }), 400
            
            if not message:
                return jsonify({
                    "success": False,
                    "answer": "Message cannot be empty"
                }), 400
            
            # Apply guardrails - check if question is GigBridge-related
            guardrails_result = guardrails.check_message(message)
            if not guardrails_result["allowed"]:
                return jsonify({
                    "success": False,
                    "answer": guardrails_result["reason"]
                })
            
            # Parse intent using LLM
            parsed_intent = intent_parser.parse(message, user_id, role)
            if not parsed_intent:
                # Try emergency fallback
                parsed_intent = intent_parser.emergency_fallback(message)
                if not parsed_intent:
                    return jsonify({
                        "success": False,
                        "answer": "I couldn't understand your GigBridge request. Please rephrase it."
                    })
            
            # Validate intent
            validation_result = intent_validator.validate(parsed_intent, role, user_id)
            if not validation_result["valid"]:
                return jsonify({
                    "success": False,
                    "answer": validation_result["reason"]
                })
            
            # Build safe query
            query_result = query_builder.build_query(parsed_intent, role, user_id)
            if not query_result["success"]:
                return jsonify({
                    "success": False,
                    "answer": query_result["error"]
                })
            
            # Execute query
            execution_result = query_executor.execute(
                query_result["query"], 
                query_result["params"], 
                query_result["db"]
            )
            if not execution_result["success"]:
                return jsonify({
                    "success": False,
                    "answer": "Database error occurred while processing your request."
                })
            
            # Format response
            response = response_formatter.format_response(
                parsed_intent["intent"],
                execution_result["data"],
                message
            )
            
            return jsonify({
                "success": True,
                "answer": response["answer"],
                "intent": parsed_intent["intent"],
                "data_count": response["data_count"]
            })
            
        except Exception as e:
            print(f"Error in ai_chat route: {type(e).__name__}: {str(e)}")
            return jsonify({
                "success": False,
                "answer": "Server error occurred while processing your request."
            }), 500
