import { Clock, AlertTriangle, CheckCircle, Activity } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { RecentAlert } from '../../types';
import { formatDateRelative } from '../../utils/formatters';
import StatusBadge from '../common/StatusBadge';
import type { SeverityLevel } from '../../utils/constants';
import LoadingSpinner from '../common/LoadingSpinner';
import EmptyState from '../common/EmptyState';

interface ActivityTimelineProps {
  alerts: RecentAlert[] | undefined;
  isLoading: boolean;
  isError: boolean;
}

export default function ActivityTimeline({
  alerts,
  isLoading,
  isError,
}: ActivityTimelineProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-dark-border bg-dark-card p-5">
        <div className="animate-pulse space-y-4">
          <div className="h-5 w-36 rounded bg-dark-border" />
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-dark-border" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-3/4 rounded bg-dark-border" />
                <div className="h-3 w-1/4 rounded bg-dark-border" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5">
        <p className="text-sm text-red-400">Failed to load activity</p>
      </div>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div className="rounded-xl border border-dark-border bg-dark-card p-5">
        <EmptyState
          title="No recent activity"
          message="No recent alert activity to display."
          icon={<Activity className="h-10 w-10" />}
        />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-dark-border bg-dark-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <Clock className="h-5 w-5 text-blue-400" />
        <h3 className="text-sm font-semibold text-gray-200">
          Recent Activity
        </h3>
      </div>

      <div className="relative space-y-0">
        {alerts.slice(0, 8).map((alert, index) => (
          <div key={alert.id} className="relative flex gap-4 pb-5">
            {/* Timeline line */}
            {index < alerts.length - 1 && index < 7 && (
              <div className="absolute left-4 top-8 bottom-0 w-px bg-dark-border" />
            )}

            {/* Icon */}
            <div
              className={cn(
                'relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
                alert.severity === 'critical'
                  ? 'bg-red-500/20 text-red-400'
                  : alert.severity === 'high'
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'bg-blue-500/20 text-blue-400'
              )}
            >
              {alert.severity === 'critical' || alert.severity === 'high' ? (
                <AlertTriangle className="h-4 w-4" />
              ) : (
                <CheckCircle className="h-4 w-4" />
              )}
            </div>

            {/* Content */}
            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-gray-200 line-clamp-2">
                  {alert.title}
                </p>
                <StatusBadge severity={alert.severity as SeverityLevel} />
              </div>
              <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                <span>{formatDateRelative(alert.created_at)}</span>
                <span>·</span>
                <span className="uppercase">{alert.source_type}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
