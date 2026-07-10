import { useState, useCallback } from 'react';
import PageHeader from '../components/common/PageHeader';
import ActorList from '../components/actors/ActorList';
import { useActors } from '../hooks/useActors';
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates';
import { toast } from 'react-hot-toast';

export default function ActorsPage() {
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('risk_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [search, setSearch] = useState('');

  const params = {
    page,
    per_page: 25,
    q: search || undefined,
    sort_by: sortBy,
  };

  const { data, isLoading, isError, refetch } = useActors(params);

  // Real-time actor updates
  useRealtimeUpdates({
    channels: 'actor',
    onActor: (event) => {
      const action = event.action as string;
      if (action === 'new_actor') {
        toast(`👤 New actor identified: ${event.name || 'Unknown'}`, {
          duration: 4000,
          style: { background: '#1f2937', color: '#f9fafb' },
        });
      }
      // Auto-refresh on first page
      if (page === 1) {
        refetch();
      }
    },
  });

  const handleSort = useCallback(
    (key: string) => {
      if (sortBy === key) {
        setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
      } else {
        setSortBy(key);
        setSortOrder('desc');
      }
      setPage(1);
    },
    [sortBy, sortOrder]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Threat Actors"
        subtitle={`${data?.pagination?.total?.toLocaleString() || 0} tracked actors`}
      >
        <div className="relative">
          <input
            type="text"
            placeholder="Search actors..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-64 rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            aria-label="Search actors"
          />
        </div>
      </PageHeader>

      <ActorList
        actors={data?.data}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.pagination?.total_pages || 1}
        onPageChange={setPage}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSort={handleSort}
      />
    </div>
  );
}
