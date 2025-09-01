import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://qtwso5m6o6.execute-api.us-east-1.amazonaws.com/prod';

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
  health: () => api.get('/api/health'),

  // Prediction - core functionality
  predict: (text) => api.post('/api/predict', { text }),

  // Statistics - for dashboard
  getStats: () => api.get('/api/stats'),
};

export default apiService;
