import { formatDateRelative } from '../../utils/formatters';
import StatusBadge from '../common/StatusBadge';
import { cn } from '../../utils/cn';
import type { Alert } from '../../types';
import type { SeverityLevel } from '../../utils/constants';

interface AlertCardProps {
  alert: Alert;
  onSelect?: (id: string) => void;
  isSelected?: boolean;
}

export default function AlertCard({ alert, onSelect, isSelected }: AlertCardProps) {
  return (
    <div
      className={cn(
        'cursor-pointer rounded-lg border bg-dark-card p-4 transition-colors hover:bg-dark-surface',
        isSelected
          ? 'border-blue-500/50 ring-1 ring-blue-500/20'
          : 'border-dark-border'
      )}
      onClick={() => onSelect?.(alert.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect?.(alert.id);
        }
      }}
      aria-label={`Alert: ${alert.title}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <StatusBadge severity={alert.severity as SeverityLevel} />
            <span className="rounded bg-dark-border px-2 py-0.5 text-xs text-gray-400 uppercase">
              {alert.category.replace(/_/g, ' ')}
            </span>
            <span className="text-xs text-gray-500">{alert.source_type.toUpperCase()}</span>
          </div>
          <h4 className="mt-2 text-sm font-medium text-gray-100 line-clamp-2">
            {alert.title}
          </h4>
          {alert.summary && (
            <p className="mt-1 text-xs text-gray-400 line-clamp-2">
              {alert.summary}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="text-xs font-mono font-bold text-gray-400">
            {alert.score}
          </span>
          <span className="text-xs text-gray-500">
            {formatDateRelative(alert.created_at)}
          </span>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {alert.matched_keywords.slice(0, 3).map((kw) => (
          <span
            key={kw}
            className="rounded bg-blue-500/10 px-2 py-0.5 text-xs text-blue-400"
          >
            {kw}
          </span>
        ))}
        {alert.matched_keywords.length > 3 && (
          <span className="text-xs text-gray-500">
            +{alert.matched_keywords.length - 3} more
          </span>
        )}
        {alert.actor_pseudonym && (
          <span className="text-xs text-purple-400">
            @{alert.actor_pseudonym}
          </span>
        )}
      </div>
    </div>
  );
}
