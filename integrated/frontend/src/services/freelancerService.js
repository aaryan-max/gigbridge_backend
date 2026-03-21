import { api } from './api';

export const freelancerService = {
  searchFreelancers: async (params) => {
    const queryParams = new URLSearchParams();
    if (params.category) queryParams.append('category', params.category);
    if (params.query) queryParams.append('query', params.query);
    if (params.skills) queryParams.append('skills', params.skills);
    if (params.min_rate) queryParams.append('min_rate', params.min_rate);
    if (params.max_rate) queryParams.append('max_rate', params.max_rate);
    if (params.location) queryParams.append('location', params.location);
    if (params.availability) queryParams.append('availability', params.availability);

    const queryString = queryParams.toString();
    return await api.get(`/freelancers/search${queryString ? `?${queryString}` : ''}`);
  },

  getAllFreelancers: async () => {
    return await api.get('/freelancers/all');
  },

  getFreelancerById: async (id) => {
    return await api.get(`/freelancers/${id}`);
  },

  createProfile: async (profileData) => {
    return await api.post('/freelancer/profile', profileData);
  },

  updateAvailability: async (email, availability) => {
    return await api.post('/freelancer/update-availability', { email, availability });
  },

  getStats: async (email) => {
    return await api.get(`/freelancer/stats?email=${email}`);
  },

  saveClient: async (freelancerEmail, clientEmail) => {
    return await api.post('/freelancer/save-client', {
      freelancer_email: freelancerEmail,
      client_email: clientEmail
    });
  },

  getSavedClients: async (freelancerEmail) => {
    return await api.get(`/freelancer/saved-clients?email=${freelancerEmail}`);
  },

  changePassword: async (email, oldPassword, newPassword) => {
    return await api.post('/freelancer/change-password', {
      email,
      old_password: oldPassword,
      new_password: newPassword,
    });
  },
};
