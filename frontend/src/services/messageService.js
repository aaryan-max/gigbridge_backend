import { api } from './api';

export const messageService = {
  getHistory: async (user1Email, user2Email) => {
    return await api.get(`/message/history?user1=${user1Email}&user2=${user2Email}`);
  },

  sendFreelancerMessage: async (freelancerEmail, clientEmail, message) => {
    return await api.post('/freelancer/message/send', {
      freelancer_email: freelancerEmail,
      client_email: clientEmail,
      message,
    });
  },

  sendClientMessage: async (clientEmail, freelancerEmail, message) => {
    return await api.post('/client/message/send', {
      client_email: clientEmail,
      freelancer_email: freelancerEmail,
      message,
    });
  },
};
