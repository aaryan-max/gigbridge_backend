import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import ImageGrid from "./OnboardingImageGrid.jsx";
import Stats from "./OnboardingStats.jsx";

export default function Onboarding() {
  const navigate = useNavigate();
  useEffect(() => {
    const entries = document.querySelectorAll(".reveal");
    const io = new IntersectionObserver(
      (obs) => {
        obs.forEach((e) => {
          if (e.isIntersecting) e.target.classList.add("is-visible");
        });
      },
      { threshold: 0.12 }
    );
    entries.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <main className="ob-wrap">
      <section className="ob-hero reveal">
        <div className="ob-left">
          <ImageGrid />
        </div>
        <div className="ob-right">
          <h1 className="ob-title">Find the perfect artist for your next project</h1>
          <p className="ob-sub">
            Connect with talented dancers, singers, illustrators, musicians, and photographers.
            Bring your creative vision to life with verified professionals.
          </p>
          <div className="ob-cta">
            <button className="ob-primary" onClick={() => navigate("/choose-path")}>Get Started →</button>
          </div>
          <Stats artists="10K+" projects="50K+" rating="4.9/5" className="ob-inline-stats" />
        </div>
      </section>
    </main>
  );
}
