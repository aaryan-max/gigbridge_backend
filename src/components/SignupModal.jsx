export default function SignupModal({ onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="close" onClick={onClose}>✕</button>

        <h2>Welcome to GigBridge</h2>
        <p className="modal-subtitle">Choose how you'd like to continue</p>

        <div className="option">
          <h3>I'm a Freelancer</h3>
          <span>Create your freelancer account</span>
        </div>

        <div className="option">
          <h3>I'm a Client</h3>
          <span>Create your client account</span>
        </div>
      </div>
    </div>
  );
}
