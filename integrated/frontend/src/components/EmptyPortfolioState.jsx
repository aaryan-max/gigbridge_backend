import React from 'react';

export default function EmptyPortfolioState({ onAddClick }) {
  return (
    <div className="empty-portfolio-wrap">
      <div className="glass-empty-card">
        <div className="empty-icon-wrap">
          📁
        </div>
        <h3>No projects posted yet</h3>
        <p>Showcase your work to attract clients on GigBridge. High-quality portfolios increase your booking chances by up to 3x.</p>
        <button className="db-primary" onClick={onAddClick}>
          Add Your First Project
        </button>
      </div>
    </div>
  );
}
