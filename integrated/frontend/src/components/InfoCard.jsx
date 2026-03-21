export default function InfoCard({ title, items, actionLabel }) {
  return (
    <div className="pp-info-card">
      <h4>{title}</h4>
      <ul>
        {items.map((t, i) => (
          <li key={i}>
            <span className="pp-info-bullet">{t.icon || i + 1}</span>
            <span className="pp-info-text">{t.text || t}</span>
          </li>
        ))}
      </ul>
      {actionLabel && (
        <div className="pp-info-footer">
          {actionLabel}
        </div>
      )}
    </div>
  );
}
