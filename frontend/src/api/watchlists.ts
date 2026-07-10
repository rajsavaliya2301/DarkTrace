import apiClient from './client';
import type {
  Watchlist,
  CreateWatchlistRequest,
  CreateWatchlistResponse,
  UpdateWatchlistRequest,
  UpdateWatchlistResponse,
} from '../types';

export const watchlistsApi = {
  list: async (): Promise<{ data: Watchlist[] }> => {
    const response = await apiClient.get('/watchlists');
    return response.data;
  },

  create: async (data: CreateWatchlistRequest): Promise<CreateWatchlistResponse> => {
    const response = await apiClient.post<CreateWatchlistResponse>('/watchlists', data);
    return response.data;
  },

  update: async (id: string, data: UpdateWatchlistRequest): Promise<UpdateWatchlistResponse> => {
    const response = await apiClient.put<UpdateWatchlistResponse>(`/watchlists/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/watchlists/${id}`);
  },
};
