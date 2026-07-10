import apiClient from './client';
import type { Actor, ActorDetail } from '../types';

export interface ActorsQueryParams {
  page?: number;
  per_page?: number;
  risk_score_min?: number;
  q?: string;
  sort_by?: string;
}

export const actorsApi = {
  list: async (params?: ActorsQueryParams): Promise<{ data: Actor[]; pagination: { page: number; per_page: number; total: number; total_pages: number } }> => {
    const response = await apiClient.get('/actors', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ActorDetail> => {
    const response = await apiClient.get<ActorDetail>(`/actors/${id}`);
    return response.data;
  },

  search: async (q: string): Promise<{ data: Actor[] }> => {
    const response = await apiClient.get('/actors/search', { params: { q } });
    return response.data;
  },
};
