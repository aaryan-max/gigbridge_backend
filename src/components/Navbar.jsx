export default function Navbar({ onSignup }) {
  return (
    <nav className="navbar">
      <div className="logo">
        <span className="logo-circle">G</span> GigBridge
      </div>

      <ul className="nav-links">
        <li>Home</li>
        <li>Browse Artists</li>
        <li>How It Works</li>
        <li>Contact</li>
      </ul>

      <div className="nav-actions">
        <span className="login">Login</span>
        <button className="signup-btn" onClick={onSignup}>Sign Up</button>
      </div>
    </nav>
  );
}
