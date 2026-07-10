import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/dashboard';

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: () => dashboardApi.getSummary(),
    refetchInterval: 30000,
  });
}

export function useTrendingData(days: number = 7) {
  return useQuery({
    queryKey: ['trendingData', days],
    queryFn: () => dashboardApi.getTrending(days),
    refetchInterval: 60000,
  });
}
