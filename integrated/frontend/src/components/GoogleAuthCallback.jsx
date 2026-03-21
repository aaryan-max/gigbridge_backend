import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function GoogleAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState("");

  useEffect(() => {
    const errorMsg = searchParams.get("error");
    if (errorMsg) {
      setError(errorMsg);
      return;
    }

    const success = searchParams.get("success");
    if (success !== "1") {
      setError("Google login failed. Please try again.");
      return;
    }

    const role = searchParams.get("role");
    const email = searchParams.get("email");
    const name = searchParams.get("name");
    const id = searchParams.get("id");
    const profileCompleted = searchParams.get("profile_completed") === "1";

    if (!role || !email || !id) {
      setError("Invalid login response. Please try again.");
      return;
    }

    const loginData = {
      email,
      role,
      name: name || "",
      profile_completed: profileCompleted,
    };

    if (role === "client") {
      loginData.client_id = parseInt(id, 10);
    } else {
      loginData.freelancer_id = parseInt(id, 10);
    }

    login(loginData);
    console.log("User role:", role);
    if (role === "freelancer") {
      if (profileCompleted) {
        navigate("/artist/dashboard", { replace: true });
      } else {
        navigate("/freelancer/create-profile/step-1", { replace: true });
      }
    } else {
      navigate("/", { replace: true });
    }
  }, [searchParams, login, navigate]);

  if (error) {
    return (
      <section style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
        <div style={{ textAlign: "center", maxWidth: 420, padding: "2rem" }}>
          <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>!</div>
          <h2 style={{ marginBottom: "0.5rem" }}>Login Failed</h2>
          <p style={{ color: "#666", marginBottom: "1.5rem" }}>{error}</p>
          <button
            onClick={() => navigate("/login/client")}
            style={{
              padding: "0.75rem 2rem",
              background: "#2563eb",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            Back to Login
          </button>
        </div>
      </section>
    );
  }

  return (
    <section style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
      <p>Signing you in...</p>
    </section>
  );
}
