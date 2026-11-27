'use client';

import { getErrorMessage } from '@/utils/handleError';

export interface FieldErrorItem {
  field: string;
  message: string;
}

export class ApiError extends Error {
  status: number;
  fieldErrors: FieldErrorItem[];

  constructor(message: string, status = 500, fieldErrors: FieldErrorItem[] = []) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

interface RequestProps {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  params?: Record<string, string | number | undefined | null>;
}

export const DefaultHeaders: Record<string, string> = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
};

export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  return raw.replace(/\/+$/, '');
}

export function buildApiUrl(
  path: string,
  params?: Record<string, string | number | undefined | null>
): string {
  const baseUrl = getApiBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const apiPath = normalizedPath.startsWith('/api/')
    ? normalizedPath
    : `/api/v1${normalizedPath}`;

  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && String(value).trim() !== '') {
        searchParams.set(key, String(value));
      }
    });
  }

  const qs = searchParams.toString();
  return `${baseUrl}${apiPath}${qs ? `?${qs}` : ''}`;
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    // Non-JSON error body
  }

  if (payload && typeof payload === 'object') {
    const obj = payload as Record<string, unknown>;
    if (Array.isArray(obj.detail)) {
      const fieldErrors: FieldErrorItem[] = obj.detail
        .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
        .map((item) => ({
          field: String(item.field ?? 'body'),
          message: String(item.message ?? 'Nilai tidak valid'),
        }));

      const message =
        fieldErrors.length > 0
          ? fieldErrors.map((e) => `${e.field}: ${e.message}`).join('; ')
          : 'Validasi gagal';

      return new ApiError(message, response.status, fieldErrors);
    }

    if (typeof obj.detail === 'string') {
      return new ApiError(obj.detail, response.status);
    }

    if (typeof obj.message === 'string') {
      return new ApiError(obj.message, response.status);
    }
  }

  return new ApiError(
    `Permintaan gagal (HTTP ${response.status})`,
    response.status
  );
}

export const ApiService = async <T = unknown>({
  url,
  method = 'GET',
  body,
  headers = {},
  params,
}: RequestProps): Promise<T> => {
  try {
    const fullUrl = buildApiUrl(url, params);
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

    const response = await fetch(fullUrl, {
      method,
      credentials: 'include',
      headers: {
        ...(isFormData ? { Accept: 'application/json' } : DefaultHeaders),
        ...headers,
      },
      ...(body !== undefined && {
        body: isFormData ? (body as FormData) : JSON.stringify(body),
      }),
    });

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      return (await response.text()) as unknown as T;
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(getErrorMessage(error), 0);
  }
};

export const ApiDownload = async (
  url: string,
  params?: Record<string, string | number | undefined | null>
): Promise<{ blob: Blob; filename: string }> => {
  const fullUrl = buildApiUrl(url, params);
  const response = await fetch(fullUrl, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename="?([^"]+)"?/i);
  const filename = match?.[1] || 'riwayat_prediksi.csv';
  const blob = await response.blob();
  return { blob, filename };
};
