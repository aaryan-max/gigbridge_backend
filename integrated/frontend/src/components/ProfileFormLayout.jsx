import { useMemo } from "react";

export default function ProfileFormLayout({ step = 1, children, tabs = ["Basic Info", "Contact & Bio"] }) {
  const pct = useMemo(() => (step === 1 ? 50 : 100), [step]);
  return (
    <section className="cp-wrap cp-stage">
      <div className="cp-card cp-appear">
        <header className="cp-header">
          <span className="cp-pill">👤 Freelancer Profile</span>
          <h3>Create Your Profile</h3>
          <p>{step === 1 ? "Step 1 of 2 — Basic Info" : "Step 2 of 2 — Contact & Bio"}</p>
        </header>

        <div className="cp-tabs">
          <span className={step === 1 ? "active" : ""}>{tabs[0]}</span>
          <span className={step === 2 ? "active" : ""}>{tabs[1]}</span>
        </div>

        <div className="cp-progress">
          <div className="cp-bar" style={{ width: `${pct}%` }} />
          <div className="cp-dot" style={{ left: `calc(${pct}% - 8px)` }} />
        </div>

        {children}
      </div>
    </section>
  );
}
