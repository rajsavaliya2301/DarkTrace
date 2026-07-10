import { Globe } from 'lucide-react';
import type { DashboardSummary } from '../../types';
import LoadingSpinner from '../common/LoadingSpinner';
import EmptyState from '../common/EmptyState';

interface SourceRankingProps {
  categories: DashboardSummary['top_categories'] | undefined;
  isLoading: boolean;
  isError: boolean;
}

export default function SourceRanking({
  categories,
  isLoading,
  isError,
}: SourceRankingProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-dark-border bg-dark-card p-5">
        <div className="animate-pulse space-y-4">
          <div className="h-5 w-40 rounded bg-dark-border" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="h-8 w-8 rounded bg-dark-border" />
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
        <p className="text-sm text-red-400">Failed to load source ranking</p>
      </div>
    );
  }

  if (!categories || categories.length === 0) {
    return (
      <div className="rounded-xl border border-dark-border bg-dark-card p-5">
        <EmptyState title="No categories" message="No threat category data available." />
      </div>
    );
  }

  const maxCount = Math.max(...categories.map((c) => c.count));

  return (
    <div className="rounded-xl border border-dark-border bg-dark-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <Globe className="h-5 w-5 text-blue-400" />
        <h3 className="text-sm font-semibold text-gray-200">
          Threat Categories
        </h3>
      </div>
      <div className="space-y-3">
        {categories.map((cat) => (
          <div key={cat.category} className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-300 capitalize">
                {cat.category.replace(/_/g, ' ')}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">{cat.count}</span>
                <span
                  className={`text-xs font-medium ${
                    cat.trend.startsWith('+')
                      ? 'text-red-400'
                      : cat.trend.startsWith('-')
                        ? 'text-emerald-400'
                        : 'text-gray-500'
                  }`}
                >
                  {cat.trend}
                </span>
              </div>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-dark-border">
              <div
                className="h-full rounded-full bg-blue-500 transition-all duration-500"
                style={{
                  width: `${(cat.count / maxCount) * 100}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
