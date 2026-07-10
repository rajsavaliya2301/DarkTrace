import { useNavigate } from 'react-router-dom';
import DataTable, { type Column } from '../common/DataTable';
import { formatDate } from '../../utils/formatters';
import type { Actor } from '../../types';

interface ActorListProps {
  actors: Actor[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (key: string) => void;
}

const riskBadge = (score: number) => {
  if (score >= 700)
    return 'bg-red-500/20 text-red-400 border-red-500/30';
  if (score >= 500)
    return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
  if (score >= 300)
    return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
  return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
};

export default function ActorList({
  actors,
  isLoading,
  isError,
  onRetry,
  page,
  totalPages,
  onPageChange,
  sortBy,
  sortOrder,
  onSort,
}: ActorListProps) {
  const navigate = useNavigate();

  const columns: Column<Actor>[] = [
    {
      key: 'pseudonyms',
      header: 'Pseudonym',
      sortable: true,
      render: (actor) => (
        <div>
          <p className="text-sm font-medium text-gray-200">
            {actor.pseudonyms[0]}
          </p>
          {actor.pseudonyms.length > 1 && (
            <p className="text-xs text-gray-500">
              +{actor.pseudonyms.length - 1} aliases
            </p>
          )}
        </div>
      ),
    },
    {
      key: 'risk_score',
      header: 'Risk Score',
      sortable: true,
      width: '100px',
      render: (actor) => (
        <span
          className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${riskBadge(actor.risk_score)}`}
        >
          {actor.risk_score}
        </span>
      ),
    },
    {
      key: 'source_url',
      header: 'Source',
      width: '180px',
      render: (actor) => {
        const url = actor.source_url || actor.urls?.[0] || actor.recent_activity?.find((a) => a.url)?.url;
        if (!url) {
          return <span className="text-xs text-gray-600">No URL</span>;
        }
        return (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-cyan-400 hover:text-cyan-300 underline truncate block max-w-[160px]"
            title={url}
            onClick={(e) => e.stopPropagation()}
          >
            {url.length > 35 ? url.slice(0, 32) + '...' : url}
          </a>
        );
      },
    },
    {
      key: 'active_platforms',
      header: 'Platforms',
      hideOnMobile: true,
      render: (actor) => (
        <div className="flex flex-wrap gap-1">
          {actor.active_platforms.map((p) => (
            <span
              key={p}
              className="rounded bg-dark-border px-1.5 py-0.5 text-xs text-gray-400"
            >
              {p}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: 'first_seen',
      header: 'First Seen',
      sortable: true,
      width: '100px',
      hideOnMobile: true,
      render: (actor) => (
        <span className="text-xs text-gray-400">
          {formatDate(actor.first_seen)}
        </span>
      ),
    },
    {
      key: 'last_seen',
      header: 'Last Seen',
      sortable: true,
      width: '100px',
      hideOnMobile: true,
      render: (actor) => (
        <span className="text-xs text-gray-400">
          {formatDate(actor.last_seen)}
        </span>
      ),
    },
    {
      key: 'total_posts',
      header: 'Posts',
      sortable: true,
      width: '60px',
      render: (actor) => (
        <span className="text-sm text-gray-300">
          {actor.total_posts.toLocaleString()}
        </span>
      ),
    },
    {
      key: 'top_categories',
      header: 'Top Categories',
      hideOnMobile: true,
      render: (actor) => (
        <span className="text-xs text-gray-400 capitalize">
          {actor.top_categories.slice(0, 2).join(', ')}
        </span>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={actors || []}
      keyExtractor={(a) => a.id}
      isLoading={isLoading}
      isError={isError}
      onRetry={onRetry}
      page={page}
      totalPages={totalPages}
      onPageChange={onPageChange}
      onRowClick={(actor) => navigate(`/actors/${actor.id}`)}
      sortBy={sortBy}
      sortOrder={sortOrder}
      onSort={onSort}
      emptyTitle="No actors tracked"
      emptyMessage="Threat actor profiles will appear here as content is crawled and analyzed."
    />
  );
}
