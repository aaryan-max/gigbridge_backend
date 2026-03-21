import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { authService } from "../services";

export default function AuthSignup() {
  const { role = "freelancer" } = useParams();
  const navigate = useNavigate();
  const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
  const isFreelancer = role !== "client";
  const switchRole = (next) => navigate(`/signup/${next}`);

  const [formData, setFormData] = useState({
    name: "",
    username: "",
    email: "",
    password: "",
    otp: "",
  });
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGoogleSignup = () => {
    window.location.href = `${apiBase}/auth/google?role=${role}`;
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSendOTP = async () => {
    if (!formData.email) {
      setError("Please enter your email first");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await authService.sendOTP(formData.email, role);
      setOtpSent(true);
      if (res.debug_otp) {
        alert(`OTP (dev mode): ${res.debug_otp}`);
      } else {
        alert("OTP sent to your email!");
      }
    } catch (err) {
      setError(err.message || "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!otpSent || !formData.otp) {
      setError("Please verify OTP first");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await authService.verifyOTPAndSignup({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        otp: formData.otp,
      }, role);
      localStorage.setItem(`gb_has_account_${role}`, "1");
      if (role === "client") {
        localStorage.removeItem("client_profile_done");
      }
      navigate(`/login/${role}`);
    } catch (err) {
      setError(err.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-left">
          <h2>Sign Up</h2>

          <div className="segmented">
            <button
              className={isFreelancer ? "seg active" : "seg"}
              onClick={() => switchRole("freelancer")}
            >
              I am a Freelancer
            </button>
            <button
              className={!isFreelancer ? "seg active" : "seg"}
              onClick={() => switchRole("client")}
            >
              I am a Client
            </button>
          </div>

          {error && <div style={{color: 'red', marginBottom: '1rem'}}>{error}</div>}

          <form className="auth-form" onSubmit={handleSubmit}>
            <label>
              <span>Full Name</span>
              <input
                type="text"
                name="name"
                placeholder="John Doe"
                value={formData.name}
                onChange={handleInputChange}
                required
              />
            </label>
            <label>
              <span>Username</span>
              <input
                type="text"
                name="username"
                placeholder="your_username"
                value={formData.username}
                onChange={handleInputChange}
                required
              />
            </label>
            <label>
              <span>Email</span>
              <input
                type="email"
                name="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={handleInputChange}
                required
              />
            </label>
            <label>
              <span>Password</span>
              <input
                type="password"
                name="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleInputChange}
                required
              />
            </label>
            <div className="otp-row">
              <label>
                <span>Enter OTP</span>
                <input
                  type="text"
                  name="otp"
                  placeholder="123456"
                  value={formData.otp}
                  onChange={handleInputChange}
                  required
                />
              </label>
              <button
                type="button"
                className="link-like"
                onClick={handleSendOTP}
                disabled={loading || !formData.email}
              >
                {otpSent ? "Resend OTP" : "Send OTP"}
              </button>
            </div>

            <button className="auth-primary" type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Account"}
            </button>

            <button type="button" className="auth-google" onClick={handleGoogleSignup}>
              <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="" />
              Continue with Google
            </button>
          </form>

          <p className="auth-foot">
            Already have an account?{" "}
            <Link to={`/login/${isFreelancer ? "freelancer" : "client"}`}>Sign In</Link>
          </p>
        </div>

        <aside className="auth-right">
          <div className="auth-right-inner">
            <h3>JOIN</h3>
            <h3>GIGBRIDGE</h3>
            <p>Start your {isFreelancer ? "freelancing" : "hiring"} journey today</p>
          </div>
        </aside>
      </div>
    </section>
  );
}
