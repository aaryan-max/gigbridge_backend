import React, { useEffect, useState } from 'react';
import { getNotifications, markAsRead, markAllAsRead } from '../services/notificationService';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getNotifications().then(data => {
      setNotifications(data);
      setLoading(false);
    });
  }, []);

  const handleMarkAsRead = async (id) => {
    await markAsRead(id);
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
  };

  const handleMarkAllAsRead = async () => {
    await markAllAsRead();
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  return (
    <div className="page-wrap" style={{ marginTop: '24px' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 className="page-title" style={{ margin: 0 }}>Notifications</h1>
        {notifications.some(n => !n.read) && (
          <button className="mark-all-btn" onClick={handleMarkAllAsRead} style={{ background: 'transparent', color: '#3b82f6', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
            Mark all as read
          </button>
        )}
      </div>

      <div className="page-card" style={{ padding: '0', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="skeleton-item"></div>
            <div className="skeleton-item"></div>
          </div>
        ) : notifications.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#6b7280' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
            <p>You have no notifications yet.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {notifications.map((notif, index) => (
              <div 
                key={notif.id} 
                className="fade-in"
                onClick={() => !notif.read && handleMarkAsRead(notif.id)}
                style={{ 
                  padding: '20px 24px', 
                  borderBottom: index !== notifications.length - 1 ? '1px solid #f3f4f6' : 'none',
                  background: notif.read ? '#ffffff' : '#f0f9ff',
                  cursor: notif.read ? 'default' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'background 0.2s ease'
                }}
              >
                <div>
                  <p style={{ margin: '0 0 8px 0', fontSize: '15px', color: '#1f2937', fontWeight: notif.read ? 400 : 500 }}>
                    {notif.message}
                  </p>
                  <span style={{ fontSize: '12px', color: '#9ca3af' }}>Just now</span>
                </div>
                {!notif.read && (
                  <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#3b82f6', flexShrink: 0 }}></div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
