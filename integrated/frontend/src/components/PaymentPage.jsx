import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { paymentService } from "../services";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

export default function PaymentPage() {
  const { user } = useAuth();
  const [freelancerId, setFreelancerId] = useState("");
  const [amount, setAmount] = useState("");
  const [projectTitle, setProjectTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [payments, setPayments] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (user.id) {
      loadPaymentHistory();
    }
  }, [user.id]);

  const loadPaymentHistory = async () => {
    setHistoryLoading(true);
    try {
      const data = await paymentService.getHistory(user.id, null);
      setPayments(data.payments || []);
    } catch {
      /* empty */
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      if (document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]')) {
        resolve(true);
        return;
      }
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handlePayment = async (e) => {
    e.preventDefault();
    if (!amount || parseFloat(amount) <= 0) {
      setError("Enter a valid amount");
      return;
    }
    if (!freelancerId) {
      setError("Enter freelancer ID");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded) {
        setError("Failed to load payment gateway. Check your connection.");
        setLoading(false);
        return;
      }

      const orderData = await paymentService.createOrder(
        user.id,
        parseInt(freelancerId),
        parseFloat(amount),
        projectTitle
      );

      const options = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: "GigBridge",
        description: projectTitle || "Payment for services",
        order_id: orderData.order_id,
        handler: async function (response) {
          try {
            await paymentService.verifyPayment(
              response.razorpay_order_id,
              response.razorpay_payment_id,
              response.razorpay_signature
            );
            setSuccess("Payment successful!");
            setAmount("");
            setFreelancerId("");
            setProjectTitle("");
            loadPaymentHistory();
          } catch (err) {
            setError(err.message || "Payment verification failed");
          }
        },
        prefill: {
          email: user.email || "",
          name: user.name || "",
        },
        theme: {
          color: "#2563eb",
        },
        modal: {
          ondismiss: function () {
            setLoading(false);
          },
        },
      };

      const razorpay = new window.Razorpay(options);
      razorpay.on("payment.failed", function (response) {
        setError(response.error?.description || "Payment failed");
        setLoading(false);
      });
      razorpay.open();
    } catch (err) {
      setError(err.message || "Failed to initiate payment");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{maxWidth: '800px', margin: '2rem auto', padding: '0 1.5rem'}}>
      <h1 style={{fontSize: '1.75rem', fontWeight: 700, marginBottom: '1.5rem'}}>Payments</h1>

      <div style={{
        background: '#fff',
        borderRadius: '12px',
        padding: '2rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '2rem',
      }}>
        <h2 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem'}}>Make a Payment</h2>

        {error && (
          <div style={{
            background: '#fef2f2', color: '#dc2626', padding: '0.75rem 1rem',
            borderRadius: '8px', marginBottom: '1rem', fontSize: '0.9rem',
          }}>{error}</div>
        )}
        {success && (
          <div style={{
            background: '#f0fdf4', color: '#16a34a', padding: '0.75rem 1rem',
            borderRadius: '8px', marginBottom: '1rem', fontSize: '0.9rem',
          }}>{success}</div>
        )}

        <form onSubmit={handlePayment}>
          <div style={{display: 'grid', gap: '1rem', marginBottom: '1.5rem'}}>
            <label style={{display: 'flex', flexDirection: 'column', gap: '0.25rem'}}>
              <span style={{fontSize: '0.85rem', fontWeight: 500, color: '#374151'}}>Freelancer ID</span>
              <input
                type="number"
                placeholder="e.g. 1"
                value={freelancerId}
                onChange={(e) => { setFreelancerId(e.target.value); setError(""); }}
                required
                style={{
                  padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #d1d5db',
                  fontSize: '0.95rem', outline: 'none',
                }}
              />
            </label>
            <label style={{display: 'flex', flexDirection: 'column', gap: '0.25rem'}}>
              <span style={{fontSize: '0.85rem', fontWeight: 500, color: '#374151'}}>Project Title</span>
              <input
                type="text"
                placeholder="e.g. Website Redesign"
                value={projectTitle}
                onChange={(e) => setProjectTitle(e.target.value)}
                style={{
                  padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #d1d5db',
                  fontSize: '0.95rem', outline: 'none',
                }}
              />
            </label>
            <label style={{display: 'flex', flexDirection: 'column', gap: '0.25rem'}}>
              <span style={{fontSize: '0.85rem', fontWeight: 500, color: '#374151'}}>Amount (INR)</span>
              <input
                type="number"
                placeholder="e.g. 5000"
                min="1"
                step="0.01"
                value={amount}
                onChange={(e) => { setAmount(e.target.value); setError(""); }}
                required
                style={{
                  padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #d1d5db',
                  fontSize: '0.95rem', outline: 'none',
                }}
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '0.85rem', background: '#2563eb', color: '#fff',
              border: 'none', borderRadius: '8px', fontSize: '1rem', fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? "Processing..." : `Pay ${amount ? `Rs. ${amount}` : ""}`}
          </button>
        </form>
      </div>

      <div style={{
        background: '#fff',
        borderRadius: '12px',
        padding: '2rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}>
        <h2 style={{fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem'}}>Payment History</h2>

        {historyLoading ? (
          <p style={{color: '#6b7280'}}>Loading...</p>
        ) : payments.length === 0 ? (
          <p style={{color: '#6b7280'}}>No payments yet.</p>
        ) : (
          <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem'}}>
            {payments.map((p) => (
              <div
                key={p.order_id}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '1rem', background: '#f9fafb', borderRadius: '8px',
                }}
              >
                <div>
                  <div style={{fontWeight: 600, fontSize: '0.95rem'}}>
                    {p.project_title || `Order #${p.order_id.slice(-8)}`}
                  </div>
                  <div style={{fontSize: '0.8rem', color: '#6b7280', marginTop: '0.25rem'}}>
                    Freelancer #{p.freelancer_id}
                    {p.paid_at && ` - ${new Date(p.paid_at * 1000).toLocaleDateString()}`}
                  </div>
                </div>
                <div style={{textAlign: 'right'}}>
                  <div style={{fontWeight: 700, fontSize: '1rem'}}>
                    Rs. {p.amount.toLocaleString()}
                  </div>
                  <span style={{
                    fontSize: '0.75rem', fontWeight: 600,
                    color: p.status === 'paid' ? '#16a34a' : '#d97706',
                    background: p.status === 'paid' ? '#f0fdf4' : '#fffbeb',
                    padding: '0.15rem 0.5rem', borderRadius: '4px',
                  }}>
                    {p.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
