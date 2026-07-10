import DataTable, { type Column } from '../common/DataTable';
import { formatDate } from '../../utils/formatters';
import { cn } from '../../utils/cn';
import type { AuditLogEntry } from '../../types';

interface AuditLogViewerProps {
  logs: AuditLogEntry[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

const actionColors: Record<string, string> = {
  login: 'text-emerald-400',
  logout: 'text-gray-400',
  alert_update: 'text-blue-400',
  alert_bulk_update: 'text-blue-400',
  report_generated: 'text-purple-400',
  report_downloaded: 'text-purple-400',
  target_added: 'text-cyan-400',
  target_updated: 'text-cyan-400',
  target_deleted: 'text-red-400',
  watchlist_created: 'text-amber-400',
  watchlist_updated: 'text-amber-400',
  watchlist_deleted: 'text-red-400',
  user_created: 'text-emerald-400',
  user_updated: 'text-amber-400',
  user_deleted: 'text-red-400',
};

export default function AuditLogViewer({
  logs,
  isLoading,
  isError,
  onRetry,
  page,
  totalPages,
  onPageChange,
}: AuditLogViewerProps) {
  const columns: Column<AuditLogEntry>[] = [
    {
      key: 'timestamp',
      header: 'Timestamp',
      width: '140px',
      render: (log) => (
        <span className="text-xs text-gray-400">
          {formatDate(log.timestamp)}
        </span>
      ),
    },
    {
      key: 'user_name',
      header: 'User',
      width: '140px',
      render: (log) => (
        <span className="text-sm text-gray-200">{log.user_name}</span>
      ),
    },
    {
      key: 'action',
      header: 'Action',
      render: (log) => (
        <span
          className={cn(
            'text-sm capitalize',
            actionColors[log.action] || 'text-gray-400'
          )}
        >
          {log.action.replace(/_/g, ' ')}
        </span>
      ),
    },
    {
      key: 'resource_type',
      header: 'Resource',
      width: '100px',
      hideOnMobile: true,
      render: (log) => (
        <span className="text-xs text-gray-400 capitalize">
          {log.resource_type.replace(/_/g, ' ')}
        </span>
      ),
    },
    {
      key: 'details',
      header: 'Details',
      hideOnMobile: true,
      render: (log) => (
        <span className="text-xs text-gray-400 truncate max-w-[200px] block">
          {typeof log.details === 'object' ? JSON.stringify(log.details) : log.details}
        </span>
      ),
    },
    {
      key: 'ip_address',
      header: 'IP',
      width: '100px',
      hideOnMobile: true,
      render: (log) => (
        <span className="text-xs font-mono text-gray-500">
          {log.ip_address}
        </span>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={logs || []}
      keyExtractor={(l) => l.id}
      isLoading={isLoading}
      isError={isError}
      onRetry={onRetry}
      page={page}
      totalPages={totalPages}
      onPageChange={onPageChange}
      emptyTitle="No audit logs"
      emptyMessage="Audit logs will appear here as users perform actions."
    />
  );
}
