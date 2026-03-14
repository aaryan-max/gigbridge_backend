"""
EXAMPLE: How to modify existing routes with security decorators
========================================================

This shows the BEFORE and AFTER of adding security to existing routes
without changing the internal logic.

BEFORE: Original Client Login Route
----------------------------------
```python
@app.route("/client/login", methods=["POST"])
def client_login():
    d = get_json()
    missing = require_fields(d, ["email", "password"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400

    email = str(d["email"]).strip().lower()
    password = str(d["password"])
    
    conn = client_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM client WHERE email=%s", (email,))
        row = cur.fetchone()
        
        if not row or not check_password_hash(row[1], password):
            return jsonify({"success": False, "msg": "Invalid credentials"}), 401
        
        client_id = row[0]
        return jsonify({"success": True, "client_id": client_id})
    finally:
        conn.close()
```

AFTER: Enhanced with Security Decorators
-------------------------------------
```python
@app.route("/client/login", methods=["POST"])
@rate_login_limit                    # 10 requests per minute
@validate_request(LoginSchema)         # Input validation
def client_login():
    # Use validated data instead of raw get_json()
    email = request.validated_data["email"]
    password = request.validated_data["password"]
    
    conn = client_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM client WHERE email=%s", (email,))
        row = cur.fetchone()
        
        if not row or not check_password_hash(row[1], password):
            return jsonify({"success": False, "msg": "Invalid credentials"}), 401
        
        client_id = row[0]
        
        # Create JWT token (NEW)
        token = create_jwt_token(client_id, "client")
        
        # Return existing response + token (NEW)
        return jsonify({
            "success": True, 
            "client_id": client_id,
            "token": token
        })
    finally:
        conn.close()
```

BEFORE: Original Client Send OTP Route
------------------------------------
```python
@app.route("/client/send-otp", methods=["POST"])
def client_send_otp():
    d = get_json()
    missing = require_fields(d, ["email"])
    if missing:
        return jsonify({"success": False, "msg": "Email required"}), 400

    email = str(d["email"]).strip().lower()
    if not valid_email(email):
        return jsonify({"success": False, "msg": "Invalid email"}), 400
    
    # ... rest of existing OTP logic ...
```

AFTER: Enhanced with Security Decorators
-------------------------------------
```python
@app.route("/client/send-otp", methods=["POST"])
@rate_otp_limit                    # 5 requests per minute
@validate_request(OTPSchema)         # Email validation only
def client_send_otp():
    # Use validated data - no need for manual validation
    email = request.validated_data["email"]
    
    # Email is already validated and sanitized
    # ... rest of existing OTP logic remains exactly the same ...
```

BEFORE: Original Hire Request Route
----------------------------------
```python
@app.route("/client/hire", methods=["POST"])
def client_hire():
    d = get_json()
    missing = require_fields(d, ["client_id", "freelancer_id", "job_title", "proposed_budget"])
    if missing:
        return jsonify({"success": False, "msg": "Missing fields"}), 400
    
    client_id = int(d["client_id"])
    freelancer_id = int(d["freelancer_id"])
    job_title = str(d["job_title"]).strip()
    proposed_budget = float(d["proposed_budget"])
    
    # ... rest of existing hire logic ...
```

AFTER: Enhanced with Security Decorators
-------------------------------------
```python
@app.route("/client/hire", methods=["POST"])
@rate_general_limit                 # 100 requests per hour
@validate_request(HireRequestSchema)   # Full validation
@optional_jwt_required               # Optional JWT protection
def client_hire():
    # Use validated data - all fields are already validated
    client_id = request.validated_data["client_id"]
    freelancer_id = request.validated_data["freelancer_id"]
    job_title = request.validated_data["job_title"]
    proposed_budget = request.validated_data["proposed_budget"]
    contract_type = request.validated_data.get("contract_type", "FIXED")
    note = request.validated_data.get("note", "")
    
    # Optional: Check if JWT user matches client_id
    if request.current_user_id and request.current_user_id != client_id:
        return jsonify({"success": False, "msg": "Unauthorized"}), 403
    
    # ... rest of existing hire logic remains exactly the same ...
```

KEY DIFFERENCES:
---------------

1. DECORATORS ADDED:
   - @rate_login_limit - Rate limiting
   - @validate_request(Schema) - Input validation
   - @optional_jwt_required - Optional JWT protection

2. DATA ACCESS CHANGED:
   - OLD: d = get_json(); email = d["email"]
   - NEW: email = request.validated_data["email"]

3. JWT TOKEN ADDED:
   - Token creation and inclusion in response for login routes

4. NO LOGIC CHANGES:
   - All existing business logic remains identical
   - Database queries unchanged
   - Response formats unchanged (except token addition)

5. AUTOMATIC VALIDATION:
   - Email format validation
   - Password length validation
   - Required field checking
   - Data type validation
   - SQL injection protection
   - XSS protection

This approach ensures:
- ZERO breaking changes to existing logic
- ENHANCED security through decorators
- MAINTAINABLE separation of concerns
- EASY to enable/disable features
- BACKWARD compatible API responses
```
