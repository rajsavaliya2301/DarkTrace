import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { watchlistsApi } from '../api/watchlists';
import type { CreateWatchlistRequest, UpdateWatchlistRequest } from '../types';
import toast from 'react-hot-toast';

export function useWatchlists() {
  return useQuery({
    queryKey: ['watchlists'],
    queryFn: () => watchlistsApi.list(),
    refetchInterval: 30000,
  });
}

export function useCreateWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateWatchlistRequest) => watchlistsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
      toast.success('Watchlist created');
    },
    onError: () => {
      toast.error('Failed to create watchlist');
    },
  });
}

export function useUpdateWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateWatchlistRequest }) =>
      watchlistsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
      toast.success('Watchlist updated');
    },
    onError: () => {
      toast.error('Failed to update watchlist');
    },
  });
}

export function useDeleteWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => watchlistsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
      toast.success('Watchlist deleted');
    },
    onError: () => {
      toast.error('Failed to delete watchlist');
    },
  });
}
