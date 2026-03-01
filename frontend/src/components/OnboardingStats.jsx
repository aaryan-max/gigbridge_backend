export default function OnboardingStats({ artists = "10K+", projects = "50K+", rating = "4.9/5", className = "" }) {
  return (
    <div className={`ob-stats ${className}`}>
      <div className="ob-stat">
        <div className="ob-stat-value">{artists}</div>
        <div className="ob-stat-label">Active Artists</div>
      </div>
      <div className="ob-stat">
        <div className="ob-stat-value">{projects}</div>
        <div className="ob-stat-label">Projects Completed</div>
      </div>
      <div className="ob-stat">
        <div className="ob-stat-value">{rating}</div>
        <div className="ob-stat-label">Average Rating</div>
      </div>
    </div>
  );
}
