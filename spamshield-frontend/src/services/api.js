import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.ignaspanavas.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Health check
  health: () => api.get('/health'),

  // Prediction - core functionality
  predict: (text) => api.post('/predict', { text }),

  // Statistics - for dashboard
  getStats: () => api.get('/stats'),

  // EC2 Status
  getEc2Status: () => api.get('/ec2-status'),

  // Bot Status
  getBotStatus: () => api.get('/bot-status'),

  // Model Status
  getModelStatus: () => api.get('/model-status'),

  // Fast Status Summary - new comprehensive endpoint
  getStatusSummary: () => api.get('/status-summary'),
  getFastStatusSummary: () => api.get('/fast/status-summary'),

  // Uptime history (proxied via API Gateway to EC2 health server)
  getUptimeHistory: (params = {}) => api.get('/uptime-history', { params }),
  postUptimeRecord: ({ service, status, details }) => api.post('/uptime-history', { service, status, details }),
};

export default apiService;
