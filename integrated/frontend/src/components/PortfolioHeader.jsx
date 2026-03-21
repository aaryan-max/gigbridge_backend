import React from 'react';

export default function PortfolioHeader({ onAddClick }) {
  return (
    <div className="portfolio-header-section">
      <div className="portfolio-header-text">
        <h2>Portfolio</h2>
        <p>Showcase your best work to attract clients</p>
      </div>
      <button className="db-primary" onClick={onAddClick}>
        <span style={{ fontSize: '18px', marginRight: '8px' }}>+</span> Add Project
      </button>
    </div>
  );
}
