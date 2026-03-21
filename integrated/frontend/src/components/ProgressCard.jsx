export default function ProgressCard({ title, desc, percent = 0 }) {
  const pct = Math.max(0, Math.min(100, Math.round(percent)));
  return (
    <div className="db-progress-card">
      <div className="db-progress-title">{title}</div>
      <div className="db-progress-sub">{desc}</div>
      <div className="db-progress-bar">
        <div className="db-progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="db-progress-val">{pct}%</div>
    </div>
  );
}
