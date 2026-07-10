import { TrendingUp, ArrowUp, ArrowDown } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { TrendingData } from '../../types';
import LoadingSpinner from '../common/LoadingSpinner';
import EmptyState from '../common/EmptyState';

interface TrendingPanelProps {
  data: TrendingData | undefined;
  isLoading: boolean;
  isError: boolean;
}

function TrendIndicator({ trend }: { trend: string }) {
  const isUp = trend.startsWith('+');
  const isDown = trend.startsWith('-');
  const color = isUp
    ? 'text-red-400'
    : isDown
      ? 'text-emerald-400'
      : 'text-gray-400';

  return (
    <span className={cn('inline-flex items-center gap-0.5 text-xs font-medium', color)}>
      {isUp && <ArrowUp className="h-3 w-3" />}
      {isDown && <ArrowDown className="h-3 w-3" />}
      {trend}
    </span>
  );
}

export default function TrendingPanel({
  data,
  isLoading,
  isError,
}: TrendingPanelProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-dark-border bg-dark-card p-5">
        <div className="animate-pulse space-y-4">
          <div className="h-5 w-40 rounded bg-dark-border" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-10 rounded bg-dark-border" />
          ))}
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5">
        <p className="text-sm text-red-400">Failed to load trending data</p>
      </div>
    );
  }

  if (
    !data.most_mentioned_products ||
    data.most_mentioned_products.length === 0
  ) {
    return (
      <div className="rounded-xl border border-dark-border bg-dark-card p-5">
        <EmptyState title="No trending data" message="No trending data available yet." />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-dark-border bg-dark-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-blue-400" />
        <h3 className="text-sm font-semibold text-gray-200">
          Trending Products & Services
        </h3>
      </div>

      <div className="space-y-3">
        {data.most_mentioned_products.slice(0, 10).map((item, index) => (
          <div
            key={item.product}
            className="flex items-center justify-between rounded-lg bg-dark-surface px-3 py-2.5"
          >
            <div className="flex items-center gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded bg-dark-border text-xs font-bold text-gray-500">
                {index + 1}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-200">
                  {item.product}
                </p>
                <p className="text-xs text-gray-500">
                  {item.mentions} mentions
                </p>
              </div>
            </div>
            <TrendIndicator trend={item.trend} />
          </div>
        ))}
      </div>

      {data.most_active_marketplaces &&
        data.most_active_marketplaces.length > 0 && (
          <div className="mt-6">
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Most Active Marketplaces
            </h4>
            <div className="space-y-2">
              {data.most_active_marketplaces.slice(0, 5).map((item) => (
                <div
                  key={item.site}
                  className="flex items-center justify-between"
                >
                  <span className="text-sm text-gray-300">{item.site}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400">
                      {item.posts} posts
                    </span>
                    <TrendIndicator trend={item.trend} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
    </div>
  );
}
