export default function ActivityFeed({ items = [] }) {
  return (
    <div className="db-section">
      <div className="db-section-title">Recent Activity</div>
      <div className="db-feed">
        {items.map((a) => (
          <div key={a.id} className="db-feed-item">
            <span className="db-feed-ico">{a.icon || "•"}</span>
            <div className="db-feed-text">
              <div className="db-feed-title">{a.text}</div>
              <div className="db-feed-time">{a.time}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
