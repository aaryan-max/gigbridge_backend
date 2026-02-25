from flask import Blueprint, request, jsonify, send_file
import sqlite3
import time
import secrets
import json
import os
from werkzeug.security import check_password_hash
from database import client_db, freelancer_db
from settings import FEATURE_ADMIN_LOGOUT, FEATURE_KYC_RETENTION_CLEANUP

admin_bp = Blueprint("admin", __name__)

def _now():
    return int(time.time())

def require_admin(fn):
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-ADMIN-TOKEN", "").strip()
        if not token:
            return jsonify({"success": False, "msg": "Unauthorized"}), 401
        conn = freelancer_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.admin_id, s.expires_at, u.is_enabled, u.role
                FROM admin_session s
                JOIN admin_user u ON u.id = s.admin_id
                WHERE s.token=?
            """, (token,))
            r = cur.fetchone()
            if not r:
                return jsonify({"success": False, "msg": "Unauthorized"}), 401
            if int(r[1] or 0) < _now():
                return jsonify({"success": False, "msg": "Unauthorized"}), 401
            if int(r[2] or 0) != 1:
                return jsonify({"success": False, "msg": "Unauthorized"}), 401
            request.admin_id = r[0]
            request.admin_role = r[3]
        finally:
            conn.close()
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@admin_bp.route("/admin/login", methods=["POST"])
def admin_login():
    d = request.get_json(silent=True) or {}
    email = str(d.get("email", "")).strip()
    password = str(d.get("password", "")).strip()
    if not email or not password:
        return jsonify({"success": False, "msg": "Invalid"}), 400
    conn = freelancer_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash, role, is_enabled FROM admin_user WHERE email=?", (email,))
        r = cur.fetchone()
        if not r or int(r[3] or 0) != 1 or not check_password_hash(r[1], password):
            return jsonify({"success": False, "msg": "Unauthorized"}), 401
        admin_id = r[0]
        role = r[2]
        token = secrets.token_urlsafe(32)
        expires = _now() + 86400
        cur.execute("INSERT INTO admin_session (token, admin_id, expires_at, created_at) VALUES (?,?,?,?)",
                    (token, admin_id, expires, _now()))
        cur.execute("INSERT INTO admin_audit_log (admin_id, action, payload_json, created_at) VALUES (?,?,?,?)",
                    (admin_id, "login", json.dumps({"email": email}), _now()))
        conn.commit()
        return jsonify({"success": True, "token": token, "admin_id": admin_id, "role": role})
    finally:
        conn.close()

@admin_bp.route("/admin/stats", methods=["GET"])
@require_admin
def admin_stats():
    totals = {}
    c = client_db()
    try:
        cur = c.cursor()
        cur.execute("SELECT COUNT(*) FROM client")
        totals["total_clients"] = cur.fetchone()[0]
    finally:
        c.close()
    f = freelancer_db()
    try:
        cur = f.cursor()
        cur.execute("SELECT COUNT(*) FROM freelancer")
        totals["total_freelancers"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM hire_request")
        totals["total_hire_requests"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM message")
        totals["total_messages"] = cur.fetchone()[0]
        try:
            cur.execute("SELECT COUNT(*) FROM kyc_document WHERE status='PENDING'")
            totals["total_kyc_pending"] = cur.fetchone()[0]
        except Exception:
            totals["total_kyc_pending"] = 0
        try:
            cur.execute("SELECT COUNT(*) FROM freelancer_profile WHERE is_verified=1")
            totals["total_verified_freelancers"] = cur.fetchone()[0]
        except Exception:
            totals["total_verified_freelancers"] = 0
    finally:
        f.close()
    return jsonify({"success": True, **totals})

@admin_bp.route("/admin/clients", methods=["GET"])
@require_admin
def admin_clients():
    c = client_db()
    try:
        cur = c.cursor()
        try:
            cur.execute("SELECT id, name, email, COALESCE(auth_provider,'local') FROM client")
        except Exception:
            cur.execute("SELECT id, name, email, 'local' FROM client")
        rows = cur.fetchall()
        res = []
        for r in rows:
            res.append({"id": r[0], "name": r[1], "email": r[2], "auth_provider": r[3]})
        return jsonify({"success": True, "results": res})
    finally:
        c.close()

@admin_bp.route("/admin/freelancers", methods=["GET"])
@require_admin
def admin_freelancers():
    f = freelancer_db()
    try:
        cur = f.cursor()
        cur.execute("""
            SELECT f.id, f.name, f.email,
                   COALESCE(fp.category,''), COALESCE(fp.rating,0),
                   COALESCE(fp.verification_status,'NOT_SUBMITTED'), COALESCE(fp.is_verified,0)
            FROM freelancer f
            LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
            ORDER BY f.id DESC
        """)
        rows = cur.fetchall()
        res = []
        for r in rows:
            res.append({
                "id": r[0], "name": r[1], "email": r[2],
                "category": r[3], "rating": r[4],
                "verification_status": r[5], "is_verified": r[6],
            })
        return jsonify({"success": True, "results": res})
    finally:
        f.close()

def _audit(admin_id, action, payload):
    f = freelancer_db()
    try:
        cur = f.cursor()
        cur.execute("INSERT INTO admin_audit_log (admin_id, action, payload_json, created_at) VALUES (?,?,?,?)",
                    (admin_id, action, json.dumps(payload), _now()))
        f.commit()
    finally:
        f.close()

@admin_bp.route("/admin/user/disable", methods=["POST"])
@require_admin
def admin_user_disable():
    d = request.get_json(silent=True) or {}
    role = str(d.get("role","")).strip().lower()
    uid = int(d.get("id", 0))
    if role not in ("client","freelancer") or uid <= 0:
        return jsonify({"success": False, "msg": "Invalid"}), 400
    if role == "client":
        db = client_db()
        try:
            cur = db.cursor()
            cur.execute("UPDATE client SET is_enabled=0 WHERE id=?", (uid,))
            db.commit()
        finally:
            db.close()
    else:
        db = freelancer_db()
        try:
            cur = db.cursor()
            cur.execute("UPDATE freelancer SET is_enabled=0 WHERE id=?", (uid,))
            db.commit()
        finally:
            db.close()
    _audit(getattr(request, "admin_id", None), "user_disable", {"role": role, "id": uid})
    return jsonify({"success": True})

@admin_bp.route("/admin/user/enable", methods=["POST"])
@require_admin
def admin_user_enable():
    d = request.get_json(silent=True) or {}
    role = str(d.get("role","")).strip().lower()
    uid = int(d.get("id", 0))
    if role not in ("client","freelancer") or uid <= 0:
        return jsonify({"success": False, "msg": "Invalid"}), 400
    if role == "client":
        db = client_db()
        try:
            cur = db.cursor()
            cur.execute("UPDATE client SET is_enabled=1 WHERE id=?", (uid,))
            db.commit()
        finally:
            db.close()
    else:
        db = freelancer_db()
        try:
            cur = db.cursor()
            cur.execute("UPDATE freelancer SET is_enabled=1 WHERE id=?", (uid,))
            db.commit()
        finally:
            db.close()
    _audit(getattr(request, "admin_id", None), "user_enable", {"role": role, "id": uid})
    return jsonify({"success": True})

@admin_bp.route("/admin/kyc/pending", methods=["GET"])
@require_admin
def admin_kyc_pending():
    f = freelancer_db()
    try:
        cur = f.cursor()
        cur.execute("""
            SELECT k.id, k.freelancer_id, k.doc_type, k.uploaded_at,
                   frel.name, frel.email
            FROM kyc_document k
            JOIN freelancer frel ON frel.id = k.freelancer_id
            WHERE k.status='PENDING'
            ORDER BY k.uploaded_at DESC
        """)
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "doc_id": r[0],
                "freelancer_id": r[1],
                "doc_type": r[2],
                "uploaded_at": r[3],
                "freelancer_name": r[4],
                "freelancer_email": r[5],
            })
        return jsonify({"success": True, "results": out})
    finally:
        f.close()

@admin_bp.route("/admin/kyc/document/<int:doc_id>", methods=["GET"])
@require_admin
def admin_kyc_document(doc_id: int):
    f = freelancer_db()
    try:
        cur = f.cursor()
        cur.execute("SELECT file_path FROM kyc_document WHERE id=?", (doc_id,))
        r = cur.fetchone()
        if not r:
            return jsonify({"success": False, "msg": "Not found"}), 404
        path = r[0]
        if not os.path.isfile(path):
            return jsonify({"success": False, "msg": "Not found"}), 404
        return send_file(path, as_attachment=True)
    finally:
        f.close()

@admin_bp.route("/admin/kyc/verify", methods=["POST"])
@require_admin
def admin_kyc_verify():
    d = request.get_json(silent=True) or {}
    doc_id = int(d.get("doc_id", 0))
    action = str(d.get("action","")).strip().lower()
    reason = str(d.get("reason","")).strip()
    if doc_id <= 0 or action not in ("approve","reject"):
        return jsonify({"success": False, "msg": "Invalid"}), 400
    admin_id = getattr(request, "admin_id", None)
    f = freelancer_db()
    try:
        cur = f.cursor()
        cur.execute("SELECT freelancer_id, doc_type FROM kyc_document WHERE id=?", (doc_id,))
        r = cur.fetchone()
        if not r:
            return jsonify({"success": False, "msg": "Not found"}), 404
        fid, doc_type = r[0], r[1]
        if action == "approve":
            cur.execute("""
                UPDATE kyc_document
                SET status='APPROVED', verified_by_admin_id=?, verified_at=?
                WHERE id=?
            """, (admin_id, _now(), doc_id))
            # Latest-approval check per type
            latest_ok = True
            for t in ("AADHAAR", "PAN"):
                cur.execute("""
                    SELECT status FROM kyc_document
                    WHERE freelancer_id=? AND doc_type=?
                    ORDER BY uploaded_at DESC, id DESC
                    LIMIT 1
                """, (fid, t))
                rr = cur.fetchone()
                if not rr or rr[0] != "APPROVED":
                    latest_ok = False
                    break
            if latest_ok:
                cur.execute("""
                    UPDATE freelancer_profile
                    SET verification_status='VERIFIED', is_verified=1, verification_note=''
                    WHERE freelancer_id=?
                """, (fid,))
            else:
                cur.execute("""
                    UPDATE freelancer_profile
                    SET verification_status='PENDING', is_verified=0
                    WHERE freelancer_id=?
                """, (fid,))
        else:
            cur.execute("""
                UPDATE kyc_document
                SET status='REJECTED', reject_reason=?, verified_by_admin_id=?, verified_at=?
                WHERE id=?
            """, (reason, admin_id, _now(), doc_id))
            cur.execute("""
                UPDATE freelancer_profile
                SET verification_status='REJECTED', is_verified=0, verification_note=?
                WHERE freelancer_id=?
            """, (reason, fid))
        f.commit()
        _audit(admin_id, "kyc_verify", {"doc_id": doc_id, "action": action, "reason": reason})
        return jsonify({"success": True})
    finally:
        f.close()

@admin_bp.route("/admin/logout", methods=["POST"])
@require_admin
def admin_logout():
    if not FEATURE_ADMIN_LOGOUT:
        return jsonify({"success": False, "msg": "disabled"}), 404
    token = request.headers.get("X-ADMIN-TOKEN", "").strip()
    admin_id = getattr(request, "admin_id", None)
    f = freelancer_db()
    try:
        cur = f.cursor()
        cur.execute("DELETE FROM admin_session WHERE token=?", (token,))
        f.commit()
        _audit(admin_id, "logout", {"token": "self"})
        return jsonify({"success": True})
    finally:
        f.close()

@admin_bp.route("/admin/logout_all", methods=["POST"])
@require_admin
def admin_logout_all():
    if not FEATURE_ADMIN_LOGOUT:
        return jsonify({"success": False, "msg": "disabled"}), 404
    admin_id = getattr(request, "admin_id", None)
    f = freelancer_db()
    try:
        cur = f.cursor()
        cur.execute("DELETE FROM admin_session WHERE admin_id=?", (admin_id,))
        f.commit()
        _audit(admin_id, "logout_all", {"admin_id": admin_id})
        return jsonify({"success": True})
    finally:
        f.close()

@admin_bp.route("/admin/kyc/cleanup", methods=["POST"])
@require_admin
def admin_kyc_cleanup():
    if not FEATURE_KYC_RETENTION_CLEANUP:
        return jsonify({"success": False, "msg": "disabled"}), 404
    cutoff = _now() - 30 * 24 * 3600
    f = freelancer_db()
    removed_files = 0
    removed_rows = 0
    try:
        cur = f.cursor()
        cur.execute("""
            SELECT id, file_path FROM kyc_document
            WHERE uploaded_at < ? AND status IN ('PENDING','REJECTED')
        """, (cutoff,))
        rows = cur.fetchall()
        for r in rows:
            path = r[1]
            try:
                if path and os.path.isfile(path):
                    os.remove(path)
                    removed_files += 1
            except Exception:
                pass
            cur.execute("DELETE FROM kyc_document WHERE id=?", (r[0],))
            removed_rows += 1
        f.commit()
        _audit(getattr(request, "admin_id", None), "kyc_cleanup", {"removed_rows": removed_rows, "removed_files": removed_files})
        return jsonify({"success": True, "removed_rows": removed_rows, "removed_files": removed_files})
    finally:
        f.close()
