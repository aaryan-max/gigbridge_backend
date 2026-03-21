import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const { user, logout } = useAuth();
  const name = user.name || user.email || "User";
  const isFreelancerOnboarding = location.pathname.startsWith("/freelancer/create-profile/");
  const isClient = user.role === "client";
  const isFreelancer = user.role === "freelancer";

  useEffect(() => {
    const close = () => { setMenuOpen(false); setNavOpen(false); };
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, []);
  const isArtistDashboard = location.pathname.startsWith("/artist/") || location.pathname === "/dashboard";

  if (isArtistDashboard) return null;

  return (
    <nav className={`navbar${isFreelancerOnboarding ? " minimal" : ""}`}>
      <div className="navbar-inner">
        <div className="logo" onClick={(e)=>{e.stopPropagation(); navigate("/");}}>
          <span className="logo-circle">G</span> GigBridge
        </div>

        {!isFreelancerOnboarding && (
          <button
            className="hamburger"
            aria-label="Toggle menu"
            onClick={(e) => { e.stopPropagation(); setNavOpen(!navOpen); }}
          >
            <span />
            <span />
            <span />
          </button>
        )}

        {!isFreelancerOnboarding && (
          <ul className="nav-links">
            <li className={location.pathname === "/" ? "active" : ""} onClick={() => navigate("/")}>Home</li>
            <li className={location.pathname === "/client/post-project" ? "active" : ""} onClick={() => navigate("/client/post-project")}>Post a Project</li>
            <li className={location.pathname === "/browse-artists" ? "active" : ""} onClick={() => navigate("/browse-artists")}>Browse Artists</li>
            <li className={location.pathname === "/messages" ? "active" : ""} onClick={() => navigate("/messages")}>Messages</li>
          </ul>
        )}

        <div className="nav-actions">

          {!isFreelancerOnboarding && !user.isAuthenticated ? (
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
      </div>

      {!isFreelancerOnboarding && navOpen && (
        <div className="mobile-menu" onClick={(e)=>e.stopPropagation()}>
          <button className={`mobile-item ${location.pathname === '/' ? 'active' : ''}`} onClick={() => { navigate("/"); setNavOpen(false); }}>Home</button>
          <button className={`mobile-item ${location.pathname === '/client/post-project' ? 'active' : ''}`} onClick={() => { navigate("/client/post-project"); setNavOpen(false); }}>Post a Project</button>
          <button className={`mobile-item ${location.pathname === '/browse-artists' ? 'active' : ''}`} onClick={() => { navigate("/browse-artists"); setNavOpen(false); }}>Browse Artists</button>
          <button className={`mobile-item ${location.pathname === '/messages' ? 'active' : ''}`} onClick={() => { navigate("/messages"); setNavOpen(false); }}>Messages</button>
          {!user.isAuthenticated && (
            <button className="mobile-item" onClick={() => { navigate("/login/client"); setNavOpen(false); }}>Login</button>
          )}
        </div>
      )}
    </nav>
  );
}
