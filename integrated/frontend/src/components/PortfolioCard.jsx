import React from 'react';

export default function PortfolioCard({ project, onDelete }) {
  return (
    <div className="portfolio-card-item">
      <div className="portfolio-card-img-wrap">
        <img src={project.image} alt={project.title} />
      </div>
      <div className="portfolio-card-content">
        <h4 className="portfolio-card-title">{project.title}</h4>
        <p className="portfolio-card-desc">{project.description}</p>
        <div className="portfolio-card-tags">
          {project.tags.map((tag, idx) => (
            <span key={idx} className="portfolio-tag">{tag}</span>
          ))}
        </div>
      </div>
      <div className="portfolio-card-actions">
        <button className="action-btn delete" onClick={onDelete} title="Delete Project">
          🗑️
        </button>
      </div>
    </div>
  );
}
