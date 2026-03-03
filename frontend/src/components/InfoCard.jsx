export default function InfoCard({ title, items }) {
  return (
    <div className="info-card">
      <h4>{title}</h4>
      <ul>
        {items.map((t, i) => (
          <li key={i}>
            <span className="info-bullet">{i + 1}</span>
            <span className="info-text">{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
