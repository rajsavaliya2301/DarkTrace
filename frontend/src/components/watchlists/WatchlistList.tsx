import { useState } from 'react';
import { Edit, Trash2, Plus, ToggleLeft, ToggleRight } from 'lucide-react';
import DataTable, { type Column } from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import ConfirmDialog from '../common/ConfirmDialog';
import { formatDate } from '../../utils/formatters';
import type { Watchlist, CreateWatchlistRequest } from '../../types';
import type { SeverityLevel } from '../../utils/constants';
import WatchlistForm from './WatchlistForm';
import {
  useCreateWatchlist,
  useUpdateWatchlist,
  useDeleteWatchlist,
} from '../../hooks/useWatchlists';

interface WatchlistListProps {
  watchlists: Watchlist[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
}

export default function WatchlistList({
  watchlists,
  isLoading,
  isError,
  onRetry,
}: WatchlistListProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingWatchlist, setEditingWatchlist] = useState<Watchlist | null>(
    null
  );
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const createWatchlist = useCreateWatchlist();
  const updateWatchlist = useUpdateWatchlist();
  const deleteWatchlist = useDeleteWatchlist();

  const handleCreate = (data: CreateWatchlistRequest) => {
    createWatchlist.mutate(data, {
      onSuccess: () => setShowForm(false),
    });
  };

  const handleUpdate = (data: CreateWatchlistRequest) => {
    if (!editingWatchlist) return;
    updateWatchlist.mutate(
      { id: editingWatchlist.id, data },
      {
        onSuccess: () => {
          setEditingWatchlist(null);
        },
      }
    );
  };

  const handleToggleActive = (wl: Watchlist) => {
    updateWatchlist.mutate({
      id: wl.id,
      data: { is_active: !wl.is_active },
    });
  };

  const handleDelete = () => {
    if (!deletingId) return;
    deleteWatchlist.mutate(deletingId, {
      onSuccess: () => setDeletingId(null),
    });
  };

  const getSeverityForBoost = (boost: number): SeverityLevel => {
    if (boost >= 300) return 'critical';
    if (boost >= 200) return 'high';
    if (boost >= 100) return 'medium';
    return 'low';
  };

  const columns: Column<Watchlist>[] = [
    {
      key: 'name',
      header: 'Name',
      render: (wl) => (
        <div>
          <p className="text-sm font-medium text-gray-200">{wl.name}</p>
          {wl.description && (
            <p className="text-xs text-gray-500 truncate max-w-xs">
              {wl.description}
            </p>
          )}
        </div>
      ),
    },
    {
      key: 'keywords',
      header: 'Keywords',
      render: (wl) => (
        <div className="flex flex-wrap gap-1 max-w-xs">
          {wl.keywords.slice(0, 4).map((kw) => (
            <span
              key={kw}
              className="rounded bg-blue-500/10 px-1.5 py-0.5 text-xs text-blue-400"
            >
              {kw}
            </span>
          ))}
          {wl.keywords.length > 4 && (
            <span className="text-xs text-gray-500">
              +{wl.keywords.length - 4}
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'severity_boost',
      header: 'Boost',
      width: '80px',
      render: (wl) => (
        <StatusBadge severity={getSeverityForBoost(wl.severity_boost)} />
      ),
    },
    {
      key: 'match_count',
      header: 'Matches',
      width: '80px',
      hideOnMobile: true,
      render: (wl) => (
        <span className="text-sm text-gray-300">
          {wl.match_count.toLocaleString()}
        </span>
      ),
    },
    {
      key: 'is_active',
      header: 'Status',
      width: '80px',
      render: (wl) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleToggleActive(wl);
          }}
          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
            wl.is_active
              ? 'bg-emerald-500/20 text-emerald-400'
              : 'bg-gray-500/20 text-gray-400'
          }`}
        >
          {wl.is_active ? (
            <ToggleRight className="h-3 w-3" />
          ) : (
            <ToggleLeft className="h-3 w-3" />
          )}
          {wl.is_active ? 'Active' : 'Inactive'}
        </button>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '80px',
      render: (wl) => (
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setEditingWatchlist(wl);
            }}
            className="rounded p-1 text-gray-500 hover:text-gray-300"
            aria-label="Edit watchlist"
          >
            <Edit className="h-4 w-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setDeletingId(wl.id);
            }}
            className="rounded p-1 text-gray-500 hover:text-red-400"
            aria-label="Delete watchlist"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <>
      <DataTable
        columns={columns}
        data={watchlists || []}
        keyExtractor={(wl) => wl.id}
        isLoading={isLoading}
        isError={isError}
        onRetry={onRetry}
        emptyTitle="No watchlists"
        emptyMessage="Create your first watchlist to start monitoring for specific keywords."
        emptyAction={{
          label: 'Create Watchlist',
          onClick: () => setShowForm(true),
        }}
      />

      {showForm && (
        <WatchlistForm
          onSubmit={handleCreate}
          onCancel={() => setShowForm(false)}
          isLoading={createWatchlist.isPending}
        />
      )}

      {editingWatchlist && (
        <WatchlistForm
          onSubmit={handleUpdate}
          onCancel={() => setEditingWatchlist(null)}
          initialData={editingWatchlist}
          isLoading={updateWatchlist.isPending}
        />
      )}

      <ConfirmDialog
        isOpen={!!deletingId}
        onClose={() => setDeletingId(null)}
        onConfirm={handleDelete}
        title="Delete Watchlist"
        message="Are you sure you want to delete this watchlist? This action cannot be undone."
        confirmLabel="Delete"
        isLoading={deleteWatchlist.isPending}
      />
    </>
  );
}
