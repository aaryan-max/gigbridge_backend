 import { useNavigate } from "react-router-dom";

export default function Hero() {
  const navigate = useNavigate();
  const go = (role) => {
    const key = `gb_has_account_${role}`;
    const hasAccount = localStorage.getItem(key) === "1";
    if (hasAccount) {
      navigate(`/login/${role}`);
    } else {
      navigate(`/signup/${role}`);
    }
  };
  return (
    <section className="hero">
      <div className="hero-card">
        <span className="badge">#1 Platform for Creative Talent</span>
        <h1>
          Hire Talented Artists for Your<br />
          <span className="hero-title-dark">Creative Projects</span>
        </h1>
        <p>
          Connect with professional designers, illustrators, painters,
          and digital artists worldwide.
        </p>

        <div className="hero-buttons">
          <button className="primary" onClick={() => go("client")}>
            Hire a Freelancer
          </button>
          <button className="secondary" onClick={() => go("freelancer")}>
            Become an Artist
          </button>
        </div>
      </div>

      <div className="hero-illustration">
        <img
          src="/assets/hero-image.png"
          alt="Creative talent and artists"
          className="hero-image"
        />
      </div>
    </section>
  );
}
