import { Search, X } from 'lucide-react';
import { cn } from '../../utils/cn';
import {
  ALERT_STATUSES,
  ALERT_CATEGORIES,
  SOURCE_TYPES,
  SEVERITY_LEVELS,
  type SeverityLevel,
  type AlertStatus,
  type AlertCategory,
  type SourceType,
} from '../../utils/constants';

export interface AlertFilterValues {
  severity: string;
  status: string;
  category: string;
  source_type: string;
  q: string;
}

interface AlertFiltersProps {
  filters: AlertFilterValues;
  onFilterChange: (filters: AlertFilterValues) => void;
  className?: string;
}

export default function AlertFilters({
  filters,
  onFilterChange,
  className,
}: AlertFiltersProps) {
  const updateFilter = (key: keyof AlertFilterValues, value: string) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const clearFilters = () => {
    onFilterChange({
      severity: '',
      status: '',
      category: '',
      source_type: '',
      q: '',
    });
  };

  const hasActiveFilters =
    filters.severity ||
    filters.status ||
    filters.category ||
    filters.source_type ||
    filters.q;

  const selectClass =
    'rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-300 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500';

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search alerts..."
            value={filters.q}
            onChange={(e) => updateFilter('q', e.target.value)}
            className="w-full rounded-lg border border-dark-border bg-dark-surface py-2 pl-10 pr-3 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <select
          value={filters.severity}
          onChange={(e) => updateFilter('severity', e.target.value)}
          className={selectClass}
          aria-label="Filter by severity"
        >
          <option value="">All Severities</option>
          {SEVERITY_LEVELS.map((s) => (
            <option key={s} value={s}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>

        <select
          value={filters.status}
          onChange={(e) => updateFilter('status', e.target.value)}
          className={selectClass}
          aria-label="Filter by status"
        >
          <option value="">All Statuses</option>
          {ALERT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s
                .split('_')
                .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(' ')}
            </option>
          ))}
        </select>

        <select
          value={filters.category}
          onChange={(e) => updateFilter('category', e.target.value)}
          className={selectClass}
          aria-label="Filter by category"
        >
          <option value="">All Categories</option>
          {ALERT_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c
                .split('_')
                .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(' ')}
            </option>
          ))}
        </select>

        <select
          value={filters.source_type}
          onChange={(e) => updateFilter('source_type', e.target.value)}
          className={selectClass}
          aria-label="Filter by source type"
        >
          <option value="">All Sources</option>
          {SOURCE_TYPES.map((s) => (
            <option key={s} value={s}>
              {s === 'onion' ? 'Tor (.onion)' : s === 'i2p' ? 'I2P' : 'Surface Web'}
            </option>
          ))}
        </select>

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="inline-flex items-center gap-1 rounded-lg px-3 py-2 text-sm text-gray-400 hover:text-gray-200"
          >
            <X className="h-4 w-4" />
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
