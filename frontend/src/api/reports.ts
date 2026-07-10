import apiClient from './client';
import type {
  GenerateReportRequest,
  GenerateReportResponse,
  Report,
  ReportDetail,
} from '../types';

export const reportsApi = {
  generate: async (data: GenerateReportRequest): Promise<GenerateReportResponse> => {
    const response = await apiClient.post<GenerateReportResponse>('/reports', data);
    return response.data;
  },

  generateFromSearch: async (data: { query: string; format: string; include_evidence: boolean }): Promise<GenerateReportResponse> => {
    const response = await apiClient.post<GenerateReportResponse>('/reports/from-search', data);
    return response.data;
  },

  list: async (params?: { page?: number; per_page?: number; type?: string }): Promise<{ data: Report[]; pagination: { page: number; per_page: number; total: number; total_pages: number } }> => {
    const response = await apiClient.get('/reports', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ReportDetail> => {
    const response = await apiClient.get<ReportDetail>(`/reports/${id}`);
    return response.data;
  },

  getDownloadUrl: async (id: string): Promise<string> => {
    const report = await reportsApi.getById(id);
    return report.download_url;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/reports/${id}`);
  },
};
