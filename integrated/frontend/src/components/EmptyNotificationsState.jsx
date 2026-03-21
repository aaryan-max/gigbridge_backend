import { Bell, Inbox } from 'lucide-react';

const EmptyNotificationsState = () => {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      {/* Glass style card */}
      <div className="
        relative bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg 
        border border-gray-200/50 p-8 max-w-md w-full text-center
      ">
        {/* Icon illustration */}
        <div className="mb-6">
          <div className="relative inline-flex">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <Bell className="w-8 h-8 text-blue-600" />
            </div>
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center">
              <Inbox className="w-3 h-3 text-gray-400" />
            </div>
          </div>
        </div>

        {/* Content */}
        <h2 className="text-xl font-semibold text-gray-900 mb-3">
          No Notifications Yet
        </h2>
        
        <p className="text-gray-600 text-sm leading-relaxed mb-6">
          When clients contact you or send hire requests, they will appear here.
        </p>

        {/* Decorative elements */}
        <div className="absolute top-4 left-4 w-2 h-2 bg-blue-200 rounded-full opacity-60"></div>
        <div className="absolute top-6 right-6 w-1.5 h-1.5 bg-purple-200 rounded-full opacity-40"></div>
        <div className="absolute bottom-8 left-8 w-2.5 h-2.5 bg-green-200 rounded-full opacity-50"></div>
        <div className="absolute bottom-4 right-4 w-1 h-1 bg-orange-200 rounded-full opacity-60"></div>
      </div>

      {/* Additional helpful text */}
      <div className="mt-6 text-center max-w-md">
        <p className="text-gray-500 text-xs">
          Stay tuned! You'll receive notifications for new messages, hire requests, and project opportunities.
        </p>
      </div>
    </div>
  );
};

export default EmptyNotificationsState;
