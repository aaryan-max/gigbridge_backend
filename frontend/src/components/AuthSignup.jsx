import { useNavigate, useParams, Link } from "react-router-dom";

export default function AuthSignup() {
  const { role = "freelancer" } = useParams();
  const navigate = useNavigate();
  const isFreelancer = role !== "client";
  const switchRole = (next) => navigate(`/signup/${next}`);

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

          <form
            className="auth-form"
            onSubmit={(e) => {
              e.preventDefault();
              localStorage.setItem(`gb_has_account_${role}`, "1");
              if (role === "client") {
                // Ensure first login after signup triggers profile creation
                localStorage.removeItem("client_profile_done");
              }
              navigate(`/login/${role}`);
            }}
          >
            <label>
              <span>Full Name</span>
              <input type="text" placeholder="John Doe" required />
            </label>
            <label>
              <span>Username</span>
              <input type="text" placeholder="your_username" required />
            </label>
            <label>
              <span>Email</span>
              <input type="email" placeholder="you@example.com" required />
            </label>
            <label>
              <span>Password</span>
              <input type="password" placeholder="••••••••" required />
            </label>
            <div className="otp-row">
              <label>
                <span>Enter OTP</span>
                <input type="text" placeholder="123456" />
              </label>
              <button type="button" className="link-like">Send OTP</button>
            </div>

            <button className="auth-primary" type="submit">Create Account</button>

            <button type="button" className="auth-google">
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
