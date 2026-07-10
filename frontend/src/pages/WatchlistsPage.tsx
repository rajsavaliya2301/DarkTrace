import { useState } from 'react';
import { Plus } from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import WatchlistList from '../components/watchlists/WatchlistList';
import WatchlistForm from '../components/watchlists/WatchlistForm';
import { useWatchlists, useCreateWatchlist } from '../hooks/useWatchlists';
import type { CreateWatchlistRequest } from '../types';

export default function WatchlistsPage() {
  const [showForm, setShowForm] = useState(false);
  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useWatchlists();
  const createWatchlist = useCreateWatchlist();

  const handleCreate = (formData: CreateWatchlistRequest) => {
    createWatchlist.mutate(formData, {
      onSuccess: () => setShowForm(false),
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Watchlists"
        subtitle="Manage keyword and pattern watchlists for threat detection"
      >
        <button
          onClick={() => setShowForm(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Create Watchlist
        </button>
      </PageHeader>

      <WatchlistList
        watchlists={data?.data}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
      />

      {showForm && (
        <WatchlistForm
          onSubmit={handleCreate}
          onCancel={() => setShowForm(false)}
          isLoading={createWatchlist.isPending}
        />
      )}
    </div>
  );
}
