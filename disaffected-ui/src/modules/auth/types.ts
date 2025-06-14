export interface User {
  id: number;
  username: string;
  accessLevel: 'admin' | 'user' | 'guest';
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}