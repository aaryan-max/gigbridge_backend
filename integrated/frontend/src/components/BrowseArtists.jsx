import { useMemo, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const VALID_CATEGORIES = [
  "Photographer",
  "Videographer",
  "DJ",
  "Singer",
  "Dancer",
  "Anchor",
  "Makeup Artist",
  "Mehendi Artist",
  "Decorator",
  "Wedding Planner",
  "Choreographer",
  "Band / Live Music",
  "Magician / Entertainer",
  "Artist",
  "Event Organizer"
];

// Mock API response mirroring backend-ready structure requested
const MOCK_API_RESPONSE = [
  {
    id: "sarah-martinez",
    name: "Sarah Martinez",
    category: "Dancer",
    rating: 4.9,
    description: "Professional contemporary dancer with 10+ years of experience. Specialized in modern dance, ballet, and choreography for events and performances.",
    image: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=256&auto=format&fit=crop",
    experience: "10+ Years",
    portfolio: ["Contemporary Dance", "Live Performance", "Choreography"],
    priceRange: "₹10K – ₹50K",
    availability: "Immediate",
    online: true,
  },
  {
    id: "david-rodriguez",
    name: "David Rodriguez",
    category: "Photographer",
    rating: 4.8,
    description: "Expert photographer with a focus on events, portraits, and commercial photography. 15 years of experience capturing memorable moments.",
    image: "https://images.unsplash.com/photo-1544717305-996b815c338c?q=80&w=256&auto=format&fit=crop",
    experience: "15 Years",
    portfolio: ["Event Photography", "Portraits", "Commercial"],
    priceRange: "₹50K – ₹2L",
    availability: "Flexible",
    online: true,
  }
];

export default function BrowseArtists() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("relevant");
  
  // Modal states
  const [inviteId, setInviteId] = useState(null);
  const [inviteText, setInviteText] = useState("");
  const [resetPulse, setResetPulse] = useState(false);

  // Filter states
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [budget, setBudget] = useState("");
  const [avail, setAvail] = useState("");
  
  // Artist state
  const [artists, setArtists] = useState([]);
  const [loading, setLoading] = useState(true);

  // Backend ready fetch logic
  useEffect(() => {
    async function fetchArtists() {
      setLoading(true);
      // For now: return mock data
      // Later: replace with API call
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(MOCK_API_RESPONSE);
        }, 1500);
      });
    }

    fetchArtists().then(data => {
      setArtists(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  const toggle = (arr, setter, v) =>
    setter((prev) => (prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v]));

  // Separated filtering logic
  const filteredArtists = useMemo(() => {
    const base = artists.filter(
      (a) =>
        a.name.toLowerCase().includes(q.toLowerCase()) ||
        (a.category || "").toLowerCase().includes(q.toLowerCase()) ||
        (a.portfolio || []).join(" ").toLowerCase().includes(q.toLowerCase())
    );
    const byCat = selectedCategories.length ? base.filter((a) => selectedCategories.includes(a.category)) : base;
    const byBudget = budget ? byCat.filter((a) => a.priceRange === budget) : byCat;
    const byAvail = avail ? byBudget.filter((a) => a.availability === avail) : byBudget;
    
    if (sort === "rating") return [...byAvail].sort((a, b) => b.rating - a.rating);
    return byAvail;
  }, [artists, q, sort, selectedCategories, budget, avail]);

  return (
    <main className="ba-wrap">
      <header className="ba-header">
        <h1>Browse Artists</h1>
        <div className="ba-searchbar">
          <div className="ba-search">
            <span className="ba-search-ico">🔎</span>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search for dancers, singers, photographers, and more…"
            />
          </div>
          <select value={sort} onChange={(e) => setSort(e.target.value)} className="ba-sort">
            <option value="relevant">Most Relevant</option>
            <option value="rating">Highest Rated</option>
          </select>
        </div>
      </header>

      <section className="ba-grid">
        <aside className="ba-filters">
          <div className="ba-f-title">Filters</div>

          <div className="ba-filter-sec">
            <div className="ba-sec-title">Artist Categories</div>
            <div className="ba-pills">
              {VALID_CATEGORIES.map((x) => (
                <button
                  key={x}
                  className={`chip ${selectedCategories.includes(x) ? "chip-active" : ""}`}
                  onClick={() => toggle(selectedCategories, setSelectedCategories, x)}
                >
                  {x}
                </button>
              ))}
            </div>
          </div>

          <div className="ba-filter-sec">
            <div className="ba-sec-title">Budget Range (INR)</div>
            <div className="ba-pills column">
              {["Under ₹10K", "₹10K – ₹50K", "₹50K – ₹2L", "₹2L+"].map((x) => (
                <button
                  key={x}
                  className={`ba-opt ${budget === x ? "opt-active" : ""}`}
                  onClick={() => setBudget(budget === x ? "" : x)}
                >
                  {x}
                </button>
              ))}
            </div>
          </div>

          {/* LOCATION FILTER COMPLETELY REMOVED */}

          <div className="ba-filter-sec">
            <div className="ba-sec-title">Availability</div>
            <div className="ba-pills">
              {["Immediate", "This Week", "Flexible"].map((x) => (
                <button
                  key={x}
                  className={`seg ${avail === x ? "seg-active" : ""}`}
                  onClick={() => setAvail(avail === x ? "" : x)}
                >
                  {x}
                </button>
              ))}
            </div>
          </div>

          <button
            className="ba-clear"
            onClick={() => {
              setSelectedCategories([]); setBudget(""); setAvail("");
              setResetPulse(true); setTimeout(() => setResetPulse(false), 240);
            }}
          >
            Reset Filters
          </button>
        </aside>

        <div className={`ba-results ${resetPulse ? "ba-pulse" : ""}`}>
          <div className="ba-meta">Showing {filteredArtists.length} talented artists</div>
          
          {loading ? (
             // SKELETON LOADER
             <>
               {[1, 2, 3].map(n => (
                 <article className="ba-card skeleton-card-legacy" key={n}>
                   <div className="ba-card-left">
                     <div className="skeleton-avatar-lg" style={{ width: '80px', height: '80px', borderRadius: '50%', background: '#e2e8f0', animation: 'shimmer 1.5s infinite linear' }}></div>
                   </div>
                   <div className="ba-card-mid" style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
                     <div className="skeleton-line title" style={{ width: '50%', height: '24px', background: '#e2e8f0', borderRadius: '4px', animation: 'shimmer 1.5s infinite linear' }}></div>
                     <div className="skeleton-line sub" style={{ width: '30%', height: '16px', background: '#e2e8f0', borderRadius: '4px', animation: 'shimmer 1.5s infinite linear' }}></div>
                     <div className="skeleton-line text" style={{ width: '90%', height: '12px', background: '#e2e8f0', borderRadius: '4px', marginTop: '10px', animation: 'shimmer 1.5s infinite linear' }}></div>
                     <div className="skeleton-line text" style={{ width: '60%', height: '12px', background: '#e2e8f0', borderRadius: '4px', animation: 'shimmer 1.5s infinite linear' }}></div>
                   </div>
                 </article>
               ))}
             </>
          ) : filteredArtists.length === 0 ? (
            <div className="ba-empty">
              <div className="ba-empty-illus">🎭</div>
              <div className="ba-empty-title">No artists found</div>
              <div className="ba-empty-sub">Try adjusting your filters.</div>
            </div>
          ) : (
            filteredArtists.map((a) => (
              <article className="ba-card" key={a.id}>
                <div className="ba-card-left">
                  <div className="ba-avatar-wrap">
                    <img src={a.image} alt={a.name} className="ba-avatar" />
                    {a.online && <span className="ba-online" />}
                  </div>
                </div>
                <div className="ba-card-mid">
                  <div className="ba-name">{a.name}</div>
                  <div className="ba-role" onClick={() => navigate(`/artist/${a.id}`)}>{a.category}</div>
                  <p className="ba-bio">{a.description}</p>
                  <div className="ba-tags">
                    {(a.portfolio || []).map((t) => <span key={t} className="ba-tag">{t}</span>)}
                  </div>
                  <div className="ba-actions">
                    <button className="ba-invite" onClick={() => navigate(`/artist/${a.id}`)}>Know More About</button>
                    <button className="ba-view" onClick={() => setInviteId(a.id)}>Message</button>
                  </div>
                </div>
                <div className="ba-card-right">
                  <div className="ba-rating">⭐ {a.rating}</div>
                </div>
              </article>
            ))
          )}
          
          {!loading && filteredArtists.length > 0 && (
            <div className="ba-load-more">
              <button className="ba-view">Load More Artists</button>
            </div>
          )}
        </div>
      </section>

      {inviteId && (
        <div className="ba-modal">
          <div className="ba-modal-inner">
            <h3>Message Artist</h3>
            <p>Send a quick message to discuss your project.</p>
            <textarea
              rows="4"
              value={inviteText}
              onChange={(e) => setInviteText(e.target.value)}
              placeholder="Hi! I’d love to know more about your work…"
            />
            <div className="ba-modal-actions">
              <button
                className="ba-view"
                onClick={() => {
                  setInviteId(null);
                  setInviteText("");
                }}
              >
                Cancel
              </button>
              <button
                className="ba-invite"
                onClick={() => {
                  // Message flow implementation
                  alert(`Message sent to backend API for artist ID: ${inviteId}`);
                  setInviteId(null);
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
