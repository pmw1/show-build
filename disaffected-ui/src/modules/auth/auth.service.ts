import axios from 'axios';
import type { LoginCredentials, AuthResponse } from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await axios.post(`${API_URL}/auth/login`, credentials);
    
    if (response.data.token) {
      // Store token in localStorage
      localStorage.setItem('auth-token', response.data.token);
      // Set default auth header for future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
    }
    
    return response.data;
  }

  logout(): void {
    localStorage.removeItem('auth-token');
    delete axios.defaults.headers.common['Authorization'];
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth-token');
  }
}

export default new AuthService();