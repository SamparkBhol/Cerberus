const API_BASE_URL = 'http://127.0.0.1:8000/api';

const storeTokens = (tokens) => {
  localStorage.setItem('access_token', tokens.access);
  localStorage.setItem('refresh_token', tokens.refresh);
};

const storeUser = (user) => {
  localStorage.setItem('user', JSON.stringify(user));
};

export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

export const isAuthenticated = () => {
  const token = localStorage.getItem('access_token');
  return !!token; 
};

export const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
};

const apiRequest = async (url, method, body = null) => {
  const headers = getAuthHeaders();
  if (!body) {
    delete headers['Content-Type'];
  }

  const config = {
    method: method,
    headers: headers,
    body: body ? JSON.stringify(body) : null
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      if (response.status === 401) {
        logout();
        window.location.href = '/login';
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("API request failed:", error);
    throw error;
  }
};

export const login = async (username, password) => {
  const response = await fetch(`${API_BASE_URL}/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const data = await response.json();
  storeTokens(data);
  storeUser(data.user);
  return data;
};

export const getAlerts = () => {
  return apiRequest(`${API_BASE_URL}/alerts/`, 'GET');
};

export const getStats = () => {
  return apiRequest(`${API_BASE_URL}/stats/`, 'GET');
};

export const startTraining = () => {
  return apiRequest(`${API_BASE_URL}/model/train/`, 'POST');
};

export const getModelStatus = () => {
  return apiRequest(`${API_BASE_URL}/model/status/`, 'GET');
};
