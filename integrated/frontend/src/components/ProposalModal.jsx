import React, { useState } from 'react';

export default function ProposalModal({ project, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    coverLetter: '',
    bidAmount: '',
    deliveryTime: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  if (!project) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="proposal-modal" onClick={e => e.stopPropagation()}>
        <header className="modal-header">
          <h3>Submit Proposal</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </header>

        <form onSubmit={handleSubmit} className="proposal-form">
          <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <h4 style={{ fontWeight: 600, color: '#1e293b', marginBottom: '4px' }}>{project.title}</h4>
            <p style={{ fontSize: '14px', color: '#64748b' }}>{project.client} • {project.budget}</p>
          </div>

          <div className="form-group">
            <label>Cover Letter</label>
            <textarea 
              placeholder="Explain why you're the best fit for this project..." 
              rows={6}
              value={formData.coverLetter}
              onChange={(e) => setFormData(prev => ({ ...prev, coverLetter: e.target.value }))}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Bid Amount ($)</label>
              <input 
                type="number" 
                placeholder="5000" 
                value={formData.bidAmount}
                onChange={(e) => setFormData(prev => ({ ...prev, bidAmount: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label>Delivery Time</label>
              <input 
                type="text" 
                placeholder="2 weeks" 
                value={formData.deliveryTime}
                onChange={(e) => setFormData(prev => ({ ...prev, deliveryTime: e.target.value }))}
                required
              />
            </div>
          </div>
        </form>

        <footer className="proposal-footer">
          <button className="secondary-btn" onClick={onClose}>Cancel</button>
          <button className="db-primary" onClick={handleSubmit}>🚀 Send Proposal</button>
        </footer>
      </div>
    </div>
  );
}
