import React from 'react';

export default function FilterPanel({ onClose }) {
  return (
    <div className="filter-panel" style={{ 
      background: '#fff', 
      border: '1px solid #e2e8f0', 
      borderRadius: '16px', 
      padding: '24px',
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: '20px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
    }}>
      <div className="form-group">
        <label>Category</label>
        <select defaultValue="Designer">
          <option>Designer</option>
          <option>Dance</option>
          <option>Photography</option>
          <option>Musician</option>
        </select>
      </div>

      <div className="form-group">
        <label>Budget Range</label>
        <select defaultValue="All">
          <option>All</option>
          <option>$0 - $1,000</option>
          <option>$1,000 - $5,000</option>
          <option>$5,000+</option>
        </select>
      </div>

      <div className="form-group">
        <label>Duration</label>
        <select defaultValue="All">
          <option>All</option>
          <option>&lt; 1 month</option>
          <option>1 - 3 months</option>
          <option>3+ months</option>
        </select>
      </div>

      <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
        <button className="db-primary" style={{ width: '100%' }} onClick={onClose}>
          Apply Filters
        </button>
      </div>
    </div>
  );
}
