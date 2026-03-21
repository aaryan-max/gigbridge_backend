import { useState } from "react";
import CategoryCard from "./CategoryCard.jsx";
import InfoCard from "./InfoCard.jsx";
import StatsCard from "./StatsCard.jsx";

const VALID_CATEGORIES = [
  { label: "Photographer", icon: "📷" },
  { label: "Videographer", icon: "🎥" },
  { label: "DJ", icon: "🎧" },
  { label: "Singer", icon: "🎤" },
  { label: "Dancer", icon: "💃" },
  { label: "Anchor", icon: "🎙️" },
  { label: "Makeup Artist", icon: "💄" },
  { label: "Mehendi Artist", icon: "🌿" },
  { label: "Decorator", icon: "🎀" },
  { label: "Wedding Planner", icon: "📋" },
  { label: "Choreographer", icon: "🩰" },
  { label: "Band / Live Music", icon: "🎸" },
  { label: "Magician / Entertainer", icon: "🎩" },
  { label: "Artist", icon: "🎨" },
  { label: "Event Organizer", icon: "🎪" },
];

export default function PostProject() {
  const [cat, setCat] = useState("");
  const [title, setTitle] = useState("");
  const [locationStr, setLocationStr] = useState("");
  const [budgetType, setBudgetType] = useState("");
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
        location: locationStr,
        budgetType,
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
      <div className="pp-grid">
        <form className="pp-form" onSubmit={submit}>
          <h2 className="pp-form-title">Post Your Creative Project</h2>

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
              {VALID_CATEGORIES.map((c) => (
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

          <label className="pp-label">
            <span>Location</span>
            <input
              type="text"
              placeholder="Enter city, state or remote"
              value={locationStr}
              onChange={(e) => setLocationStr(e.target.value)}
            />
          </label>

          <div className="pp-label">
            <span>Budget Type (Optional)</span>
            <div className="pp-budget-grid">
              {["Hourly Budget", "Fixed Rate", "Package"].map((b) => (
                <button
                  key={b}
                  type="button"
                  className={`budget-btn ${budgetType === b ? "active" : ""}`}
                  onClick={() => setBudgetType(budgetType === b ? "" : b)}
                >
                  {b}
                </button>
              ))}
            </div>
          </div>

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

          <button className="pp-primary" type="submit">Find Artists for My Project</button>
        </form>

        <aside className="pp-side">
          <InfoCard
            title="Why Choose GigBridge?"
            items={[
              { text: "Verified artists only", icon: "✔️" },
              { text: "Secure payments", icon: "🔒" },
              { text: "Fast responses", icon: "⚡" }
            ]}
            actionLabel="✨ 100% GigBridge Guarantee"
          />
          <InfoCard
            title="What Happens Next?"
            items={[
              { text: "Your project is reviewed", icon: "1️⃣" },
              { text: "Artists send proposals", icon: "2️⃣" },
              { text: "You compare portfolios", icon: "3️⃣" },
              { text: "Start collaborating", icon: "4️⃣" }
            ]}
            actionLabel="✨ Seamless Hiring Process"
          />
        </aside>
      </div>

      {toast && (
        <div className="pp-toast">Project submitted successfully</div>
      )}
    </section>
  );
}
