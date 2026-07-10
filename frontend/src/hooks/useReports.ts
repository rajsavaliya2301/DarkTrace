import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportsApi } from '../api/reports';
import type { GenerateReportRequest } from '../types';
import toast from 'react-hot-toast';

export function useReports(params?: { page?: number; per_page?: number; type?: string }) {
  return useQuery({
    queryKey: ['reports', params],
    queryFn: () => reportsApi.list(params),
    refetchInterval: 15000,
  });
}

export function useReportDetail(id: string) {
  return useQuery({
    queryKey: ['report', id],
    queryFn: () => reportsApi.getById(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'generating') return 5000;
      return false;
    },
  });
}

export function useGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GenerateReportRequest) => reportsApi.generate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast.success('Report generation started');
    },
    onError: () => {
      toast.error('Failed to generate report');
    },
  });
}

export function useDeleteReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => reportsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast.success('Report deleted');
    },
    onError: () => {
      toast.error('Failed to delete report');
    },
  });
}
