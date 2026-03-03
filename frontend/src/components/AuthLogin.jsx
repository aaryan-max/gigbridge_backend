import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { authService } from "../services";

export default function AuthLogin() {
  const { role = "freelancer" } = useParams();
  const navigate = useNavigate();
  const { loginClient } = useAuth();
  const isFreelancer = role !== "client";
  const switchRole = (next) => navigate(`/login/${next}`);

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await authService.login(formData.email, formData.password, role);

      if (!isFreelancer) {
        loginClient({ email: formData.email, role: "client", ...response });
        const done = localStorage.getItem("client_profile_done") === "1";
        if (done) {
          navigate("/onboarding", { replace: true });
        } else {
          navigate("/client/profile-setup");
        }
      } else {
        const done = localStorage.getItem("freelancer_profile_done") === "1";
        if (done) {
          navigate("/dashboard/freelancer");
        } else {
          navigate("/freelancer/profile-setup");
        }
      }
    } catch (err) {
      setError(err.message || "Login failed");
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

          {error && <div style={{color: 'red', marginBottom: '1rem'}}>{error}</div>}

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
                placeholder="••••••••"
                value={formData.password}
                onChange={handleInputChange}
                required
              />
            </label>

            <button className="auth-primary" type="submit" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </button>

            <button type="button" className="auth-google">
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
