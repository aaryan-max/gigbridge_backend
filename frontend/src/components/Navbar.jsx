import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const name = typeof window !== "undefined" ? localStorage.getItem("client_profile_username") || "Client" : "Client";
  useEffect(() => {
    const close = () => setMenuOpen(false);
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, []);
  return (
    <nav className="navbar">
      <div className="logo" onClick={(e)=>{e.stopPropagation(); navigate("/");}}>
        <span className="logo-circle">G</span> GigBridge
      </div>

      <ul className="nav-links">
        <li onClick={() => (user.isAuthenticated ? navigate("/onboarding") : navigate("/"))}>
          Home
        </li>
        <li onClick={() => navigate("/browse-artists")}>
          Browse
        </li>
        <li onClick={() => (user.isAuthenticated ? navigate("/client/post-project") : undefined)}>
          Projects
        </li>
        <li onClick={() => (user.isAuthenticated ? navigate("/messages") : undefined)}>
          Messages
        </li>
        <li onClick={() => (user.isAuthenticated ? navigate("/profile") : undefined)}>
          Profile
        </li>
      </ul>

      <div className="nav-actions">
        {user.isAuthenticated && (
          <button
            className="post-btn"
            onClick={() => navigate("/client/post-project")}
          >
            Post a Project
          </button>
        )}
        {!user.isAuthenticated ? (
          <>
            <span
              className="login"
              onClick={() => navigate("/login/client")}
            >
              Login
            </span>
            <button
              className="signup-btn"
              onClick={() => navigate("/signup/client")}
            >
              Sign Up
            </button>
          </>
        ) : (
          <div className="profile-wrap" onClick={(e) => { e.stopPropagation(); setMenuOpen(!menuOpen); }}>
            <div className="avatar">{name.slice(0,1).toUpperCase()}</div>
            <span className="profile-name">{name}</span>
            {menuOpen && (
              <div className="profile-menu">
                <button onClick={() => { logout(); navigate("/"); }}>Logout</button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
