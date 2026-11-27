'use client';

import React, { createContext, useCallback, useEffect, useState } from 'react';
import { showToast } from '@/app/components/atoms/toast';
import { useAuth } from '@/hooks/useAuth';
import { HealthResponse, MetaOptions, ModelInfo } from '@/model/ModelInfo';
import {
  HistoryFilters,
  PredictionCreate,
  PredictionRead,
} from '@/model/Prediction';
import { MetaService } from '@/services/api/meta.service';
import { PredictionsService } from '@/services/api/predictions.service';
import { getErrorMessage } from '@/utils/handleError';

interface HistContextProps {
  items: PredictionRead[];
  total: number;
  page: number;
  pageSize: number;
  pages: number;
  filters: HistoryFilters;
  loadingHistory: boolean;
  submittingPrediction: boolean;
  exportingCsv: boolean;
  detailLoading: boolean;
  latestPrediction: PredictionRead | null;
  selectedPrediction: PredictionRead | null;
  metaOptions: MetaOptions | null;
  modelInfo: ModelInfo | null;
  health: HealthResponse | null;
  loadingMeta: boolean;
  fetchHistory: (overrideFilters?: HistoryFilters) => Promise<void>;
  createPrediction: (payload: PredictionCreate) => Promise<PredictionRead | null>;
  openDetail: (predictionId: number) => Promise<void>;
  closeDetail: () => void;
  exportCsv: () => Promise<void>;
  refreshHealth: () => Promise<void>;
  refreshMetaAndModel: () => Promise<void>;
  setFilters: React.Dispatch<React.SetStateAction<HistoryFilters>>;
}

const DEFAULT_FILTERS: HistoryFilters = {
  page: 1,
  page_size: 10,
  date_from: '',
  date_to: '',
  region: '',
  q: '',
};

const OFFLINE_HEALTH: HealthResponse = {
  status: 'offline',
  database: 'error',
  model_ready: false,
  model_version: null,
  model_error: 'Tidak dapat terhubung ke server backend',
};

export const HistContext = createContext<HistContextProps>({
  items: [],
  total: 0,
  page: 1,
  pageSize: 10,
  pages: 0,
  filters: DEFAULT_FILTERS,
  loadingHistory: false,
  submittingPrediction: false,
  exportingCsv: false,
  detailLoading: false,
  latestPrediction: null,
  selectedPrediction: null,
  metaOptions: null,
  modelInfo: null,
  health: null,
  loadingMeta: false,
  fetchHistory: async () => {},
  createPrediction: async () => null,
  openDetail: async () => {},
  closeDetail: () => {},
  exportCsv: async () => {},
  refreshHealth: async () => {},
  refreshMetaAndModel: async () => {},
  setFilters: () => {},
});

export const HistProvider = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();

  const [items, setItems] = useState<PredictionRead[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [pages, setPages] = useState(0);
  const [filters, setFilters] = useState<HistoryFilters>(DEFAULT_FILTERS);

  const [loadingHistory, setLoadingHistory] = useState(false);
  const [submittingPrediction, setSubmittingPrediction] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [loadingMeta, setLoadingMeta] = useState(false);

  const [latestPrediction, setLatestPrediction] = useState<PredictionRead | null>(null);
  const [selectedPrediction, setSelectedPrediction] = useState<PredictionRead | null>(null);
  const [metaOptions, setMetaOptions] = useState<MetaOptions | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const refreshHealth = useCallback(async () => {
    try {
      const data = await MetaService.getHealth();
      setHealth(data);
    } catch {
      setHealth(OFFLINE_HEALTH);
    }
  }, []);

  const refreshMetaAndModel = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoadingMeta(true);
    try {
      const [optionsRes, modelRes] = await Promise.all([
        MetaService.getOptions(),
        MetaService.getModelInfo(),
      ]);
      setMetaOptions(optionsRes);
      setModelInfo(modelRes);
    } catch (error) {
      showToast(getErrorMessage(error), 'warning');
    } finally {
      setLoadingMeta(false);
    }
  }, [isAuthenticated]);

  const fetchHistory = useCallback(
    async (overrideFilters?: HistoryFilters) => {
      if (!isAuthenticated) return;
      const active = overrideFilters ?? filters;
      setLoadingHistory(true);
      try {
        const res = await PredictionsService.list(active);
        setItems(res.items);
        setTotal(res.total);
        setPage(res.page);
        setPageSize(res.page_size);
        setPages(res.pages);
      } catch (error) {
        showToast(getErrorMessage(error), 'error');
      } finally {
        setLoadingHistory(false);
      }
    },
    [isAuthenticated, filters]
  );

  const createPrediction = useCallback(
    async (payload: PredictionCreate): Promise<PredictionRead | null> => {
      setSubmittingPrediction(true);
      try {
        const created = await PredictionsService.create(payload);
        setLatestPrediction(created);
        showToast(
          `Prediksi selesai: ${created.predicted_class.toUpperCase()} (Prioritas SAR: ${created.sar_priority_level})`,
          'success'
        );
        const resetPageFilters = { ...filters, page: 1 };
        setFilters(resetPageFilters);
        await fetchHistory(resetPageFilters);
        return created;
      } catch (error) {
        showToast(getErrorMessage(error), 'error');
        return null;
      } finally {
        setSubmittingPrediction(false);
      }
    },
    [filters, fetchHistory]
  );

  const openDetail = useCallback(async (predictionId: number) => {
    setDetailLoading(true);
    try {
      const detail = await PredictionsService.getById(predictionId);
      setSelectedPrediction(detail);
    } catch (error) {
      showToast(getErrorMessage(error), 'error');
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const closeDetail = useCallback(() => {
    setSelectedPrediction(null);
  }, []);

  const exportCsv = useCallback(async () => {
    setExportingCsv(true);
    try {
      await PredictionsService.exportCsv(filters);
      showToast('File CSV riwayat prediksi berhasil diunduh', 'success');
    } catch (error) {
      showToast(getErrorMessage(error), 'error');
    } finally {
      setExportingCsv(false);
    }
  }, [filters]);

  useEffect(() => {
    let active = true;
    MetaService.getHealth()
      .then((data) => {
        if (active) setHealth(data);
      })
      .catch(() => {
        if (active) setHealth(OFFLINE_HEALTH);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;

    Promise.all([MetaService.getOptions(), MetaService.getModelInfo()])
      .then(([optionsRes, modelRes]) => {
        if (!active) return;
        setMetaOptions(optionsRes);
        setModelInfo(modelRes);
      })
      .catch((error) => {
        if (active) showToast(getErrorMessage(error), 'warning');
      });

    PredictionsService.list(DEFAULT_FILTERS)
      .then((res) => {
        if (!active) return;
        setItems(res.items);
        setTotal(res.total);
        setPage(res.page);
        setPageSize(res.page_size);
        setPages(res.pages);
      })
      .catch((error) => {
        if (active) showToast(getErrorMessage(error), 'error');
      });

    return () => {
      active = false;
    };
  }, [isAuthenticated]);

  return (
    <HistContext.Provider
      value={{
        items: isAuthenticated ? items : [],
        total: isAuthenticated ? total : 0,
        page: isAuthenticated ? page : 1,
        pageSize: isAuthenticated ? pageSize : 10,
        pages: isAuthenticated ? pages : 0,
        filters,
        loadingHistory: isAuthenticated ? loadingHistory : false,
        submittingPrediction,
        exportingCsv,
        detailLoading,
        latestPrediction: isAuthenticated ? latestPrediction : null,
        selectedPrediction: isAuthenticated ? selectedPrediction : null,
        metaOptions: isAuthenticated ? metaOptions : null,
        modelInfo: isAuthenticated ? modelInfo : null,
        health,
        loadingMeta: isAuthenticated ? loadingMeta : false,
        fetchHistory,
        createPrediction,
        openDetail,
        closeDetail,
        exportCsv,
        refreshHealth,
        refreshMetaAndModel,
        setFilters,
      }}
    >
      {children}
    </HistContext.Provider>
  );
};
