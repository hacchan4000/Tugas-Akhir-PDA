export interface CoordinateBounds {
  latitude: [number, number];
  longitude: [number, number];
}

export interface ValidCategories {
  landslide_category: string[];
  landslide_trigger: string[];
  landslide_setting: string[];
  location_accuracy: string[];
  [key: string]: string[];
}

export interface MetaOptions {
  valid_categories: ValidCategories;
  coordinate_bounds: CoordinateBounds;
  class_labels: string[];
  max_event_date: string;
}

export interface PerClassMetric {
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface EvaluationMetrics {
  macro_f1: number;
  balanced_accuracy: number;
  accuracy: number;
  precision_macro: number;
  recall_macro: number;
  confusion_matrix: number[][];
  labels: string[];
  per_class: Record<string, PerClassMetric>;
}

export interface ComparatorInfo {
  model_name: string;
  best_params?: Record<string, unknown>;
  mean_test_macro_f1?: number;
  artifact_file?: string;
}

export interface ModelInfo {
  model_id: number | null;
  model_name: string;
  model_version: string;
  trained_date: string | null;
  best_params: Record<string, unknown>;
  d_enc: number;
  class_labels: string[];
  evaluation_metrics: EvaluationMetrics | null;
  comparator_info: ComparatorInfo | null;
}

export interface HealthResponse {
  status: string;
  database: string;
  model_ready: boolean;
  model_version: string | null;
  model_error: string | null;
}
