import { useQuery } from '@tanstack/react-query';
import { actorsApi, type ActorsQueryParams } from '../api/actors';

export function useActors(params?: ActorsQueryParams) {
  return useQuery({
    queryKey: ['actors', params],
    queryFn: () => actorsApi.list(params),
    refetchInterval: 60000,
  });
}

export function useActorDetail(id: string) {
  return useQuery({
    queryKey: ['actor', id],
    queryFn: () => actorsApi.getById(id),
    enabled: !!id,
  });
}
