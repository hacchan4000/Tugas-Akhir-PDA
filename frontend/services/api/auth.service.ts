import { User } from '@/model/User';
import { ApiService } from './api.service';

export const AuthService = {
  login: (email: string, password: string): Promise<User> => {
    return ApiService<User>({
      url: '/auth/login',
      method: 'POST',
      body: { email, password },
    });
  },

  logout: (): Promise<void> => {
    return ApiService<void>({
      url: '/auth/logout',
      method: 'POST',
    });
  },

  me: (): Promise<User> => {
    return ApiService<User>({
      url: '/auth/me',
      method: 'GET',
    });
  },
};
