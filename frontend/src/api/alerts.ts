import apiClient from './client';
import type {
  AlertsResponse,
  AlertDetail,
  AlertUpdateRequest,
  AlertUpdateResponse,
  BulkAlertRequest,
  BulkAlertResponse,
  AlertStats,
} from '../types';

export interface AlertsQueryParams {
  page?: number;
  per_page?: number;
  severity?: string;
  status?: string;
  category?: string;
  source_type?: string;
  date_from?: string;
  date_to?: string;
  q?: string;
  sort_by?: string;
  sort_order?: string;
}

export const alertsApi = {
  list: async (params?: AlertsQueryParams): Promise<AlertsResponse> => {
    const response = await apiClient.get<AlertsResponse>('/alerts', { params });
    return response.data;
  },

  getById: async (id: string): Promise<AlertDetail> => {
    const response = await apiClient.get<AlertDetail>(`/alerts/${id}`);
    return response.data;
  },

  update: async (id: string, data: AlertUpdateRequest): Promise<AlertUpdateResponse> => {
    const response = await apiClient.patch<AlertUpdateResponse>(`/alerts/${id}`, data);
    return response.data;
  },

  bulkUpdate: async (data: BulkAlertRequest): Promise<BulkAlertResponse> => {
    const response = await apiClient.post<BulkAlertResponse>('/alerts/bulk', data);
    return response.data;
  },

  getStats: async (params?: { date_from?: string; date_to?: string; granularity?: string }): Promise<AlertStats> => {
    const response = await apiClient.get<AlertStats>('/alerts/stats', { params });
    return response.data;
  },
};
