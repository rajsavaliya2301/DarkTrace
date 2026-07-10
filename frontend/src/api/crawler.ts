import apiClient from './client';
import type {
  CrawlTarget,
  AddTargetRequest,
  AddTargetResponse,
  TriggerCrawlResponse,
  CrawlJobsResponse,
  CrawlJob,
} from '../types';

export const crawlerApi = {
  listTargets: async (): Promise<{ data: CrawlTarget[] }> => {
    const response = await apiClient.get('/crawler/targets');
    return response.data;
  },

  addTarget: async (data: AddTargetRequest): Promise<AddTargetResponse> => {
    const response = await apiClient.post<AddTargetResponse>('/crawler/targets', data);
    return response.data;
  },

  triggerCrawl: async (targetId: string): Promise<TriggerCrawlResponse> => {
    const response = await apiClient.post<TriggerCrawlResponse>(`/crawler/targets/${targetId}/crawl`);
    return response.data;
  },

  listJobs: async (params?: {
    status?: string;
    target_id?: string;
    page?: number;
    per_page?: number;
  }): Promise<CrawlJobsResponse> => {
    const response = await apiClient.get<CrawlJobsResponse>('/crawler/jobs', { params });
    return response.data;
  },

  getJob: async (jobId: string): Promise<CrawlJob> => {
    const response = await apiClient.get<CrawlJob>(`/crawler/jobs/${jobId}`);
    return response.data;
  },
};
