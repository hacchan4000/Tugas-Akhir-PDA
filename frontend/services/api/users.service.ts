import { User } from '@/model/User';
import { ApiService } from './api.service';

export const UsersService = {
  getCurrentOperator: (): Promise<User> => {
    return ApiService<User>({
      url: '/auth/me',
      method: 'GET',
    });
  },
};
