import { cn } from '../../utils/cn';
import {
  Bell,
  Radio,
  Users,
  TrendingUp,
  AlertTriangle,
  Activity,
} from 'lucide-react';
import type { DashboardSummary } from '../../types';
import LoadingSpinner from '../common/LoadingSpinner';

interface SummaryCardsProps {
  data: DashboardSummary | undefined;
  isLoading: boolean;
  isError: boolean;
}

export default function SummaryCards({
  data,
  isLoading,
  isError,
}: SummaryCardsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-xl border border-dark-border bg-dark-card p-5"
          >
            <div className="h-4 w-24 rounded bg-dark-border" />
            <div className="mt-3 h-8 w-16 rounded bg-dark-border" />
            <div className="mt-2 h-3 w-32 rounded bg-dark-border" />
          </div>
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-red-500/20 bg-red-500/5 p-5"
          >
            <p className="text-sm text-red-400">Failed to load</p>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: 'Active Alerts',
      value: data.active_alerts.total,
      subtext: `${data.active_alerts.critical} critical, ${data.active_alerts.high} high`,
      trend: data.active_alerts.trend,
      icon: Bell,
      color: 'text-red-400 bg-red-500/10',
      trendColor: data.active_alerts.trend.startsWith('+')
        ? 'text-red-400'
        : 'text-emerald-400',
    },
    {
      label: 'Crawler Status',
      value: data.crawler_status.active_targets,
      subtext: `${data.crawler_status.running_jobs} running, ${data.crawler_status.queued_jobs} queued`,
      trend: `${data.crawler_status.pages_today} pages today`,
      icon: Radio,
      color: 'text-blue-400 bg-blue-500/10',
      trendColor: 'text-blue-400',
    },
    {
      label: 'Tracked Actors',
      value: data.actors.total_tracked,
      subtext: `${data.actors.high_risk} high risk`,
      trend: `${data.actors.new_today} new today`,
      icon: Users,
      color: 'text-purple-400 bg-purple-500/10',
      trendColor: 'text-emerald-400',
    },
    {
      label: 'Success Rate',
      value: data.crawler_status.success_rate,
      subtext: '',
      trend: '',
      icon: Activity,
      color: 'text-emerald-400 bg-emerald-500/10',
      trendColor: 'text-emerald-400',
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-xl border border-dark-border bg-dark-card p-5 transition-colors hover:border-gray-600"
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-400">{card.label}</p>
            <div className={cn('rounded-lg p-2', card.color)}>
              <card.icon className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-gray-100">
              {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
            </span>
            {card.trend && (
              <span className={cn('text-xs font-medium', card.trendColor)}>
                {card.trend}
              </span>
            )}
          </div>
          {card.subtext && (
            <p className="mt-1 text-xs text-gray-500">{card.subtext}</p>
          )}
        </div>
      ))}
    </div>
  );
}
