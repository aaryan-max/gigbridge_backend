import { useState } from 'react';
import { Search } from 'lucide-react';
import { 
  MessageCircle, 
  UserPlus, 
  Briefcase, 
  Phone, 
  CheckCircle, 
  CreditCard
} from 'lucide-react';

const NotificationList = ({ notifications, selectedNotification, onNotificationSelect, onSearch }) => {
  const getNotificationIcon = (type) => {
    const iconClass = "w-5 h-5";
    
    switch (type) {
      case 'message':
        return <MessageCircle className={`${iconClass} text-blue-500`} />;
      case 'hire_request':
        return <UserPlus className={`${iconClass} text-green-500`} />;
      case 'project_invitation':
        return <Briefcase className={`${iconClass} text-purple-500`} />;
      case 'call':
        return <Phone className={`${iconClass} text-red-500`} />;
      case 'verification':
        return <CheckCircle className={`${iconClass} text-emerald-500`} />;
      case 'subscription':
        return <CreditCard className={`${iconClass} text-orange-500`} />;
      default:
        return <MessageCircle className={`${iconClass} text-gray-500`} />;
    }
  };

  const getNotificationBgColor = (type) => {
    switch (type) {
      case 'message':
        return 'bg-blue-50';
      case 'hire_request':
        return 'bg-green-50';
      case 'project_invitation':
        return 'bg-purple-50';
      case 'call':
        return 'bg-red-50';
      case 'verification':
        return 'bg-emerald-50';
      case 'subscription':
        return 'bg-orange-50';
      default:
        return 'bg-gray-50';
    }
  };

  return (
    <div className="w-full md:w-1/3 border-r border-gray-200 bg-white">
      {/* Search Bar */}
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search notifications..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onChange={(e) => onSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Notification List */}
      <div className="overflow-y-auto" style={{ height: 'calc(100vh - 200px)' }}>
        {notifications.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <p>No notifications found</p>
          </div>
        ) : (
          notifications.map(notification => (
            <div
              key={notification.id}
              className={`
                p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors
                ${selectedNotification?.id === notification.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''}
                ${notification.unread ? 'bg-white' : 'bg-gray-50'}
              `}
              onClick={() => onNotificationSelect(notification)}
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div className={`
                  flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                  ${getNotificationBgColor(notification.type)}
                `}>
                  {getNotificationIcon(notification.type)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900 text-sm truncate">
                      {notification.title}
                    </h3>
                    <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
                      {notification.time}
                    </span>
                  </div>
                  <p className="text-gray-600 text-sm mt-1 truncate">
                    {notification.message}
                  </p>
                </div>

                {/* Unread indicator */}
                {notification.unread && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NotificationList;
