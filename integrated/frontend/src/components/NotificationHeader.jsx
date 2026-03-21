import { Check } from 'lucide-react';

const NotificationHeader = ({ unreadCount, onMarkAllAsRead }) => {
  return (
    <div className="mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Notifications
          </h1>
          <p className="text-gray-600 text-sm">
            You have {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
          </p>
        </div>
        
        {unreadCount > 0 && (
          <button
            onClick={onMarkAllAsRead}
            className="
              flex items-center gap-2 px-4 py-2 bg-blue-600 text-white
              rounded-lg hover:bg-blue-700 transition-colors duration-200
              text-sm font-medium shadow-sm hover:shadow-md
            "
          >
            <Check className="w-4 h-4" />
            Mark all as read
          </button>
        )}
      </div>
    </div>
  );
};

export default NotificationHeader;
