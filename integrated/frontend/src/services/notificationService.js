export const getNotifications = async () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        {
          id: "1",
          message: "Freelancer sent you a proposal",
          type: "proposal",
          read: false,
          createdAt: new Date()
        },
        {
          id: "2",
          message: "New artist matches your project",
          type: "match",
          read: false,
          createdAt: new Date()
        }
      ]);
    }, 800);
  });
};

export const markAsRead = async (id) => {
  return Promise.resolve();
};

export const markAllAsRead = async () => {
  return Promise.resolve();
};

export const addNewNotification = (notification) => {
  // To be used by WebSocket integration
  // This is a placeholder since state is maintained in the component currently 
  console.log("New notification received:", notification);
};
