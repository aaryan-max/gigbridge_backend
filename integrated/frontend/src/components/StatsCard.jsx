export default function StatsCard({ color = "#2563eb", icon = "📈", title, value, subtext }) {
  return (
    <div className="db-card">
      <div className="db-card-head">
        <div className="db-card-ico" style={{ background: color }}>{icon}</div>
        <div className="db-card-title">{title}</div>
      </div>
      <div className="db-card-value">{value}</div>
      {subtext && <div className="db-card-sub">{subtext}</div>}
    </div>
  );
}
