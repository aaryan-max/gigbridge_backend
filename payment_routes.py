"""
Payment, event lifecycle, dispute and payout routes for GigBridge.
Modular extension - does not change existing hire/signup/login flows.
"""
import time
import hmac
import hashlib
from flask import Blueprint, request, jsonify
from database import freelancer_db, client_db, get_dict_cursor, mark_job_completed
from payment_config import (
    RAZORPAY_KEY_ID,
    RAZORPAY_KEY_SECRET,
    CANCELLATION_FULL_REFUND_DAYS,
    CANCELLATION_PARTIAL_REFUND_HOURS,
    PAYMENT_PENDING,
    PAYMENT_CREATED,
    PAYMENT_PAID,
    PAYOUT_ON_HOLD,
    PAYOUT_RELEASED,
    PAYOUT_REFUNDED,
    PAYOUT_PARTIAL_SETTLEMENT,
    EVENT_SCHEDULED,
    EVENT_CHECKED_IN,
    EVENT_COMPLETED,
    EVENT_DISPUTED,
    EVENT_CLOSED,
    EVENT_CANCELLED,
)

payment_bp = Blueprint("payment", __name__)


def _now():
    return int(time.time())


def _get_razorpay_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception:
        return None


def _verify_razorpay_signature(order_id, payment_id, signature):
    if not RAZORPAY_KEY_SECRET:
        return False
    body = f"{order_id}|{payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ============================================================
# HIRE PAYMENT FLOW
# ============================================================

@payment_bp.route("/payment/success", methods=["POST"])
def payment_success():
    """Handle successful payment and mark job as completed"""
    data = request.get_json()

    job_id = data.get("job_id")
    amount = data.get("amount")

    # Validate input
    if not job_id:
        return jsonify({"success": False, "msg": "job_id required"}), 400

    try:
        job_id = int(job_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid job_id"}), 400

    # TODO: Add real payment verification here (Razorpay/Stripe)
    # For now assume payment is successful
    
    success, msg = mark_job_completed(job_id)

    if not success:
        return jsonify({"success": False, "msg": msg}), 400

    return jsonify({
        "success": True,
        "msg": "Payment successful and job completed"
    })

@payment_bp.route("/payment/hire/create-order", methods=["POST"])
def payment_hire_create_order():
    """Create Razorpay order for a hire. Client calls after confirming hire."""
    data = request.get_json(silent=True) or {}
    hire_id = data.get("hire_id")
    client_id = data.get("client_id")
    if not hire_id or not client_id:
        return jsonify({"success": False, "msg": "hire_id and client_id required"}), 400
    try:
        hire_id = int(hire_id)
        client_id = int(client_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "msg": "Invalid ids"}), 400

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, client_id, freelancer_id, proposed_budget, status, payment_status
            FROM hire_request WHERE id=%s
        """, (hire_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "msg": "Hire not found"}), 404
        if int(row["client_id"]) != client_id:
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        if str(row["status"] or "").upper() != "ACCEPTED":
            return jsonify({"success": False, "msg": "Hire must be ACCEPTED to pay"}), 400
        if str(row.get("payment_status") or "pending") == "paid":
            return jsonify({"success": False, "msg": "Already paid"}), 400

        amount_paise = int(float(row["proposed_budget"] or 0) * 100)
        if amount_paise < 100:
            return jsonify({"success": False, "msg": "Invalid amount"}), 400

        client = _get_razorpay_client()
        if not client:
            return jsonify({"success": False, "msg": "Razorpay not configured"}), 503

        order = client.order.create(data={"amount": amount_paise, "currency": "INR"})
        order_id = order.get("id")
        if not order_id:
            return jsonify({"success": False, "msg": "Failed to create order"}), 500

        cur.execute("""
            INSERT INTO payment_records (hire_id, record_type, razorpay_order_id, amount, status, created_at)
            VALUES (%s, 'hire', %s, %s, 'created', %s)
        """, (hire_id, order_id, float(row["proposed_budget"]), _now()))
        conn.commit()

        cur.execute("""
            UPDATE hire_request SET payment_status='created' WHERE id=%s
        """, (hire_id,))
        conn.commit()

        return jsonify({
            "success": True,
            "razorpay_order_id": order_id,
            "amount": amount_paise,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID
        })
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": str(e)}), 500
    finally:
        conn.close()


@payment_bp.route("/payment/hire/verify", methods=["POST"])
def payment_hire_verify():
    """Verify Razorpay payment and mark hire as funded."""
    data = request.get_json(silent=True) or {}
    hire_id = data.get("hire_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_signature = data.get("razorpay_signature")
    if not all([hire_id, razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return jsonify({"success": False, "msg": "Missing payment verification fields"}), 400

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT payment_id, hire_id, status FROM payment_records
            WHERE hire_id=%s AND razorpay_order_id=%s AND record_type='hire'
        """, (int(hire_id), razorpay_order_id))
        rec = cur.fetchone()
        if not rec:
            return jsonify({"success": False, "msg": "Order not found"}), 404
        if str(rec.get("status") or "") == "paid":
            return jsonify({"success": True, "msg": "Already verified"})

        if not _verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            return jsonify({"success": False, "msg": "Invalid signature"}), 400

        cur.execute("""
            UPDATE payment_records SET razorpay_payment_id=%s, razorpay_signature=%s, status='paid', created_at=created_at
            WHERE payment_id=%s
        """, (razorpay_payment_id, razorpay_signature, rec["payment_id"]))
        cur.execute("""
            UPDATE hire_request SET payment_status='paid', payout_status='on_hold', event_status=%s WHERE id=%s
        """, (EVENT_SCHEDULED, int(hire_id)))
        conn.commit()
        return jsonify({"success": True, "msg": "Payment verified"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": str(e)}), 500
    finally:
        conn.close()


# ============================================================
# EVENT CHECK-IN
# ============================================================

@payment_bp.route("/freelancer/event/checkin", methods=["POST"])
def freelancer_event_checkin():
    """Freelancer check-in at venue."""
    data = request.get_json(silent=True) or {}
    hire_id = data.get("hire_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    timestamp = data.get("timestamp", _now())
    if hire_id is None:
        return jsonify({"success": False, "msg": "hire_id required"}), 400
    try:
        hire_id = int(hire_id)
        lat = float(latitude) if latitude is not None else None
        lon = float(longitude) if longitude is not None else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "msg": "Invalid hire_id or coordinates"}), 400

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, freelancer_id, event_status, payment_status
            FROM hire_request WHERE id=%s
        """, (hire_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "msg": "Hire not found"}), 404
        if data.get("freelancer_id") and int(row["freelancer_id"]) != int(data["freelancer_id"]):
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        if str(row.get("payment_status") or "") != "paid":
            return jsonify({"success": False, "msg": "Hire must be paid before check-in"}), 400

        cur.execute("""
            UPDATE hire_request SET
                checkin_time=%s, checkin_latitude=%s, checkin_longitude=%s, checkin_verified=1, event_status=%s
            WHERE id=%s
        """, (int(timestamp), lat, lon, EVENT_CHECKED_IN, hire_id))
        conn.commit()
        return jsonify({"success": True, "msg": "Check-in recorded"})
    finally:
        conn.close()


# ============================================================
# EVENT COMPLETION
# ============================================================

@payment_bp.route("/freelancer/event/complete", methods=["POST"])
def freelancer_event_complete():
    """Freelancer marks event completed."""
    data = request.get_json(silent=True) or {}
    hire_id = data.get("hire_id")
    completion_note = data.get("completion_note", "").strip()
    proof = data.get("proof") or data.get("completion_proof") or ""
    if not hire_id:
        return jsonify({"success": False, "msg": "hire_id required"}), 400
    hire_id = int(hire_id)

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, freelancer_id, event_status
            FROM hire_request WHERE id=%s
        """, (hire_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "msg": "Hire not found"}), 404
        if str(row.get("event_status") or "") not in (EVENT_SCHEDULED, EVENT_CHECKED_IN):
            return jsonify({"success": False, "msg": "Invalid state for completion"}), 400

        cur.execute("""
            UPDATE hire_request SET completion_note=%s, completion_proof=%s, completed_at=%s, event_status=%s
            WHERE id=%s
        """, (completion_note, proof, _now(), EVENT_COMPLETED, hire_id))
        conn.commit()
        return jsonify({"success": True, "msg": "Completion recorded"})
    finally:
        conn.close()


@payment_bp.route("/client/event/approve", methods=["POST"])
def client_event_approve():
    """Client approves completion -> payout becomes eligible."""
    data = request.get_json(silent=True) or {}
    hire_id = data.get("hire_id")
    client_id = data.get("client_id")
    if not hire_id or not client_id:
        return jsonify({"success": False, "msg": "hire_id and client_id required"}), 400
    hire_id, client_id = int(hire_id), int(client_id)

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, client_id, event_status
            FROM hire_request WHERE id=%s
        """, (hire_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "msg": "Hire not found"}), 404
        if int(row["client_id"]) != client_id:
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        if str(row.get("event_status") or "") != EVENT_COMPLETED:
            return jsonify({"success": False, "msg": "Event must be completed by freelancer first"}), 400

        cur.execute("""
            UPDATE hire_request SET payout_status=%s WHERE id=%s
        """, ("requested", hire_id))
        conn.commit()
        return jsonify({"success": True, "msg": "Completion approved; payout eligible"})
    finally:
        conn.close()


# ============================================================
# DISPUTE
# ============================================================

@payment_bp.route("/client/event/dispute", methods=["POST"])
def client_event_dispute():
    """Client raises dispute."""
    data = request.get_json(silent=True) or {}
    hire_id = data.get("hire_id")
    client_id = data.get("client_id")
    reason = data.get("dispute_reason", "").strip()
    proof = data.get("proof", "").strip()
    if not hire_id or not client_id:
        return jsonify({"success": False, "msg": "hire_id and client_id required"}), 400
    hire_id, client_id = int(hire_id), int(client_id)

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("SELECT id, client_id, event_status FROM hire_request WHERE id=%s", (hire_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "msg": "Hire not found"}), 404
        if int(row["client_id"]) != client_id:
            return jsonify({"success": False, "msg": "Not authorized"}), 403

        cur.execute("""
            INSERT INTO disputes (hire_id, raised_by, dispute_reason, proof, status, resolved_at)
            VALUES (%s, 'client', %s, %s, 'OPEN', NULL)
        """, (hire_id, reason, proof))
        cur.execute("UPDATE hire_request SET event_status=%s WHERE id=%s", (EVENT_DISPUTED, hire_id))
        conn.commit()
        return jsonify({"success": True, "msg": "Dispute raised"})
    finally:
        conn.close()


@payment_bp.route("/admin/disputes/list", methods=["GET"])
def admin_disputes_list():
    """List open disputes (admin)."""
    token = request.headers.get("X-ADMIN-TOKEN", "").strip()
    if not token:
        return jsonify({"success": False, "msg": "Unauthorized"}), 401
    conn = freelancer_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT admin_id, expires_at FROM admin_session WHERE token=%s
        """, (token,))
        r = cur.fetchone()
        if not r or (r[1] or 0) < _now():
            return jsonify({"success": False, "msg": "Unauthorized"}), 401
    finally:
        conn.close()

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT d.dispute_id, d.hire_id, d.raised_by, d.dispute_reason, d.proof, d.status, d.admin_decision, d.resolved_at
            FROM disputes d ORDER BY d.dispute_id DESC
        """)
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "dispute_id": r.get("dispute_id"),
                "hire_id": r.get("hire_id"),
                "raised_by": r.get("raised_by"),
                "dispute_reason": r.get("dispute_reason"),
                "proof": r.get("proof"),
                "status": r.get("status"),
                "admin_decision": r.get("admin_decision"),
                "resolved_at": r.get("resolved_at"),
            })
        return jsonify({"success": True, "disputes": out})
    finally:
        conn.close()


@payment_bp.route("/admin/disputes/resolve", methods=["POST"])
def admin_disputes_resolve():
    """Admin: release payout / refund client / partial settlement."""
    data = request.get_json(silent=True) or {}
    token = request.headers.get("X-ADMIN-TOKEN", "").strip()
    if not token:
        return jsonify({"success": False, "msg": "Unauthorized"}), 401
    conn = freelancer_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT admin_id, expires_at FROM admin_session WHERE token=%s", (token,))
        r = cur.fetchone()
        if not r or (r[1] or 0) < _now():
            return jsonify({"success": False, "msg": "Unauthorized"}), 401
    finally:
        conn.close()

    dispute_id = data.get("dispute_id")
    resolution_type = (data.get("resolution_type") or "").strip().lower()
    admin_note = (data.get("admin_note") or "").strip()
    if not dispute_id or resolution_type not in ("release_payout", "refund_client", "partial_settlement"):
        return jsonify({"success": False, "msg": "dispute_id and resolution_type (release_payout|refund_client|partial_settlement) required"}), 400
    dispute_id = int(dispute_id)

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("SELECT dispute_id, hire_id FROM disputes WHERE dispute_id=%s AND status='OPEN'", (dispute_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "msg": "Dispute not found or already resolved"}), 404
        hire_id = row["hire_id"]

        if resolution_type == "release_payout":
            cur.execute("UPDATE hire_request SET payout_status=%s, event_status=%s WHERE id=%s",
                        (PAYOUT_RELEASED, EVENT_CLOSED, hire_id))
        elif resolution_type == "refund_client":
            cur.execute("UPDATE hire_request SET payout_status=%s, payment_status='refunded', event_status=%s WHERE id=%s",
                        (PAYOUT_REFUNDED, EVENT_CLOSED, hire_id))
        else:
            cur.execute("UPDATE hire_request SET payout_status=%s, event_status=%s WHERE id=%s",
                        (PAYOUT_PARTIAL_SETTLEMENT, EVENT_CLOSED, hire_id))

        cur.execute("""
            UPDATE disputes SET status='CLOSED', admin_decision=%s, admin_note=%s, resolution_type=%s, resolved_at=%s
            WHERE dispute_id=%s
        """, (resolution_type, admin_note, resolution_type, _now(), dispute_id))
        conn.commit()
        return jsonify({"success": True, "msg": "Dispute resolved"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": str(e)}), 500
    finally:
        conn.close()


# ============================================================
# CANCELLATION (configurable rules)
# ============================================================

@payment_bp.route("/admin/payout/release", methods=["POST"])
def admin_payout_release():
    """Admin: release payout for a hire (no dispute)."""
    data = request.get_json(silent=True) or {}
    token = request.headers.get("X-ADMIN-TOKEN", "").strip()
    if not token:
        return jsonify({"success": False, "msg": "Unauthorized"}), 401
    conn = freelancer_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT admin_id, expires_at FROM admin_session WHERE token=%s", (token,))
        r = cur.fetchone()
        if not r or (r[1] or 0) < _now():
            return jsonify({"success": False, "msg": "Unauthorized"}), 401
    finally:
        conn.close()

    hire_id = data.get("hire_id")
    if not hire_id:
        return jsonify({"success": False, "msg": "hire_id required"}), 400
    hire_id = int(hire_id)
    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("SELECT id, payout_status, event_status FROM hire_request WHERE id=%s", (hire_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "msg": "Hire not found"}), 404
        if str(row.get("event_status") or "") == EVENT_DISPUTED:
            return jsonify({"success": False, "msg": "Use dispute resolve for disputed hires"}), 400
        cur.execute("UPDATE hire_request SET payout_status=%s, event_status=%s WHERE id=%s",
                    (PAYOUT_RELEASED, EVENT_CLOSED, hire_id))
        conn.commit()
        return jsonify({"success": True, "msg": "Payout released"})
    finally:
        conn.close()


@payment_bp.route("/hire/cancel", methods=["POST"])
def hire_cancel():
    """Cancel hire. Refund per config: 7+ days full, 48h partial, same day none."""
    data = request.get_json(silent=True) or {}
    hire_id = data.get("hire_id")
    client_id = data.get("client_id")
    if not hire_id or not client_id:
        return jsonify({"success": False, "msg": "hire_id and client_id required"}), 400
    hire_id, client_id = int(hire_id), int(client_id)

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, client_id, event_date, start_time, payment_status, event_status
            FROM hire_request WHERE id=%s
        """, (hire_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "msg": "Hire not found"}), 404
        if int(row["client_id"]) != client_id:
            return jsonify({"success": False, "msg": "Not authorized"}), 403
        if str(row.get("event_status") or "") == EVENT_CANCELLED:
            return jsonify({"success": False, "msg": "Already cancelled"}), 400

        event_date_str = (row.get("event_date") or "").strip()
        if not event_date_str:
            refund_type = "full"
        else:
            try:
                from datetime import datetime, timedelta
                event_dt = datetime.strptime(event_date_str, "%Y-%m-%d")
                now = datetime.now()
                delta = (event_dt - now).total_seconds() / 3600
                if delta >= CANCELLATION_FULL_REFUND_DAYS * 24:
                    refund_type = "full"
                elif delta >= CANCELLATION_PARTIAL_REFUND_HOURS:
                    refund_type = "partial"
                else:
                    refund_type = "none"
            except Exception:
                refund_type = "partial"

        cur.execute("""
            UPDATE hire_request SET event_status=%s WHERE id=%s
        """, (EVENT_CANCELLED, hire_id))
        if str(row.get("payment_status") or "") == "paid":
            cur.execute("""
                UPDATE payment_records SET status='refunded' WHERE hire_id=%s AND record_type='hire'
            """, (hire_id,))
        conn.commit()
        return jsonify({"success": True, "refund_type": refund_type, "msg": "Cancelled"})
    finally:
        conn.close()


# ============================================================
# SUBSCRIPTION PAYMENT (Razorpay)
# ============================================================

@payment_bp.route("/payment/subscription/create-order", methods=["POST"])
def payment_subscription_create_order():
    """Create Razorpay order for freelancer subscription upgrade."""
    data = request.get_json(silent=True) or {}
    freelancer_id = data.get("freelancer_id")
    plan_name = (data.get("plan_name") or "").strip().upper()
    if not freelancer_id or plan_name != "PREMIUM":
        return jsonify({"success": False, "msg": "freelancer_id and plan_name PREMIUM required"}), 400
    freelancer_id = int(freelancer_id)
    amount_paise = 69900  # 699 INR

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("SELECT id FROM freelancer WHERE id=%s", (freelancer_id,))
        if not cur.fetchone():
            return jsonify({"success": False, "msg": "Freelancer not found"}), 404
    finally:
        conn.close()

    client = _get_razorpay_client()
    if not client:
        return jsonify({"success": False, "msg": "Razorpay not configured"}), 503

    try:
        order = client.order.create(data={"amount": amount_paise, "currency": "INR"})
        order_id = order.get("id")
        if not order_id:
            return jsonify({"success": False, "msg": "Failed to create order"}), 500
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            INSERT INTO payment_records (subscription_id, record_type, razorpay_order_id, amount, status, created_at)
            VALUES (%s, 'subscription', %s, %s, 'created', %s)
        """, (freelancer_id, order_id, 699.0, _now()))
        conn.commit()
        return jsonify({
            "success": True,
            "razorpay_order_id": order_id,
            "amount": amount_paise,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID
        })
    finally:
        conn.close()


@payment_bp.route("/payment/subscription/verify", methods=["POST"])
def payment_subscription_verify():
    """Verify subscription payment and activate plan."""
    data = request.get_json(silent=True) or {}
    freelancer_id = data.get("freelancer_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_signature = data.get("razorpay_signature")
    if not all([freelancer_id, razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return jsonify({"success": False, "msg": "Missing verification fields"}), 400
    freelancer_id = int(freelancer_id)

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT payment_id, subscription_id, status FROM payment_records
            WHERE subscription_id=%s AND razorpay_order_id=%s AND record_type='subscription'
        """, (freelancer_id, razorpay_order_id))
        rec = cur.fetchone()
        if not rec:
            return jsonify({"success": False, "msg": "Order not found"}), 404
        if str(rec.get("status") or "") == "paid":
            from database import update_freelancer_subscription
            update_freelancer_subscription(freelancer_id, "PREMIUM", 30)
            return jsonify({"success": True, "msg": "Already activated"})

        if not _verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            return jsonify({"success": False, "msg": "Invalid signature"}), 400

        cur.execute("""
            UPDATE payment_records SET razorpay_payment_id=%s, razorpay_signature=%s, status='paid'
            WHERE payment_id=%s
        """, (razorpay_payment_id, razorpay_signature, rec["payment_id"]))
        conn.commit()

        from database import update_freelancer_subscription
        update_freelancer_subscription(freelancer_id, "PREMIUM", 30)
        return jsonify({"success": True, "msg": "Subscription activated"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "msg": str(e)}), 500
    finally:
        conn.close()


# ============================================================
# PAYOUT DETAILS (separate from profile)
# ============================================================

@payment_bp.route("/freelancer/payout/details", methods=["GET"])
def freelancer_payout_details():
    """GET freelancer payout details (bank or UPI)."""
    freelancer_id = request.args.get("freelancer_id")
    if not freelancer_id:
        return jsonify({"success": False, "msg": "freelancer_id required"}), 400
    try:
        freelancer_id = int(freelancer_id)
    except ValueError:
        return jsonify({"success": False, "msg": "Invalid freelancer_id"}), 400

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT id, payout_method, account_holder_name, account_number, ifsc_code, upi_id, created_at
            FROM payout_details WHERE freelancer_id=%s ORDER BY id DESC
        """, (freelancer_id,))
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "id": r.get("id"),
                "payout_method": r.get("payout_method"),
                "account_holder_name": r.get("account_holder_name"),
                "account_number": r.get("account_number") and "****" + str(r.get("account_number"))[-4:] or None,
                "ifsc_code": r.get("ifsc_code"),
                "upi_id": r.get("upi_id"),
                "created_at": r.get("created_at"),
            })
        return jsonify({"success": True, "details": out})
    finally:
        conn.close()


@payment_bp.route("/freelancer/payout/add", methods=["POST"])
def freelancer_payout_add():
    """POST add payout details - bank or UPI. No card/UPI PIN."""
    data = request.get_json(silent=True) or {}
    freelancer_id = data.get("freelancer_id")
    payout_method = (data.get("payout_method") or "").strip().upper()
    account_holder_name = (data.get("account_holder_name") or "").strip()
    if not freelancer_id or not payout_method or not account_holder_name:
        return jsonify({"success": False, "msg": "freelancer_id, payout_method (BANK|UPI), account_holder_name required"}), 400
    freelancer_id = int(freelancer_id)

    if payout_method == "BANK":
        account_number = (data.get("account_number") or "").strip()
        ifsc_code = (data.get("ifsc_code") or "").strip()
        if not account_number or not ifsc_code:
            return jsonify({"success": False, "msg": "account_number and ifsc_code required for BANK"}), 400
        upi_id = None
    elif payout_method == "UPI":
        upi_id = (data.get("upi_id") or "").strip()
        if not upi_id:
            return jsonify({"success": False, "msg": "upi_id required for UPI"}), 400
        account_number = None
        ifsc_code = None
    else:
        return jsonify({"success": False, "msg": "payout_method must be BANK or UPI"}), 400

    conn = freelancer_db()
    try:
        cur = get_dict_cursor(conn)
        cur.execute("SELECT id FROM freelancer WHERE id=%s", (freelancer_id,))
        if not cur.fetchone():
            return jsonify({"success": False, "msg": "Freelancer not found"}), 404

        cur.execute("""
            INSERT INTO payout_details (freelancer_id, payout_method, account_holder_name, account_number, ifsc_code, upi_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (freelancer_id, payout_method, account_holder_name, account_number, ifsc_code, upi_id, _now()))
        conn.commit()
        return jsonify({"success": True, "msg": "Payout details added"})
    finally:
        conn.close()
