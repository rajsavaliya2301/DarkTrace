import DataTable, { type Column } from '../common/DataTable';
import { formatDate, formatDateRelative } from '../../utils/formatters';
import type { CrawlTarget } from '../../types';
import { cn } from '../../utils/cn';

interface TargetListProps {
  targets: CrawlTarget[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
  onTriggerCrawl: (targetId: string) => void;
}

const statusConfig: Record<
  string,
  { label: string; className: string }
> = {
  active: {
    label: 'Active',
    className: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  },
  paused: {
    label: 'Paused',
    className: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  },
  pending_verification: {
    label: 'Pending',
    className: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  },
  error: {
    label: 'Error',
    className: 'bg-red-500/20 text-red-400 border-red-500/30',
  },
};

const columns: Column<CrawlTarget>[] = [
  {
    key: 'site_name',
    header: 'Site',
    render: (target) => (
      <div>
        <p className="text-sm font-medium text-gray-200">{target.site_name}</p>
        <p className="text-xs text-gray-500 font-mono truncate max-w-[200px]">
          {target.url}
        </p>
      </div>
    ),
  },
  {
    key: 'source_type',
    header: 'Type',
    width: '80px',
    hideOnMobile: true,
    render: (target) => (
      <span className="text-xs uppercase text-gray-500">
        {target.source_type}
      </span>
    ),
  },
  {
    key: 'status',
    header: 'Status',
    width: '100px',
    render: (target) => {
      const config = statusConfig[target.status] || statusConfig.error;
      return (
        <span
          className={cn(
            'inline-block rounded-full border px-2 py-0.5 text-xs font-medium',
            config.className
          )}
        >
          {config.label}
        </span>
      );
    },
  },
  {
    key: 'crawl_frequency',
    header: 'Frequency',
    width: '100px',
    hideOnMobile: true,
    render: (target) => (
      <span className="text-xs text-gray-400">
        {target.crawl_frequency
          .replace('every_', 'Every ')
          .replace('_', ' ')
          .replace('weekly', 'Weekly')}
      </span>
    ),
  },
  {
    key: 'last_crawled',
    header: 'Last Crawled',
    width: '120px',
    render: (target) => (
      <div>
        <p className="text-xs text-gray-400">
          {target.last_crawled
            ? formatDateRelative(target.last_crawled)
            : 'Never'}
        </p>
        {target.last_status && (
          <span
            className={cn(
              'text-xs',
              target.last_status === 'success'
                ? 'text-emerald-400'
                : 'text-red-400'
            )}
          >
            {target.last_status}
          </span>
        )}
      </div>
    ),
  },
  {
    key: 'pages_crawled',
    header: 'Pages',
    width: '70px',
    hideOnMobile: true,
    render: (target) => (
      <span className="text-sm text-gray-300">
        {target.pages_crawled.toLocaleString()}
      </span>
    ),
  },
  {
    key: 'actions',
    header: '',
    width: '80px',
    render: (target) => (
      <button
        onClick={(e) => {
          e.stopPropagation();
        }}
        className="rounded bg-blue-600/20 px-2 py-1 text-xs text-blue-400 hover:bg-blue-600/30"
      >
        Crawl Now
      </button>
    ),
  },
];

export default function TargetList({
  targets,
  isLoading,
  isError,
  onRetry,
}: TargetListProps) {
  return (
    <DataTable
      columns={columns}
      data={targets || []}
      keyExtractor={(t) => t.id}
      isLoading={isLoading}
      isError={isError}
      onRetry={onRetry}
      emptyTitle="No crawl targets"
      emptyMessage="Add your first crawl target to start monitoring dark web sources."
    />
  );
}
