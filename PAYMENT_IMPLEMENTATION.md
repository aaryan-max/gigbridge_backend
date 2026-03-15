# GigBridge – Razorpay Payment & Dispute Implementation

This document describes the **modular** payment and dispute extensions. No existing login, signup, hire-request, search, or profile logic was changed.

---

## 1. Files Modified

| File | Change |
|------|--------|
| **database.py** | Added columns to `hire_request` (payment_status, payout_status, event_status, check-in/completion fields). Added tables: `payment_records`, `payout_details`, `disputes`. |
| **app.py** | Registered `payment_bp` (import + `app.register_blueprint(payment_bp)`). |
| **requirements.txt** | Added `razorpay`. |

## 2. Files Created

| File | Purpose |
|------|--------|
| **payment_config.py** | Razorpay env keys, cancellation constants, status constants. |
| **payment_routes.py** | Blueprint with all payment, event, dispute, payout routes. |
| **PAYMENT_IMPLEMENTATION.md** | This document. |

---

## 3. New Routes

| Method | Route | Description |
|--------|--------|-------------|
| POST | `/payment/hire/create-order` | Create Razorpay order for a hire (client pays after hire accepted). |
| POST | `/payment/hire/verify` | Verify Razorpay payment and mark hire as funded. |
| POST | `/freelancer/event/checkin` | Freelancer check-in at venue (hire_id, latitude, longitude, timestamp). |
| POST | `/freelancer/event/complete` | Freelancer marks event completed (hire_id, completion_note, proof). |
| POST | `/client/event/approve` | Client approves completion → payout eligible. |
| POST | `/client/event/dispute` | Client raises dispute (hire_id, client_id, dispute_reason, proof). |
| GET | `/admin/disputes/list` | List disputes (admin token). |
| POST | `/admin/disputes/resolve` | Resolve dispute: release_payout / refund_client / partial_settlement. |
| POST | `/admin/payout/release` | Admin release payout for non-disputed hire. |
| POST | `/hire/cancel` | Cancel hire; refund rule from config (7d full, 48h partial, same day none). |
| POST | `/payment/subscription/create-order` | Create Razorpay order for PREMIUM subscription. |
| POST | `/payment/subscription/verify` | Verify subscription payment and activate PREMIUM. |
| GET | `/freelancer/payout/details` | Get freelancer payout details (masked). |
| POST | `/freelancer/payout/add` | Add bank or UPI payout details (no card/UPI PIN). |

---

## 4. Tables / Columns Added

### hire_request (new columns)

- `payment_status` – pending | created | paid | failed | refunded  
- `payout_status` – on_hold | requested | approved | released | frozen | refunded | partial_settlement  
- `event_status` – scheduled | checked_in | completed | disputed | closed | cancelled  
- `checkin_time`, `checkin_latitude`, `checkin_longitude`, `checkin_verified`  
- `completion_note`, `completion_proof`, `completed_at`

### payment_records (new table)

- `payment_id`, `hire_id`, `subscription_id`, `record_type` ('hire' | 'subscription')  
- `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`  
- `amount`, `currency`, `status`, `created_at`

### payout_details (new table)

- `id`, `freelancer_id`, `payout_method` (BANK | UPI)  
- `account_holder_name`, `account_number`, `ifsc_code`, `upi_id`  
- `razorpay_contact_id`, `razorpay_fund_account_id`, `created_at`

### disputes (new table)

- `dispute_id`, `hire_id`, `raised_by`, `dispute_reason`, `proof`  
- `status`, `admin_decision`, `admin_note`, `resolution_type`, `resolved_at`

---

## 5. How Razorpay Order Creation Works

1. Client has an **ACCEPTED** hire.  
2. Client calls **POST /payment/hire/create-order** with `hire_id`, `client_id`.  
3. Backend loads `hire_request` by `hire_id`, checks `client_id` and status, and ensures payment not already done.  
4. Amount = `proposed_budget` (INR) → converted to paise.  
5. `razorpay.Client.order.create(data={"amount": amount_paise, "currency": "INR"})` is called.  
6. Response `order_id` is stored in `payment_records` (record_type='hire', status='created') and `hire_request.payment_status` is set to `created`.  
7. Response returns `razorpay_order_id`, `amount`, `currency`, `key_id` for frontend Checkout.

Subscription flow is similar: **POST /payment/subscription/create-order** with `freelancer_id`, `plan_name=PREMIUM`; creates order and stores it in `payment_records` with `record_type='subscription'`.

---

## 6. How Payment Verification Works

1. After Razorpay Checkout, frontend sends **POST /payment/hire/verify** with `hire_id`, `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`.  
2. Backend finds `payment_records` row by `hire_id` and `razorpay_order_id`.  
3. Signature is verified with HMAC-SHA256: `expected = HMAC(secret, order_id|payment_id)`; must match `razorpay_signature`.  
4. On success: `payment_records` is updated with `razorpay_payment_id`, `razorpay_signature`, `status='paid'`; `hire_request` gets `payment_status='paid'`, `payout_status='on_hold'`, `event_status='scheduled'`.

Subscription: **POST /payment/subscription/verify** with `freelancer_id` and same Razorpay fields; after verification, `payment_records` is marked paid and `update_freelancer_subscription(freelancer_id, "PREMIUM", 30)` is called.

---

## 7. How Dispute Resolution Works

1. Client raises dispute: **POST /client/event/dispute** → insert into `disputes` (status='OPEN'), set `hire_request.event_status='disputed'`.  
2. Admin lists: **GET /admin/disputes/list** (header `X-ADMIN-TOKEN`).  
3. Admin resolves: **POST /admin/disputes/resolve** with `dispute_id`, `resolution_type`, optional `admin_note`.  
   - **release_payout**: set hire `payout_status='released'`, `event_status='closed'`.  
   - **refund_client**: set hire `payout_status='refunded'`, `payment_status='refunded'`, `event_status='closed'`.  
   - **partial_settlement**: set hire `payout_status='partial_settlement'`, `event_status='closed'`.  
4. Dispute row is updated: `status='CLOSED'`, `admin_decision`, `admin_note`, `resolution_type`, `resolved_at`.

---

## 8. How Payout Release Works

- **With dispute:** Admin uses **POST /admin/disputes/resolve** with `resolution_type=release_payout` (or refund/partial).  
- **Without dispute:** After client approves completion (**POST /client/event/approve**), hire `payout_status` becomes `requested`. Admin then calls **POST /admin/payout/release** with `hire_id` and optional `X-ADMIN-TOKEN`; backend sets `payout_status='released'`, `event_status='closed'`.

Payout details are collected separately via **GET/POST /freelancer/payout/details** and **/freelancer/payout/add** (bank or UPI only; no card or UPI PIN stored). Actual transfer to freelancer (e.g. Razorpay Transfer API) can be added later; this implementation only manages status and eligibility.

---

## 9. Cancellation Rules (Configurable)

Defined in **payment_config.py**:

- **7+ days before event** → full refund (refund_type=full).  
- **48 hours to 7 days** → partial refund.  
- **Same day / &lt; 48h** → no refund.

**POST /hire/cancel** sets `hire_request.event_status='cancelled'` and, if payment was paid, marks related `payment_records` as `refunded`. The returned `refund_type` is used by the client; actual Razorpay refund API can be wired separately.

---

## 10. Environment Variables

- `RAZORPAY_KEY_ID` – Razorpay key (for Checkout).  
- `RAZORPAY_KEY_SECRET` – Used for signature verification and server-side order create.

If these are not set, hire/subscription payment routes return 503 (Razorpay not configured). Rest of the app (including existing hire, login, signup, search, profile) is unchanged.
