import React from 'react';

export default function EmptyStateCard({ onAdd }) {
  return (
    <div className="empty-gig-state">
      <div className="empty-gig-icon">🎭</div>
      <h4>No gigs added yet</h4>
      <p>Start building your artist portfolio by adding your performances and events.</p>
      <button className="db-primary" onClick={onAdd}>
        Add First Gig
      </button>
    </div>
  );
}
