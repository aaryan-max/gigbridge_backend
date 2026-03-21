import { api } from './api';

export const clientService = {
  getProfile: async (clientId) => {
    return await api.get(`/client/profile/${clientId}`);
  },

  createProfile: async (profileData) => {
    return await api.post('/client/profile', profileData);
  },

  sendMessage: async (clientEmail, freelancerEmail, message) => {
    return await api.post('/client/message/send', {
      client_email: clientEmail,
      freelancer_email: freelancerEmail,
      message,
    });
  },

  hireFreelancer: async (hireData) => {
    return await api.post('/client/hire', hireData);
  },

  getMessageThreads: async (clientEmail) => {
    return await api.get(`/client/messages/threads?client_email=${clientEmail}`);
  },

  getJobRequests: async (clientEmail) => {
    return await api.get(`/client/job-requests?client_email=${clientEmail}`);
  },

  getJobs: async (clientEmail) => {
    return await api.get(`/client/jobs?client_email=${clientEmail}`);
  },

  saveFreelancer: async (clientEmail, freelancerEmail) => {
    return await api.post('/client/save-freelancer', {
      client_email: clientEmail,
      freelancer_email: freelancerEmail,
    });
  },

  getSavedFreelancers: async (clientEmail) => {
    return await api.get(`/client/saved-freelancers?client_email=${clientEmail}`);
  },

  getNotifications: async (clientEmail) => {
    return await api.get(`/client/notifications?client_email=${clientEmail}`);
  },
};
