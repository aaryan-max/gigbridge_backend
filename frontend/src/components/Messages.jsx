import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Messages() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);

  const load = () => {
    try {
      const raw = localStorage.getItem("gb_messages");
      const arr = raw ? JSON.parse(raw) : [];
      setItems(arr);
    } catch {
      setItems([]);
    }
  };

  useEffect(() => {
    load();
    const onStorage = () => load();
    const onCustom = () => load();
    window.addEventListener("storage", onStorage);
    window.addEventListener("gb:messages", onCustom);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("gb:messages", onCustom);
    };
  }, []);

  const unreadCount = useMemo(() => items.filter((m) => m.unread).length, [items]);

  const markAllRead = () => {
    const next = items.map((m) => ({ ...m, unread: false }));
    localStorage.setItem("gb_messages", JSON.stringify(next));
    setItems(next);
  };
  const clearAll = () => {
    localStorage.removeItem("gb_messages");
    setItems([]);
  };

  return (
    <main className="page-wrap">
      <button className="back-min" onClick={() => navigate(-1)} aria-label="Back">←</button>
      <h2 className="page-title">Messages</h2>
      <p className="page-sub">Keep in touch with artists and manage conversations.</p>

      <div className="page-card" style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
        <div style={{ color: "#0f172a", fontWeight: 700 }}>Unread: {unreadCount}</div>
        <button className="ba-view" onClick={markAllRead}>Mark all read</button>
        <button className="ba-view" onClick={clearAll}>Clear</button>
      </div>

      {items.length === 0 ? (
        <div className="page-placeholder">No messages yet</div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {items.map((m) => (
            <div key={m.id} className="page-card" style={{ display: "grid", gridTemplateColumns: "1fr auto", alignItems: "center" }}>
              <div>
                <div style={{ fontWeight: 800, color: "#0f172a" }}>{m.toName}</div>
                <div style={{ color: "#64748b" }}>{m.preview}</div>
                <div style={{ color: "#667085", fontSize: 12, marginTop: 4 }}>
                  {new Date(m.timestamp).toLocaleString()}
                </div>
              </div>
              <div>
                {m.unread && <span style={{ color: "#2563eb", fontWeight: 700 }}>• Unread</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
