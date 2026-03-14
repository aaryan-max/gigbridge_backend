"""
Security Module for GigBridge Flask Backend
Provides rate limiting, CORS, JWT, input validation, and HTTPS configuration
"""

from functools import wraps
from datetime import datetime, timedelta
import os
from flask import request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity,
    set_access_cookies
)
from marshmallow import Schema, fields, validate, ValidationError
import re


# ============================================================================
# INPUT VALIDATION SCHEMAS
# ============================================================================

class LoginSchema(Schema):
    """Schema for login validation"""
    email = fields.Email(required=True, validate=validate.Length(min=5, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128))
    role = fields.Str(required=False, validate=validate.OneOf(['client', 'freelancer']))

class SignupSchema(Schema):
    """Schema for signup validation"""
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True, validate=validate.Length(min=5, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128))
    role = fields.Str(required=False, validate=validate.OneOf(['client', 'freelancer']))

class OTPSchema(Schema):
    """Schema for OTP requests"""
    email = fields.Email(required=True, validate=validate.Length(min=5, max=100))

class OTPVerifySchema(Schema):
    """Schema for OTP verification"""
    name = fields.Str(required=False, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True, validate=validate.Length(min=5, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128))
    otp = fields.Str(required=True, validate=validate.Length(min=6, max=6))
    role = fields.Str(required=False, validate=validate.OneOf(['client', 'freelancer']))

class HireRequestSchema(Schema):
    """Schema for hire requests"""
    client_id = fields.Int(required=True, validate=validate.Range(min=1))
    freelancer_id = fields.Int(required=True, validate=validate.Range(min=1))
    job_title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    proposed_budget = fields.Float(required=True, validate=validate.Range(min=0))
    note = fields.Str(required=False, validate=validate.Length(max=1000))
    contract_type = fields.Str(required=True, validate=validate.OneOf(['FIXED', 'HOURLY', 'EVENT']))

# ============================================================================
# RATE LIMITING CONFIGURATION
# ============================================================================

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Rate limit configurations
OTP_RATE_LIMIT = "5 per minute"
LOGIN_RATE_LIMIT = "10 per minute"
GENERAL_RATE_LIMIT = "100 per hour"
STRICT_RATE_LIMIT = "20 per minute"

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

def configure_cors(app):
    """Configure CORS for the Flask app"""
    # Get allowed origins from environment or use defaults
    allowed_origins = [
        "https://gigbridge.com",  # Production
        "http://localhost:3000",   # Development
        "http://127.0.0.1:3000",  # Development alternative
    ]
    
    # Add additional origins from environment if specified
    additional_origins = os.getenv("CORS_ORIGINS", "")
    if additional_origins:
        allowed_origins.extend([origin.strip() for origin in additional_origins.split(",")])
    
    CORS(app, 
         origins=allowed_origins,
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=True,
         max_age=86400)  # 24 hours

# ============================================================================
# JWT CONFIGURATION
# ============================================================================

def configure_jwt(app):
    """Configure JWT for the Flask app"""
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", app.config.get("SECRET_KEY", "dev-secret-key"))
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    app.config["JWT_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
    app.config["JWT_COOKIE_HTTPONLY"] = True
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    
    jwt = JWTManager(app)
    return jwt

# ============================================================================
# HTTPS CONFIGURATION
# ============================================================================

def configure_https(app):
    """Configure HTTPS readiness settings"""
    # Security headers
    @app.after_request
    def after_request(response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        
        return response
    
    # HTTPS configuration for production
    if os.getenv("FLASK_ENV") == "production":
        app.config.update(
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            PREFERRED_URL_SCHEME='https'
        )

# ============================================================================
# VALIDATION DECORATORS
# ============================================================================

def validate_request(schema_class):
    """Decorator to validate request data using Marshmallow schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get JSON data
                data = request.get_json() or {}
                
                # Validate against schema
                schema = schema_class()
                validated_data = schema.load(data)
                
                # Store validated data in request context
                request.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                return jsonify({
                    "success": False,
                    "msg": f"Validation error: {', '.join([f'{field}: {error}' for field, errors in e.messages.items() for error in errors])}"
                }), 400
            except Exception as e:
                return jsonify({
                    "success": False,
                    "msg": f"Invalid request format: {str(e)}"
                }), 400
        
        return decorated_function
    return decorator

# ============================================================================
# JWT DECORATORS
# ============================================================================

def optional_jwt_required(f):
    """Decorator that makes JWT optional but provides identity if available"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Try to get JWT identity
            current_user_id = get_jwt_identity()
            request.current_user_id = current_user_id
        except:
            # No JWT provided or invalid, continue without user
            request.current_user_id = None
        
        return f(*args, **kwargs)
    return decorated_function

def create_jwt_token(user_id, user_role="client"):
    """Create JWT token for user"""
    additional_claims = {
        "role": user_role,
        "user_id": user_id
    }
    return create_access_token(identity=user_id, additional_claims=additional_claims)

# ============================================================================
# SECURITY MIDDLEWARE
# ============================================================================

def security_middleware(app):
    """Apply all security configurations to Flask app"""
    # Configure each security layer
    configure_cors(app)
    jwt = configure_jwt(app)
    configure_https(app)
    
    # Initialize rate limiting
    limiter.init_app(app)
    
    return jwt

# ============================================================================
# RATE LIMIT DECORATORS
# ============================================================================

def rate_otp_limit(f):
    """Apply OTP rate limiting"""
    return limiter.limit(OTP_RATE_LIMIT)(f)

def rate_login_limit(f):
    """Apply login rate limiting"""
    return limiter.limit(LOGIN_RATE_LIMIT)(f)

def rate_general_limit(f):
    """Apply general rate limiting"""
    return limiter.limit(GENERAL_RATE_LIMIT)(f)

def rate_strict_limit(f):
    """Apply strict rate limiting"""
    return limiter.limit(STRICT_RATE_LIMIT)(f)

# ============================================================================
# INPUT SANITIZATION
# ============================================================================

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return ""
    
    # Remove potential script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove SQL injection patterns
    dangerous_patterns = [
        r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)',
        r'(--|#|/\*|\*/)',
        r'(\b(or|and)\s+\d+\s*=\s*\d+)',
        r'(\b(or|and)\s+\'\w+\'\s*=\s*\'\w+\'',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def sanitize_request_data():
    """Sanitize all incoming request data"""
    if request.is_json:
        data = request.get_json()
        if data:
            sanitized = {}
            for key, value in data.items():
                if isinstance(value, str):
                    sanitized[key] = sanitize_input(value)
                else:
                    sanitized[key] = value
            request.sanitized_data = sanitized
        else:
            request.sanitized_data = {}
    else:
        request.sanitized_data = {}
