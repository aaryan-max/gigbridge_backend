import React from 'react';

export default function ProjectCard({ data, onApply }) {
  return (
    <div className="opp-card">
      <div className="opp-card-header">
        <div className="opp-client-info">
          <div className="opp-avatar">{data.avatar}</div>
          <div className="opp-title-wrap">
            <h3>{data.title}</h3>
            <div className="opp-client-meta">
              <span style={{ fontWeight: 600, color: '#1e293b' }}>{data.client}</span>
              <span className="opp-rating">⭐ {data.rating}</span>
              <span className="opp-posted">{data.postedAt}</span>
            </div>
          </div>
        </div>
        <div className="opp-badges">
          <span className="match-badge">{data.matchScore}% Match</span>
          <span className={`urgency-badge ${data.urgency.toLowerCase()}`}>{data.urgency}</span>
        </div>
      </div>
      
      <p className="opp-desc">{data.description}</p>
      
      <div className="opp-details">
        <div className="opp-detail-item">💰 {data.budget} ({data.budgetType})</div>
        <div className="opp-detail-item">🕒 {data.timeline}</div>
        <div className="opp-detail-item">📄 {data.proposals} Proposals</div>
      </div>
      
      <div className="opp-tags">
        {data.skills.map(skill => (
          <span key={skill} className="opp-tag">{skill}</span>
        ))}
      </div>
      
      <div className="opp-actions">
        <button 
          className="db-primary" 
          style={{ height: '40px', padding: '0 24px', borderRadius: '10px' }}
          onClick={onApply}
        >
          🚀 Submit Proposal
        </button>
      </div>
    </div>
  );
}
