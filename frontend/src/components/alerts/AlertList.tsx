import { useNavigate } from 'react-router-dom';
import DataTable, { type Column } from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import type { Alert } from '../../types';
import type { SeverityLevel } from '../../utils/constants';
import { formatDateRelative, capitalize } from '../../utils/formatters';

interface AlertListProps {
  alerts: Alert[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (key: string) => void;
  selectable?: boolean;
  selectedIds?: Set<string>;
  onSelectionChange?: (ids: Set<string>) => void;
}

export default function AlertList({
  alerts,
  isLoading,
  isError,
  onRetry,
  page,
  totalPages,
  onPageChange,
  sortBy,
  sortOrder,
  onSort,
  selectable,
  selectedIds,
  onSelectionChange,
}: AlertListProps) {
  const navigate = useNavigate();

  const columns: Column<Alert>[] = [
    {
      key: 'created_at',
      header: 'Time',
      sortable: true,
      width: '140px',
      render: (alert) => (
        <span className="text-xs text-gray-400">
          {formatDateRelative(alert.created_at)}
        </span>
      ),
    },
    {
      key: 'severity',
      header: 'Severity',
      sortable: true,
      width: '100px',
      render: (alert) => (
        <StatusBadge severity={alert.severity as SeverityLevel} />
      ),
    },
    {
      key: 'title',
      header: 'Title',
      sortable: true,
      render: (alert) => (
        <div className="min-w-0 max-w-md">
          <p className="text-sm font-medium text-gray-200 truncate">
            {alert.title}
          </p>
          {alert.actor_pseudonym && (
            <p className="text-xs text-purple-400">@{alert.actor_pseudonym}</p>
          )}
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      sortable: true,
      hideOnMobile: true,
      render: (alert) => (
        <span className="text-xs text-gray-400 capitalize">
          {alert.category.replace(/_/g, ' ')}
        </span>
      ),
    },
    {
      key: 'source_type',
      header: 'Source',
      sortable: true,
      width: '80px',
      hideOnMobile: true,
      render: (alert) => (
        <span className="text-xs uppercase text-gray-500">
          {alert.source_type}
        </span>
      ),
    },
    {
      key: 'source_url',
      header: 'URL',
      width: '160px',
      hideOnMobile: true,
      render: (alert) => {
        if (!alert.source_url) {
          return <span className="text-xs text-gray-600">—</span>;
        }
        return (
          <a
            href={alert.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-cyan-400 hover:text-cyan-300 underline truncate block max-w-[140px]"
            title={alert.source_url}
            onClick={(e) => e.stopPropagation()}
          >
            {alert.source_url.length > 30
              ? alert.source_url.slice(0, 27) + '...'
              : alert.source_url}
          </a>
        );
      },
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      width: '120px',
      render: (alert) => (
        <span className="text-xs text-gray-400 capitalize">
          {alert.status.replace(/_/g, ' ')}
        </span>
      ),
    },
    {
      key: 'score',
      header: 'Score',
      sortable: true,
      width: '70px',
      render: (alert) => (
        <span className="font-mono text-sm font-bold text-gray-300">
          {alert.score}
        </span>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={alerts || []}
      keyExtractor={(a) => a.id}
      isLoading={isLoading}
      isError={isError}
      onRetry={onRetry}
      page={page}
      totalPages={totalPages}
      onPageChange={onPageChange}
      onRowClick={(alert) => navigate(`/alerts/${alert.id}`)}
      sortBy={sortBy}
      sortOrder={sortOrder}
      onSort={onSort}
      selectable={selectable}
      selectedIds={selectedIds}
      onSelectionChange={onSelectionChange}
    />
  );
}
