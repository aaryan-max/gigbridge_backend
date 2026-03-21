import React from "react";

export default function PortfolioPreview({ portfolio }) {
  return (
    <div className="portfolio-preview">
      <h3 className="section-title">Portfolio Preview</h3>
      <div className="portfolio-grid">
        {portfolio.map(item => (
          <div key={item.id} className="portfolio-card">
            <img src={item.image} alt={item.title} className="portfolio-img" />
            <div className="portfolio-info">
              <h4 className="portfolio-title">{item.title}</h4>
              <p className="portfolio-desc">{item.description}</p>
            </div>
          </div>
        ))}
        <div className="portfolio-card add-card" style={{ display: 'grid', placeItems: 'center', height: '100%', border: '1px dashed #cbd5e1', cursor: 'pointer', minHeight: '200px' }}>
          <div style={{ textAlign: 'center', color: '#64748b' }}>
            <span style={{ fontSize: '32px' }}>+</span>
            <p style={{ fontSize: '14px', fontWeight: 500 }}>Add Work</p>
          </div>
        </div>
      </div>
    </div>
  );
}
