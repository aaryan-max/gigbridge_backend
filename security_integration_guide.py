"""
SECURITY INTEGRATION GUIDE FOR APP.PY
=====================================

Follow these exact steps to add security features to your existing Flask app.

STEP 1: ADD SECURITY IMPORTS
----------------------------
Add these imports at the TOP of app.py (after existing imports):

```python
# Security imports
from security import (
    security_middleware, rate_otp_limit, rate_login_limit, 
    rate_general_limit, validate_request, create_jwt_token,
    optional_jwt_required, sanitize_request_data,
    LoginSchema, SignupSchema, OTPSchema, OTPVerifySchema, HireRequestSchema
)
```

STEP 2: CONFIGURE SECURITY MIDDLEWARE
-----------------------------------
Add this RIGHT AFTER app initialization (after app = Flask(__name__)):

```python
# ============================================================
# SECURITY CONFIGURATION
# ============================================================

# Apply security middleware (CORS, JWT, HTTPS, Rate Limiting)
jwt_manager = security_middleware(app)

# Apply input sanitization to all requests
@app.before_request
def apply_security_middleware():
    sanitize_request_data()
```

STEP 3: ADD SECURITY DECORATORS TO ROUTES
-----------------------------------------

Add decorators to existing routes WITHOUT changing route logic:

CLIENT LOGIN ROUTE:
```python
@app.route("/client/login", methods=["POST"])
@rate_login_limit
@validate_request(LoginSchema)
def client_login():
    # Existing login logic remains EXACTLY the same
    d = request.get_json()
    # ... rest of existing code ...
    
    # ADD JWT TOKEN CREATION before returning success response
    if login_successful:
        token = create_jwt_token(client_id, "client")
        return jsonify({
            "success": True, 
            "client_id": client_id,
            "token": token  # Add token to existing response
        })
```

FREELANCER LOGIN ROUTE:
```python
@app.route("/freelancer/login", methods=["POST"])
@rate_login_limit
@validate_request(LoginSchema)
def freelancer_login():
    # Existing login logic remains EXACTLY the same
    d = request.get_json()
    # ... rest of existing code ...
    
    # ADD JWT TOKEN CREATION before returning success response
    if login_successful:
        token = create_jwt_token(freelancer_id, "freelancer")
        return jsonify({
            "success": True, 
            "freelancer_id": freelancer_id,
            "token": token  # Add token to existing response
        })
```

CLIENT SEND OTP ROUTE:
```python
@app.route("/client/send-otp", methods=["POST"])
@rate_otp_limit
@validate_request(OTPSchema)
def client_send_otp():
    # Existing OTP logic remains EXACTLY the same
    d = request.get_json()
    # ... rest of existing code ...
```

FREELANCER SEND OTP ROUTE:
```python
@app.route("/freelancer/send-otp", methods=["POST"])
@rate_otp_limit
@validate_request(OTPSchema)
def freelancer_send_otp():
    # Existing OTP logic remains EXACTLY the same
    d = request.get_json()
    # ... rest of existing code ...
```

CLIENT SIGNUP ROUTE:
```python
@app.route("/client/signup", methods=["POST"])
@rate_general_limit
@validate_request(SignupSchema)
def client_signup():
    # Existing signup logic remains EXACTLY the same
    d = request.get_json()
    # ... rest of existing code ...
```

FREELANCER SIGNUP ROUTE:
```python
@app.route("/freelancer/signup", methods=["POST"])
@rate_general_limit
@validate_request(SignupSchema)
def freelancer_signup():
    # Existing signup logic remains EXACTLY the same
    d = request.get_json()
    # ... rest of existing code ...
```

CLIENT VERIFY OTP ROUTE:
```python
@app.route("/client/verify-otp", methods=["POST"])
@rate_general_limit
@validate_request(OTPVerifySchema)
def client_verify_otp():
    # Existing verification logic remains EXACTLY the same
    d = request.get_json()
    # ... rest of existing code ...
```

FREELANCER VERIFY OTP ROUTE:
```python
@app.route("/freelancer/verify-otp", methods=["POST"])
@rate_general_limit
@validate_request(OTPVerifySchema)
def freelancer_verify_otp():
    # Existing verification logic remains EXACTLY the same
    d = request.get_json()
    # ... rest of existing code ...
```

HIRE REQUEST ROUTE:
```python
@app.route("/client/hire", methods=["POST"])
@rate_general_limit
@validate_request(HireRequestSchema)
@optional_jwt_required  # Optional JWT protection
def client_hire():
    # Existing hire logic remains EXACTLY the same
    d = request.get_json()
    # ... rest of existing code ...
```

STEP 4: PROTECTED ROUTES (Optional)
-----------------------------------
Add JWT protection to sensitive routes (optional but recommended):

```python
@app.route("/client/dashboard", methods=["GET"])
@rate_general_limit
@jwt_required()  # Required JWT
def client_dashboard():
    # Existing dashboard logic remains EXACTLY the same
    # ... rest of existing code ...

@app.route("/freelancer/dashboard", methods=["GET"])
@rate_general_limit
@jwt_required()  # Required JWT
def freelancer_dashboard():
    # Existing dashboard logic remains EXACTLY the same
    # ... rest of existing code ...
```

STEP 5: INSTALL DEPENDENCIES
----------------------------
Install the security packages:

```bash
pip install -r security_requirements.txt
```

Or individually:
```bash
pip install flask-limiter==3.5.0
pip install flask-cors==4.0.0
pip install flask-jwt-extended==4.5.3
pip install marshmallow==3.20.1
```

STEP 6: ENVIRONMENT VARIABLES
----------------------------
Add these to your environment or .env file:

```bash
# JWT Secret Key (required for production)
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# CORS Origins (optional, comma-separated)
CORS_ORIGINS=https://gigbridge.com,https://app.gigbridge.com

# Flask Environment
FLASK_ENV=production  # or 'development'
```

STEP 7: VALIDATION USAGE
------------------------
Replace get_json() calls with validated data in routes that have @validate_request decorator:

```python
# OLD WAY (still works but not validated)
d = get_json()
email = d["email"]

# NEW WAY (validated and sanitized)
email = request.validated_data["email"]
```

BENEFITS OF THIS APPROACH:
---------------------------

1. NO LOGIC CHANGES - Existing routes work exactly as before
2. LAYERED SECURITY - Multiple security features working together
3. EASY TO ENABLE/DISABLE - Just remove decorators
4. GRADUAL ROLLOUT - Apply to routes one by one
5. BACKWARD COMPATIBLE - Existing API responses unchanged
6. MAINTAINABLE - Security logic separated from business logic

RATE LIMITING EFFECTS:
-----------------------

- OTP endpoints: 5 requests per minute per IP
- Login endpoints: 10 requests per minute per IP
- General endpoints: 100 requests per hour per IP
- Strict endpoints: 20 requests per minute per IP

CORS PROTECTION:
-----------------

- Only allows https://gigbridge.com in production
- Allows http://localhost:3000 in development
- Blocks all other origins

JWT SECURITY:
--------------

- Tokens expire after 24 hours
- Secure cookies in production
- CSRF protection enabled
- Optional protection on sensitive routes

HTTPS READINESS:
---------------

- Security headers added to all responses
- Secure cookies in production
- HSTS enforcement
- CSP headers

INPUT VALIDATION:
----------------

- Email format validation
- Password length requirements
- SQL injection protection
- XSS prevention
```
