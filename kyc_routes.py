from flask import Blueprint, request, jsonify
import sqlite3
import os
import time
import secrets
from werkzeug.utils import secure_filename
from database import freelancer_db
from settings import FEATURE_AUTHENTICATE_KYC_UPLOAD, FEATURE_KYC_REUPLOAD_POLICY

kyc_bp = Blueprint("kyc", __name__)

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

@kyc_bp.route("/freelancer/kyc/upload", methods=["POST"])
def kyc_upload():
    fid = request.form.get("freelancer_id", "").strip()
    doc_type = (request.form.get("doc_type","") or "").strip().upper()
    file = request.files.get("file")
    
    # Check for CLI file path in form data
    file_path = request.form.get("file_path")
    
    # Use CLI path if file is not provided
    if not file and file_path:
        file = file_path
    
    if FEATURE_AUTHENTICATE_KYC_UPLOAD:
        header_id = request.headers.get("X-FREELANCER-ID", "").strip()
        try:
            if int(header_id) != int(fid or 0):
                return jsonify({"success": False, "msg": "Unauthorized"}), 401
        except Exception:
            return jsonify({"success": False, "msg": "Unauthorized"}), 401
    try:
        fid_int = int(fid)
    except Exception:
        return jsonify({"success": False, "msg": "Invalid"}), 400
    if doc_type not in ("AADHAAR","PAN"):
        return jsonify({"success": False, "msg": "Invalid doc_type"}), 400
    if not file:
        return jsonify({"success": False, "msg": "File required"}), 400
    
    # Get filename for validation
    filename = getattr(file, 'filename', file) or file
    ok, ext = _allowed_ext(filename)
    if not ok:
        return jsonify({"success": False, "msg": "Invalid file type"}), 400
    
    # Handle file upload (both multipart and CLI)
    data, error = _handle_file_upload(file)
    if error:
        return jsonify({"success": False, "msg": error}), 400
    fconn = freelancer_db()
    try:
        cur = fconn.cursor()
        cur.execute("SELECT id FROM freelancer WHERE id=%s", (fid_int,))
        r = cur.fetchone()
        if not r:
            return jsonify({"success": False, "msg": "Freelancer not found"}), 404
        base_dir = os.path.join(os.path.dirname(__file__), "uploads", "kyc", str(fid_int))
        os.makedirs(base_dir, exist_ok=True)
        token = secrets.token_urlsafe(16)
        filename = secure_filename(token + "." + ext)
        full_path = os.path.join(base_dir, filename)
        with open(full_path, "wb") as fp:
            fp.write(data)
        
        try:
            if FEATURE_KYC_REUPLOAD_POLICY:
                cur.execute("""
                    UPDATE kyc_document
                    SET status='REPLACED'
                    WHERE freelancer_id=%s AND doc_type=%s AND status='PENDING'
                """, (fid_int, doc_type))
            cur.execute("""
                INSERT INTO kyc_document (freelancer_id, doc_type, file_path, status, uploaded_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (fid_int, doc_type, full_path, "PENDING", _now()))
            doc_id = cur.lastrowid
            cur.execute("""
                UPDATE freelancer_profile
                SET verification_status='PENDING', is_verified=0
                WHERE freelancer_id=%s
            """, (fid_int,))
            fconn.commit()
            return jsonify({"success": True, "doc_id": doc_id})
        except Exception as db_e:
            import logging
            logging.getLogger(__name__).error(f"Database error: {str(db_e)}")
            fconn.rollback()
            return jsonify({"success": False, "msg": "Database error occurred"}), 500
    finally:
        fconn.close()
