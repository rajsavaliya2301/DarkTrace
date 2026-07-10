import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { crawlerApi } from '../api/crawler';
import type { AddTargetRequest } from '../types';
import toast from 'react-hot-toast';

export function useCrawlTargets() {
  return useQuery({
    queryKey: ['crawlTargets'],
    queryFn: () => crawlerApi.listTargets(),
    refetchInterval: 30000,
  });
}

export function useAddTarget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AddTargetRequest) => crawlerApi.addTarget(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crawlTargets'] });
      toast.success('Crawl target added');
    },
    onError: () => {
      toast.error('Failed to add crawl target');
    },
  });
}

export function useTriggerCrawl() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (targetId: string) => crawlerApi.triggerCrawl(targetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crawlJobs'] });
      queryClient.invalidateQueries({ queryKey: ['crawlTargets'] });
      toast.success('Crawl triggered');
    },
    onError: () => {
      toast.error('Failed to trigger crawl');
    },
  });
}

export function useCrawlJobs(params?: { status?: string; target_id?: string; page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ['crawlJobs', params],
    queryFn: () => crawlerApi.listJobs(params),
    refetchInterval: 15000,
  });
}

export function useCrawlJob(jobId: string) {
  return useQuery({
    queryKey: ['crawlJob', jobId],
    queryFn: () => crawlerApi.getJob(jobId),
    enabled: !!jobId,
    refetchInterval: 10000,
  });
}
