import React, { useState } from 'react';

const CATEGORIES = ["Dance", "Photography", "Music Band", "DJ Performance", "Makeup Artist", "Event Host"];
const STATUSES = ["Completed", "Ongoing", "Upcoming"];

export default function AddGigModal({ onClose, onSave }) {
  const userCategory = React.useMemo(() => {
    return localStorage.getItem('gb_artist_category') || 'Dance';
  }, []);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: userCategory,
    date: new Date().toISOString().split('T')[0],
    hours: 2,
    status: 'Completed'
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      ...formData,
      hours: parseInt(formData.hours, 10)
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="add-project-modal" onClick={e => e.stopPropagation()}>
        <header className="modal-header">
          <h3>Add Gig Activity</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </header>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Gig Title</label>
            <input 
              name="title" 
              placeholder="e.g. Wedding Dance Performance" 
              value={formData.title}
              onChange={handleChange}
              required 
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea 
              name="description" 
              placeholder="Short description of the task..." 
              value={formData.description}
              onChange={handleChange}
              rows={3}
              required 
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Category</label>
              <select name="category" value={formData.category} onChange={handleChange} disabled>
                <option value={userCategory}>{userCategory}</option>
              </select>
              <small style={{ color: '#64748b', fontSize: '11px', marginTop: '4px' }}>
                Your account is locked to {userCategory} gigs.
              </small>
            </div>
            <div className="form-group">
              <label>Status</label>
              <select name="status" value={formData.status} onChange={handleChange}>
                {STATUSES.map(status => <option key={status} value={status}>{status}</option>)}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Event Date</label>
              <input 
                type="date" 
                name="date" 
                value={formData.date}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label>Hours Spent</label>
              <input 
                type="number" 
                name="hours" 
                value={formData.hours}
                onChange={handleChange}
                min="1"
                required
              />
            </div>
          </div>
        </form>

        <footer className="modal-footer">
          <button type="button" className="secondary-btn" onClick={onClose}>Cancel</button>
          <button type="submit" className="db-primary" onClick={handleSubmit}>Save Gig</button>
        </footer>
      </div>
    </div>
  );
}
