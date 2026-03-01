import { useNavigate, useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function AuthLogin() {
  const { role = "freelancer" } = useParams();
  const navigate = useNavigate();
  const { loginClient } = useAuth();
  const isFreelancer = role !== "client";
  const switchRole = (next) => navigate(`/login/${next}`);

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

          <form
            className="auth-form"
            onSubmit={(e) => {
              e.preventDefault();
              if (!isFreelancer) {
                loginClient();
                const done = localStorage.getItem("client_profile_done") === "1";
                if (done) return navigate("/onboarding", { replace: true });
                return navigate("/client/profile-setup");
              } else {
                const done = localStorage.getItem("freelancer_profile_done") === "1";
                if (done) return navigate("/dashboard/freelancer");
                return navigate("/freelancer/profile-setup");
              }
            }}
          >
            <label>
              <span>Username</span>
              <input type="text" placeholder="your username" required />
            </label>
            <label>
              <span>Password</span>
              <input type="password" placeholder="••••••••" required />
            </label>

            <button className="auth-primary" type="submit">Login</button>

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
