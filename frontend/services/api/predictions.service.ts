import {
  HistoryFilters,
  HistoryPage,
  PredictionCreate,
  PredictionRead,
} from '@/model/Prediction';
import { ApiDownload, ApiService } from './api.service';

export const PredictionsService = {
  create: (payload: PredictionCreate): Promise<PredictionRead> => {
    return ApiService<PredictionRead>({
      url: '/predictions',
      method: 'POST',
      body: payload,
    });
  },

  list: (filters: HistoryFilters = {}): Promise<HistoryPage> => {
    return ApiService<HistoryPage>({
      url: '/predictions',
      method: 'GET',
      params: {
        page: filters.page ?? 1,
        page_size: filters.page_size ?? 10,
        date_from: filters.date_from,
        date_to: filters.date_to,
        region: filters.region,
        q: filters.q,
      },
    });
  },

  getById: (predictionId: number): Promise<PredictionRead> => {
    return ApiService<PredictionRead>({
      url: `/predictions/${predictionId}`,
      method: 'GET',
    });
  },

  exportCsv: async (filters: HistoryFilters = {}): Promise<void> => {
    const { blob, filename } = await ApiDownload('/predictions/export', {
      date_from: filters.date_from,
      date_to: filters.date_to,
      region: filters.region,
      q: filters.q,
    });

    const objectUrl = URL.createObjectURL(blob);
    try {
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      URL.revokeObjectURL(objectUrl);
    }
  },
};
