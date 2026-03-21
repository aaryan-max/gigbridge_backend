import { api } from './api';

export const artistService = {
  getDashboard: async (freelancerId) => {
    try {
      const res = await api.get(`/api/artist/dashboard?freelancer_id=${freelancerId}`);
      if (res.success && res.artist) {
        // Save category to localStorage for UI consistency
        localStorage.setItem('gb_artist_category', res.artist.category || 'Artist');
      }
      return res;
    } catch (e) {
      const cachedCategory = localStorage.getItem('gb_artist_category') || 'Singer';
      return {
        success: true,
        artist: { name: 'Artist', email: 'artist@example.com', category: cachedCategory },
        progress: { completeness: 0.65 },
        stats: {
          earnings: 45000,
          bookings: 5,
          requests: 8,
          successRate: 92,
          growthText: { earnings: '+12% this week', bookings: '+2 this month', requests: '+4 new today', successRate: '+3% from last month' },
        },
      };
    }
  },
  getBookings: async (freelancerId) => {
    try {
      return await api.get(`/api/artist/bookings?freelancer_id=${freelancerId}`);
    } catch {
      return {
        success: true,
        bookings: [
          { id: 1, event: 'Corporate Gala', client: 'TechCorp', date: '2026-04-03', value: 25000, progress: 70 },
          { id: 2, event: 'Wedding Reception', client: 'Arora Family', date: '2026-04-12', value: 18000, progress: 40 },
          { id: 3, event: 'Music Fest', client: 'City Events', date: '2026-05-05', value: 52000, progress: 90 },
        ],
      };
    }
  },
  getActivity: async (freelancerId) => {
    try {
      return await api.get(`/api/artist/activity?freelancer_id=${freelancerId}`);
    } catch {
      return {
        success: true,
        items: [
          { id: 'a1', icon: '📩', text: 'New booking request received', time: '4 hours ago' },
          { id: 'a2', icon: '💸', text: 'Payment received', time: '1 day ago' },
          { id: 'a3', icon: '✅', text: 'Event completed', time: '2 days ago' },
          { id: 'a4', icon: '🛡️', text: 'Profile verification required', time: '2 days ago' },
          { id: 'a5', icon: '💬', text: 'New message from client', time: '3 days ago' },
        ],
      };
    }
  },
};
