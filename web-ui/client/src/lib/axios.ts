import axios from 'axios';

// Create axios instance with base url and credentials support
export const apiRequest = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Add a request interceptor to include auth token if available
apiRequest.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle common errors
// In your API client (axios.ts):
apiRequest.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token invalid or expired
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    } else if (error.response?.status === 423) {
      // Account locked
      alert('Account temporarily locked due to security concerns');
    } else if (error.response?.status === 429) {
      // Rate limited
      alert('Too many requests. Please try again later.');
    }
    return Promise.reject(error);
  }
);

export default apiRequest;
