export default function ArtistCard({ artist, loading, onKnowMore }) {
  if (loading) {
    return (
      <article className="skeleton-card">
        <div className="skeleton-image"></div>
        <div className="ac-content" style={{ gap: '10px', paddingTop: '10px' }}>
          <div className="skeleton-line title"></div>
          <div className="skeleton-line sub"></div>
          <div className="skeleton-line text" style={{ marginTop: '12px' }}></div>
          <div className="skeleton-line text"></div>
          <div className="skeleton-line text short"></div>
          <div className="ac-footer" style={{ marginTop: 'auto' }}>
            <div className="skeleton-line skeleton-btn"></div>
          </div>
        </div>
      </article>
    );
  }

  return (
    <article className="artist-card-modern">
      <div className="ac-image-wrap">
        <img
          src={artist.image}
          alt={artist.name}
          className="ac-image"
        />
      </div>
      <div className="ac-content">
        <div className="ac-name">{artist.name}</div>
        <div className="ac-category">{artist.category}</div>
        <p className="ac-desc">
          {artist.description?.length > 90 
            ? artist.description.slice(0, 90) + '...' 
            : artist.description}
        </p>
        <div className="ac-footer">
          <div className="ac-rating">⭐ {artist.rating}</div>
          <button className="ac-know-more" onClick={() => onKnowMore(artist.id)}>
            Know More
          </button>
        </div>
      </div>
    </article>
  );
}
