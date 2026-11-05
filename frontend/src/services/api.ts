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

// Multi-Factor Authentication (MFA - RFC 6238 TOTP & Recovery Codes)
export const mfaApi = {
  getStatus: async () => {
    const res = await apiClient.get('/auth/mfa/status');
    return res.data;
  },
  setup: async (token?: string) => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await apiClient.post('/auth/mfa/setup', {}, { headers });
    return res.data;
  },
  confirm: async (code: string, token?: string) => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await apiClient.post('/auth/mfa/confirm', { code }, { headers });
    return res.data;
  },
  verifyLogin: async (mfaToken: string, code: string, method: 'totp' | 'recovery' = 'totp') => {
    const res = await apiClient.post('/auth/mfa/verify', {
      mfa_token: mfaToken,
      code,
      method,
    });
    return res.data;
  },
  regenerateRecoveryCodes: async () => {
    const res = await apiClient.post('/auth/mfa/regenerate-recovery-codes');
    return res.data;
  },
  disable: async (code: string, method: 'totp' | 'recovery' = 'totp') => {
    const res = await apiClient.post('/auth/mfa/disable', { code, method });
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
  getMalwareStatus: async () => {
    const res = await apiClient.get('/security/malware/status');
    return res.data;
  },
  scanFileForMalware: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/security/malware/scan', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  getMalwareScanReport: async (scanId: string) => {
    const res = await apiClient.get(`/security/malware/scans/${scanId}`);
    return res.data;
  },
  getMalwareHistory: async (limit: number = 20) => {
    const res = await apiClient.get('/security/malware/history', {
      params: { limit },
    });
    return res.data;
  },
};

// Projects & Video Export APIs
export const projectsApi = {
  getProjects: async () => {
    const res = await apiClient.get('/projects/');
    return res.data;
  },
  getProject: async (id: number | string) => {
    const res = await apiClient.get(`/projects/${id}`);
    return res.data;
  },
  renderVideo: async (id: number | string, sanitizeMetadata: boolean = true) => {
    const res = await apiClient.post(`/projects/${id}/render`, {
      sanitize_metadata: sanitizeMetadata,
    });
    return res.data;
  },
  updateMetadataPolicy: async (id: number | string, sanitizeMetadata: boolean) => {
    const res = await apiClient.post(`/projects/${id}/metadata-policy`, {
      sanitize_metadata: sanitizeMetadata,
    });
    return res.data;
  },
};

// Image-to-Video APIs
export const imageToVideoApi = {
  getVoices: async () => {
    const res = await apiClient.get('/image-to-video/voices');
    return res.data;
  },
  getMusicTracks: async () => {
    const res = await apiClient.get('/image-to-video/music-tracks');
    return res.data;
  },
  uploadImages: async (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const res = await apiClient.post('/image-to-video/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  uploadAudio: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/image-to-video/upload-audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  previewScene: async (data: any) => {
    const res = await apiClient.post('/image-to-video/preview-scene', data);
    return res.data;
  },
  generateVideo: async (data: any) => {
    const res = await apiClient.post('/image-to-video/generate', data);
    return res.data;
  },
  getJobStatus: async (jobId: number | string) => {
    const res = await apiClient.get(`/image-to-video/status/${jobId}`);
    return res.data;
  },
  getRecentProjects: async () => {
    const res = await apiClient.get('/image-to-video/projects');
    return res.data;
  },
};

export default apiClient;
