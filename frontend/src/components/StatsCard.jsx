export default function StatsCard({
  artists = "2,500+",
  projects = "1,200+",
  rating = "4.9/5",
  includeRating = true,
}) {
  const rowClass = includeRating ? "stats-row" : "stats-row two";
  return (
    <div className="stats-card">
      <div className={rowClass}>
        <div className="stats-item">
          <div className="stats-val">{artists}</div>
          <div className="stats-lbl">Active Artists</div>
        </div>
        <div className="stats-item">
          <div className="stats-val">{projects}</div>
          <div className="stats-lbl">Projects Completed</div>
        </div>
        {includeRating && (
          <div className="stats-item">
            <div className="stats-val">{rating}</div>
            <div className="stats-lbl">Average Rating</div>
          </div>
        )}
      </div>
    </div>
  );
}
