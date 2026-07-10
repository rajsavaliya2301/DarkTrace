import apiClient from './client';
import type {
  SearchRequest,
  SearchResponse,
  CreateSavedSearchRequest,
  SavedSearch,
} from '../types';

export const searchApi = {
  search: async (params: SearchRequest): Promise<SearchResponse> => {
    const response = await apiClient.get<SearchResponse>('/search', { params });
    return response.data;
  },

  saveSearch: async (data: CreateSavedSearchRequest): Promise<SavedSearch> => {
    const response = await apiClient.post<{data: SavedSearch}>('/search/saved', data);
    return response.data.data;
  },

  getSavedSearches: async (): Promise<{data: SavedSearch[]; pagination: any}> => {
    const response = await apiClient.get<{data: SavedSearch[]; pagination: any}>('/search/saved');
    return response.data;
  },

  deleteSavedSearch: async (id: string): Promise<void> => {
    await apiClient.delete(`/search/saved/${id}`);
  },

  generateReportFromSavedSearch: async (id: string): Promise<{ report_id: string }> => {
    const response = await apiClient.post<{report_id: string; status: string}>(`/search/saved/${id}/generate-report`);
    return response.data;
  },
};
