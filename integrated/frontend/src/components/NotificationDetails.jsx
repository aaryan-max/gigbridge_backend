import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Clock, CheckCircle } from 'lucide-react';
import { 
  MessageCircle, 
  UserPlus, 
  Briefcase, 
  Phone, 
  CreditCard
} from 'lucide-react';

const NotificationDetails = ({ notification, onBack, onMarkAsRead, onDismiss }) => {
  const navigate = useNavigate();

  const getNotificationIcon = (type) => {
    const iconClass = "w-6 h-6";
    
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

  const handleActionClick = () => {
    if (notification?.redirectTo) {
      navigate(notification.redirectTo);
    }
  };

  if (!notification) {
    return (
      <div className="w-full md:w-2/3 bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MessageCircle className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Select a notification to view details
          </h3>
          <p className="text-gray-600 text-sm">
            Choose a notification from the list to see more information and take action.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full md:w-2/3 bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors md:hidden"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <h2 className="text-lg font-semibold text-gray-900">
              Notification Details
            </h2>
          </div>
          <div className="flex items-center gap-2">
            {notification.unread && (
              <button
                onClick={() => onMarkAsRead(notification.id)}
                className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
              >
                Mark as read
              </button>
            )}
            <button
              onClick={() => onDismiss(notification.id)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              ×
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Notification Header */}
        <div className="flex items-start gap-4 mb-6">
          <div className={`
            w-12 h-12 rounded-full flex items-center justify-center
            ${getNotificationBgColor(notification.type)}
          `}>
            {getNotificationIcon(notification.type)}
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {notification.title}
            </h3>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {notification.time}
              </div>
              {notification.unread && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                  Unread
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Message Content */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <p className="text-gray-700 leading-relaxed">
            {notification.message}
          </p>
        </div>

        {/* Additional Details */}
        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 mb-3">Details</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Type</span>
              <span className="text-sm font-medium text-gray-900 capitalize">
                {notification.type.replace('_', ' ')}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Status</span>
              <span className={`text-sm font-medium ${notification.unread ? 'text-blue-600' : 'text-green-600'}`}>
                {notification.unread ? 'Unread' : 'Read'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-gray-600">Received</span>
              <span className="text-sm font-medium text-gray-900">
                {notification.time}
              </span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        {notification.redirectTo && (
          <button
            onClick={handleActionClick}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            {notification.type === 'message' && 'View Messages'}
            {notification.type === 'hire_request' && 'View Opportunities'}
            {notification.type === 'project_invitation' && 'View Opportunities'}
            {notification.type === 'call' && 'View Messages'}
            {notification.type === 'verification' && 'View Verification'}
            {notification.type === 'subscription' && 'Manage Subscription'}
            <ExternalLink className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default NotificationDetails;
