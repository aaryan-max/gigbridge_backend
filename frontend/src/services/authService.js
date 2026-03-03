import { api } from './api';

export const authService = {
  sendOTP: async (email, role) => {
    const endpoint = role === 'client' ? '/client/send-otp' : '/freelancer/send-otp';
    return await api.post(endpoint, { email });
  },

  verifyOTPAndSignup: async ({ name, email, password, otp }, role) => {
    const endpoint = role === 'client' ? '/client/verify-otp' : '/freelancer/verify-otp';
    return await api.post(endpoint, { name, email, password, otp });
  },

  signup: async (userData, role) => {
    const endpoint = role === 'client' ? '/client/signup' : '/freelancer/signup';
    return await api.post(endpoint, userData);
  },

  login: async (email, password, role) => {
    const endpoint = role === 'client' ? '/client/login' : '/freelancer/login';
    return await api.post(endpoint, { email, password });
  },
};
