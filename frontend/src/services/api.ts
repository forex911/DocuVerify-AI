import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMsg =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected network error occurred';
    console.error('API Error:', errorMsg, error.response?.status);
    return Promise.reject(new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg)));
  }
);

