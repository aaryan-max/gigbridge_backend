import { useNavigate } from "react-router-dom";
import Snowfall from "react-snowfall";

export default function ChoosePath() {
  const navigate = useNavigate();
  return (
    <main className="choose-wrap">
      <Snowfall color="#bcd7ff" snowflakeCount={80} radius={[1.2, 2.4]} speed={[0.4, 1.1]} style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0 }} />
      <section className="choose-inner">
        <div className="choose-header">
          <span className="choose-badge">✨ Choose Your Path</span>
          <h1 className="choose-title">What would you like to do?</h1>
          <p className="choose-sub">Choose an option to get started with GigBridge</p>
        </div>
        <div className="choose-grid">
          <button className="choose-card" onClick={() => navigate("/client/post-project")}>
            <div className="choose-ico" data-variant="doc">📄</div>
            <h3>Post a Project</h3>
            <p>Tell us what you need and receive proposals from talented artists</p>
          </button>
          <button className="choose-card" onClick={() => navigate("/browse-artists")}>
            <div className="choose-ico" data-variant="users">👥</div>
            <h3>Browse Artists</h3>
            <p>Explore artist profiles and portfolios to find the perfect match</p>
          </button>
          <button className="choose-card">
            <div className="choose-ico" data-variant="star">⭐</div>
            <h3>Explore Showcase</h3>
            <p>Get inspired by featured work from our top-rated artists</p>
          </button>
        </div>
        <div className="choose-footer">
          <button className="choose-link" onClick={() => navigate("/")}>Skip for now</button>
        </div>
      </section>
    </main>
  );
}
