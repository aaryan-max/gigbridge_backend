import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { authService } from "../services";

export default function AuthLogin() {
  const { role = "freelancer" } = useParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const isFreelancer = role !== "client";
  const switchRole = (next) => navigate(`/login/${next}`);

  const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

  const [formData, setFormData] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleGoogleLogin = () => {
    window.location.href = `${apiBase}/auth/google?role=${role}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await authService.login(formData.email, formData.password, role);
      console.log("User role:", response.role);
      // Persist role/id using AuthContext
      login({ email: formData.email, role: response.role || role, ...response });

      const r = response.role || role;
      if (r === "freelancer") {
        if (response.profile_completed) {
          navigate("/artist/dashboard", { replace: true });
        } else {
          navigate("/freelancer/create-profile/step-1", { replace: true });
        }
      } else {
        // Clients land on Home
        navigate("/", { replace: true });
      }
    } catch (err) {
      setError(err.message || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-left">
          <h2>Login</h2>

          <div className="segmented">
            <button
              className={isFreelancer ? "seg active" : "seg"}
              onClick={() => switchRole("freelancer")}
            >
              Login as Freelancer
            </button>
            <button
              className={!isFreelancer ? "seg active" : "seg"}
              onClick={() => switchRole("client")}
            >
              Login as Client
            </button>
          </div>

          {error && <div style={{color: '#dc2626', marginBottom: '1rem', fontSize: '0.9rem'}}>{error}</div>}

          <form className="auth-form" onSubmit={handleSubmit}>
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
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleInputChange}
                required
              />
            </label>

            <div style={{textAlign: 'right', marginTop: '-0.5rem', marginBottom: '0.5rem'}}>
              <Link
                to={`/forgot-password/${role}`}
                style={{fontSize: '0.85rem', color: '#2563eb', textDecoration: 'none'}}
              >
                Forgot Password?
              </Link>
            </div>

            <button className="auth-primary" type="submit" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </button>

            <button type="button" className="auth-google" onClick={handleGoogleLogin}>
              <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="" />
              Continue with Google
            </button>
          </form>

          <p className="auth-foot">
            Don't have an account?{" "}
            <Link to={`/signup/${isFreelancer ? "freelancer" : "client"}`}>Sign Up</Link>
          </p>
        </div>

        <aside className="auth-right">
          <div className="auth-right-inner">
            <h3>WELCOME</h3>
            <h3>BACK!</h3>
            <p>Login to continue to GigBridge</p>
          </div>
        </aside>
      </div>
    </section>
  );
}
