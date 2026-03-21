import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardHeader from '../components/DashboardHeader';
import DashboardSidebar from '../components/DashboardSidebar';
import NotificationCard from '../components/NotificationCard';
import EmptyNotificationsState from '../components/EmptyNotificationsState';
import './dashboard.css';
import './notifications.css';

const NotificationsPage = () => {
  const navigate = useNavigate();
  const [activeSidebar, setActiveSidebar] = useState('notifications');
  const [notifications, setNotifications] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Mock notification data - structured for easy backend replacement later
  const mockNotifications = [
    {
      id: 1,
      type: 'message',
      title: 'New message from Sarah Johnson',
      message: 'Thanks for the update! The design looks great.',
      time: '5 minutes ago',
      unread: true,
      redirectTo: '/artist/messages'
    },
    {
      id: 2,
      type: 'payment',
      title: 'Payment received',
      message: 'You have received $500 from Event Manager Rahul.',
      time: '1 hour ago',
      unread: true,
      redirectTo: '/artist/dashboard'
    },
    {
      id: 3,
      type: 'hire_request',
      title: 'New hire request',
      message: 'Music Festival Team invited you to perform at their upcoming event.',
      time: '3 hours ago',
      unread: true,
      redirectTo: '/artist/opportunities'
    },
    {
      id: 4,
      type: 'verification',
      title: 'Project completed',
      message: 'Your KYC verification has been approved successfully.',
      time: '1 day ago',
      unread: false,
      redirectTo: '/artist/verification'
    },
    {
      id: 5,
      type: 'subscription',
      title: 'Subscription expiring soon',
      message: 'Your GigBridge Pro plan expires in 3 days.',
      time: '2 days ago',
      unread: false,
      redirectTo: '/artist/subscription'
    },
    {
      id: 6,
      type: 'project_invitation',
      title: 'New project opportunity',
      message: 'A client posted a new Photography project matching your skills.',
      time: '3 days ago',
      unread: false,
      redirectTo: '/artist/opportunities'
    }
  ];

  useEffect(() => {
    // Initialize with mock data
    // In future, this will be replaced with API call:
    // const fetchNotifications = async () => {
    //   try {
    //     const response = await notificationService.getNotifications();
    //     setNotifications(response);
    //   } catch (error) {
    //     console.error('Failed to fetch notifications:', error);
    //   }
    // };
    // fetchNotifications();
    
    setNotifications(mockNotifications);
  }, []);

  const getUnreadCount = () => {
    return notifications.filter(notification => notification.unread).length;
  };

  const getFilteredNotifications = () => {
    if (!searchQuery.trim()) {
      return notifications;
    }
    
    return notifications.filter(notification =>
      notification.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      notification.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      notification.type.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const markAsRead = (id) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, unread: false }
          : notification
      )
    );
    
    // In future, make API call:
    // await notificationService.markAsRead(id);
  };

  const dismissNotification = (id) => {
    setNotifications(prev => 
      prev.filter(notification => notification.id !== id)
    );
    
    // In future, make API call:
    // await notificationService.dismissNotification(id);
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, unread: false }))
    );
    
    // In future, make API call:
    // await notificationService.markAllAsRead();
  };

  const handleNotificationClick = (notification) => {
    markAsRead(notification.id);
    navigate(notification.redirectTo);
  };

  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell">
        <DashboardSidebar active={activeSidebar} onSelect={setActiveSidebar} />
        <main className="db-main notifications-page">
          <div className="notifications-header">
            <div className="notifications-title-section">
              <h2>Notifications</h2>
              <p className="notifications-unread-count">You have {getUnreadCount()} unread notification{getUnreadCount() !== 1 ? 's' : ''}</p>
            </div>
            {getUnreadCount() > 0 && (
              <button className="notifications-mark-all-read" onClick={markAllAsRead}>
                <span className="icon-check"></span> Mark all as read
              </button>
            )}
          </div>

          {/* Search Bar */}
          <div className="notifications-search">
            <input
              type="text"
              placeholder="Search notifications..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="db-search-input"
            />
          </div>

          {/* Notifications List */}
          {getFilteredNotifications().length === 0 ? (
            searchQuery ? (
              <div className="db-empty-state">
                <p>No notifications found matching "{searchQuery}"</p>
              </div>
            ) : (
              <EmptyNotificationsState />
            )
          ) : (
            <div className="notifications-list">
              {getFilteredNotifications().map(notification => (
                <NotificationCard
                  key={notification.id}
                  notification={notification}
                  onMarkAsRead={markAsRead}
                  onDismiss={dismissNotification}
                  onClick={handleNotificationClick}
                />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default NotificationsPage;
