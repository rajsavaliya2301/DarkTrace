import DataTable, { type Column } from '../common/DataTable';
import { formatDate, formatDuration } from '../../utils/formatters';
import type { CrawlJob } from '../../types';
import { cn } from '../../utils/cn';

interface JobListProps {
  jobs: CrawlJob[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

const jobStatusConfig: Record<
  string,
  { label: string; className: string }
> = {
  queued: {
    label: 'Queued',
    className: 'bg-gray-500/20 text-gray-400',
  },
  in_progress: {
    label: 'Running',
    className: 'bg-blue-500/20 text-blue-400',
  },
  completed: {
    label: 'Completed',
    className: 'bg-emerald-500/20 text-emerald-400',
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-500/20 text-red-400',
  },
};

const columns: Column<CrawlJob>[] = [
  {
    key: 'target_url',
    header: 'Target',
    render: (job) => (
      <span className="text-sm font-mono text-gray-300 truncate max-w-[250px] block">
        {job.target_url}
      </span>
    ),
  },
  {
    key: 'status',
    header: 'Status',
    width: '100px',
    render: (job) => {
      const config = jobStatusConfig[job.status] || jobStatusConfig.queued;
      return (
        <span
          className={cn(
            'inline-block rounded-full px-2 py-0.5 text-xs font-medium',
            config.className
          )}
        >
          {config.label}
        </span>
      );
    },
  },
  {
    key: 'pages',
    header: 'Progress',
    width: '140px',
    render: (job) => (
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 rounded-full bg-dark-border overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full transition-all',
              job.status === 'completed'
                ? 'bg-emerald-500'
                : job.status === 'failed'
                  ? 'bg-red-500'
                  : 'bg-blue-500'
            )}
            style={{
              width:
                job.pages_total > 0
                  ? `${(job.pages_fetched / job.pages_total) * 100}%`
                  : job.status === 'in_progress'
                    ? '30%'
                    : '0%',
            }}
          />
        </div>
        <span className="text-xs text-gray-500 min-w-[60px]">
          {job.pages_fetched}/{job.pages_total || '?'}
        </span>
      </div>
    ),
  },
  {
    key: 'errors',
    header: 'Errors',
    width: '60px',
    hideOnMobile: true,
    render: (job) => (
      <span
        className={cn(
          'text-sm',
          job.errors > 0 ? 'text-red-400' : 'text-gray-500'
        )}
      >
        {job.errors}
      </span>
    ),
  },
  {
    key: 'duration',
    header: 'Duration',
    width: '80px',
    hideOnMobile: true,
    render: (job) => (
      <span className="text-xs text-gray-400">
        {formatDuration(job.started_at, job.completed_at)}
      </span>
    ),
  },
  {
    key: 'started_at',
    header: 'Started',
    width: '120px',
    hideOnMobile: true,
    render: (job) => (
      <span className="text-xs text-gray-400">
        {formatDate(job.started_at)}
      </span>
    ),
  },
];

export default function JobList({
  jobs,
  isLoading,
  isError,
  onRetry,
  page,
  totalPages,
  onPageChange,
}: JobListProps) {
  return (
    <DataTable
      columns={columns}
      data={jobs || []}
      keyExtractor={(j) => j.id}
      isLoading={isLoading}
      isError={isError}
      onRetry={onRetry}
      page={page}
      totalPages={totalPages}
      onPageChange={onPageChange}
      emptyTitle="No crawl jobs"
      emptyMessage="Crawl jobs will appear here once targets are crawled."
    />
  );
}
