import { useState, useCallback } from 'react';
import {
  ChevronDown,
  ChevronUp,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

export interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
  hideOnMobile?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  isLoading?: boolean;
  isError?: boolean;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyMessage?: string;
  emptyAction?: { label: string; onClick: () => void };
  page?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  onRowClick?: (item: T) => void;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (key: string) => void;
  selectable?: boolean;
  selectedIds?: Set<string>;
  onSelectionChange?: (ids: Set<string>) => void;
  className?: string;
}

export default function DataTable<T>({
  columns,
  data,
  keyExtractor,
  isLoading,
  isError,
  onRetry,
  emptyTitle,
  emptyMessage,
  emptyAction,
  page,
  totalPages,
  onPageChange,
  onRowClick,
  sortBy,
  sortOrder,
  onSort,
  selectable,
  selectedIds,
  onSelectionChange,
  className,
}: DataTableProps<T>) {
  const [localSelected, setLocalSelected] = useState<Set<string>>(new Set());
  const effectiveSelected = selectedIds ?? localSelected;

  const handleSelectAll = useCallback(() => {
    if (effectiveSelected.size === data.length) {
      const newSet = new Set<string>();
      if (onSelectionChange) onSelectionChange(newSet);
      setLocalSelected(newSet);
    } else {
      const newSet = new Set(data.map((item) => keyExtractor(item)));
      if (onSelectionChange) onSelectionChange(newSet);
      setLocalSelected(newSet);
    }
  }, [data, effectiveSelected.size, keyExtractor, onSelectionChange]);

  const handleSelect = useCallback(
    (id: string) => {
      const newSet = new Set(effectiveSelected);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      if (onSelectionChange) onSelectionChange(newSet);
      setLocalSelected(newSet);
    },
    [effectiveSelected, onSelectionChange]
  );

  const handleSort = (key: string) => {
    if (onSort) onSort(key);
  };

  const renderSortIcon = (key: string) => {
    if (sortBy !== key) return <ChevronsUpDown className="h-3 w-3 text-gray-600" />;
    return sortOrder === 'asc' ? (
      <ChevronUp className="h-3 w-3 text-blue-400" />
    ) : (
      <ChevronDown className="h-3 w-3 text-blue-400" />
    );
  };

  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center py-16', className)}>
        <LoadingSpinner size="lg" label="Loading data..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className={cn('py-8', className)}>
        <div className="flex flex-col items-center gap-4 rounded-lg border border-red-500/20 bg-red-500/5 p-8 text-center">
          <p className="text-red-400">Failed to load data.</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="rounded-md bg-red-500/10 px-4 py-2 text-sm text-red-400 hover:bg-red-500/20"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        message={emptyMessage}
        action={emptyAction}
      />
    );
  }

  return (
    <div className={cn('overflow-x-auto rounded-lg border border-dark-border', className)}>
      <table className="min-w-full divide-y divide-dark-border">
        <thead className="bg-dark-surface">
          <tr>
            {selectable && (
              <th className="w-10 px-4 py-3">
                <input
                  type="checkbox"
                  checked={data.length > 0 && effectiveSelected.size === data.length}
                  onChange={handleSelectAll}
                  className="rounded border-dark-border bg-dark-card text-blue-600 focus:ring-blue-500"
                  aria-label="Select all rows"
                />
              </th>
            )}
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400',
                  col.sortable && 'cursor-pointer select-none hover:text-gray-200',
                  col.hideOnMobile && 'hidden md:table-cell'
                )}
                style={col.width ? { width: col.width } : undefined}
                onClick={() => col.sortable && handleSort(col.key)}
                aria-sort={
                  sortBy === col.key
                    ? sortOrder === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : undefined
                }
              >
                <div className="flex items-center gap-1">
                  {col.header}
                  {col.sortable && renderSortIcon(col.key)}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-dark-border">
          {data.map((item) => {
            const id = keyExtractor(item);
            return (
              <tr
                key={id}
                className={cn(
                  'transition-colors hover:bg-dark-surface/50',
                  onRowClick && 'cursor-pointer'
                )}
                onClick={() => onRowClick?.(item)}
              >
                {selectable && (
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={effectiveSelected.has(id)}
                      onChange={() => handleSelect(id)}
                      className="rounded border-dark-border bg-dark-card text-blue-600 focus:ring-blue-500"
                      aria-label={`Select row ${id}`}
                    />
                  </td>
                )}
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn(
                      'whitespace-nowrap px-4 py-3 text-sm text-gray-300',
                      col.hideOnMobile && 'hidden md:table-cell'
                    )}
                  >
                    {col.render(item)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>

      {totalPages && totalPages > 1 && page && onPageChange && (
        <div className="flex items-center justify-between border-t border-dark-border px-4 py-3">
          <p className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="rounded p-1 text-gray-400 hover:text-gray-200 disabled:opacity-50"
              aria-label="Previous page"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="rounded p-1 text-gray-400 hover:text-gray-200 disabled:opacity-50"
              aria-label="Next page"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
