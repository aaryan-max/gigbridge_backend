import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

const MOCK = [
  {
    id: "sarah-martinez",
    name: "Sarah Martinez",
    role: "Contemporary Dancer",
    category: "Dancer",
    priceRange: "₹10K – ₹50K",
    availability: "Immediate",
    location: "Mumbai, MH",
    bio: "Professional contemporary dancer with 10+ years of experience. Specialized in modern dance, ballet, and choreography for events and performances.",
    tags: ["Contemporary Dance", "Live Performance", "Choreography"],
    rating: 4.9,
    avatar: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=256&auto=format&fit=crop",
    online: true,
  },
  {
    id: "david-rodriguez",
    name: "David Rodriguez",
    role: "Professional Photographer",
    category: "Photographer",
    priceRange: "₹50K – ₹2L",
    availability: "Flexible",
    location: "Chennai, TN",
    bio: "Expert photographer with a focus on events, portraits, and commercial photography. 15 years of experience capturing memorable moments.",
    tags: ["Event Photography", "Portraits", "Commercial"],
    rating: 4.9,
    avatar: "https://images.unsplash.com/photo-1544717305-996b815c338c?q=80&w=256&auto=format&fit=crop",
    online: true,
  },
  {
    id: "sophia-anderson",
    name: "Sophia Anderson",
    role: "Jazz & Pop Singer",
    category: "Singer",
    priceRange: "₹10K – ₹50K",
    availability: "This Week",
    location: "Delhi, DL",
    bio: "Versatile vocalist with experience in jazz, pop, and R&B. Available for weddings, corporate events, and studio recordings.",
    tags: ["Jazz", "Pop", "Events"],
    rating: 5.0,
    avatar: "https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?q=80&w=256&auto=format&fit=crop",
    online: false,
  },
  {
    id: "alex-turner",
    name: "Alex Turner",
    role: "Fine Art Painter",
    category: "Painter",
    priceRange: "₹2L+",
    availability: "Flexible",
    location: "Bengaluru, KA",
    bio: "Contemporary painter creating custom pieces for homes, offices, and galleries. Specializing in abstract and modern art styles.",
    tags: ["Abstract Art", "Custom Commissions", "Modern"],
    rating: 4.7,
    avatar: "https://images.unsplash.com/photo-1527980965255-d3b416303d12?q=80&w=256&auto=format&fit=crop",
    online: true,
  },
  {
    id: "michael-chen",
    name: "Michael Chen",
    role: "Musician & Composer",
    category: "Musician",
    priceRange: "Under ₹10K",
    availability: "Immediate",
    location: "Kolkata, WB",
    bio: "Composer and multi-instrumentalist creating original scores and live music for performances and media.",
    tags: ["Composer", "Live Music", "Studio"],
    rating: 4.8,
    avatar: "https://images.unsplash.com/photo-1544005316-44fdd1f7fa9c?q=80&w=256&auto=format&fit=crop",
    online: true,
  },
  {
    id: "isabella-russo",
    name: "Isabella Russo",
    role: "Illustrator & Designer",
    category: "Illustrator",
    priceRange: "₹10K – ₹50K",
    availability: "This Week",
    location: "Hyderabad, TS",
    bio: "Digital illustrator specializing in character art, brand illustrations, and editorial visuals. Portfolio includes work for major publications.",
    tags: ["Digital Art", "Character Design", "Brand Illustration"],
    rating: 4.9,
    avatar: "https://images.unsplash.com/photo-1548142813-c348350df52b?q=80&w=256&auto=format&fit=crop",
    online: false,
  },
];

export default function BrowseArtists() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("relevant");
  const [inviteId, setInviteId] = useState(null);
  const [inviteText, setInviteText] = useState("");
  const [resetPulse, setResetPulse] = useState(false);
  // Filters state
  const [selCats, setSelCats] = useState([]);
  const [budget, setBudget] = useState("");
  const [selLocs, setSelLocs] = useState([]);
  const [avail, setAvail] = useState("");

  const toggle = (arr, setter, v) =>
    setter((prev) => (prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v]));

  const filtered = useMemo(() => {
    const base = MOCK.filter(
      (a) =>
        a.name.toLowerCase().includes(q.toLowerCase()) ||
        (a.category || "").toLowerCase().includes(q.toLowerCase()) ||
        a.tags.join(" ").toLowerCase().includes(q.toLowerCase())
    );
    const byCat = selCats.length ? base.filter((a) => selCats.includes(a.category)) : base;
    const byBudget = budget ? byCat.filter((a) => a.priceRange === budget) : byCat;
    const byLoc = selLocs.length ? byBudget.filter((a) => selLocs.includes(a.location)) : byBudget;
    const byAvail = avail ? byLoc.filter((a) => a.availability === avail) : byLoc;
    if (sort === "rating") return [...byAvail].sort((a, b) => b.rating - a.rating);
    return byAvail;
  }, [q, sort, selCats, budget, selLocs, avail]);

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
              {["Dancer", "Singer", "Illustrator", "Musician", "Photographer", "Painter", "Sculptor", "Actor"].map(
                (x) => (
                  <button
                    key={x}
                    className={`chip ${selCats.includes(x) ? "chip-active" : ""}`}
                    onClick={() => toggle(selCats, setSelCats, x)}
                  >
                    {x}
                  </button>
                )
              )}
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

          <div className="ba-filter-sec">
            <div className="ba-sec-title">Location</div>
            <ul className="ba-list">
              {["Mumbai, MH", "Delhi, DL", "Bengaluru, KA", "Chennai, TN", "Kolkata, WB", "Hyderabad, TS", "Remote/Online"].map((x) => (
                <li key={x}>
                  <button
                    className={`chip loc ${selLocs.includes(x) ? "chip-active" : ""}`}
                    onClick={() => toggle(selLocs, setSelLocs, x)}
                  >
                    📍 {x}
                  </button>
                </li>
              ))}
            </ul>
          </div>

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
              setSelCats([]); setBudget(""); setSelLocs([]); setAvail("");
              setResetPulse(true); setTimeout(() => setResetPulse(false), 240);
            }}
          >
            Reset Filters
          </button>
        </aside>

        <div className={`ba-results ${resetPulse ? "ba-pulse" : ""}`}>
          <div className="ba-meta">Showing {filtered.length} talented artists</div>
          {filtered.length === 0 && (
            <div className="ba-empty">
              <div className="ba-empty-illus">🎭</div>
              <div className="ba-empty-title">No artists found</div>
              <div className="ba-empty-sub">No artists found. Try adjusting filters.</div>
            </div>
          )}
          {filtered.map((a) => (
            <article className="ba-card" key={a.id}>
              <div className="ba-card-left">
                <div className="ba-avatar-wrap">
                  <img
                    src={`/assets/artists/${a.id}.jpg`}
                    data-next={`/assets/artists/${(a.category || a.role || "artist").toLowerCase().replace(/\\s+/g,"-")}.jpg`}
                    onError={(ev) => {
                      const img = ev.currentTarget;
                      const nextStr = img.dataset.next || "";
                      if (nextStr) {
                        img.removeAttribute("data-next");
                        img.src = nextStr;
                      } else {
                        img.src = a.avatar;
                      }
                    }}
                    alt={a.name}
                    className="ba-avatar"
                  />
                  {a.online && <span className="ba-online" />}
                </div>
              </div>
              <div className="ba-card-mid">
                <div className="ba-name">{a.name}</div>
                <div className="ba-role" onClick={() => navigate(`/artist/${a.id}`)}>{a.role}</div>
                <div className="ba-loc">📍 {a.location}</div>
                <p className="ba-bio">{a.bio}</p>
                <div className="ba-tags">
                  {a.tags.map((t) => <span key={t} className="ba-tag">{t}</span>)}
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
          ))}
          <div className="ba-load-more">
            <button className="ba-view">Load More Artists</button>
          </div>
        </div>
      </section>

      {inviteId && (
        <div className="ba-modal">
          <div className="ba-modal-inner">
            <h3>Message Artist</h3>
            <p>Send a quick message.</p>
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
                  try {
                    const target = MOCK.find((x) => x.id === inviteId);
                    const msg = {
                      id: Date.now(),
                      toId: inviteId,
                      toName: target?.name || "Artist",
                      preview: inviteText || "Invitation sent",
                      timestamp: Date.now(),
                      unread: true,
                      type: "message",
                    };
                    const raw = localStorage.getItem("gb_messages");
                    const arr = raw ? JSON.parse(raw) : [];
                    arr.unshift(msg);
                    localStorage.setItem("gb_messages", JSON.stringify(arr));
                    window.dispatchEvent(new Event("gb:messages"));
                  } catch {}
                  setInviteId(null);
                  setInviteText("");
                }}
              >
                Send Invite
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
