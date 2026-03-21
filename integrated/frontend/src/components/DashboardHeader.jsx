import { useMemo, useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { useNavigate } from "react-router-dom";

export default function DashboardHeader({ onSearch }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const name = useMemo(() => user.name || user.email || "Artist", [user]);

  useEffect(() => {
    const close = () => setMenuOpen(false);
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, []);

  return (
    <header className="db-header">
      <div className="db-logo" onClick={() => navigate("/")}>
        <span className="db-logo-dot">G</span>
        <span className="db-logo-text">GigBridge</span>
      </div>
      <div className="db-search">
        <span className="db-search-ico">🔎</span>
        <input
          placeholder="Search gigs, events, clients..."
          onChange={(e) => onSearch?.(e.target.value)}
        />
      </div>
      <div className="db-actions">
        <div className="db-user" onClick={(e) => { e.stopPropagation(); setMenuOpen(!menuOpen); }}>
          <div className="db-avatar">{name.slice(0,1).toUpperCase()}</div>
          <span className="db-username">{name}</span>
          {menuOpen && (
            <div className="profile-menu">
              <button onClick={() => { logout(); navigate("/"); }}>Logout</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
