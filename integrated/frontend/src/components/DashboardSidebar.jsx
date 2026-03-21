import { useAuth } from "../context/AuthContext.jsx";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

const MENU = [
  { key: "dashboard", label: "Dashboard", ico: "▦", path: "/artist/dashboard" },
  { key: "profile", label: "Profile", ico: "👤", path: "/artist/profile" },
  { key: "portfolio", label: "Portfolio", ico: "💼", path: "/artist/portfolio" },
  { key: "hire-requests", label: "Hire Requests", ico: "📄", path: "/artist/opportunities" },
  { key: "projects", label: "Projects", ico: "📁", path: "/artist/projects" },
  { key: "messages", label: "Messages", ico: "💬", path: "/artist/messages" },
  { key: "notifications", label: "Notifications", ico: "🔔", path: "/artist/notifications" },
  { key: "verification", label: "Verification", ico: "🛡️", path: "/artist/verification" },
  { key: "subscription", label: "Subscription", ico: "💳", path: "/artist/subscription" },
  { key: "settings", label: "Settings", ico: "⚙️", path: "/artist/settings" },
];

export default function DashboardSidebar({ active = "dashboard", onSelect }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const name = user.name || user.email || "Artist";
  
  // Dynamic counts for messages and notifications
  const [messageCount, setMessageCount] = useState(3); // This will come from backend/messages
  const [notificationCount, setNotificationCount] = useState(5); // This will come from backend/notifications

  // Simulate dynamic updates (in real app, this would come from backend)
  useEffect(() => {
    // In real implementation:
    // 1. Fetch message count from messages API
    // 2. Fetch notification count from notifications API
    // 3. Update counts when new messages/notifications arrive
    // 4. Update counts when messages/notifications are read/dismissed
    
    // For demo: You can change these values to test different states
    setMessageCount(2); // Change to see different message count
    setNotificationCount(3); // Change to see different notification count
  }, []);

  const handleNav = (item) => {
    if (item.path) {
      navigate(item.path);
    }
    onSelect?.(item.key);
  };

  return (
    <aside className="db-sidebar">
      <nav className="db-nav">
        {MENU.map((m) => (
          <button
            key={m.key}
            className={`db-nav-item ${active === m.key ? "active" : ""}`}
            onClick={() => handleNav(m)}
          >
            <span className="db-nav-ico">{m.ico}</span>
            <span className="db-nav-label">{m.label}</span>
            {m.key === 'messages' && messageCount > 0 && <span className="db-nav-badge">{messageCount}</span>}
            {m.key === 'notifications' && notificationCount > 0 && <span className="db-nav-badge">{notificationCount}</span>}
          </button>
        ))}
      </nav>
      <div className="db-profile-preview">
        <div className="db-avatar">{name.slice(0,1).toUpperCase()}</div>
        <div className="db-preview-text">
          <div className="db-preview-name">{name}</div>
          <div className="db-preview-email">{user.email}</div>
        </div>
      </div>
    </aside>
  );
}
