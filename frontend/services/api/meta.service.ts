import { HealthResponse, MetaOptions, ModelInfo } from '@/model/ModelInfo';
import { ApiService } from './api.service';

export const MetaService = {
  getOptions: (): Promise<MetaOptions> => {
    return ApiService<MetaOptions>({
      url: '/meta/options',
      method: 'GET',
    });
  },

  getModelInfo: (): Promise<ModelInfo> => {
    return ApiService<ModelInfo>({
      url: '/model/info',
      method: 'GET',
    });
  },

  getHealth: (): Promise<HealthResponse> => {
    return ApiService<HealthResponse>({
      url: '/health',
      method: 'GET',
    });
  },
};
