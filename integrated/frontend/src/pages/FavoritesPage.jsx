import React, { useEffect, useState } from 'react';
import { useFavorites } from '../hooks/useFavorites';
import { useNavigate } from 'react-router-dom';

// We duplicate the mock data here for the frontend-only simulation
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

export default function FavoritesPage() {
  const { favorites, toggleFavorite } = useFavorites();
  const [artists, setArtists] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    // In a real app, this would be an API call: fetchArtistsByIds(favorites)
    const result = MOCK_API_RESPONSE.filter(artist => favorites.includes(artist.id));
    setArtists(result);
  }, [favorites]);

  return (
    <main className="ba-wrap" style={{ marginTop: '24px' }}>
      <header className="ba-header">
        <h1>My Liked Freelancers</h1>
        <p style={{ color: '#64748b', fontSize: '15px' }}>Here are all the artists you've saved.</p>
      </header>

      <section className="ba-grid" style={{ gridTemplateColumns: '1fr', marginTop: '24px' }}>
        <div className="ba-results">
          {artists.length === 0 ? (
            <div className="ba-empty" style={{ padding: '60px 0', background: '#fff', borderRadius: '16px', border: '1px solid #e9f0ff' }}>
              <div className="ba-empty-illus" style={{ fontSize: '48px', marginBottom: '16px' }}>❤️</div>
              <div className="ba-empty-title">No liked freelancers</div>
              <div className="ba-empty-sub">Explore artists and click the heart icon to save them here.</div>
              <button 
                onClick={() => navigate('/browse-artists')} 
                style={{ marginTop: '24px', padding: '12px 24px', background: '#2563eb', color: 'white', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: 600 }}
              >
                Browse Artists
              </button>
            </div>
          ) : (
            artists.map((a) => (
              <article className="ba-card" key={a.id} style={{ position: 'relative' }}>
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
                    <button className="ba-view">Message</button>
                  </div>
                </div>
                <div className="ba-card-right" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'space-between' }}>
                  <button 
                    onClick={() => toggleFavorite(a.id)}
                    style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '24px', padding: '0', margin: '0', transition: 'transform 0.2s' }}
                    title="Remove from favorites"
                    onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
                    onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
                  >
                    ❤️
                  </button>
                  <div className="ba-rating">⭐ {a.rating}</div>
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
