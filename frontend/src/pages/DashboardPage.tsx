import PageHeader from '../components/common/PageHeader';
import SummaryCards from '../components/dashboard/SummaryCards';
import SeverityChart from '../components/dashboard/SeverityChart';
import AlertTrendChart from '../components/dashboard/AlertTrendChart';
import TrendingPanel from '../components/dashboard/TrendingPanel';
import ActivityTimeline from '../components/dashboard/ActivityTimeline';
import SourceRanking from '../components/dashboard/SourceRanking';
import { useDashboardSummary, useTrendingData } from '../hooks/useDashboard';
import { useAlertStats } from '../hooks/useAlerts';
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates';
import { toast } from 'react-hot-toast';

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading, isError: summaryError, refetch: refetchSummary } =
    useDashboardSummary();
  const {
    data: trending,
    isLoading: trendingLoading,
    isError: trendingError,
    refetch: refetchTrending,
  } = useTrendingData(7);
  const {
    data: stats,
    isLoading: statsLoading,
    isError: statsError,
    refetch: refetchStats,
  } = useAlertStats();

  // Real-time dashboard updates
  useRealtimeUpdates({
    channels: 'dashboard,alert',
    onDashboard: () => {
      refetchSummary();
      refetchTrending();
      refetchStats();
    },
    onAlert: () => {
      refetchSummary();
      refetchStats();
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle="Overview of threat intelligence activities"
      />

      <SummaryCards
        data={summary}
        isLoading={summaryLoading}
        isError={summaryError}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <SeverityChart
          data={stats?.by_severity}
          isLoading={statsLoading}
          isError={statsError}
        />
        <AlertTrendChart
          data={stats?.trend}
          isLoading={statsLoading}
          isError={statsError}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TrendingPanel
            data={trending}
            isLoading={trendingLoading}
            isError={trendingError}
          />
        </div>
        <ActivityTimeline
          alerts={summary?.recent_alerts}
          isLoading={summaryLoading}
          isError={summaryError}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SourceRanking
          categories={summary?.top_categories}
          isLoading={summaryLoading}
          isError={summaryError}
        />
        {trending?.language_distribution && (
          <div className="rounded-xl border border-dark-border bg-dark-card p-5">
            <h3 className="mb-4 text-sm font-semibold text-gray-200">
              Language Distribution
            </h3>
            <div className="space-y-3">
              {trending.language_distribution.map((lang) => (
                <div key={lang.language} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-300 uppercase">
                      {lang.language === 'other' ? 'Other' : lang.language}
                    </span>
                    <span className="text-gray-400">
                      {lang.percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-dark-border">
                    <div
                      className="h-full rounded-full bg-blue-500"
                      style={{ width: `${lang.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
