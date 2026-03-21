import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { api } from "../services/api";

const STEPS = { EMAIL: 1, OTP: 2, RESET: 3, DONE: 4 };

export default function ForgotPassword() {
  const { role = "client" } = useParams();
  const navigate = useNavigate();

  const [step, setStep] = useState(STEPS.EMAIL);
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSendOTP = async (e) => {
    e.preventDefault();
    if (!email) { setError("Enter your email"); return; }
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/forgot-password", { email, role });
      if (res.debug_otp) {
        setOtp(res.debug_otp);
      }
      setStep(STEPS.OTP);
    } catch (err) {
      setError(err.message || "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (!otp) { setError("Enter the OTP"); return; }
    setLoading(true);
    setError("");
    try {
      await api.post("/verify-reset-otp", { email, otp, role });
      setStep(STEPS.RESET);
    } catch (err) {
      setError(err.message || "Invalid OTP");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.post("/reset-password", { email, otp, new_password: newPassword, role });
      setStep(STEPS.DONE);
    } catch (err) {
      setError(err.message || "Failed to reset password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-left">
          <h2>Reset Password</h2>

          {step !== STEPS.DONE && (
            <div className="cp-progress" style={{marginBottom: '1.5rem'}}>
              <div
                className="cp-bar"
                style={{width: step === STEPS.EMAIL ? '33%' : step === STEPS.OTP ? '66%' : '100%'}}
              />
            </div>
          )}

          {error && <div style={{color: '#dc2626', marginBottom: '1rem', fontSize: '0.9rem'}}>{error}</div>}

          {step === STEPS.EMAIL && (
            <form className="auth-form" onSubmit={handleSendOTP}>
              <p style={{color: '#6b7280', marginBottom: '1rem', fontSize: '0.9rem'}}>
                Enter the email address associated with your {role} account. We'll send you a verification code.
              </p>
              <label>
                <span>Email</span>
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setError(""); }}
                  required
                />
              </label>
              <button className="auth-primary" type="submit" disabled={loading}>
                {loading ? "Sending..." : "Send Reset Code"}
              </button>
            </form>
          )}

          {step === STEPS.OTP && (
            <form className="auth-form" onSubmit={handleVerifyOTP}>
              <p style={{color: '#6b7280', marginBottom: '1rem', fontSize: '0.9rem'}}>
                We sent a 6-digit code to <strong>{email}</strong>. Enter it below.
              </p>
              <label>
                <span>Verification Code</span>
                <input
                  type="text"
                  placeholder="123456"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => { setOtp(e.target.value); setError(""); }}
                  required
                  style={{textAlign: 'center', letterSpacing: '0.5em', fontSize: '1.2rem'}}
                />
              </label>
              <button className="auth-primary" type="submit" disabled={loading}>
                {loading ? "Verifying..." : "Verify Code"}
              </button>
              <button
                type="button"
                className="link-like"
                onClick={handleSendOTP}
                disabled={loading}
                style={{marginTop: '0.5rem', fontSize: '0.85rem'}}
              >
                Resend Code
              </button>
            </form>
          )}

          {step === STEPS.RESET && (
            <form className="auth-form" onSubmit={handleResetPassword}>
              <p style={{color: '#6b7280', marginBottom: '1rem', fontSize: '0.9rem'}}>
                Create a new password for your account.
              </p>
              <label>
                <span>New Password</span>
                <input
                  type="password"
                  placeholder="At least 6 characters"
                  value={newPassword}
                  onChange={(e) => { setNewPassword(e.target.value); setError(""); }}
                  required
                  minLength={6}
                />
              </label>
              <label>
                <span>Confirm Password</span>
                <input
                  type="password"
                  placeholder="Re-enter password"
                  value={confirmPassword}
                  onChange={(e) => { setConfirmPassword(e.target.value); setError(""); }}
                  required
                  minLength={6}
                />
              </label>
              <button className="auth-primary" type="submit" disabled={loading}>
                {loading ? "Resetting..." : "Reset Password"}
              </button>
            </form>
          )}

          {step === STEPS.DONE && (
            <div style={{textAlign: 'center', padding: '2rem 0'}}>
              <div style={{fontSize: '3rem', marginBottom: '1rem'}}>&#10003;</div>
              <h3 style={{marginBottom: '0.5rem'}}>Password Reset Complete</h3>
              <p style={{color: '#6b7280', marginBottom: '1.5rem'}}>
                Your password has been updated. You can now log in with your new password.
              </p>
              <button
                className="auth-primary"
                onClick={() => navigate(`/login/${role}`)}
                style={{maxWidth: '200px', margin: '0 auto'}}
              >
                Go to Login
              </button>
            </div>
          )}

          {step !== STEPS.DONE && (
            <p className="auth-foot">
              Remember your password?{" "}
              <Link to={`/login/${role}`}>Back to Login</Link>
            </p>
          )}
        </div>

        <aside className="auth-right">
          <div className="auth-right-inner">
            <h3>RESET</h3>
            <h3>PASSWORD</h3>
            <p>Secure your GigBridge account</p>
          </div>
        </aside>
      </div>
    </section>
  );
}
