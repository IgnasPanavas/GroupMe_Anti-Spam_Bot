import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

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

  // Prediction
  predict: (text) => api.post('/predict', { text }),

  // Statistics
  getStats: () => api.get('/stats'),

  // Groups
  getGroups: () => api.get('/groups'),

  // Activity
  getActivity: () => api.get('/activity'),

  // Settings
  getSettings: () => api.get('/settings'),
  updateSettings: (settings) => api.post('/settings', settings),

  // Test predictions
  testPredictions: () => api.get('/test'),
};

export default apiService;
