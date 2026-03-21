import React from 'react';

export default function RecommendedProjects({ projects, onApply }) {
  return (
    <div className="recommended-section">
      <div className="recommended-header">
        <span style={{ fontSize: '18px' }}>✨</span> Recommended for You
      </div>
      <div className="recommended-grid">
        {projects.map(project => (
          <div key={project.id} className="rec-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="match-badge">{project.matchScore}% Match</span>
              <span className={`urgency-badge ${project.urgency.toLowerCase()}`}>{project.urgency}</span>
            </div>
            <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#1e293b' }}>{project.title}</h4>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>{project.budget}</span>
              <button className="db-primary" style={{ height: '32px', padding: '0 12px', fontSize: '12px' }} onClick={() => onApply(project)}>
                Apply Now
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
