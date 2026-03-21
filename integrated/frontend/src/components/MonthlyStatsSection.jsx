import React from 'react';

export default function MonthlyStatsSection({ stats }) {
  const statsList = [
    { id: 1, label: 'Total Gigs', value: stats.totalGigs, icon: '🌟' },
    { id: 2, label: 'Performance Hours', value: `${stats.performanceHours}h`, icon: '🕒' },
    { id: 3, label: 'Events Worked', value: stats.eventsWorked, icon: '🏟️' },
    { id: 4, label: 'Estimated Earnings', value: `₹${stats.estimatedEarnings.toLocaleString()}`, icon: '💰' }
  ];

  return (
    <div className="monthly-stats-section">
      <h3 className="monthly-title">This Month Performance</h3>
      <div className="stats-grid">
        {statsList.map(stat => (
          <div key={stat.id} className="stat-box">
            <div className="stat-ico">{stat.icon}</div>
            <div className="stat-lbl">{stat.label}</div>
            <div className="stat-val">{stat.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
