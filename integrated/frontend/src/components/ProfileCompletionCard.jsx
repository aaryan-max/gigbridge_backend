import React from "react";

export default function ProfileCompletionCard({ completion }) {
  const items = [
    { key: "basicInfo", label: "Basic Info", done: completion.basicInfo },
    { key: "skills", label: "Skills / Category", done: completion.skills },
    { key: "verification", label: "Verification Pending", done: completion.verification },
    { key: "portfolio", label: "Add Portfolio", done: completion.portfolio }
  ];

  const doneCount = items.filter(i => i.done).length;
  const pct = Math.round((doneCount / items.length) * 100);

  return (
    <div className="profile-completion-card">
      <div className="completion-header">
        <div>
          <h3>Profile Completion</h3>
          <p>Complete your profile to attract more clients</p>
        </div>
        <div className="completion-pct">{pct}%</div>
      </div>
      <div className="completion-bar-outer">
        <div className="completion-bar-inner" style={{ width: `${pct}%` }} />
      </div>
      <div className="completion-checklist">
        {items.map(item => (
          <div key={item.key} className={`check-item ${item.done ? 'done' : ''}`}>
            <span className="check-icon">{item.done ? "✅" : "⏳"}</span>
            {item.label}
          </div>
        ))}
      </div>
    </div>
  );
}
