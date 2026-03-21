import React from 'react';

export default function WeeklySummaryCard({ summary }) {
  const breakdownEntries = Object.entries(summary.categoryBreakdown);

  return (
    <div className="weekly-summary-card">
      <h3 className="summary-title">Weekly Performance Summary</h3>
      <div className="summary-item">
        <div className="summary-icon gigs">🎭</div>
        <div className="summary-text">
          <span className="summary-label">Total Gigs This Week</span>
          <span className="summary-value">{summary.totalGigs}</span>
        </div>
      </div>
      <div className="summary-item">
        <div className="summary-icon hours">🕒</div>
        <div className="summary-text">
          <span className="summary-label">Total Performance Hours</span>
          <span className="summary-value">{summary.totalHours}h</span>
        </div>
      </div>

      {breakdownEntries.length > 0 && (
        <div className="breakdown-section">
          <h4 className="breakdown-title">Gig Category Breakdown</h4>
          <div className="breakdown-list">
            {breakdownEntries.map(([category, count]) => (
              <div key={category} className="breakdown-item">
                <span className="breakdown-label">{category}</span>
                <span className="breakdown-count">{count} {count === 1 ? 'gig' : 'gigs'}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
