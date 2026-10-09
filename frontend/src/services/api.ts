import axios from 'axios';

export const API_BASE = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('qoneqt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Authentication APIs
export const authApi = {
  requestOtp: async (email: string) => {
    const res = await apiClient.post('/auth/otp/request', { email });
    return res.data;
  },
  resendOtp: async (email: string) => {
    const res = await apiClient.post('/auth/otp/resend', { email });
    return res.data;
  },
  verifyOtp: async (email: string, otp: string) => {
    const res = await apiClient.post('/auth/otp/verify', { email, otp });
    return res.data;
  },
  getCurrentSession: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
  logout: async () => {
    const res = await apiClient.post('/auth/logout');
    return res.data;
  },
};

// Security Center APIs
export const securityApi = {
  calculateHash: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/security/integrity/hash', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  verifyIntegrity: async (file: File, referenceHash: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('reference_hash', referenceHash);
    const res = await apiClient.post('/security/integrity/verify', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  inspectMetadata: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/security/metadata/inspect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  sanitizeMetadata: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/security/metadata/sanitize', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  getSecurityStats: async () => {
    const res = await apiClient.get('/security/stats');
    return res.data;
  },
};

export default apiClient;
