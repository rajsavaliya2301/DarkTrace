import { useQuery } from '@tanstack/react-query';
import { searchApi } from '../api/search';
import type { SearchRequest } from '../types';

export function useSearch(params: SearchRequest) {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => searchApi.search(params),
    enabled: !!params.q && params.q.length >= 2,
    staleTime: 30000,
  });
}
