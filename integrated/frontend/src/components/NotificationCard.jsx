import { X } from 'lucide-react';
import { 
  MessageCircle, 
  UserPlus, 
  Briefcase, 
  Phone, 
  CheckCircle, 
  CreditCard,
  DollarSign,
  FileText
} from 'lucide-react';

const NotificationCard = ({ notification, onMarkAsRead, onDismiss, onClick }) => {
  const getNotificationIcon = (type) => {
    const iconClass = "w-5 h-5";
    
    switch (type) {
      case 'message':
        return <MessageCircle className={`${iconClass} text-white`} />;
      case 'hire_request':
        return <FileText className={`${iconClass} text-white`} />;
      case 'project_invitation':
        return <Briefcase className={`${iconClass} text-white`} />;
      case 'call':
        return <Phone className={`${iconClass} text-white`} />;
      case 'verification':
        return <CheckCircle className={`${iconClass} text-white`} />;
      case 'subscription':
        return <CreditCard className={`${iconClass} text-white`} />;
      case 'payment':
        return <DollarSign className={`${iconClass} text-white`} />;
      default:
        return <MessageCircle className={`${iconClass} text-white`} />;
    }
  };

  const getNotificationBgColor = (type) => {
    switch (type) {
      case 'message':
        return 'bg-blue-500';
      case 'hire_request':
        return 'bg-orange-500';
      case 'project_invitation':
        return 'bg-purple-500';
      case 'call':
        return 'bg-red-500';
      case 'verification':
        return 'bg-green-500';
      case 'subscription':
        return 'bg-orange-500';
      case 'payment':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div
      className={`
        relative bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200
        border border-gray-100 cursor-pointer group p-5
      `}
      onClick={() => onClick(notification)}
    >
      <div className="flex items-start gap-4">
        {/* Left side icon - rounded square */}
        <div className={`
          flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center
          ${getNotificationBgColor(notification.type)}
        `}>
          {getNotificationIcon(notification.type)}
        </div>

        {/* Notification content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 text-base leading-tight mb-1">
                {notification.title}
              </h3>
              <p className="text-gray-600 text-sm leading-normal mb-2">
                {notification.message}
              </p>
              <div className="flex items-center gap-2">
                <p className="text-gray-400 text-xs">
                  {notification.time}
                </p>
                {/* Unread indicator */}
                {notification.unread && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                )}
              </div>
            </div>

            {/* Dismiss button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDismiss(notification.id);
              }}
              className="
                flex-shrink-0 p-1.5 rounded-lg hover:bg-gray-100 
                opacity-0 group-hover:opacity-100 transition-all duration-200
              "
              aria-label="Dismiss notification"
            >
              <X className="w-4 h-4 text-gray-400 hover:text-gray-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Hover effect */}
      <div className="absolute inset-0 bg-blue-50 opacity-0 group-hover:opacity-5 rounded-xl transition-opacity duration-200 pointer-events-none"></div>
    </div>
  );
};

export default NotificationCard;
