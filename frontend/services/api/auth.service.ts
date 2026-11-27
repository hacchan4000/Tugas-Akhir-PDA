import { RegisterProps } from '@/model/Auth';
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

  register: (payload: RegisterProps): Promise<User> => {
    return ApiService<User>({
      url: '/auth/register',
      method: 'POST',
      body: payload,
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
