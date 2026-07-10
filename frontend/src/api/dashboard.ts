import apiClient from './client';
import type { DashboardSummary, TrendingData } from '../types';

export const dashboardApi = {
  getSummary: async (): Promise<DashboardSummary> => {
    const response = await apiClient.get<DashboardSummary>('/dashboard/summary');
    return response.data;
  },

  getTrending: async (days: number = 7): Promise<TrendingData> => {
    const response = await apiClient.get<TrendingData>('/dashboard/trending', {
      params: { days },
    });
    return response.data;
  },
};
