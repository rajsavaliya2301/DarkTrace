import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertsApi, type AlertsQueryParams } from '../api/alerts';
import type { AlertUpdateRequest, BulkAlertRequest } from '../types';
import toast from 'react-hot-toast';

export function useAlerts(params?: AlertsQueryParams) {
  return useQuery({
    queryKey: ['alerts', params],
    queryFn: () => alertsApi.list(params),
    refetchInterval: 30000,
  });
}

export function useAlertDetail(id: string) {
  return useQuery({
    queryKey: ['alert', id],
    queryFn: () => alertsApi.getById(id),
    enabled: !!id,
  });
}

export function useUpdateAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AlertUpdateRequest }) =>
      alertsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alert', variables.id] });
      toast.success('Alert updated successfully');
    },
    onError: () => {
      toast.error('Failed to update alert');
    },
  });
}

export function useBulkAlertUpdate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BulkAlertRequest) => alertsApi.bulkUpdate(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      toast.success(response.message);
    },
    onError: () => {
      toast.error('Failed to bulk update alerts');
    },
  });
}

export function useAlertStats(params?: { date_from?: string; date_to?: string; granularity?: string }) {
  return useQuery({
    queryKey: ['alertStats', params],
    queryFn: () => alertsApi.getStats(params),
    refetchInterval: 60000,
  });
}
