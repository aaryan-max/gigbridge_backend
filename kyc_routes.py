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

def _allowed_ext(filename):
    exts = {"jpg","jpeg","png","pdf"}
    ext = filename.rsplit(".",1)[-1].lower() if "." in filename else ""
    return ext in exts, ext

@kyc_bp.route("/freelancer/kyc/upload", methods=["POST"])
def kyc_upload():
    fid = request.form.get("freelancer_id", "").strip()
    doc_type = (request.form.get("doc_type","") or "").strip().upper()
    file = request.files.get("file")
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
    if not file or not file.filename:
        return jsonify({"success": False, "msg": "File required"}), 400
    ok, ext = _allowed_ext(file.filename)
    if not ok:
        return jsonify({"success": False, "msg": "Invalid file type"}), 400
    data = file.read()
    if len(data) > 5 * 1024 * 1024:
        return jsonify({"success": False, "msg": "File too large"}), 400
    fconn = freelancer_db()
    try:
        cur = fconn.cursor()
        cur.execute("SELECT id FROM freelancer WHERE id=?", (fid_int,))
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
        if FEATURE_KYC_REUPLOAD_POLICY:
            cur.execute("""
                UPDATE kyc_document
                SET status='REPLACED'
                WHERE freelancer_id=? AND doc_type=? AND status='PENDING'
            """, (fid_int, doc_type))
        cur.execute("""
            INSERT INTO kyc_document (freelancer_id, doc_type, file_path, status, uploaded_at)
            VALUES (?,?,?,?,?)
        """, (fid_int, doc_type, full_path, "PENDING", _now()))
        doc_id = cur.lastrowid
        cur.execute("""
            UPDATE freelancer_profile
            SET verification_status='PENDING', is_verified=0
            WHERE freelancer_id=?
        """, (fid_int,))
        fconn.commit()
        return jsonify({"success": True, "doc_id": doc_id})
    finally:
        fconn.close()
