import { api } from './api';

export const paymentService = {
  createOrder: async (clientId, freelancerId, amount, projectTitle) => {
    return await api.post('/create-order', {
      client_id: clientId,
      freelancer_id: freelancerId,
      amount,
      project_title: projectTitle,
    });
  },

  verifyPayment: async (razorpayOrderId, razorpayPaymentId, razorpaySignature) => {
    return await api.post('/verify-payment', {
      razorpay_order_id: razorpayOrderId,
      razorpay_payment_id: razorpayPaymentId,
      razorpay_signature: razorpaySignature,
    });
  },

  getHistory: async (clientId, freelancerId) => {
    const params = new URLSearchParams();
    if (clientId) params.append('client_id', clientId);
    if (freelancerId) params.append('freelancer_id', freelancerId);
    return await api.get(`/payments/history?${params.toString()}`);
  },
};
