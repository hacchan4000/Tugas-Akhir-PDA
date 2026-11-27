export type PredictedClass = 'small' | 'medium' | 'large';

export interface PredictionCreate {
  event_date: string; // YYYY-MM-DD
  latitude: number;
  longitude: number;
  landslide_category: string;
  landslide_trigger: string;
  landslide_setting: string;
  location_accuracy: string;
}

export interface PredictionRead {
  prediction_id: number;
  input_id: number;
  event_date: string;
  latitude: number;
  longitude: number;
  nama_wilayah: string | null;
  geocoding_status: string;
  landslide_category: string;
  landslide_trigger: string;
  landslide_setting: string;
  location_accuracy: string;
  predicted_class: PredictedClass;
  confidence_score: number;
  probabilities: Record<string, number>;
  sar_priority_level: string;
  sar_recommendation: string;
  status: string;
  prediction_date: string;
  model_name: string;
  model_version: string;
}

export interface HistoryPage {
  items: PredictionRead[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface HistoryFilters {
  page?: number;
  page_size?: number;
  date_from?: string;
  date_to?: string;
  region?: string;
  q?: string;
}
