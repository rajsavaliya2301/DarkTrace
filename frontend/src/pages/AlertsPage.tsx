import { useState, useCallback } from 'react';
import PageHeader from '../components/common/PageHeader';
import AlertFilters, {
  type AlertFilterValues,
} from '../components/alerts/AlertFilters';
import AlertList from '../components/alerts/AlertList';
import AlertBulkActions from '../components/alerts/AlertBulkActions';
import { useAlerts } from '../hooks/useAlerts';
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates';
import { toast } from 'react-hot-toast';

export default function AlertsPage() {
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState<AlertFilterValues>({
    severity: '',
    status: '',
    category: '',
    source_type: '',
    q: '',
  });

  const queryParams = {
    page,
    per_page: 25,
    severity: filters.severity || undefined,
    status: filters.status || undefined,
    category: filters.category || undefined,
    source_type: filters.source_type || undefined,
    q: filters.q || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  };

  const { data, isLoading, isError, refetch } = useAlerts(queryParams);

  // Real-time alert updates
  useRealtimeUpdates({
    channels: 'alert',
    onAlert: (event) => {
      // Show toast notification for new alerts
      const severity = (event.severity as string) || 'medium';
      const title = (event.title as string) || 'New Alert';
      const severityColors: Record<string, string> = {
        critical: '#ef4444',
        high: '#f59e0b',
        medium: '#06b6d4',
        low: '#10b981',
      };
      toast(
        `🚨 ${title}`,
        {
          duration: 5000,
          style: {
            background: '#1f2937',
            color: '#f9fafb',
            borderLeft: `4px solid ${severityColors[severity] || '#6b7280'}`,
          },
        }
      );
      // Auto-refresh the list when on first page
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

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    setSelectedIds(new Set());
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Alerts"
        subtitle={`${data?.pagination?.total?.toLocaleString() || 0} total alerts`}
      />

      <AlertFilters
        filters={filters}
        onFilterChange={(f) => {
          setFilters(f);
          setPage(1);
          setSelectedIds(new Set());
        }}
      />

      {selectedIds.size > 0 && (
        <AlertBulkActions
          selectedIds={selectedIds}
          onClear={() => setSelectedIds(new Set())}
        />
      )}

      <AlertList
        alerts={data?.data}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.pagination?.total_pages || 1}
        onPageChange={handlePageChange}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSort={handleSort}
        selectable
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
      />
    </div>
  );
}
