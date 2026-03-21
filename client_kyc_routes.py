from flask import Blueprint, request, jsonify
import os
import time
import secrets
from werkzeug.utils import secure_filename
from database import client_db, update_client_kyc, get_client_kyc
from postgres_config import get_dict_cursor

client_kyc_bp = Blueprint("client_kyc", __name__)

def _now():
    return int(time.time())

def clean_path(p):
    """Clean file path by removing quotes and trailing spaces"""
    return p.strip().strip('"').strip("'").strip()

def _allowed_ext(filename):
    """Extract and validate file extension from filename or path"""
    filename = clean_path(filename)
    # Extract just the filename from full path
    basename = os.path.basename(filename)
    ext = os.path.splitext(basename)[1].lower()
    exts = {".jpg",".jpeg",".png",".pdf"}
    return ext in exts, ext

def _handle_file_upload(file_input, max_size=5*1024*1024):
    """Handle both file objects and file paths from CLI"""
    if hasattr(file_input, 'read'):
        # It's a file object (multipart upload)
        data = file_input.read()
        if len(data) > max_size:
            return None, "File too large"
        return data, None
    else:
        # It's a file path (CLI upload)
        file_path = clean_path(file_input)
        
        if not os.path.exists(file_path):
            return None, "File not found"
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            if len(data) > max_size:
                return None, "File too large"
            return data, None
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"File read error: {str(e)}")
            return None, "Failed to read file"

@client_kyc_bp.route("/client/kyc/upload", methods=["POST"])
def client_kyc_upload():
    client_id = request.form.get("client_id", "").strip()
    
    # Handle both multipart files and CLI file paths
    government_id = request.files.get("government_id")
    pan_card = request.files.get("pan_card")
    
    # Check for CLI file paths in form data
    gov_path = request.form.get("government_id_path")
    pan_path = request.form.get("pan_card_path")
    
    # Use CLI paths if files are not provided
    if not government_id and gov_path:
        government_id = gov_path
    if not pan_card and pan_path:
        pan_card = pan_path
    
    try:
        client_id_int = int(client_id)
    except Exception:
        return jsonify({"success": False, "msg": "Invalid client ID"}), 400
    
    # Validate files exist (either as file object or path)
    if not government_id:
        return jsonify({"success": False, "msg": "Government ID file required"}), 400
    if not pan_card:
        return jsonify({"success": False, "msg": "PAN card file required"}), 400
    
    # Get filenames for validation
    gov_filename = getattr(government_id, 'filename', government_id) or government_id
    pan_filename = getattr(pan_card, 'filename', pan_card) or pan_card
    
    # Validate file extensions
    gov_ok, gov_ext = _allowed_ext(gov_filename)
    pan_ok, pan_ext = _allowed_ext(pan_filename)
    
    if not gov_ok:
        return jsonify({"success": False, "msg": "Invalid government ID file type"}), 400
    if not pan_ok:
        return jsonify({"success": False, "msg": "Invalid PAN card file type"}), 400
    
    # Handle file uploads (both multipart and CLI)
    gov_data, gov_error = _handle_file_upload(government_id)
    if gov_error:
        return jsonify({"success": False, "msg": f"Government ID: {gov_error}"}), 400
    
    pan_data, pan_error = _handle_file_upload(pan_card)
    if pan_error:
        return jsonify({"success": False, "msg": f"PAN card: {pan_error}"}), 400
    
    # Verify client exists
    conn = client_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("SELECT id FROM client WHERE id=%s", (client_id_int,))
        r = cur.fetchone()
        if not r:
            return jsonify({"success": False, "msg": "Client not found"}), 404
        
        # Create upload directory
        base_dir = os.path.join(os.path.dirname(__file__), "uploads", "client_kyc", str(client_id_int))
        os.makedirs(base_dir, exist_ok=True)
        
        # Generate secure filenames
        gov_token = secrets.token_urlsafe(16)
        pan_token = secrets.token_urlsafe(16)
        gov_filename = secure_filename(f"gov_{gov_token}.{gov_ext}")
        pan_filename = secure_filename(f"pan_{pan_token}.{pan_ext}")
        
        gov_path = os.path.join(base_dir, gov_filename)
        pan_path = os.path.join(base_dir, pan_filename)
        
        # Save files
        with open(gov_path, "wb") as fp:
            fp.write(gov_data)
        with open(pan_path, "wb") as fp:
            fp.write(pan_data)
        
        # Update database
        try:
            if update_client_kyc(client_id_int, gov_path, pan_path):
                return jsonify({
                    "success": True, 
                    "msg": "Verification documents submitted successfully. Awaiting admin approval."
                })
            else:
                return jsonify({"success": False, "msg": "Failed to save verification data"}), 500
        except Exception as db_e:
            import logging
            logging.getLogger(__name__).error(f"Database error: {str(db_e)}")
            cconn.rollback()
            return jsonify({"success": False, "msg": "Database error occurred"}), 500
            
    finally:
        conn.close()

@client_kyc_bp.route("/client/kyc/status", methods=["GET"])
def client_kyc_status():
    client_id = request.args.get("client_id", "").strip()
    
    try:
        client_id_int = int(client_id)
    except Exception:
        return jsonify({"success": False, "msg": "Invalid client ID"}), 400
    
    kyc_data = get_client_kyc(client_id_int)
    
    if not kyc_data:
        return jsonify({
            "success": False,
            "msg": "No verification submitted yet."
        })
    
    return jsonify({
        "success": True,
        "status": kyc_data["status"]
    })
