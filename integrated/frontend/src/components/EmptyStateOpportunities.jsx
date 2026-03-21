import React from 'react';

export default function EmptyStateOpportunities({ onRefresh }) {
  return (
    <div className="empty-opps-wrap">
      <div className="glass-search-card">
        <div className="magnifier-animation">
          🔍
        </div>
        <h3>No opportunities yet</h3>
        <p>GigBridge is searching for clients that match your skills. High-quality profiles increase your booking chances by up to 3x.</p>
        <button className="db-primary" onClick={onRefresh}>
          Refresh Opportunities
        </button>
      </div>
    </div>
  );
}
