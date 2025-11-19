import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add session ID if available
    const sessionId = localStorage.getItem('session_id');
    if (sessionId) {
      config.headers['X-Session-ID'] = sessionId;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Text query
export const queryText = async (queryText, filters = {}, maxResults = 10) => {
  const response = await api.post('/api/query/text', {
    query_text: queryText,
    query_type: 'text',
    filters,
    max_results: maxResults,
  });
  return response.data;
};

// Image query
export const queryImage = async (imageFile, queryText = null, maxResults = 10) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  if (queryText) {
    formData.append('query_text', queryText);
  }
  formData.append('max_results', maxResults);

  const response = await api.post('/api/query/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Voice query
export const queryVoice = async (audioBlob, maxResults = 10) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.wav');
  formData.append('max_results', maxResults);

  const response = await api.post('/api/query/voice', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Multimodal query
export const queryMultimodal = async (data) => {
  const formData = new FormData();
  
  if (data.queryText) {
    formData.append('query_text', data.queryText);
  }
  if (data.imageFile) {
    formData.append('image', data.imageFile);
  }
  if (data.audioBlob) {
    formData.append('audio', data.audioBlob, 'recording.wav');
  }
  formData.append('max_results', data.maxResults || 10);

  const response = await api.post('/api/query/multimodal', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Get product details
export const getProduct = async (productId) => {
  const response = await api.get(`/api/products/${productId}`);
  return response.data;
};

// Get product reviews
export const getProductReviews = async (productId, limit = 10) => {
  const response = await api.get(`/api/products/${productId}/reviews`, {
    params: { limit },
  });
  return response.data;
};

// Get product prices
export const getProductPrices = async (productId) => {
  const response = await api.get(`/api/products/${productId}/prices`);
  return response.data;
};

// Get recommendations
export const getRecommendations = async (userId = null, sessionId = null, limit = 10) => {
  const response = await api.get('/api/recommendations', {
    params: { user_id: userId, session_id: sessionId, limit },
  });
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
