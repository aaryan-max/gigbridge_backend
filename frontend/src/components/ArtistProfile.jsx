import { useNavigate, useParams } from "react-router-dom";

export default function ArtistProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  return (
    <main className="page-wrap">
      <button className="back-min" onClick={() => navigate(-1)} aria-label="Back">←</button>
      <h2 className="page-title">Artist Profile</h2>
      <p className="page-sub">Profile for: {id}</p>
      <div className="page-card">
        This is a placeholder profile page for routing verification.
      </div>
    </main>
  );
}
