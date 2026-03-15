"""
Payment and cancellation configuration for GigBridge.
Configurable constants - do not hardcode in business logic.
"""
import os

# Razorpay (set via env in production)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# Cancellation refund rules (days/hours before event)
CANCELLATION_FULL_REFUND_DAYS = 7
CANCELLATION_PARTIAL_REFUND_HOURS = 48
CANCELLATION_SAME_DAY_HOURS = 0

# Refund types
REFUND_FULL = "full"
REFUND_PARTIAL = "partial"
REFUND_NONE = "none"

# Payment statuses
PAYMENT_PENDING = "pending"
PAYMENT_CREATED = "created"
PAYMENT_PAID = "paid"
PAYMENT_FAILED = "failed"
PAYMENT_REFUNDED = "refunded"

# Payout statuses
PAYOUT_ON_HOLD = "on_hold"
PAYOUT_REQUESTED = "requested"
PAYOUT_APPROVED = "approved"
PAYOUT_RELEASED = "released"
PAYOUT_FROZEN = "frozen"
PAYOUT_REFUNDED = "refunded"
PAYOUT_PARTIAL_SETTLEMENT = "partial_settlement"

# Event/job statuses
EVENT_SCHEDULED = "scheduled"
EVENT_CHECKED_IN = "checked_in"
EVENT_COMPLETED = "completed"
EVENT_DISPUTED = "disputed"
EVENT_CLOSED = "closed"
EVENT_CANCELLED = "cancelled"
