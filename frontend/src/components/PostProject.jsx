import { useState } from "react";
import CategoryCard from "./CategoryCard.jsx";
import InfoCard from "./InfoCard.jsx";
import StatsCard from "./StatsCard.jsx";

const categories = [
  { label: "Musician", icon: "🎵" },
  { label: "Dancer", icon: "🕺" },
  { label: "Painter/Illustrator", icon: "🎨" },
  { label: "Photographer", icon: "📷" },
  { label: "Videographer", icon: "🎬" },
  { label: "Designer", icon: "✏️" },
];

export default function PostProject() {
  const [cat, setCat] = useState("");
  const [title, setTitle] = useState("");
  const [budget, setBudget] = useState("");
  const [timeline, setTimeline] = useState("");
  const [location, setLocation] = useState("");
  const [desc, setDesc] = useState("");
  const [toast, setToast] = useState(false);

  const submit = (e) => {
    e.preventDefault();
    try {
      const raw = localStorage.getItem("gb_projects");
      const arr = raw ? JSON.parse(raw) : [];
      arr.unshift({
        id: Date.now(),
        title,
        category: cat,
        budget,
        timeline,
        location,
        description: desc,
        status: "active",
        createdAt: Date.now(),
      });
      localStorage.setItem("gb_projects", JSON.stringify(arr));
      window.dispatchEvent(new Event("gb:projects"));
    } catch {}
    setToast(true);
    setTimeout(() => setToast(false), 1500);
  };

  return (
    <section className="pp-wrap">
      <div className="pp-sky" aria-hidden="true">
        <span className="ppi p1">🎵</span>
        <span className="ppi p2">📷</span>
        <span className="ppi p3">🎨</span>
        <span className="ppi p4">✨</span>
        <span className="ppi p5">🖌️</span>
        <span className="ppi p6">🎬</span>
        <span className="ppi p7">🎭</span>
        <span className="ppi p8">✨</span>
      </div>
      <div className="pp-hero">
        <div className="pp-float pp-f1">🎨</div>
        <div className="pp-float pp-f2">🎵</div>
        <div className="pp-float pp-f3">📷</div>
        <div className="pp-float pp-f4">🖌️</div>
        <div className="pp-float pp-f5">✨</div>
        <h1 className="pp-title">Post Your Creative Project</h1>
        <p className="pp-sub">Tell us about your project and we'll connect you with talented artists</p>
      </div>
      <div className="pp-grid">
        <form className="pp-form" onSubmit={submit}>
          <label className="pp-label">
            <span>Project Title *</span>
            <input
              type="text"
              placeholder="e.g., Wedding Photography, Music Video Production"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </label>

          <div className="pp-label">
            <span>Category *</span>
            <div className="pp-cat-grid">
              {categories.map((c) => (
                <CategoryCard
                  key={c.label}
                  icon={c.icon}
                  label={c.label}
                  selected={cat === c.label}
                  onClick={() => setCat(c.label)}
                />
              ))}
            </div>
          </div>

          <div className="pp-row">
            <label className="pp-label">
              <span>Budget Range (INR) *</span>
              <select value={budget} onChange={(e) => setBudget(e.target.value)} required>
                <option value="">Select budget</option>
                <option>Under ₹10K</option>
                <option>₹10K–₹50K</option>
                <option>₹50K–₹2L</option>
                <option>₹2L+</option>
              </select>
            </label>
            <label className="pp-label">
              <span>Project Timeline *</span>
              <input
                type="text"
                placeholder="e.g., Within 2 weeks"
                value={timeline}
                onChange={(e) => setTimeline(e.target.value)}
                required
              />
            </label>
          </div>

          <label className="pp-label">
            <span>Location</span>
            <input
              type="text"
              placeholder="City, State or Remote"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </label>

          <label className="pp-label">
            <span>Project Description *</span>
            <textarea
              rows="5"
              placeholder="Describe your project in detail — style preferences, specific requirements, deliverables, etc."
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              required
            />
          </label>

          <button className="pp-primary pp-fixed" type="submit">Find Artists for My Project</button>
        </form>

        <aside className="pp-side">
          <InfoCard
            title="Why Choose GigBridge?"
            items={["Verified artists only", "Secure payments", "Fast responses"]}
          />
          <InfoCard
            title="What Happens Next?"
            items={["Your project is reviewed", "Artists send proposals", "You compare portfolios", "Start collaborating"]}
          />
        </aside>
      </div>

      {toast && (
        <div className="pp-toast">Project submitted successfully</div>
      )}
    </section>
  );
}
