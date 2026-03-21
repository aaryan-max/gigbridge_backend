import React from 'react';
import DashboardHeader from './DashboardHeader';
import DashboardSidebar from './DashboardSidebar';

export default function DashboardPlaceholder({ activeKey, title, description }) {
  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell">
        <DashboardSidebar active={activeKey} />
        <main className="db-main">
          <div className="db-welcome">
            <h2>{title}</h2>
            <p>{description}</p>
          </div>
          
          <div style={{ 
            marginTop: '40px', 
            padding: '60px', 
            background: '#fff', 
            borderRadius: '16px', 
            border: '1px solid #e2e8f0',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>🛠️</div>
            <h3 style={{ fontSize: '20px', fontWeight: 600, color: '#1e293b', marginBottom: '8px' }}>
              {title} is Under Development
            </h3>
            <p style={{ color: '#64748b', fontSize: '15px' }}>
              We're working hard to bring you the best experience. Check back soon!
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
