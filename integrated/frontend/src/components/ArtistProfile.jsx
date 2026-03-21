import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

// Mock API Data containing extra details for the portfolio
const MOCK_PROFILES = {
  "sarah-martinez": {
    id: "sarah-martinez",
    name: "Sarah Martinez",
    category: "Dancer",
    rating: 4.9,
    reviews: 124,
    description: "I am a professional contemporary dancer with over 10 years of experience. I specialize in modern dance, ballet, and choreography for large events and performances. I've worked with top-tier event planners and directed live stage setups.",
    image: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=256&auto=format&fit=crop",
    experience: "10+ Years",
    portfolio: ["Contemporary Dance", "Live Performance", "Choreography", "Ballet"],
    priceRange: "₹10K – ₹50K",
    availability: "Immediate",
    location: "Mumbai, MH",
    gallery: [
      "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=400&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1547153760-18fc86324498?q=80&w=400&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1518834107812-67b0b7c58434?q=80&w=400&auto=format&fit=crop"
    ]
  },
  "david-rodriguez": {
    id: "david-rodriguez",
    name: "David Rodriguez",
    category: "Photographer",
    rating: 4.8,
    reviews: 89,
    description: "Expert photographer with a focus on events, portraits, and commercial photography. With 15 years capturing memorable moments, I bring stories to life through the lens.",
    image: "https://images.unsplash.com/photo-1544717305-996b815c338c?q=80&w=256&auto=format&fit=crop",
    experience: "15 Years",
    portfolio: ["Event Photography", "Portraits", "Commercial", "Drone"],
    priceRange: "₹50K – ₹2L",
    availability: "Flexible",
    location: "Delhi, DL",
    gallery: [
      "https://images.unsplash.com/photo-1520390116613-2d1ae5af46e2?q=80&w=400&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1511895426328-dc8714191300?q=80&w=400&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?q=80&w=400&auto=format&fit=crop"
    ]
  },
  "sophia-anderson": {
    id: "sophia-anderson",
    name: "Sophia Anderson",
    category: "Singer",
    rating: 5.0,
    reviews: 215,
    description: "Versatile vocalist experienced in jazz, pop, and R&B. Available for grand weddings, corporate events, and acoustic studio recordings.",
    image: "https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?q=80&w=256&auto=format&fit=crop",
    experience: "8 Years",
    portfolio: ["Jazz", "Pop", "R&B", "Live Event Vocals"],
    priceRange: "₹20K – ₹80K",
    availability: "Immediate",
    location: "Kolkata, WB",
    gallery: [
      "https://images.unsplash.com/photo-1511192336575-5a79af67a629?q=80&w=400&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=400&auto=format&fit=crop"
    ]
  },
  "alex-turner": {
    id: "alex-turner",
    name: "Alex Turner",
    category: "Artist",
    rating: 4.7,
    reviews: 62,
    description: "Contemporary painter creating custom pieces for homes, offices, and galleries. Specializing in abstract and modern immersive styles.",
    image: "https://images.unsplash.com/photo-1527980965255-d3b416303d12?q=80&w=256&auto=format&fit=crop",
    experience: "12 Years",
    portfolio: ["Abstract Art", "Custom Design", "Gallery Installation"],
    priceRange: "₹1L+",
    availability: "Flexible",
    location: "Bengaluru, KA",
    gallery: [
      "https://images.unsplash.com/photo-1513364776144-60967b0f800f?q=80&w=400&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1543857778-c4a1a3e0b2eb?q=80&w=400&auto=format&fit=crop"
    ]
  },
  "michael-chen": {
    id: "michael-chen",
    name: "Michael Chen",
    category: "Band / Live Music",
    rating: 4.9,
    reviews: 144,
    description: "Composer and multi-instrumentalist creating original live music bands for performances and large media gatherings.",
    image: "https://images.unsplash.com/photo-1544005316-44fdd1f7fa9c?q=80&w=256&auto=format&fit=crop",
    experience: "7 Years",
    portfolio: ["Composer", "Live Event", "Studio"],
    priceRange: "₹50K – ₹1.5L",
    availability: "This Week",
    location: "Mumbai, MH",
    gallery: [
      "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?q=80&w=400&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1470229722913-7c090be5f524?q=80&w=400&auto=format&fit=crop"
    ]
  }
};

export default function ArtistProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteText, setInviteText] = useState("");

  // FUTURE BACKEND FETCH LOGIC
  useEffect(() => {
    async function fetchArtistDetails() {
      setLoading(true);
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          const data = MOCK_PROFILES[id];
          if (data) resolve(data);
          else reject(new Error("Artist not found"));
        }, 800);
      });
    }

    fetchArtistDetails()
      .then(data => { setProfile(data); setLoading(false); })
      .catch(err => { console.error(err); setLoading(false); });
  }, [id]);

  const handleMessage = () => {
    setInviteOpen(true);
  };

  const handleBook = () => {
    alert(`Booking initiated for ${profile?.name}. (Backend Ready)`);
  };

  if (loading) {
    return (
      <main className="ap-wrap ap-loading">
        <div className="ap-skeleton-header"></div>
        <div className="ap-skeleton-body"></div>
      </main>
    );
  }

  if (!profile && !loading) {
    return (
      <main className="ap-wrap ap-not-found">
        <h2>Artist Not Found</h2>
        <button onClick={() => navigate('/browse-artists')} style={{ padding: '12px 24px', background: '#3b82f6', color: 'white', borderRadius: '8px', border: 'none', cursor: 'pointer', marginTop: '16px' }}>Back to Artists</button>
      </main>
    );
  }

  return (
    <main className="ap-wrap">
      <div className="ap-header">
        <button className="ap-back-btn" onClick={() => navigate(-1)}>← Back</button>
        <div className="ap-header-card">
          <div className="ap-avatar-box">
            <img src={profile.image} alt={profile.name} className="ap-avatar" />
            <span className="ap-status-badge">Available {profile.availability}</span>
          </div>
          <div className="ap-header-details">
            <h1>{profile.name}</h1>
            <h2 className="ap-category">{profile.category}</h2>
            <div className="ap-meta">
              <span>📍 {profile.location || "Remote"}</span>
              <span>⭐ {profile.rating} ({profile.reviews} reviews)</span>
              <span>🕒 {profile.experience}</span>
              <span>💰 {profile.priceRange}</span>
            </div>
          </div>
          <div className="ap-header-actions">
            <button className="ap-btn-primary" onClick={handleBook}>Book Now</button>
            <button className="ap-btn-secondary" onClick={handleMessage}>Message</button>
          </div>
        </div>
      </div>

      <div className="ap-body grid">
        <div className="ap-main-col">
          <section className="ap-section">
            <h3>About the Artist</h3>
            <p>{profile.description}</p>
          </section>

          <section className="ap-section">
            <h3>Portfolio Gallery</h3>
            {profile.gallery && profile.gallery.length > 0 ? (
              <div className="ap-gallery">
                {profile.gallery.map((img, i) => (
                  <img key={i} src={img} alt="Portfolio item" className="ap-gallery-img" />
                ))}
              </div>
            ) : (
              <p className="ap-text-muted">No gallery items uploaded yet.</p>
            )}
          </section>
        </div>

        <aside className="ap-side-col">
          <section className="ap-section">
            <h3>Specialties & Tags</h3>
            <div className="ap-tags">
              {profile.portfolio.map((tag, i) => (
                <span key={i} className="ap-tag">{tag}</span>
              ))}
            </div>
          </section>
          
          <section className="ap-section ap-guarantee">
            <h4>🛡️ GigBridge Protected</h4>
            <p>Payments are held securely until the project is successfully delivered.</p>
          </section>
        </aside>
      </div>

      {inviteOpen && (
        <div className="ba-modal">
          <div className="ba-modal-inner">
            <h3>Message {profile.name}</h3>
            <p>Send a quick message to discuss your upcoming project or event.</p>
            <textarea
              rows="4"
              value={inviteText}
              onChange={(e) => setInviteText(e.target.value)}
              placeholder="Hi! I’d love to know more about your work…"
              style={{ width: '100%', padding: '12px', boxSizing: 'border-box', border: '1px solid #dbeafe', borderRadius: '8px', margin: '12px 0', fontFamily: 'inherit', resize: 'vertical' }}
            />
            <div className="ba-modal-actions">
              <button
                className="ba-view"
                onClick={() => {
                  setInviteOpen(false);
                  setInviteText("");
                }}
              >
                Cancel
              </button>
              <button
                className="ba-invite"
                onClick={() => {
                  alert(`Message successfully sent to ${profile.name}!`);
                  setInviteOpen(false);
                  setInviteText("");
                }}
              >
                Send Message
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
