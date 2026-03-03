from flask import Blueprint, request, jsonify
import sqlite3
import os
import time
import secrets
from werkzeug.utils import secure_filename
from database import client_db, update_client_kyc, get_client_kyc

client_kyc_bp = Blueprint("client_kyc", __name__)

def _now():
    return int(time.time())

def _allowed_ext(filename):
    exts = {"jpg","jpeg","png","pdf"}
    ext = filename.rsplit(".",1)[-1].lower() if "." in filename else ""
    return ext in exts, ext

@client_kyc_bp.route("/client/kyc/upload", methods=["POST"])
def client_kyc_upload():
    client_id = request.form.get("client_id", "").strip()
    government_id = request.files.get("government_id")
    pan_card = request.files.get("pan_card")
    
    try:
        client_id_int = int(client_id)
    except Exception:
        return jsonify({"success": False, "msg": "Invalid client ID"}), 400
    
    # Validate files exist
    if not government_id or not government_id.filename:
        return jsonify({"success": False, "msg": "Government ID file required"}), 400
    if not pan_card or not pan_card.filename:
        return jsonify({"success": False, "msg": "PAN card file required"}), 400
    
    # Validate file extensions
    gov_ok, gov_ext = _allowed_ext(government_id.filename)
    pan_ok, pan_ext = _allowed_ext(pan_card.filename)
    
    if not gov_ok:
        return jsonify({"success": False, "msg": "Invalid government ID file type"}), 400
    if not pan_ok:
        return jsonify({"success": False, "msg": "Invalid PAN card file type"}), 400
    
    # Validate file sizes (5MB max)
    gov_data = government_id.read()
    pan_data = pan_card.read()
    
    if len(gov_data) > 5 * 1024 * 1024:
        return jsonify({"success": False, "msg": "Government ID file too large"}), 400
    if len(pan_data) > 5 * 1024 * 1024:
        return jsonify({"success": False, "msg": "PAN card file too large"}), 400
    
    # Verify client exists
    conn = client_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM client WHERE id=?", (client_id_int,))
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
        if update_client_kyc(client_id_int, gov_path, pan_path):
            return jsonify({
                "success": True, 
                "msg": "Verification documents submitted successfully. Awaiting admin approval."
            })
        else:
            return jsonify({"success": False, "msg": "Failed to save verification data"}), 500
            
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
