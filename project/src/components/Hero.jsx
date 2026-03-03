export default function Hero({ onSignup }) {
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
          <button className="primary">Hire a Freelancer</button>
          <button className="secondary" onClick={onSignup}>
            Become an Artist
          </button>
        </div>
      </div>

      <div className="hero-illustration">
        <div className="illustration-circle">
          <img
            src="https://images.pexels.com/photos/7688336/pexels-photo-7688336.jpeg?auto=compress&cs=tinysrgb&w=600"
            alt="Creative artists - DJ, pianist, dancer, and painter"
            className="artists-illustration"
          />
        </div>
      </div>
    </section>
  );
}
